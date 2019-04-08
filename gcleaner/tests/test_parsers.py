import datetime

import pytz

from gcleaner.emails.parsers import GMailEmailParser


def test_gmail_parser_parses_response_object_that_contains_all_fields(user, gmail_api_get_3_response):
    email = gmail_api_get_3_response  # it contains 'List-Unsubscribe' header as well
    expected = {
        "google_id": "1599518a6f32a3b1",
        "thread_id": "1599518a6f32a3b1",
        "labels": [
            "UNREAD",
            "INBOX"
        ],
        "snippet": "Amazon Web Services Only 1 week until AWSome Day Online Conference starts.",
        "delivered_to": "other@email.com",
        "date": datetime.datetime(2019, 3, 19, 8, 36, 51, tzinfo=pytz.UTC),
        "sender": "Amazon Web Services <aws-marketing-email-replies@amazon.com>",
        "receiver": "other@email.com",
        "subject": "Don't miss your chance to join us for AWSome Day Online",
        "list_unsubscribe": "<mailto:728229.239056.9@unsub-sj.mktomail.com>"
    }

    # method call
    parsed = GMailEmailParser.parse(email, user)

    # assertions
    assert parsed == expected


def test_gmail_parser_parses_response_object_without_all_metadata_headers(user, gmail_api_get_1_response):
    email = gmail_api_get_1_response  # it does not contain 'List-Unsubscribe' header
    expected = {
        "google_id": "1599581458cf8986",
        "thread_id": "1599581458cf8986",
        "labels": [
            "UNREAD",
            "CATEGORY_PERSONAL",
            "INBOX"
        ],
        "snippet": "GmailCleaner connected to your Google Account",
        "delivered_to": "me@email.com",
        "date": datetime.datetime(2019, 3, 19, 10, 31, 21, tzinfo=pytz.UTC),
        "sender": "Google <no-reply@accounts.google.com>",
        "receiver": "me@email.com",
        "subject": "GmailCleaner connected to your Google Account"
    }

    # method call
    parsed = GMailEmailParser.parse(email, user)

    # assertions
    assert parsed == expected


def test_gmail_parser_date_string_to_datetime_conversion():
    timestamp = '1552991481000'
    expected_date = datetime.datetime(2019, 3, 19, 10, 31, 21, tzinfo=pytz.UTC)

    # method call
    parsed_date = GMailEmailParser.date_from_timestamp(timestamp)

    # assertions
    assert parsed_date == expected_date


def test_parser_automatically_adds_receiver_if_absent(user, gmail_api_get_1_response):
    # remove the "To" metadata header
    gmail_api_get_1_response['payload']['headers'] = gmail_api_get_1_response['payload']['headers'][:3]
    expected = {
        "google_id": "1599581458cf8986",
        "thread_id": "1599581458cf8986",
        "labels": [
            "UNREAD",
            "CATEGORY_PERSONAL",
            "INBOX"
        ],
        "snippet": "GmailCleaner connected to your Google Account",
        "delivered_to": "me@email.com",
        "date": datetime.datetime(2019, 3, 19, 10, 31, 21, tzinfo=pytz.UTC),
        "sender": "Google <no-reply@accounts.google.com>",
        "receiver": "me@email.com",
        "subject": "GmailCleaner connected to your Google Account"
    }

    # method call
    parsed = GMailEmailParser.parse(gmail_api_get_1_response, user)

    # assertions
    assert parsed == expected
