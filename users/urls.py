from .views import UserViewSet
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payments')

router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('payments/user/<int:user_id>/',
    PaymentViewSet.as_view({'get': 'list'}),
    name='user-payments'),
]