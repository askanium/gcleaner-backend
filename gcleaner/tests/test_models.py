import datetime

from gcleaner.emails.models import Email, Label
from gcleaner.users.models import User


def test_user_model_str_representation():
    email = 'my@email.com'
    user = User(username=email)

    assert str(user) == email


def test_email_model_from_dict(user, label_inbox, label_unread):
    email = Email.from_dict({
        'user': user.pk,
        'labels': [label_unread.google_id, label_inbox.google_id],
        'google_id': 'a123',
        'thread_id': 't123',
        'subject': 'Subject',
        'snippet': 'Snippet',
        'sender': 'Sender',
        'receiver': 'Receiver',
        'delivered_to': 'Delivered To',
        'starred': True,
        'important': False,
        'date': datetime.datetime(2019, 3, 19, 10, 31, 21, tzinfo=datetime.timezone.utc),
        'list_unsubscribe': '<mailto:unsubscribe@example.com>'
    })

    assert email.pk is not None
    assert email.user_id == user.pk
    assert email.google_id == 'a123'
    assert email.thread_id == 't123'
    assert email.subject == 'Subject'
    assert email.snippet == 'Snippet'
    assert email.sender == 'Sender'
    assert email.receiver == 'Receiver'
    assert email.delivered_to == 'Delivered To'
    assert email.starred is True
    assert email.important is False
    assert email.date == datetime.datetime(2019, 3, 19, 10, 31, 21, tzinfo=datetime.timezone.utc)
    assert email.list_unsubscribe == '<mailto:unsubscribe@example.com>'
    assert list(email.labels.all().values('google_id', 'user')) == [
        {
            'google_id': label_inbox.google_id,
            'user': user.pk
        },
        {
            'google_id': label_unread.google_id,
            'user': user.pk
        }
    ]


def test_email_model_from_dict_with_missing_boolean_props(user, label_inbox, label_unread):
    email = Email.from_dict({
        'user': user.pk,
        'labels': [label_unread.google_id, label_inbox.google_id],
        'google_id': 'a123',
        'thread_id': 't123',
        'subject': 'Subject',
        'snippet': 'Snippet',
        'sender': 'Sender',
        'receiver': 'Receiver',
        'delivered_to': 'Delivered To',
        'date': datetime.datetime(2019, 3, 19, 10, 31, 21, tzinfo=datetime.timezone.utc),
        'list_unsubscribe': '<mailto:unsubscribe@example.com>'
    })

    assert email.pk is not None
    assert email.user_id == user.pk
    assert email.google_id == 'a123'
    assert email.thread_id == 't123'
    assert email.subject == 'Subject'
    assert email.snippet == 'Snippet'
    assert email.sender == 'Sender'
    assert email.receiver == 'Receiver'
    assert email.delivered_to == 'Delivered To'
    assert email.starred is False
    assert email.important is False
    assert email.date == datetime.datetime(2019, 3, 19, 10, 31, 21, tzinfo=datetime.timezone.utc)
    assert email.list_unsubscribe == '<mailto:unsubscribe@example.com>'
    assert list(email.labels.all().values('google_id', 'user')) == [
        {
            'google_id': label_inbox.google_id,
            'user': user.pk
        },
        {
            'google_id': label_unread.google_id,
            'user': user.pk
        }
    ]


def test_label_creation_of_system_type(user):
    label = Label.objects.create(user=user,
                                 google_id='INBOX',
                                 type='system',
                                 name='INBOX')
    assert label.pk is not None


def test_label_creation_of_user_type(user):
    label = Label.objects.create(user=user,
                                 google_id='Label_10',
                                 type='user',
                                 name='INBOX',
                                 text_color='#cccccc',
                                 background_color='#f3f3f3')
    assert label.pk is not None
