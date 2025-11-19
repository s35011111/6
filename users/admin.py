from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group, Permission
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'date_joined')
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



class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_permissions')
    filter_horizontal = ('permissions',)

    def display_permissions(self, obj):
        return ", ".join(
            [p.name for p in obj.permissions.all()[:3]]) + "..." if obj.permissions.count() > 3 else ", ".join(
            [p.name for p in obj.permissions.all()])

    display_permissions.short_description = 'Permissions'



admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)