from gcleaner.emails.parsers import GMailEmailParser


def test_gmail_parser_parses_response_object_that_contains_all_fields(gmail_api_response):
    email = gmail_api_response[-1]  # last email contains 'List-Unsubscribe' header as well
    expected = {
        "google_id": "1599518a6f32a3b1",
        "thread_id": "1599518a6f32a3b1",
        "labels": [
            "UNREAD",
            "INBOX"
        ],
        "snippet": "Amazon Web Services Only 1 week until AWSome Day Online Conference starts.",
        "delivered_to": "other@email.com",
        "date": "Tue, 19 Mar 2019 08:36:51 +0000",
        "sender": "Amazon Web Services <aws-marketing-email-replies@amazon.com>",
        "receiver": "other@email.com",
        "subject": "Don't miss your chance to join us for AWSome Day Online",
        "list_unsubscribe": "<mailto:728229.239056.9@unsub-sj.mktomail.com>"
    }

    # method call
    parsed = GMailEmailParser.parse(email)

    # assertions
    assert parsed == expected


def test_gmail_parser_parses_response_object_without_all_metadata_headers(gmail_api_response):
    email = gmail_api_response[0]  # first email does not contain 'List-Unsubscribe' header
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
        "date": "Tue, 19 Mar 2019 10:31:21 +0000 (UTC)",
        "sender": "Google <no-reply@accounts.google.com>",
        "receiver": "me@email.com",
        "subject": "GmailCleaner connected to your Google Account"
    }

    # method call
    parsed = GMailEmailParser.parse(email)

    # assertions
    assert parsed == expected
