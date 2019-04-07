import datetime

import factory
import pytz
from factory.fuzzy import FuzzyDateTime


class UserFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'users.User'
        django_get_or_create = ('username',)

    id = factory.Faker('uuid4')
    username = factory.Sequence(lambda n: f'testuser{n}')
    password = factory.Faker('password', length=10, special_chars=True, digits=True,
                             upper_case=True, lower_case=True)
    email = factory.Faker('email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    is_staff = False


class EmailFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'emails.Email'

    user = factory.SubFactory(UserFactory)

    google_id = factory.Sequence(lambda n: 'google_id_%d' % n)
    thread_id = factory.Sequence(lambda n: 'thread_id_%d' % n)
    subject = factory.Sequence(lambda n: 'Subject %s' % n)
    snippet = factory.Sequence(lambda n: 'Snippet %s' % n)
    sender = factory.Sequence(lambda n: 'Sender %s' % n)
    receiver = factory.Sequence(lambda n: 'Receiver %s' % n)
    delivered_to = factory.Sequence(lambda n: 'Delivered to %s' % n)
    starred = False
    important = False
    date = FuzzyDateTime(datetime.datetime(2009, 1, 1, tzinfo=pytz.UTC))
    list_unsubscribe = ''
