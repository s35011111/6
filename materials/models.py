from django.db import models
from django.conf import settings

# Create your models here.

from typing import Any




########################################################################
class Course(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='materials/',blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='authored_courses'
    )
    stripe_product_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_price_id = models.CharField(max_length=100, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    def __str__(self: Any) -> str:
        return self.name

    class Meta:
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
        ordering = ['name']
        permissions = [
            ("can_approve_course", "Can approve courses"),
        ]

########################################################################
class Lesson(models.Model):
    name = models.CharField(max_length=100)
    course=models.ForeignKey('Course',on_delete=models.CASCADE)
    description = models.TextField( blank=True, null=True)
    image=models.ImageField(upload_to='materials/', blank=True, null=True)
    video_link=models.URLField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='authored_lessons'
    )

    def __str__(self: Any) -> str:
        return f"{self.course.name} - {self.name}"

    class Meta:
        verbose_name = 'Lesson'
        verbose_name_plural = 'Lessons'
        ordering = ['id']
        permissions = [
            ("can_approve_lesson", "Can approve lessons"),
        ]


########################################################################


