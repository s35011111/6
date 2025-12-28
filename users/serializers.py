from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser
from .models import Payment


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