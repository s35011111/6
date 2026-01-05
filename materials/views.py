# Create your views here.
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions
from rest_framework.permissions import IsAuthenticated

from users.permissions import IsModerator, IsAdmin, IsOwner
from .models import Course, Lesson
from .pagination import StandardPagePagination
from .serializers import CourseSerializer, LessonSerializer


class  CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    pagination_class = StandardPagePagination

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name']
    list_permissions = [IsAuthenticated]
    retrieve_permissions = [IsAuthenticated]
    create_permissions = [IsAuthenticated & ~IsModerator]
    update_permissions = [IsAuthenticated, IsOwner | IsModerator | IsAdmin]
    destroy_permissions = [IsAuthenticated, IsOwner | IsAdmin]
    def get_serializer_context(self):
        context=super().get_serializer_context()
        context['request']=self.request
        return context

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
    pagination_class = StandardPagePagination
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




