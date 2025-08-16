from rest_framework import permissions
from django.conf import settings

class AgentAPIKeyPermission(permissions.BasePermission):
    """
    Custom permission to check for a valid API key in the request header.
    """
    def has_permission(self, request, view):
        api_key = request.headers.get('X-API-KEY')
        if not api_key:
            return False # No API key provided

        # Check if the API key exists in our settings and is valid for a hostname
        return api_key in settings.API_KEYS