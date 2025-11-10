from django.db import models
from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets,  permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import CustomUser
from .serializers import UserSerializer, UserCreateSerializer, UserUpdateSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import  filters
from .models import Payment
from .serializers import PaymentSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
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
        queryset = Payment.objects.all()
        user = self.request.user
        if not user.is_staff:
            queryset = queryset.filter(user=user)
        return queryset.select_related('course', 'lesson')
