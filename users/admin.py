from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, Payment


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('id','email', 'first_name', 'last_name', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'groups')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone', 'image', 'city')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )


from django.contrib import admin
import json


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_email', 'course_name', 'amount',  ]#'status','created_at' 'status''stripe_payment_id''stripe_payment_id',
    #list_filter = ['status', 'created_at']
    search_fields = [ 'user__email']

    # Add detail view with pretty JSON
    readonly_fields = ['metadata_display']

    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'course', 'amount',)
        }),
        ('Stripe Info', {
            'fields': ( 'metadata_display',)
        }),
    )

    def user_email(self, obj):
        return obj.user.email if obj.user else 'No user'

    def course_name(self, obj):
        return obj.course.name if obj.course else 'No course'

    def metadata_display(self, obj):
        return f"<pre>{json.dumps(obj.metadata, indent=2)}</pre>" if obj.metadata else "No metadata"

    metadata_display.allow_tags = True
