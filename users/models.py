from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from materials.models import Course
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser,BaseUserManager


class CustomUserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True'))

        return self.create_user(email, password, **extra_fields)



class CustomUser(AbstractUser):
    username = None

    email=models.EmailField(unique=True,blank=False)
    phone = models.CharField(max_length=20, blank=True, null=True)
    image = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    city = models.CharField(blank=True, null=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects=CustomUserManager()
    def __str__(self):
        return self.email
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')





class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [('наличные', 'Наличные'),('перевод', 'Перевод на счет')]
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,  related_name='payments')
    payment_date = models.DateTimeField(auto_now_add=True)
    course = models.ForeignKey('materials.Course',on_delete=models.PROTECT,related_name='payments',null=True,  blank=True )
    lesson = models.ForeignKey('materials.Lesson',on_delete=models.PROTECT,related_name='payments', null=True,blank=True)
    amount = models.DecimalField(max_digits=10,decimal_places=2,)
    payment_method = models.CharField(max_length=20,choices=PAYMENT_METHOD_CHOICES)
    stripe_session_id = models.CharField(max_length=255)
    stripe_payment_intent_id = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ['-payment_date']
        indexes = [models.Index(fields=['user', 'payment_date'])]
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__gte=0),
                name='payment_amount_positive'
            ),
            models.CheckConstraint(
                check=models.Q(course__isnull=False) | models.Q(lesson__isnull=False),
                name='at_least_one_course_or_lesson'
            )
        ]

    def __str__(self):
        return f" {self.user.email} - {self.amount}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.course and self.lesson and self.lesson.course != self.course:
            raise ValidationError("The lesson must belong to the selected course.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class Subscription(models.Model):
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='subscriptions')
    course = models.ForeignKey(Course,on_delete=models.CASCADE,related_name='subscribers')

    class Meta:
        unique_together = ['user', 'course']


    def __str__(self):
        return f"{self.user.email} subscribed to {self.course.name}"