import pytest

from gcleaner.emails.models import Label, Email
from gcleaner.users.models import User


@pytest.fixture
def user(db):
    user = User.objects.create(username='me@email.com', email='me@email.com')
    return user


@pytest.fixture
def label_unread(user, db):
    label = Label.objects.create(user=user, google_id='UNREAD', name='UNREAD')
    return label


@pytest.fixture
def label_inbox(user, db):
    label = Label.objects.create(user=user, google_id='INBOX', name='INBOX')
    return label


@pytest.fixture
def email(user, label_unread, label_inbox, db):
    email = Email.objects.create(user=user,
                                 google_id='a123',
                                 thread_id='t123',
                                 subject='Subject',
                                 snippet='Snippet',
                                 sender='Sender',
                                 receiver='Receiver',
                                 delivered_to='Delivered To',
                                 starred=False,
                                 important=False,
                                 date='2019-03-19 10:31:21+00:00')
    email.labels.add(label_unread)
    email.labels.add(label_inbox)
    return email
