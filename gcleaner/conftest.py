import pytest
from google.oauth2.credentials import Credentials

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
def label_category_personal(user, db):
    label = Label.objects.create(user=user, google_id='CATEGORY_PERSONAL', name='CATEGORY_PERSONAL')
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


@pytest.fixture
def google_credentials():
    credentials = Credentials('token', refresh_token='refresh_token')
    return credentials


@pytest.fixture
def gmail_api_response():
    emails = [
        {
            "id": "1599581458cf8986",
            "threadId": "1599581458cf8986",
            "labelIds": [
                "UNREAD",
                "CATEGORY_PERSONAL",
                "INBOX"
            ],
            "snippet": "GmailCleaner connected to your Google Account",
            "payload": {
                "headers": [
                    {
                        "name": "Delivered-To",
                        "value": "me@email.com"
                    },
                    {
                        "name": "Received",
                        "value": "by :::0:0:0:0:0 with SMTP id bla bla;        Tue, 19 Mar 2019 03:31:23 -0700 (PDT)"
                    },
                    {
                        "name": "X-Received",
                        "value": "by 2002:a67::: with SMTP id bla bla;        Tue, 19 Mar 2019 03:31:22 -0700 (PDT)"
                    },
                    {
                        "name": "ARC-Seal",
                        "value": "i=1; a=rsa-sha256; t=1552991482; cv=none;"
                    },
                    {
                        "name": "ARC-Message-Signature",
                        "value": "i=1; a=rsa-sha256; c=relaxed/relaxed; d=google.com;"
                    },
                    {
                        "name": "ARC-Authentication-Results",
                        "value": "i=1; mx.google.com;"
                    },
                    {
                        "name": "Return-Path",
                        "value": "<3"
                    },
                    {
                        "name": "Received",
                        "value": "from mail-sor-f69.google.com"
                    },
                    {
                        "name": "Received-SPF",
                        "value": "pass (google.com)"
                    },
                    {
                        "name": "Authentication-Results",
                        "value": "mx.google.com;"
                    },
                    {
                        "name": "DKIM-Signature",
                        "value": "v=1; a=rsa-sha256; c=relaxed/relaxed;"
                    },
                    {
                        "name": "X-Google-DKIM-Signature",
                        "value": "v=1; a=rsa-sha256; c=relaxed/relaxed;"
                    },
                    {
                        "name": "X-Gm-Message-State",
                        "value": "APjAAAVmx3NR6vdLbgWMYK3vq"
                    },
                    {
                        "name": "X-Google-Smtp-Source",
                        "value": "APXvYqzR/58PNBAW6yVJ0SixM"
                    },
                    {
                        "name": "MIME-Version",
                        "value": "1.0"
                    },
                    {
                        "name": "X-Received",
                        "value": "by 2002:a67::: with SMTP id y64"
                    },
                    {
                        "name": "Date",
                        "value": "Tue, 19 Mar 2019 10:31:21 +0000 (UTC)"
                    },
                    {
                        "name": "X-Account-Notification-Type",
                        "value": "127-anexp#givab"
                    },
                    {
                        "name": "Feedback-ID",
                        "value": "127-anexp#givab"
                    },
                    {
                        "name": "X-Notifications",
                        "value": "0e4320bc000000"
                    },
                    {
                        "name": "Message-ID",
                        "value": "<7yIaa@notifications.google.com>"
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
                    {
                        "name": "Content-Type",
                        "value": "multipart/alternative; boundary=\"000000000000a6eea7058470012f\""
                    }
                ]
            }
        },
        {
            "id": "159951b16a5c5591",
            "threadId": "159951b16a5c5591",
            "labelIds": [
                "CATEGORY_PROMOTIONS",
                "UNREAD",
                "INBOX",
                "Label_35"
            ],
            "snippet": "Promotion! Promotion! Promotion!",
            "payload": {
                "headers": [
                    {
                        "name": "Delivered-To",
                        "value": "me@email.com"
                    },
                    {
                        "name": "Received",
                        "value": "by 2002:a19::0:0:0:0:0 with SMTP id;        Tue, 19 Mar 2019 01:39:34 -0700 (PDT)"
                    },
                    {
                        "name": "X-Google-Smtp-Source",
                        "value": "APX"
                    },
                    {
                        "name": "X-Received",
                        "value": "by :a25:3249:: with SMTP id;        Tue, 19 Mar 2019 01:39:34 -0700 (PDT)"
                    },
                    {
                        "name": "ARC-Seal",
                        "value": "i=1; a=rsa-sha256; t=1552984774; cv=none;"
                    },
                    {
                        "name": "ARC-Message-Signature",
                        "value": "i=1; a=rsa-sha256; c=relaxed/relaxed; d=google.com;"
                    },
                    {
                        "name": "ARC-Authentication-Results",
                        "value": "i=1; mx.google.com;"
                    },
                    {
                        "name": "Return-Path",
                        "value": "<bounce-md@app.com>"
                    },
                    {
                        "name": "Received",
                        "value": "from mail134-7"
                    },
                    {
                        "name": "Received-SPF",
                        "value": "pass (google.com)"
                    },
                    {
                        "name": "Authentication-Results",
                        "value": "mx.google.com;"
                    },
                    {
                        "name": "DKIM-Signature",
                        "value": "v=1; a=rsa-sha256; c=relaxed/relaxed;"
                    },
                    {
                        "name": "Received",
                        "value": "from pmta03.mandrill"
                    },
                    {
                        "name": "DKIM-Signature",
                        "value": "v=1; a=rsa-sha256; c=relaxed/relaxed;"
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
                        "name": "Return-Path",
                        "value": "<bounce-md@app.com>"
                    },
                    {
                        "name": "Received",
                        "value": "from receiver"
                    },
                    {
                        "name": "X-Mailer",
                        "value": "PHPMailer 6.0.7"
                    },
                    {
                        "name": "To",
                        "value": "Name Surname <me@email.com>"
                    },
                    {
                        "name": "Message-Id",
                        "value": "<random@mail.com>"
                    },
                    {
                        "name": "X-Report-Abuse",
                        "value": "Please forward a copy of this message, including all headers, to abuse@email.com"
                    },
                    {
                        "name": "X-Report-Abuse",
                        "value": "You can also report abuse here: http://app.com/contact/abuse"
                    },
                    {
                        "name": "X-Mandrill-User",
                        "value": "md_33536"
                    },
                    {
                        "name": "Date",
                        "value": "Tue, 19 Mar 2019 08:39:19 +0000"
                    },
                    {
                        "name": "MIME-Version",
                        "value": "1.0"
                    },
                    {
                        "name": "Content-Type",
                        "value": "multipart/alternative; boundary=\"_av-303Httd0ZOEKV5Vr5kAg-A\""
                    }
                ]
            }
        },
        {
            "id": "1599518a6f32a3b1",
            "threadId": "1599518a6f32a3b1",
            "labelIds": [
                "UNREAD",
                "INBOX"
            ],
            "snippet": "Amazon Web Services Only 1 week until AWSome Day Online Conference starts.",
            "payload": {
                "headers": [
                    {
                        "name": "Delivered-To",
                        "value": "me@email.com"
                    },
                    {
                        "name": "Received",
                        "value": "by 2002:a19::0:0:0:0:0 with SMTP id;        Tue, 19 Mar 2019 01:36:54 -0700 (PDT)"
                    },
                    {
                        "name": "X-Received",
                        "value": "by ::906:fd5:: with SMTP id;        Tue, 19 Mar 2019 01:36:54 -0700 (PDT)"
                    },
                    {
                        "name": "ARC-Seal",
                        "value": "i=2; a=rsa-sha256; t=1552984614; cv=pass;"
                    },
                    {
                        "name": "ARC-Message-Signature",
                        "value": "i=2; a=rsa-sha256; c=relaxed/relaxed;"
                    },
                    {
                        "name": "ARC-Authentication-Results",
                        "value": "i=2; mx.google.com;"
                    },
                    {
                        "name": "Return-Path",
                        "value": "<bla.bla+caf_=foo.bar=gmail.com@gmail.com>"
                    },
                    {
                        "name": "Received",
                        "value": "from receiver"
                    },
                    {
                        "name": "Received-SPF",
                        "value": "pass"
                    },
                    {
                        "name": "Authentication-Results",
                        "value": "mx.google.com;"
                    },
                    {
                        "name": "X-Google-DKIM-Signature",
                        "value": "v=1; a=rsa-sha256; c=relaxed/relaxed;"
                    },
                    {
                        "name": "X-Gm-Message-State",
                        "value": "APj"
                    },
                    {
                        "name": "X-Received",
                        "value": "by ::906:5249:: with SMTP id;        Tue, 19 Mar 2019 01:36:54 -0700 (PDT)"
                    },
                    {
                        "name": "X-Forwarded-To",
                        "value": "me@email.com"
                    },
                    {
                        "name": "X-Forwarded-For",
                        "value": "other@email.com me@email.com"
                    },
                    {
                        "name": "Delivered-To",
                        "value": "other@email.com"
                    },
                    {
                        "name": "Received",
                        "value": "by ::906:355a:0:0:0:0 with SMTP id;        Tue, 19 Mar 2019 01:36:52 -0700 (PDT)"
                    },
                    {
                        "name": "X-Google-Smtp-Source",
                        "value": "APX"
                    },
                    {
                        "name": "X-Received",
                        "value": "by ::201:: with SMTP id;        Tue, 19 Mar 2019 01:36:52 -0700 (PDT)"
                    },
                    {
                        "name": "ARC-Seal",
                        "value": "i=1; a=rsa-sha256; t=1552984612; cv=none;"
                    },
                    {
                        "name": "ARC-Message-Signature",
                        "value": "i=1; a=rsa-sha256; c=relaxed/relaxed;"
                    },
                    {
                        "name": "ARC-Authentication-Results",
                        "value": "i=1; mx.google.com;"
                    },
                    {
                        "name": "Return-Path",
                        "value": "<0100016995189b71000000@amazonses.com>"
                    },
                    {
                        "name": "Received",
                        "value": "from a10-25.smtp"
                    },
                    {
                        "name": "Received-SPF",
                        "value": "pass (google.com)"
                    },
                    {
                        "name": "DKIM-Signature",
                        "value": "v=1; a=rsa-sha256;"
                    },
                    {
                        "name": "DKIM-Signature",
                        "value": "v=1; a=rsa-sha256;"
                    },
                    {
                        "name": "X-MSFBL",
                        "value": "HxYxSKUFG81EW59eM2"
                    },
                    {
                        "name": "Date",
                        "value": "Tue, 19 Mar 2019 08:36:51 +0000"
                    },
                    {
                        "name": "From",
                        "value": "Amazon Web Services <aws-marketing-email-replies@amazon.com>"
                    },
                    {
                        "name": "Reply-To",
                        "value": "aws-marketing-email-replies@amazon.com"
                    },
                    {
                        "name": "To",
                        "value": "other@email.com"
                    },
                    {
                        "name": "Message-ID",
                        "value": "<0100016995189b71000000@email.amazonses.com>"
                    },
                    {
                        "name": "Subject",
                        "value": "Don't miss your chance to join us for AWSome Day Online"
                    },
                    {
                        "name": "MIME-Version",
                        "value": "1.0"
                    },
                    {
                        "name": "Content-Type",
                        "value": "multipart/alternative; boundary=\"----=_Part_-1061830253_1938436018.1552984593886\""
                    },
                    {
                        "name": "X-PVIQ",
                        "value": "mkto-112TZM766-000001-000000-728229"
                    },
                    {
                        "name": "X-Binding",
                        "value": "bg-sjr-03"
                    },
                    {
                        "name": "X-MarketoID",
                        "value": "112-TZM-766:55831151-2"
                    },
                    {
                        "name": "X-MktArchive",
                        "value": "false"
                    },
                    {
                        "name": "List-Unsubscribe",
                        "value": "<mailto:728229.239056.9@unsub-sj.mktomail.com>"
                    },
                    {
                        "name": "X-Mailfrom",
                        "value": "112-TZM-766.0.55831151-2@em-sj-77.mktomail.com"
                    },
                    {
                        "name": "X-MSYS-API",
                        "value": "{\"options\":{\"open_tracking\":false,\"click_tracking\":false}}"
                    },
                    {
                        "name": "X-AMAZON-MAIL-RELAY-REDIR",
                        "value": "bb9b4539191b44348ef"
                    },
                    {
                        "name": "X-SES-Outgoing",
                        "value": "2019.03.19-54.240.10.25"
                    },
                    {
                        "name": "Feedback-ID",
                        "value": "1.us-east-1.RV8Dsk7NvPH6aSFSPkf=:AmazonSES"
                    }
                ]
            }
        }
    ]

    return emails
