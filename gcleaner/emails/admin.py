from django.contrib import admin

from gcleaner.emails.models import Email, Label


@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    pass


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    pass
