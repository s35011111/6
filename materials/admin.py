from django.contrib import admin

from materials.models import Course, Lesson


# Register your models here.
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['id', 'name','author']
    search_fields = ['name']


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'author', 'course']
    list_filter = ['course','author']
    search_fields = ['name', 'description']
    autocomplete_fields = ['course']
    list_per_page = 20
    ordering = ['name']


