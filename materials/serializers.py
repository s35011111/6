from rest_framework import serializers
from .models import Course, Lesson


class LessonSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)
    class Meta:
        model = Lesson
        fields = ['id', 'name', 'course', 'course_name', 'description','image', 'video_link', ]


class CourseSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    lessons_count = serializers.SerializerMethodField()
    class Meta:
        model = Course
        fields = ['id', 'name', 'description', 'image','lessons', 'lessons_count','total_duration',]
    def get_lessons_count(self, obj):
        return obj.lessons.count()

