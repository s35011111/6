from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CourseViewSet, LessonListCreateView, LessonRetrieveUpdateDestroyView, CourseLessonsListView, \
    LessonsListView

router = DefaultRouter()
router.register(r'courses', CourseViewSet)

urlpatterns = [
    path('', include(router.urls)),

    path('lessons/', LessonListCreateView.as_view(), name='lesson-list-create'),
    path('lessons/<int:pk>/', LessonRetrieveUpdateDestroyView.as_view(), name='lesson-detail'),

    path('courses/<int:course_id>/lessons/', CourseLessonsListView.as_view(), name='course-lessons'),
    path('lessons_all/', LessonsListView.as_view(), name='lessons_list'),
]