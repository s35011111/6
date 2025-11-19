from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser
from .models import Payment


class LimitedUserSerializer(serializers.ModelSerializer):


    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'city',  'user_type']
        read_only_fields = ['user_type']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'password2']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = CustomUser.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):


    class Meta:
        model = CustomUser
        fields = ['id', 'email' , 'phone', 'image', 'city', ]

        read_only_fields = ['id',  'last_login']
        extra_kwargs = {'email': {'required': True},'username': {'required': True}}

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'password2', 'phone', 'city']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = CustomUser.objects.create_user(**validated_data)
        return user

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [ 'phone', 'image', 'city']





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
        read_only_fields = ['payment_date']

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