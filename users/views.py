from django.contrib.auth import authenticate
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import generics, permissions, status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from materials.pagination import StandardPagePagination
from users.models import CustomUser, Subscription
from users.serializers import UserRegistrationSerializer, UserProfileSerializer, UserListSerializer, \
    SubscriptionSerializer, PaymentSerializer
from .models import Course, Payment
from .serializers import (
    CreateStripeProductSerializer,
    CreateStripePriceSerializer,
    CreateCheckoutSessionSerializer,
    CheckoutSessionResponseSerializer
)
from .service import StripeService
from celery.result import AsyncResult


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
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):

        serializer = UserRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            user.is_active = True
            user.save()

            user_group = Group.objects.get(name='user')
            user.groups.add(user_group)
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


class CreateStripeProductView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CreateStripeProductSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        course = get_object_or_404(Course, id=serializer.validated_data['course_id'])
        if course.stripe_product_id:
            return Response(
                {'error': 'Stripe product already exists for this course'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            product = StripeService.create_product(
                name=course.name,
                description=course.description,
                metadata={
                    'course_id': str(course.id),
                    'author_id': str(course.author.id)
                }
            )
            course.stripe_product_id = product.id
            course.save()
            return Response({
                'success': True,
                'product_id': product.id,
                'message': 'Stripe product created successfully'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class CreateStripePriceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CreateStripePriceSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        course = get_object_or_404(Course, id=serializer.validated_data['course_id'])
        price_cents = int(float(serializer.validated_data['price']) * 100)
        try:
            price = StripeService.create_price(
                product_id=course.stripe_product_id,
                unit_amount=price_cents,
                currency=serializer.validated_data['currency']
            )
            course.stripe_price_id = price.id
            course.price = serializer.validated_data['price']
            course.save()
            return Response({
                'success': True,
                'price_id': price.id,
                'message': 'Stripe price created successfully'
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class CreateCheckoutSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CreateCheckoutSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course = get_object_or_404(Course, id=serializer.validated_data['course_id'])
        try:
            session = StripeService.create_checkout_session(
                price_id=course.stripe_price_id,
                success_url=serializer.validated_data['success_url'],
                cancel_url=serializer.validated_data['cancel_url'],
                customer_email=request.user.email,
                metadata={
                    'course_id': str(course.id),
                    'user_id': str(request.user.id),
                    'course_name': course.name
                }
            )
            Payment.objects.create(
                user=request.user,
                course=course,
                stripe_session_id=session.id,
                amount=course.price,
            )
            response_serializer = CheckoutSessionResponseSerializer({
                'session_id': session.id,
                'url': session.url
            })
            user = self.request.user
            subscribtion = Subscription.objects.create(user=user,
                                                       course=course)
            subscribtion.save()

            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class StripeWebhookView(APIView):
    permission_classes = []
    http_method_names = ['post']

    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        try:
            from django.conf import settings
            import stripe
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            return Response({'error': 'Invalid payload'}, status=400)
        except stripe.error.SignatureVerificationError:
            return Response({'error': 'Invalid signature'}, status=400)
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            self.handle_checkout_session_completed(session)
        elif event['type'] == 'checkout.session.async_payment_failed':
            session = event['data']['object']
            self.handle_checkout_session_failed(session)
        return Response({'success': True})

    def handle_checkout_session_completed(self, session):
        try:
            purchase = Payment.objects.get(stripe_session_id=session['id'])
            purchase.status = 'completed'
            purchase.stripe_payment_intent_id = session.get('payment_intent')
            purchase.completed_at = timezone.now()
            purchase.save()
        except Exception:
            pass

    def handle_checkout_session_failed(self, session):
        try:
            purchase = Payment.objects.get(stripe_session_id=session['id'])
            purchase.status = 'failed'
            purchase.save()
        except Exception:
            pass


class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter,
                       filters.OrderingFilter]
    filterset_fields = ['course']
    search_fields = ['amount', 'payment_date']
    ordering = ['-payment_date']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Payment.objects.all().select_related('course', 'user')
        return Payment.objects.filter(user=user).select_related('course')


class SubscriptionView(generics.ListAPIView):
    serializer_class = SubscriptionSerializer
    pagination_class = StandardPagePagination
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)


class TaskStatusView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, task_id):
        task_result = AsyncResult(task_id)

        response = {
            'task_id': task_id,
            'status': task_result.status,
            'result': task_result.result if task_result.ready() else None,
            'successful': task_result.successful(),
            'failed': task_result.failed(),
        }

        return Response(response)
