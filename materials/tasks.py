from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mass_mail
from django.template.loader import render_to_string
from django.utils import timezone

from materials.models import Course
from users.models import Subscription, CustomUser


@shared_task
def send_course_update_notification(course_id, update_message):
    try:
        course = Course.objects.get(id=course_id)
        subscriptions = Subscription.objects.filter(
            course=course,
        ).select_related('user')
        if not subscriptions:
            return f"No subscribers to notify for course: {course.title}"
        emails = []
        for subscription in subscriptions:
            user = subscription.user
            subject = f"Course Updated: {course.name}"
            message = render_to_string('course_updated.txt', {
                'user': user,
                'course': course,
                'update_message': update_message,
            })
            emails.append((subject,
                           message,
                           settings.DEFAULT_FROM_EMAIL,
                           [user.email]))
        send_mass_mail(emails, fail_silently=False)
        count = len(emails)
        return f"Notified {count} subscribers about course update"
    except Course.DoesNotExist:
        return "Course not found"
    except Exception as e:
        return f"Error: {str(e)}"


@shared_task
def deactivate_inactive_users():
    try:
        thirty_days_ago = timezone.now() - timedelta(days=30)
        inactive_users = CustomUser.objects.filter(
            is_active=True,
            last_login__lt=thirty_days_ago
        ).exclude(
            is_superuser=True
        ).exclude(
            is_staff=True
        )
        count = inactive_users.count()
        if count == 0:
            return "No inactive users found"
        inactive_users.update(is_active=False)
        return f"Deactivated {count} inactive users"
    except Exception as e:
        return f"Error: {str(e)}"


@shared_task
def check_and_notify_course_updates():
    try:
        one_hour_ago = timezone.now() - timedelta(hours=1)
        updated_courses = Course.objects.filter(
            updated_at__gte=one_hour_ago,
            is_published=True
        )
        results = []
        for course in updated_courses:
            if course.should_notify_subscribers():
                results = send_course_update_notification.delay(
                    course_id=course.id,
                    update_message="The course has been updated!"
                )
                results.append(f"Notified subscribers of {course.title}")
        if not results:
            return "No course updates to notify about"
        return f"Processed {len(results)} course updates"
    except Exception as e:
        return f"Error: {str(e)}"
