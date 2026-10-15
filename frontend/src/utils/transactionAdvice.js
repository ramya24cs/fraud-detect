export function getTransactionAdvice(assessment, question) {
  if (question === "email") {
    if (assessment.review_notification_status === "SENT") {
      return "The mail server accepted the review email for the address on your signed-in account. Check that the address is correct and look in your inbox and spam folder. A bounce notice means that address could not receive it.";
    }
    if (assessment.review_notification_status === "FAILED") {
      return "The transaction is saved for review, but the email could not be delivered. Use the review buttons on this page or contact support.";
    }
    if (assessment.review_notification_status === "NOT_CONFIGURED") {
      return "The transaction is saved for review, but an email could not be sent. You can still make the decision using the review buttons on this page.";
    }
    return "No review email was required for this LOW assessment.";
  }

  if (question === "recognized") {
    return assessment.review_required
      ? "If you recognize and authorize this transaction, verify the recipient, amount, and reference in your bank or payment app, then choose “Disagree” in the human review section if the risk flag is incorrect."
      : "If you recognize the transaction, verify the amount and recipient in your bank or payment app. This assessment cannot confirm the transaction is safe.";
  }

  if (question === "unrecognized") {
    return "If you do not recognize or authorize it, do not approve it. Contact your bank or payment provider using its official app or phone number, report the transaction, and ask about blocking the payment method. Never share your PIN, password, or one-time code.";
  }

  if (assessment.review_required) {
    return "This transaction is awaiting human review; the risk flag is not proof of fraud. If you did not authorize it, contact your bank immediately using the number in its official app or on your card, and ask them to block the payment method and secure your account. If you are in India, call 1930 as soon as possible to report suspected financial cyber fraud, then file a report at cybercrime.gov.in. Never share your PIN, password, or one-time code. If you recognize and authorized the transaction, review the details below and choose “Disagree”; otherwise choose “Agree with risk.”";
  }

  return "Check that the amount and currency are correct, then verify the transaction in your bank or payment app. This assessment cannot confirm whether a transaction is fraudulent.";
}
