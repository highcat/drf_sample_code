# -*- coding: utf-8 -*-
from rest_framework import permissions

class SuperuserPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated() and request.user.is_superuser
