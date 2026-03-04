from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):
    def handle(self, *args, **options):
        moderator_group, created = Group.objects.get_or_create(name='moderator')
        moderator_lst = ['view_lesson', 'change_lesson',
                       'view_course', 'change_course',
                       'view_customuser']
        moderator_permissions = []
        for i in moderator_lst:

            perm = Permission.objects.get(codename=i)
            moderator_permissions.append(perm)
        moderator_group.permissions.set(moderator_permissions)

        user_group,created = Group.objects.get_or_create(name='user')
        user_lst = ['view_lesson', 'change_lesson',
                     'add_lesson', 'delete_lesson',
                    'view_course', 'change_course',
                     'add_course', 'delete_course',
                    'view_customuser', 'change_customuser',
                     'add_customuser', 'view_payment']
        user_permissions = []
        for i in user_lst:

            perm = Permission.objects.get(codename=i)
            user_permissions.append(perm)
        user_group.permissions.set(user_permissions)
