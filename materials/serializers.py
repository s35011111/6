from rest_framework import serializers
from .models import Course, Lesson
from .validators import validate_no_links


class LessonSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)
    description = serializers.CharField(validators=[validate_no_links] )

    class Meta:
        model = Lesson
        fields = ['id', 'name', 'course', 'course_name', 'description','image', 'video_link' ]


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'name', 'description']

