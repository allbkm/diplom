from rest_framework.permissions import BasePermission


class IsAuthenticated(BasePermission):
    """Права доступа для авторизованных пользователей"""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
