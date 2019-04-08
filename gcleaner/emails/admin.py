from django.contrib import admin

from gcleaner.emails.models import Email, Label


@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'google_id',
        'thread_id',
        'sender',
        'receiver',
        'delivered_to',
        'starred',
        'important',
        'date',
        'list_unsubscribe'
    ]


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    pass
