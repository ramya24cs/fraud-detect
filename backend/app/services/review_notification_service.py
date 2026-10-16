from __future__ import annotations

import logging
import smtplib
import ssl
from email.message import EmailMessage
from typing import Any
from uuid import UUID

from backend.app.core.config import get_current_settings

logger = logging.getLogger(__name__)


def _normalize_smtp_password(
    host: str | None,
    password: str | None,
) -> str | None:
    if password is not None and host and host.lower() in {
        "smtp.gmail.com",
        "smtp.googlemail.com",
    }:
        return "".join(password.split())
    return password


def send_review_notification(
    *,
    assessment_id: UUID,
    recipient_email: str,
    transaction: dict[str, Any],
    risk_level: str,
) -> dict[str, str | None]:
    mail_settings = get_current_settings()
    host = mail_settings.SMTP_HOST
    sender = mail_settings.SMTP_FROM_EMAIL or mail_settings.SMTP_USERNAME
    username = mail_settings.SMTP_USERNAME
    password = _normalize_smtp_password(
        host,
        mail_settings.SMTP_PASSWORD,
    )

    base_url = mail_settings.FRONTEND_BASE_URL.rstrip("/")
    review_url = f"{base_url}/predict-transaction?review={assessment_id}"
    amount = transaction["amount"]
    currency = transaction["currency"]
    transaction_details = (
        ("Date and time", transaction.get("occurred_at")),
        ("Transaction type", transaction.get("transaction_type")),
        ("Merchant or recipient", transaction.get("merchant")),
        ("Payment channel", transaction.get("channel")),
        ("Reference", transaction.get("reference")),
        ("Location", transaction.get("location")),
        ("Remarks", transaction.get("remarks")),
    )
    detail_lines = "\n".join(
        f"{label}: {value or 'Not provided'}"
        for label, value in transaction_details
    )
    subject = f"Transaction review requested: {risk_level}"
    content = (
        "A transaction assessment needs a human agree/disagree decision.\n\n"
        f"Risk level: {risk_level}\n"
        f"Amount: {currency} {amount:.2f}\n"
        f"{detail_lines}\n"
        f"Assessment ID: {assessment_id}\n\n"
        "Sign in to the fraud assessment application to agree or disagree "
        f"with the assessment:\n{review_url}\n\n"
        "This alert is a review aid and is not proof of fraud."
    )

    if not host or not sender:
        return {
            "status": "NOT_CONFIGURED",
            "message": (
                "Your transaction is saved for review, but the email could "
                "not be sent. You can review it on this page."
            ),
            "recipient": recipient_email,
            "subject": subject,
            "content": content,
        }

    if bool(username) != bool(password):
        return {
            "status": "NOT_CONFIGURED",
            "message": (
                "Your transaction is saved for review, but the email could "
                "not be sent. You can review it on this page."
            ),
            "recipient": recipient_email,
            "subject": subject,
            "content": content,
        }

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient_email
    message.set_content(content)

    try:
        with smtplib.SMTP(host, mail_settings.SMTP_PORT, timeout=10) as client:
            if mail_settings.SMTP_USE_STARTTLS:
                client.starttls(context=ssl.create_default_context())
            if username and password:
                client.login(username, password)
            refused = client.send_message(message)
            if refused:
                raise smtplib.SMTPRecipientsRefused(refused)
    except (OSError, smtplib.SMTPException, ValueError):
        logger.exception(
            "Unable to email reviewer for transaction assessment %s",
            assessment_id,
        )
        return {
            "status": "FAILED",
            "message": (
                "Your transaction is saved for review, but the email could "
                "not be delivered. You can review it on this page."
            ),
            "recipient": recipient_email,
            "subject": subject,
            "content": content,
        }

    return {
        "status": "SENT",
        "message": (
            f"Review email accepted for delivery to {recipient_email}. "
            "Check that the address is correct and monitor your inbox."
        ),
        "recipient": recipient_email,
        "subject": subject,
        "content": content,
    }


def send_batch_review_notification(
    *,
    recipient_email: str,
    assessments: list[dict[str, Any]],
    total_transactions: int,
    threshold_amount: float,
) -> dict[str, str | None]:
    mail_settings = get_current_settings()
    host = mail_settings.SMTP_HOST
    sender = mail_settings.SMTP_FROM_EMAIL or mail_settings.SMTP_USERNAME
    username = mail_settings.SMTP_USERNAME
    password = _normalize_smtp_password(
        host,
        mail_settings.SMTP_PASSWORD,
    )
    subject = (
        f"Transaction amount threshold exceeded: {len(assessments)} "
        f"of {total_transactions}"
    )
    review_url = f"{mail_settings.FRONTEND_BASE_URL.rstrip('/')}/predict-transaction"
    transaction_lines = "\n".join(
        f"- {item['currency']} {item['amount']:.2f} on "
        f"{item['occurred_at']} "
        f"(risk: {item['risk_level']}; "
        f"reference: {item.get('reference') or 'not provided'}; "
        f"merchant: {item.get('merchant') or 'not provided'}; "
        f"assessment ID: {item['assessment_id']})"
        for item in assessments
    )
    content = (
        f"The uploaded transaction file contains {total_transactions} "
        f"transactions. {len(assessments)} transaction(s) exceeded the "
        f"amount threshold of {threshold_amount:,.2f} in the amount's "
        "stated currency:\n\n"
        f"{transaction_lines}\n\n"
        "Sign in to review the pending assessments:\n"
        f"{review_url}\n\n"
        "This amount-based assessment is a review aid, not proof of fraud."
    )

    if not host or not sender or bool(username) != bool(password):
        return {
            "status": "NOT_CONFIGURED",
            "message": (
                "The batch contains transactions above the amount threshold, "
                "but the alert email could not be sent. The saved "
                "transactions are available in the application."
            ),
            "recipient": recipient_email,
            "subject": subject,
            "content": content,
        }

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient_email
    message.set_content(content)

    try:
        with smtplib.SMTP(host, mail_settings.SMTP_PORT, timeout=10) as client:
            if mail_settings.SMTP_USE_STARTTLS:
                client.starttls(context=ssl.create_default_context())
            if username and password:
                client.login(username, password)
            refused = client.send_message(message)
            if refused:
                raise smtplib.SMTPRecipientsRefused(refused)
    except (OSError, smtplib.SMTPException, ValueError):
        logger.exception(
            "Unable to email reviewer for threshold-exceeding transaction batch"
        )
        return {
            "status": "FAILED",
            "message": (
                "The batch contains transactions above the amount threshold, "
                "but the alert email could not be delivered. The saved "
                "transactions are available in the application."
            ),
            "recipient": recipient_email,
            "subject": subject,
            "content": content,
        }

    return {
        "status": "SENT",
        "message": (
            f"One batch review email was accepted for delivery to "
            f"{recipient_email}."
        ),
        "recipient": recipient_email,
        "subject": subject,
        "content": content,
    }


def send_prediction_risk_alert(
    *,
    recipient_email: str,
    transaction_id: UUID,
    transaction: dict[str, Any],
    fraud_probability: float,
    decision: str,
) -> dict[str, str | None]:
    mail_settings = get_current_settings()
    host = mail_settings.SMTP_HOST
    sender = mail_settings.SMTP_FROM_EMAIL or mail_settings.SMTP_USERNAME
    username = mail_settings.SMTP_USERNAME
    password = _normalize_smtp_password(
        host,
        mail_settings.SMTP_PASSWORD,
    )

    if not host or not sender:
        return {
            "status": "NOT_CONFIGURED",
            "message": (
                "The high-risk prediction is saved, but the email could not "
                "be sent. You can review the transaction in the application."
            ),
        }

    if bool(username) != bool(password):
        return {
            "status": "NOT_CONFIGURED",
            "message": (
                "The high-risk prediction is saved, but the email could not "
                "be sent. You can review the transaction in the application."
            ),
        }

    case_url = (
        f"{mail_settings.FRONTEND_BASE_URL.rstrip('/')}/case/{transaction_id}"
    )
    amount = float(transaction["Amount"])
    message = EmailMessage()
    message["Subject"] = "High-risk transaction prediction"
    message["From"] = sender
    message["To"] = recipient_email
    message.set_content(
        "The fraud model classified a transaction as HIGH RISK.\n\n"
        f"Fraud probability: {fraud_probability:.2%} (raw model output; "
        "not calibrated)\n"
        f"Cost-sensitive action: {decision}\n"
        f"Amount: {amount:.2f}\n"
        f"Open the transaction case: {case_url}\n\n"
        "This is a model estimate, not confirmation of fraud."
    )

    try:
        with smtplib.SMTP(
            host,
            mail_settings.SMTP_PORT,
            timeout=10,
        ) as client:
            if mail_settings.SMTP_USE_STARTTLS:
                client.starttls(context=ssl.create_default_context())
            if username and password:
                client.login(username, password)
            refused = client.send_message(message)
            if refused:
                raise smtplib.SMTPRecipientsRefused(refused)
    except (OSError, smtplib.SMTPException, ValueError):
        logger.exception(
            "Unable to send high-risk prediction alert for transaction %s",
            transaction_id,
        )
        return {
            "status": "FAILED",
            "message": (
                "High-risk prediction saved, but risk-alert email could not "
                "be sent. Check SMTP settings and backend logs."
            ),
        }

    return {
        "status": "SENT",
        "message": f"High-risk alert emailed to {recipient_email}.",
    }
