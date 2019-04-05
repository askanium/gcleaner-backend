import datetime

from gcleaner.emails.parsers import GMailEmailParser


def test_gmail_parser_parses_response_object_that_contains_all_fields(gmail_api_get_3_response):
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
        "date": datetime.datetime(2019, 3, 19, 8, 36, 51, tzinfo=datetime.timezone.utc),
        "sender": "Amazon Web Services <aws-marketing-email-replies@amazon.com>",
        "receiver": "other@email.com",
        "subject": "Don't miss your chance to join us for AWSome Day Online",
        "list_unsubscribe": "<mailto:728229.239056.9@unsub-sj.mktomail.com>"
    }

    # method call
    parsed = GMailEmailParser.parse(email)

    # assertions
    assert parsed == expected


def test_gmail_parser_parses_response_object_without_all_metadata_headers(gmail_api_get_1_response):
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
        "date": datetime.datetime(2019, 3, 19, 10, 31, 21, tzinfo=datetime.timezone.utc),
        "sender": "Google <no-reply@accounts.google.com>",
        "receiver": "me@email.com",
        "subject": "GmailCleaner connected to your Google Account"
    }

    # method call
    parsed = GMailEmailParser.parse(email)

    # assertions
    assert parsed == expected


def test_gmail_parser_date_string_to_datetime_conversion():
    dates = [
        'Tue, 05 Feb 2019 12:37:09 -0800 (PST)',
        'Tue, 5 Feb 2019 12:37:09 -0800 (PST)',
        'Tue, 05 Feb 2019 12:37:09 -0800',
        'Tue, 5 Feb 2019 12:37:09 -0800',
    ]
    timezone = datetime.timezone(datetime.timedelta(-1, 57600))
    expected_date = datetime.datetime(2019, 2, 5, 12, 37, 9, tzinfo=timezone)

    for date in dates:
        parsed_date = GMailEmailParser.date_from_string(date)

        assert parsed_date == expected_date
