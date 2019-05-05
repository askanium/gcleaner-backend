from gcleaner.emails.constants import LABEL_UNREAD, LABEL_INBOX
from gcleaner.emails.serializers import EmailSerializer, LabelSerializer


def test_email_serializer(email, label_unread, label_inbox):
    # test setup
    email_json = {
        'labels': [
            {
                'google_id': LABEL_UNREAD,
                'name': 'UNREAD',
                'type': 'system',
                'text_color': '',
                'background_color': ''
            },
            {
                'google_id': LABEL_INBOX,
                'name': 'INBOX',
                'type': 'system',
                'text_color': '',
                'background_color': ''
            }
        ],
        'google_id': 'a123',
        'thread_id': 't123',
        'subject': 'Subject',
        'snippet': 'Snippet',
        'sender': 'Sender',
        'receiver': 'Receiver',
        'delivered_to': 'Delivered To',
        'starred': False,
        'important': False,
        'date': '2019-03-19 08:11:21+00:00'
    }

    # serializer instantiation
    serializer = EmailSerializer(email)

    # assertions
    assert email_json == serializer.data


def test_label_serializer(label_custom_category):
    # test setup
    label_json = {
        'google_id': 'Label_35',
        'name': 'Custom Label',
        'type': 'user',
        'text_color': '#222',
        'background_color': '#ddd'
    }

    # serializer instantiation
    serializer = LabelSerializer(label_custom_category)

    # assertions
    assert label_json == serializer.data