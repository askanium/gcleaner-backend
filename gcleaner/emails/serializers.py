from rest_framework import serializers

from gcleaner.emails.models import Email, Label


class LabelSerializer(serializers.ModelSerializer):
    """
    Serialize `gcleaner.messages.models.Label` instances.
    """
    class Meta:
        model = Label
        fields = [
            'google_id',
            'name'
        ]


class EmailSerializer(serializers.ModelSerializer):
    """
    Serialize `gcleaner.messages.models.Email` instances.
    """
    labels = LabelSerializer(many=True)

    class Meta:
        model = Email
        fields = [
            'labels',
            'google_id',
            'thread_id',
            'subject',
            'snippet',
            'sender',
            'receiver',
            'delivered_to',
            'starred',
            'important',
            'date'
        ]
