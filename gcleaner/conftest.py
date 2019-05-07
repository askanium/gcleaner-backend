import json
import pytest
from google.oauth2.credentials import Credentials

from gcleaner.emails.constants import LABEL_UNREAD, LABEL_INBOX, LABEL_TRASH
from gcleaner.emails.models import Label, Email, LatestEmail
from gcleaner.emails.services import EmailService
from gcleaner.users.models import User


@pytest.fixture
def user(db):
    user = User.objects.create(username='me@email.com', email='me@email.com')
    return user


@pytest.fixture
def label_unread(user, db):
    label = Label.objects.create(user=user, google_id=LABEL_UNREAD, name='UNREAD', type='system')
    return label


@pytest.fixture
def label_inbox(user, db):
    label = Label.objects.create(user=user, google_id=LABEL_INBOX, name='INBOX', type='system')
    return label


@pytest.fixture
def label_category_personal(user, db):
    label = Label.objects.create(user=user, google_id='CATEGORY_PERSONAL', name='CATEGORY_PERSONAL', type='system')
    return label


@pytest.fixture
def label_custom_category(user, db):
    label = Label.objects.create(user=user, google_id='Label_35', name='Custom Label', type='user', text_color='#222', background_color='#ddd')
    return label


@pytest.fixture
def label_trash(user, db):
    label = Label.objects.create(user=user, google_id=LABEL_TRASH, name='TRASH', type='system')
    return label


@pytest.fixture
def all_labels(label_inbox, label_unread, label_category_personal, label_custom_category, label_trash):
    return [
        label_inbox,
        label_unread,
        label_category_personal,
        label_custom_category,
        label_trash
    ]


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
                                 date='2019-03-19 08:11:21+00:00')
    email.labels.add(label_unread)
    email.labels.add(label_inbox)
    return email


@pytest.fixture
def latest_email(email, user):
    latest_email = LatestEmail.objects.create(user=user, email=email)

    return latest_email


@pytest.fixture
def google_credentials():
    credentials = Credentials('token', refresh_token='refresh_token')
    return credentials


@pytest.fixture
def gmail_api_get_1_response():
    return {
        "id": "1599581458cf8986",
        "threadId": "1599581458cf8986",
        "labelIds": [
            "UNREAD",
            "CATEGORY_PERSONAL",
            "INBOX"
        ],
        "internalDate": "1552991481000",
        "snippet": "GmailCleaner connected to your Google Account",
        "payload": {
            "headers": [
                {
                    "name": "Delivered-To",
                    "value": "me@email.com"
                },
                {
                    "name": "Subject",
                    "value": "GmailCleaner connected to your Google Account"
                },
                {
                    "name": "From",
                    "value": "Google <no-reply@accounts.google.com>"
                },
                {
                    "name": "To",
                    "value": "me@email.com"
                },
            ]
        }
    }


@pytest.fixture
def gmail_api_get_2_response():
    return {
        "id": "159951b16a5c5591",
        "threadId": "159951b16a5c5591",
        "labelIds": [
            "CATEGORY_PERSONAL",
            "UNREAD",
            "INBOX",
            "Label_35"
        ],
        "internalDate": "1552984759000",
        "snippet": "Promotion! Promotion! Promotion!",
        "payload": {
            "headers": [
                {
                    "name": "Delivered-To",
                    "value": "me@email.com"
                },
                {
                    "name": "From",
                    "value": "Aa from baa.co <aa@baa.co>"
                },
                {
                    "name": "Subject",
                    "value": "Nice subject line"
                },
                {
                    "name": "To",
                    "value": "Name Surname <me@email.com>"
                },
            ]
        }
    }


@pytest.fixture
def gmail_api_get_3_response():
    return {
        "id": "1599518a6f32a3b1",
        "threadId": "1599518a6f32a3b1",
        "labelIds": [
            "UNREAD",
            "INBOX"
        ],
        "internalDate": "1552984611000",
        "snippet": "Amazon Web Services Only 1 week until AWSome Day Online Conference starts.",
        "payload": {
            "headers": [
                {
                    "name": "Delivered-To",
                    "value": "me@email.com"
                },
                {
                    "name": "Delivered-To",
                    "value": "other@email.com"
                },
                {
                    "name": "From",
                    "value": "Amazon Web Services <aws-marketing-email-replies@amazon.com>"
                },
                {
                    "name": "To",
                    "value": "other@email.com"
                },
                {
                    "name": "Subject",
                    "value": "Don't miss your chance to join us for AWSome Day Online"
                },
                {
                    "name": "List-Unsubscribe",
                    "value": "<mailto:728229.239056.9@unsub-sj.mktomail.com>"
                },
            ]
        }
    }


@pytest.fixture
def gmail_api_email_1(user, google_credentials, gmail_api_get_1_response):
    service = EmailService(credentials=google_credentials, user=user)
    service.gmail_service_batch_callback(1, gmail_api_get_1_response, None)
    email = service.emails[-1]
    return email


@pytest.fixture
def gmail_api_email_2(user, google_credentials, gmail_api_get_2_response):
    service = EmailService(credentials=google_credentials, user=user)
    service.gmail_service_batch_callback(2, gmail_api_get_2_response, None)
    email = service.emails[-1]
    return email


@pytest.fixture
def gmail_api_email_3(user, google_credentials, gmail_api_get_3_response):
    service = EmailService(credentials=google_credentials, user=user)
    service.gmail_service_batch_callback(3, gmail_api_get_3_response, None)
    email = service.emails[-1]
    return email


@pytest.fixture
def gmail_api_list_response():
    emails = [
        {
            "id": "1599581458cf8986",
            "threadId": "1599581458cf8986"
        },
        {
            "id": "159951b16a5c5591",
            "threadId": "159951b16a5c5591"
        },
        {
            "id": "1599518a6f32a3b1",
            "threadId": "1599518a6f32a3b1"
        }
    ]

    return emails


@pytest.fixture
def gmail_batch_response(gmail_api_get_1_response, gmail_api_get_2_response, gmail_api_get_3_response):
    response = """
--batch_ygSpAcfQXdA_AAfKEo9rkX4\r\nContent-Type: application/http\r\nContent-ID: <response-eb0275a7-6c83-4b6c-9b9e-10c525f64f19 + 1>\r\n\r\nHTTP/1.1 200 OK\r\nETag: "LZWdHVzsAG0UZhwmZBdpM9j7eJQ/_VWh__H0wb3woEXGUB0Gw6gbJEM"\r\nContent-Type: application/json; charset=UTF-8\r\nDate: Fri, 05 Apr 2019 13:27:19 GMT\r\nExpires: Fri, 05 Apr 2019 13:27:19 GMT\r\nCache-Control: private, max-age=0\r\nContent-Length: 1000\r\n\r\n{email1}\r\n\r\n--batch_ygSpAcfQXdA_AAfKEo9rkX4\r\nContent-Type: application/http\r\nContent-ID: <response-eb0275a7-6c83-4b6c-9b9e-10c525f64f19 + 2>\r\n\r\nHTTP/1.1 200 OK\r\nETag: "LZWdHVzsAG0UZhwmZBdpM9j7eJQ/RmebJ7MNtiqLslsyXDqenB6Jbqo"\r\nContent-Type: application/json; charset=UTF-8\r\nDate: Fri, 05 Apr 2019 13:27:19 GMT\r\nExpires: Fri, 05 Apr 2019 13:27:19 GMT\r\nCache-Control: private, max-age=0\r\nContent-Length: 1000\r\n\r\n{email2}\r\n\r\n--batch_ygSpAcfQXdA_AAfKEo9rkX4\r\nContent-Type: application/http\r\nContent-ID: <response-eb0275a7-6c83-4b6c-9b9e-10c525f64f19 + 3>\r\n\r\nHTTP/1.1 200 OK\r\nETag: "LZWdHVzsAG0UZhwmZBdpM9j7eJQ/HF6WWUaqat1LByM3pYk8sNDqRh8"\r\nContent-Type: application/json; charset=UTF-8\r\nDate: Fri, 05 Apr 2019 13:27:19 GMT\r\nExpires: Fri, 05 Apr 2019 13:27:19 GMT\r\nCache-Control: private, max-age=0\r\nContent-Length: 1000\r\n\r\n{email3}
""".format(email1=json.dumps(gmail_api_get_1_response),
           email2=json.dumps(gmail_api_get_2_response),
           email3=json.dumps(gmail_api_get_3_response))

    return response


@pytest.fixture
def gmail_batch_small_response(gmail_api_get_1_response, gmail_api_get_2_response):
    response = """
--batch_ygSpAcfQXdA_AAfKEo9rkX4\r\nContent-Type: application/http\r\nContent-ID: <response-eb0275a7-6c83-4b6c-9b9e-10c525f64f19 + 1>\r\n\r\nHTTP/1.1 200 OK\r\nETag: "LZWdHVzsAG0UZhwmZBdpM9j7eJQ/_VWh__H0wb3woEXGUB0Gw6gbJEM"\r\nContent-Type: application/json; charset=UTF-8\r\nDate: Fri, 05 Apr 2019 13:27:19 GMT\r\nExpires: Fri, 05 Apr 2019 13:27:19 GMT\r\nCache-Control: private, max-age=0\r\nContent-Length: 1000\r\n\r\n{email1}\r\n\r\n--batch_ygSpAcfQXdA_AAfKEo9rkX4\r\nContent-Type: application/http\r\nContent-ID: <response-eb0275a7-6c83-4b6c-9b9e-10c525f64f19 + 2>\r\n\r\nHTTP/1.1 200 OK\r\nETag: "LZWdHVzsAG0UZhwmZBdpM9j7eJQ/RmebJ7MNtiqLslsyXDqenB6Jbqo"\r\nContent-Type: application/json; charset=UTF-8\r\nDate: Fri, 05 Apr 2019 13:27:19 GMT\r\nExpires: Fri, 05 Apr 2019 13:27:19 GMT\r\nCache-Control: private, max-age=0\r\nContent-Length: 1000\r\n\r\n{email2}
""".format(email1=json.dumps(gmail_api_get_1_response),
           email2=json.dumps(gmail_api_get_2_response))

    return response
