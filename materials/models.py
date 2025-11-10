from django.db import models

# Create your models here.

from typing import Any
########################################################################
class Course(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='materials/')

    def __str__(self: Any) -> str:
        return self.name

    class Meta:
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
        ordering = ['name']

########################################################################
class Lesson(models.Model):
    name = models.CharField(max_length=100)
    course=models.ForeignKey('Course',on_delete=models.CASCADE)
    description = models.TextField( blank=True, null=True)
    image=models.ImageField(upload_to='materials/', blank=True, null=True)
    video_link=models.URLField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self: Any) -> str:
        return f"{self.course.name} - {self.name}"

    class Meta:
        verbose_name = 'Lesson'
        verbose_name_plural = 'Lessons'
        ordering = ['id']


########################################################################
