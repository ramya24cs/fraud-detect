import assert from "node:assert/strict";
import test from "node:test";

import { formatCost } from "./formatters.js";

test("formats expected cost as a number without a currency symbol", () => {
  assert.equal(formatCost(1234.5), "1,234.50");
  assert.equal(formatCost(0), "0.00");
  assert.doesNotMatch(formatCost(1234.5), /₹|INR/);
});
