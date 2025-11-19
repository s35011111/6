from rest_framework import permissions

class IsRegisteredUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user.is_authenticated and
                request.user.groups.filter(name='Registered Users').exists())

class IsModerator(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user.is_authenticated and
                request.user.groups.filter(name='Moderators').exists())

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user

class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.author == request.user

class CanApproveContent(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user.has_perm('materials.can_approve_course') or
                request.user.has_perm('materials.can_approve_lesson'))

class ReadOnlyForPublic(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS