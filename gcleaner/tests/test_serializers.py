from gcleaner.emails.serializers import EmailSerializer


def test_email_serializer(email, label_unread, label_inbox):
    email_json = {
        'labels': [
            {
                'google_id': 'UNREAD',
                'name': 'UNREAD'
            },
            {
                'google_id':'INBOX',
                'name': 'INBOX',
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
    serializer = EmailSerializer(email)
    # serializer.is_valid()

    assert email_json == serializer.data
