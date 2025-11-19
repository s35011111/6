from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, generics, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models
from .models import Course, Lesson
from .serializers import CourseSerializer, LessonSerializer
from users.permissions import IsRegisteredUser, IsModerator, IsOwnerOrReadOnly, CanApproveContent

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name']
    @action(detail=True, methods=['get'])
    def lessons(self, request, pk=None):
        course = self.get_object()
        lessons = course.lessons.all()
        serializer = LessonSerializer(lessons, many=True)
        return Response(serializer.data)
    @action(detail=False, methods=['get'])
    def active(self, request):
        active_courses = Course.objects.filter(lessons__is_active=True).distinct()
        serializer = self.get_serializer(active_courses, many=True)
        return Response(serializer.data)


    def get_queryset(self):
        queryset = Course.objects.all()
        user = self.request.user
        if not user.is_authenticated:
            return Course.objects.none()
        if user.groups.filter(name='Registered Users').exists():
            return queryset.filter(
                models.Q(is_published=True) |
                models.Q(author=user)
            )
        if user.groups.filter(name='Moderators').exists():
            return queryset
        return Course.objects.none()
    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [IsRegisteredUser]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsOwnerOrReadOnly]
        elif self.action in ['approve']:
            permission_classes = [CanApproveContent]
        else:
            permission_classes = [IsRegisteredUser | IsModerator]
        return [permission() for permission in permission_classes]
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    @action(detail=True, methods=['post'], permission_classes=[CanApproveContent])
    def approve(self, request, pk=None):
        course = self.get_object()
        course.is_published = True
        course.save()
        return Response({'status': 'course approved and published'})


class LessonListCreateView(generics.ListCreateAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['course', 'is_active']
    def get_queryset(self):
        queryset = Lesson.objects.all()
        course_id = self.request.query_params.get('course_id')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        return queryset

class LessonRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

class CourseLessonsListView(generics.ListAPIView):
    serializer_class = LessonSerializer
    def get_queryset(self):
        course_id = self.kwargs['course_id']
        return Lesson.objects.filter(course_id=course_id)

class LessonsListView(generics.ListAPIView):
    serializer_class = LessonSerializer
    queryset = Lesson.objects.all()

class LessonViewSet(viewsets.ModelViewSet):
    serializer_class = LessonSerializer
    def get_queryset(self):
        queryset = Lesson.objects.all()
        user = self.request.user
        if not user.is_authenticated:
            return Lesson.objects.none()
        if user.groups.filter(name='Registered Users').exists():
            return queryset.filter(
                models.Q(is_published=True) |
                models.Q(author=user)
            )
        if user.groups.filter(name='Moderators').exists():
            return queryset
        return Lesson.objects.none()
    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [IsRegisteredUser]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsOwnerOrReadOnly]
        elif self.action in ['approve']:
            permission_classes = [CanApproveContent]
        else:
            permission_classes = [IsRegisteredUser | IsModerator]
        return [permission() for permission in permission_classes]
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

