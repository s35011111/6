from django.db import models
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CustomUser
from .models import Payment
from .permissions import IsRegisteredUser, IsModerator, IsOwner
from .serializers import PaymentSerializer
from .serializers import UserCreateSerializer, UserUpdateSerializer
from .serializers import UserSerializer, LimitedUserSerializer


# Create your views here.


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['list', 'retrieve'] and not self.request.user.groups.filter(name='Moderators').exists():
            return LimitedUserSerializer
        return UserSerializer
    def get_permissions(self):
        if self.action == 'create':
            permission_classes = []
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsOwner]
        elif self.action in ['list']:
            permission_classes = [IsModerator]
        elif self.action in ['retrieve']:
            permission_classes = [IsRegisteredUser | IsModerator]
        else:
            permission_classes = [IsRegisteredUser | IsModerator]
        return [permission() for permission in permission_classes]
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return CustomUser.objects.all()
        return CustomUser.objects.filter(id=user.id)
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    @action(detail=False, methods=['put', 'patch'])
    def update_me(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')
        if query:
            users = CustomUser.objects.filter(
                models.Q(email__icontains=query) |
                models.Q(username__icontains=query) |
                models.Q(city__icontains=query)
            )
            serializer = self.get_serializer(users, many=True)
            return Response(serializer.data)
        return Response([])


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = { 'course': ['exact'], 'lesson': ['exact'],  }
    search_fields = ['course__name', 'lesson__name']
    ordering_fields = ['payment_date']
    ordering = ['-payment_date']
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Payment.objects.none()
        if user.groups.filter(name='Registered Users').exists():
            return Payment.objects.filter(user=user)
        if user.groups.filter(name='Moderators').exists():
            return Payment.objects.all()
        return Payment.objects.none()
    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [IsRegisteredUser]
        elif self.action in ['list', 'retrieve']:
            permission_classes = [IsRegisteredUser | IsModerator]
        else:
            permission_classes = [IsRegisteredUser]
        return [permission() for permission in permission_classes]
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PublicRegistrationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
                'message': 'Only registration is available for unauthenticated users',
                'registration_endpoint': '/api/users/register/'
            })