from django.contrib import admin

from gcleaner.emails.models import Email, Label, LockedEmail


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
    filter_horizontal = ['labels']


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'name',
        'google_id',
        'type',
        'text_color',
        'background_color'
    ]


@admin.register(LockedEmail)
class LockedEmailAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'google_id',
        'thread_id',
        'locked'
    ]
