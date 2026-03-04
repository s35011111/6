from decimal import Decimal

from django.contrib.auth.models import Group
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from materials.models import Course
from .models import CustomUser
from .models import Payment
from .models import Subscription
from django.contrib.auth import get_user_model


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser

        fields = ['email', 'password', 'password2', 'first_name', 'last_name', 'phone', 'city']

    def validate(self, attrs):

        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = CustomUser.objects.create_user(**validated_data)
        try:
            user_group = Group.objects.get(name='user')
            user_group.add(user_group)
        except:
            user_group = []

        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser

        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'image', 'city',  'date_joined']
        read_only_fields = ['id', 'email', 'date_joined']


class UserListSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser

        fields = ['id', 'email', 'first_name', 'last_name', 'city']


class PaymentSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)
    lesson_name = serializers.CharField(source='lesson.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'user', 'user_email', 'course', 'course_name',
            'lesson', 'lesson_name', 'amount', 'payment_method',
            'payment_date'
        ]
        read_only_fields = fields

    def validate(self, data):
        course = data.get('course')
        lesson = data.get('lesson')
        if not course and not lesson:
            raise serializers.ValidationError(
                "Either course or lesson must be provided."
            )
        if course and lesson and lesson.course != course:
            raise serializers.ValidationError(
                "The selected lesson does not belong to the selected course."
            )

        return data


User = get_user_model()


class SubscriptionSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Subscription
        fields = ['id', 'user', 'user_email', 'course', 'course_name']
        read_only_fields = ['user']
        extra_kwargs = {'course': {'required': True}, }

    def validate(self, attrs):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            course = attrs.get('course')
            existing = Subscription.objects.filter(
                user=request.user,
                course=course,
            ).exists()

            if existing:
                raise serializers.ValidationError({
                    'course': 'You are already subscribed to this course.'
                })

        return attrs


class CreatePaymentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    course_id = serializers.UUIDField(required=False)
    return_url = serializers.URLField(required=False)


class CreateStripeProductSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()

    def validate_course_id(self, value):
        try:
            course = Course.objects.get(id=value)
            if course.author != self.context['request'].user:
                raise serializers.ValidationError("You are not the author of this course")
            return value
        except Course.DoesNotExist:
            raise serializers.ValidationError("Course does not exist")


class CreateStripePriceSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    currency = serializers.CharField(max_length=3, default='usd')

    def validate_course_id(self, value):
        try:
            course = Course.objects.get(id=value)
            if course.author != self.context['request'].user:
                raise serializers.ValidationError("You are not the author of this course")
            if not course.stripe_product_id:
                raise serializers.ValidationError("Course must have a Stripe product first")
            return value
        except Course.DoesNotExist:
            raise serializers.ValidationError("Course does not exist")


class CreateCheckoutSessionSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    success_url = serializers.URLField()
    cancel_url = serializers.URLField()

    def validate_course_id(self, value):
        try:
            course = Course.objects.get(id=value)
            if not course.stripe_price_id:
                raise serializers.ValidationError("This course is not available for purchase")

            return value
        except Course.DoesNotExist:
            raise serializers.ValidationError("Course does not exist")


class CheckoutSessionResponseSerializer(serializers.Serializer):
    session_id = serializers.CharField()
    url = serializers.URLField()
