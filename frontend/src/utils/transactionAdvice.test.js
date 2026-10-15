import assert from "node:assert/strict";
import test from "node:test";

import { getTransactionAdvice } from "./transactionAdvice.js";

const mediumAssessment = {
  risk_level: "MEDIUM",
  review_required: true,
  review_notification_status: "SENT",
};

test("next-step advice directs medium and high cases to human review", () => {
  const advice = getTransactionAdvice(mediumAssessment, "next");

  assert.match(advice, /awaiting human review/i);
  assert.match(advice, /Agree with risk/i);
  assert.match(advice, /not proof of fraud/i);
  assert.match(advice, /contact your bank immediately/i);
  assert.match(advice, /call 1930/i);
  assert.match(advice, /cybercrime\.gov\.in/i);
  assert.match(advice, /Never share your PIN/i);
});

test("email advice distinguishes mail-server acceptance from final delivery", () => {
  const advice = getTransactionAdvice(mediumAssessment, "email");

  assert.match(advice, /mail server accepted/i);
  assert.match(advice, /address on your signed-in account/i);
  assert.match(advice, /bounce notice/i);
});

test("email advice explains when SMTP is unavailable", () => {
  const advice = getTransactionAdvice(
    { ...mediumAssessment, review_notification_status: "NOT_CONFIGURED" },
    "email"
  );

  assert.match(advice, /an email could not be sent/i);
  assert.match(advice, /still make the decision/i);
  assert.doesNotMatch(advice, /SMTP|not configured/i);
});

test("unrecognized transaction advice recommends official bank channels", () => {
  const advice = getTransactionAdvice(mediumAssessment, "unrecognized");

  assert.match(advice, /official app or phone number/i);
  assert.match(advice, /Never share your PIN/i);
});

test("low risk advice does not imply the transaction is safe", () => {
  const advice = getTransactionAdvice(
    {
      risk_level: "LOW",
      review_required: false,
      review_notification_status: "NOT_REQUIRED",
    },
    "next"
  );

  assert.match(advice, /cannot confirm whether a transaction is fraudulent/i);
});
