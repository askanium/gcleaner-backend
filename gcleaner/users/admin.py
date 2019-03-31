from django.contrib import admin

from gcleaner.users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass
