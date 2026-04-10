from rest_framework_api_key.admin import APIKeyModelAdmin
from django.contrib import admin
from .models import UserAPIKey

@admin.register(UserAPIKey)
class UserAPIKeyAdmin(APIKeyModelAdmin):
    pass