from django.template.context_processors import request
from rest_framework import serializers
from .models import Course, Lesson
from .validators import  validate_youtube_only


class LessonSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)
    ##description = serializers.CharField(validators=[validate_no_links] )
    video_link=serializers.CharField(validators=[validate_youtube_only] ,required=False)

    class Meta:
        model = Lesson
        fields = ['id', 'name', 'course', 'course_name', 'description','image', 'video_link' ]


class CourseSerializer(serializers.ModelSerializer):
    is_subscribed=serializers.SerializerMethodField()
    class Meta:
        model = Course
        fields = ['id', 'name', 'description','is_subscribed']

    def get_is_subscribed(self,obj):
        request=self.context.get('request')
        if not request: return False
        if not hasattr(request,'user'): return False
        if not request.user.is_authenticated: return False
        return obj.subscribers.filter(user=request.user).exists()

