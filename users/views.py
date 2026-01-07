from django.contrib.auth import authenticate
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, permissions
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from materials.pagination import StandardPagePagination

from .models import CustomUser, Subscription
from .models import Payment
from .permissions import IsModerator, IsOwnerOrReadOnly
from .serializers import PaymentSerializer, UserRegistrationSerializer, UserListSerializer, UserProfileSerializer, \
    SubscriptionSerializer
import requests
import json
import hmac
import hashlib
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Payment
from .serializers import PaymentSerializer, CreatePaymentSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.filter(is_active=True)


    def get_serializer_class(self):

        if self.action == 'create':
            return UserRegistrationSerializer
        elif self.action in ['list', 'retrieve']:
            return UserListSerializer
        return UserProfileSerializer

    def get_permissions(self):


        if self.action == 'create':
            permission_classes = [AllowAny]
        if self.action == 'register':
            permission_classes = [AllowAny]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):

        serializer = UserRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            user.is_active=True
            user.save()


            refresh = RefreshToken.for_user(user)

            return Response({
                'user': UserProfileSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': 'Registration successful'
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):

        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            refresh = RefreshToken.for_user(user)

            return Response({
                'user': UserProfileSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            })

        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    @action(detail=False, methods=['get', 'put', 'patch'])
    def profile(self, request):

        if request.method == 'GET':
            serializer = UserProfileSerializer(request.user)
            return Response(serializer.data)

        elif request.method in ['PUT', 'PATCH']:
            serializer = UserProfileSerializer(
                request.user,
                data=request.data,
                partial=(request.method == 'PATCH')
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return None

    @action(detail=False, methods=['post'])
    def logout(self, request):

        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({"message": "Successfully logged out"})
        except Exception:
            return Response({"message": "Logged out"}, status=status.HTTP_200_OK)



class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    pagination_class = StandardPagePagination
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)




class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    STRIPE_API_URL = "https://api.stripe.com/v1"

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def _make_stripe_request(self, method, endpoint, data=None, params=None):
        url = f"{self.STRIPE_API_URL}/{endpoint}"
        headers = {
            'Authorization': f'Bearer {settings.STRIPE_SECRET_KEY}',
            'Stripe-Version': settings.STRIPE_API_VERSION,
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        try:
            if method == 'POST':
                response = requests.post(url, headers=headers, data=data, params=params)
            elif method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('error', {}).get('message', str(e))
                except:
                    error_msg = str(e)
            else:
                error_msg = str(e)

            raise Exception(f"Stripe API error: {error_msg}")

    def _format_stripe_data(self, data_dict):
        formatted = {}
        for key, value in data_dict.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    formatted[f'{key}[{sub_key}]'] = str(sub_value)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        for sub_key, sub_value in item.items():
                            formatted[f'{key}[{i}][{sub_key}]'] = str(sub_value)
                    else:
                        formatted[f'{key}[{i}]'] = str(item)
            else:
                formatted[key] = str(value)
        return formatted

    @action(detail=False, methods=['POST'])
    def create_payment_intent(self, request):
        serializer = CreatePaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        amount = int(float(data['amount']) * 100)

        try:
            stripe_data = {
                'amount': amount,
                'currency': data['currency'].lower(),
                'metadata[user_id]': str(request.user.id),
                'description': f"Payment from {request.user.email}",
            }

            if data.get('course_id'):
                stripe_data['metadata[course_id]'] = str(data['course_id'])

            response_data = self._make_stripe_request(
                method='POST',
                endpoint='payment_intents',
                data=stripe_data
            )

            payment = Payment.objects.create(
                user=request.user,
                amount=data['amount'],
                currency=data['currency'],
                status='pending',
                stripe_payment_id=response_data['id'],
                metadata={
                    'client_secret': response_data['client_secret'],
                    'raw_response': response_data,
                }
            )

            return Response({
                'client_secret': response_data['client_secret'],
                'payment_id': str(payment.id),
                'amount': data['amount'],
                'currency': data['currency'],
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            error_msg = str(e)
            error_type = "StripeAPIError"

            if "card_error" in error_msg.lower():
                error_type = "CardError"
            elif "rate_limit" in error_msg.lower():
                error_type = "RateLimitError"
                error_msg = "Too many requests. Please try again later."
            elif "invalid_request" in error_msg.lower():
                error_type = "InvalidRequestError"

            return Response({
                'error': error_msg,
                'type': error_type,
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['POST'])
    def confirm(self, request, pk=None):
        payment = self.get_object()

        try:
            response_data = self._make_stripe_request(
                method='GET',
                endpoint=f'payment_intents/{payment.stripe_payment_id}'
            )

            if response_data['status'] == 'succeeded':
                payment.status = 'completed'
                payment.save()
                return Response({'status': 'success'})
            else:
                return Response({
                    'status': response_data['status'],
                    'client_secret': response_data.get('client_secret'),
                })

        except Exception as e:
            payment.status = 'failed'
            payment.metadata['error'] = str(e)
            payment.save()
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def _verify_stripe_signature(self, payload, sig_header):
        try:
            timestamp = sig_header.split(',')[0].split('=')[1]
            signature = sig_header.split(',')[1].split('=')[1]

            signed_payload = f"{timestamp}.{payload.decode('utf-8')}"

            expected_signature = hmac.new(
                settings.STRIPE_WEBHOOK_SECRET.encode('utf-8'),
                signed_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(signature, expected_signature)
        except:
            return False

    @csrf_exempt
    @action(detail=False, methods=['POST'], permission_classes=[])
    def webhook(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

        if not self._verify_stripe_signature(payload, sig_header):
            return HttpResponse(status=400)

        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            return HttpResponse(status=400)

        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            self._handle_payment_success(payment_intent)
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            self._handle_payment_failed(payment_intent)

        return HttpResponse(status=200)

    def _handle_payment_success(self, payment_intent):
        try:
            payment = Payment.objects.get(stripe_payment_id=payment_intent['id'])
            payment.status = 'completed'
            payment.metadata['webhook_data'] = payment_intent
            payment.save()

            if payment.course:
                self._enroll_user_in_course(payment.user, payment.course)

        except Payment.DoesNotExist:
            pass

    def _handle_payment_failed(self, payment_intent):
        try:
            payment = Payment.objects.get(stripe_payment_id=payment_intent['id'])
            payment.status = 'failed'
            payment.metadata['failure_reason'] = payment_intent.get('last_payment_error', {})
            payment.save()
        except Payment.DoesNotExist:
            pass

    def _enroll_user_in_course(self, user, course):
        from users.models import Subscription
        Subscription.objects.get_or_create(user=user, course=course)

    @action(detail=False, methods=['GET'])
    def stripe_config(self, request):
        return Response({
            'publishableKey': settings.STRIPE_PUBLISHABLE_KEY,
            'apiVersion': settings.STRIPE_API_VERSION,
        })


