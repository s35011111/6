from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from .models import Course, Lesson
from .serializers import CourseSerializer, LessonSerializer
from users.permissions import IsModerator, IsAdmin, IsOwner


class  CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name']
    list_permissions = [IsAuthenticated]
    retrieve_permissions = [IsAuthenticated]
    create_permissions = [IsAuthenticated & ~IsModerator]
    update_permissions = [IsAuthenticated, IsOwner | IsModerator | IsAdmin]
    destroy_permissions = [IsAuthenticated, IsOwner | IsAdmin]


    def get_permissions(self):
        permission_map={'list':self.list_permissions,
                        'retrieve':self.retrieve_permissions,
                        'create':self.create_permissions,
                        'update':self.update_permissions,
                        'destroy':self.destroy_permissions,}
        permission_classes_ =permission_map.get(self.action)

        if permission_classes_ is None :return []
        return [permission() for permission in permission_classes_]


    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.groups.filter(name='moderator').exists():
            return Course.objects.all()
        if user.is_authenticated: return Course.objects.filter(author=self.request.user)
        else: return Course.objects.none()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class LessonViewSet(viewsets.ModelViewSet):
    serializer_class = LessonSerializer
    list_permissions = [IsAuthenticated]
    retrieve_permissions = [IsAuthenticated]
    create_permissions = [IsAuthenticated & ~IsModerator]
    update_permissions = [IsAuthenticated, IsOwner | IsModerator | IsAdmin]
    destroy_permissions = [IsAuthenticated, IsOwner | IsAdmin]


    def get_permissions(self):
        permission_map={'list':self.list_permissions,
                        'retrieve':self.retrieve_permissions,
                        'create':self.create_permissions,
                        'update':self.update_permissions,
                        'destroy':self.destroy_permissions,}
        permission_classes_ =permission_map.get(self.action)

        if permission_classes_ is None :return []
        return [permission() for permission in permission_classes_]
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.groups.filter(name='moderator').exists():
            return Lesson.objects.all()
        if user.is_authenticated:return Lesson.objects.filter(author=self.request.user)
        else: return Lesson.objects.none()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


