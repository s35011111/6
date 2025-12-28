from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj == request.user


class IsOwner(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user

class IsModerator(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='moderator').exists()
    def has_object_permission(self, request, view, obj):
        return request.user.groups.filter(name='moderator').exists()

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return  request.user.is_staff
    def has_object_permission(self, request, view, obj):
        return  request.user.is_staff

class IsAuthenticatedOrRegisrerOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action in ['register','login','create' ]and request.method=='POST':
            return True
        return request.user and request.user.is_authenticated
