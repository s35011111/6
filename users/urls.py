from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from .views import UserViewSet, SubscriptionViewSet, PaymentListView
from django.urls import path, include
from rest_framework.routers import DefaultRouter
#from .views import PaymentViewSet
from . import views

router = DefaultRouter()
#router.register(r'payments', PaymentViewSet, basename='payments')
router.register(r'users', UserViewSet, basename='users')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
urlpatterns = [
    path('', include(router.urls)),

    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('courses/create-stripe-product/',
         views.CreateStripeProductView.as_view(),
         name='create-stripe-product'),

    path('courses/create-stripe-price/',
         views.CreateStripePriceView.as_view(),
         name='create-stripe-price'),

    path('courses/create-checkout-session/',
         views.CreateCheckoutSessionView.as_view(),
         name='create-checkout-session'),

    path('stripe/webhook/',
         views.StripeWebhookView.as_view(),
         name='stripe-webhook'),
    path('payments/',PaymentListView.as_view(),name='payment-list'),
]