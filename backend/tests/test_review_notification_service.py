from uuid import uuid4

from backend.app.core import config
from backend.app.core.config import settings
from backend.app.services import review_notification_service


def test_email_settings_reload_after_env_file_changes(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DATABASE_URL=postgresql://user:pass@localhost/db\n"
        "SMTP_HOST=smtp.gmail.com\n"
        "SMTP_USERNAME=refreshed@example.test\n"
        "SMTP_PASSWORD=test-app-password\n"
        "SMTP_FROM_EMAIL=refreshed@example.test\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(config, "_SETTINGS_ENV_FILE", env_file)
    monkeypatch.setattr(config, "_SETTINGS_ENV_FILE_MTIME_NS", None)

    refreshed = config.get_current_settings()

    assert refreshed.SMTP_HOST == "smtp.gmail.com"
    assert refreshed.SMTP_USERNAME == "refreshed@example.test"
    assert refreshed.SMTP_FROM_EMAIL == "refreshed@example.test"
    assert config._SETTINGS_ENV_FILE_MTIME_NS == env_file.stat().st_mtime_ns


def _configure_email(monkeypatch):
    values = {
        "SMTP_HOST": "smtp.example.test",
        "SMTP_PORT": 587,
        "SMTP_USERNAME": "sender@example.test",
        "SMTP_PASSWORD": "test-password",
        "SMTP_FROM_EMAIL": "sender@example.test",
        "SMTP_USE_STARTTLS": True,
        "FRONTEND_BASE_URL": "http://localhost:5173",
    }
    for name, value in values.items():
        monkeypatch.setattr(settings, name, value)


def test_review_notification_reports_missing_configuration(monkeypatch):
    monkeypatch.setattr(settings, "SMTP_HOST", None)
    result = review_notification_service.send_review_notification(
        assessment_id=uuid4(),
        recipient_email="signed-in@example.test",
        transaction={"amount": 100, "currency": "INR"},
        risk_level="MEDIUM",
    )

    assert result["status"] == "NOT_CONFIGURED"
    assert "could not be sent" in result["message"]
    assert "SMTP" not in result["message"]
    assert "could not be sent" in result["message"]
    assert result["recipient"] == "signed-in@example.test"
    assert result["subject"] == "Transaction review requested: MEDIUM"
    assert "Amount: INR 100.00" in result["content"]
    assert "SMTP" not in result["message"]


def test_review_notification_sends_review_link(monkeypatch):
    _configure_email(monkeypatch)
    sent_messages = []

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            assert host == "smtp.example.test"
            assert port == 587
            assert timeout == 10

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def starttls(self, context):
            assert context is not None

        def login(self, username, password):
            assert username == "sender@example.test"
            assert password == "test-password"

        def send_message(self, message):
            sent_messages.append(message)
            return {}

    monkeypatch.setattr(review_notification_service.smtplib, "SMTP", FakeSMTP)
    assessment_id = uuid4()
    result = review_notification_service.send_review_notification(
        assessment_id=assessment_id,
        recipient_email="signed-in@example.test",
        transaction={
            "amount": 100,
            "currency": "INR",
            "occurred_at": "2026-10-14T17:30:00+05:30",
            "transaction_type": "UPI",
            "merchant": "Family",
            "channel": "Mobile app",
            "reference": "TX-1",
            "location": "Pune",
            "remarks": "Rent payment",
        },
        risk_level="MEDIUM",
    )

    assert result["status"] == "SENT"
    assert len(sent_messages) == 1
    assert sent_messages[0]["To"] == "signed-in@example.test"
    content = sent_messages[0].get_content()
    assert f"/predict-transaction?review={assessment_id}" in content
    assert "above INR 2,000" not in content
    assert "amount band" not in content.lower()
    for detail in (
        "Amount: INR 100.00",
        "Date and time: 2026-10-14T17:30:00+05:30",
        "Transaction type: UPI",
        "Merchant or recipient: Family",
        "Payment channel: Mobile app",
        "Reference: TX-1",
        "Location: Pune",
        "Remarks: Rent payment",
    ):
        assert detail in content


def test_batch_review_notification_summarizes_threshold_rows(monkeypatch):
    _configure_email(monkeypatch)
    sent_messages = []

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def starttls(self, context):
            pass

        def login(self, username, password):
            pass

        def send_message(self, message):
            sent_messages.append(message)
            return {}

    monkeypatch.setattr(review_notification_service.smtplib, "SMTP", FakeSMTP)
    high_id = uuid4()
    result = review_notification_service.send_batch_review_notification(
        recipient_email="signed-in@example.test",
        assessments=[
            {
                "assessment_id": high_id,
                "risk_level": "MEDIUM",
                "amount": 50_000.01,
                "currency": "INR",
                "occurred_at": "2026-10-15T11:45:00",
                "reference": "TX-THRESHOLD",
                "merchant": "Transfer",
            }
        ],
        total_transactions=3,
        threshold_amount=50_000,
    )

    assert result["status"] == "SENT"
    assert len(sent_messages) == 1
    assert sent_messages[0]["To"] == "signed-in@example.test"
    content = sent_messages[0].get_content()
    assert "contains 3 transactions" in content
    assert "1 transaction(s) exceeded the amount threshold of 50,000.00" in content
    assert "INR 50000.01" in content
    assert "risk: MEDIUM" in content
    assert f"assessment ID: {high_id}" in content


def test_gmail_app_password_whitespace_is_removed_before_login(monkeypatch):
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "abcd efgh ijkl mnop")
    logged_in = []

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def starttls(self, context):
            pass

        def login(self, username, password):
            logged_in.append(password)

        def send_message(self, message):
            return {}

    monkeypatch.setattr(review_notification_service.smtplib, "SMTP", FakeSMTP)

    result = review_notification_service.send_review_notification(
        assessment_id=uuid4(),
        recipient_email="signed-in@example.test",
        transaction={"amount": 100, "currency": "INR"},
        risk_level="MEDIUM",
    )

    assert result["status"] == "SENT"
    assert logged_in == ["abcdefghijklmnop"]


def test_prediction_risk_alert_sends_case_link(monkeypatch):
    _configure_email(monkeypatch)
    sent_messages = []

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def starttls(self, context):
            pass

        def login(self, username, password):
            pass

        def send_message(self, message):
            sent_messages.append(message)
            return {}

    monkeypatch.setattr(review_notification_service.smtplib, "SMTP", FakeSMTP)
    transaction_id = uuid4()
    result = review_notification_service.send_prediction_risk_alert(
        recipient_email="signed-in@example.test",
        transaction_id=transaction_id,
        transaction={"Amount": 100.0},
        fraud_probability=0.75,
        decision="REVIEW",
    )

    assert result["status"] == "SENT"
    assert len(sent_messages) == 1
    assert sent_messages[0]["To"] == "signed-in@example.test"
    assert "75.00%" in sent_messages[0].get_content()
    assert f"/case/{transaction_id}" in sent_messages[0].get_content()


def test_prediction_risk_alert_reports_missing_smtp(monkeypatch):
    monkeypatch.setattr(settings, "SMTP_HOST", None)
    result = review_notification_service.send_prediction_risk_alert(
        recipient_email="signed-in@example.test",
        transaction_id=uuid4(),
        transaction={"Amount": 100.0},
        fraud_probability=0.75,
        decision="BLOCK",
    )

    assert result["status"] == "NOT_CONFIGURED"
