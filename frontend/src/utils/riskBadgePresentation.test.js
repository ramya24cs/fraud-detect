import assert from "node:assert/strict";
import test from "node:test";

import { getRiskBadgePresentation } from "./riskBadgePresentation.js";

test("risk badge presents the API-provided risk level and matching color class", () => {
  for (const level of ["LOW", "MEDIUM", "HIGH"]) {
    const badge = getRiskBadgePresentation(level);

    assert.equal(badge.label, level);
    assert.equal(badge.className, `risk-badge risk-${level.toLowerCase()}`);
    assert.equal(badge.ariaLabel, `${level} risk`);
  }
});

test("risk badge does not invent a tier for unknown API values", () => {
  assert.deepEqual(getRiskBadgePresentation(""), {
    label: "UNKNOWN",
    className: "risk-badge risk-unknown",
    ariaLabel: "UNKNOWN risk",
  });
});
