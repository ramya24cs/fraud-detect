import assert from "node:assert/strict";
import test from "node:test";

import {
  isTransactionPdf,
  parseTransactionCsv,
  parseTransactionDate,
  parseTransactionPdfTextItems,
} from "./transactionFileImport.js";

test("recognizes PDF files by filename, MIME type, or file signature", async () => {
  const fileWith = (name, type, bytes = "") => ({
    name,
    type,
    slice: () => ({
      arrayBuffer: async () =>
        new TextEncoder().encode(bytes.slice(0, 5)).buffer,
    }),
  });

  assert.equal(
    await isTransactionPdf(fileWith("statement.PDF", "")),
    true
  );
  assert.equal(
    await isTransactionPdf(fileWith("statement", "application/pdf")),
    true
  );
  assert.equal(
    await isTransactionPdf(fileWith("statement", "", "%PDF-1.7")),
    true
  );
  assert.equal(
    await isTransactionPdf(fileWith("transactions.csv", "text/csv")),
    false
  );
});

test("parses common transaction CSV columns and quoted descriptions", () => {
  const records = parseTransactionCsv(
    [
      "Transaction Date,Amount,Currency,Description,Reference",
      '15/10/2026 14:30,"Rs. 2,500.00",INR,"Cafe, Market",TX-1',
    ].join("\n")
  );

  assert.equal(records.length, 1);
  assert.equal(records[0].amount, 2500);
  assert.equal(records[0].currency, "INR");
  assert.equal(records[0].occurredAt, "2026-10-15T14:30");
  assert.equal(records[0].merchant, "Cafe, Market");
  assert.equal(records[0].reference, "TX-1");
  assert.equal(records[0].type, "Other / Unknown");
});

test("parses semicolon-delimited and tab-delimited CSV exports", () => {
  const semicolon = parseTransactionCsv(
    "Date;Amount;Currency;Description\n15/10/2026;2500;INR;Utility"
  );
  const tabDelimited = parseTransactionCsv(
    "Date\tAmount\tCurrency\n15/10/2026\t3000\tINR"
  );

  assert.equal(semicolon[0].amount, 2500);
  assert.equal(semicolon[0].merchant, "Utility");
  assert.equal(tabDelimited[0].amount, 3000);
});

test("uses credit when debit is empty and marks missing data for review", () => {
  const records = parseTransactionCsv(
    [
      "Date,Debit,Credit,Description",
      "2026-10-15,,750.50,Refund",
      "not-a-date,0,,Missing details",
    ].join("\n")
  );

  assert.equal(records[0].amount, 750.5);
  assert.equal(records[1].amount, "");
  assert.equal(records[1].occurredAt, "");
});

test("rejects CSV files without required headers", () => {
  assert.throws(
    () => parseTransactionCsv("Name,Value\nShop,10"),
    /Could not find a transaction date column/
  );
});

test("parses ISO and day-first transaction dates", () => {
  assert.equal(parseTransactionDate("2026-10-15"), "2026-10-15T00:00");
  assert.equal(
    parseTransactionDate("15/10/2026 09:05 PM"),
    "2026-10-15T21:05"
  );
  assert.equal(parseTransactionDate("not a date"), "");
});

test("parses common written-month statement dates", () => {
  assert.equal(parseTransactionDate("15 Oct 2026"), "2026-10-15T00:00");
  assert.equal(parseTransactionDate("Oct 15, 2026"), "2026-10-15T00:00");
  assert.equal(
    parseTransactionDate("15-Oct-2026 09:05 PM"),
    "2026-10-15T21:05"
  );
});

test("extracts PDF transaction rows from positioned text items", () => {
  const item = (str, x, y, width) => ({
    str,
    width,
    transform: [1, 0, 0, 1, x, y],
  });
  const records = parseTransactionPdfTextItems([
    item("Date", 10, 720, 24),
    item("Description", 90, 719, 58),
    item("Amount", 230, 720, 40),
    item("15 Oct 2026", 10, 690, 58),
    item("Cafe Aurora", 90, 691, 56),
    item("INR 2,500.00", 230, 690, 65),
    item("16 Oct 2026", 10, 670, 58),
    item("Metro Store", 90, 670, 54),
    item("INR 850.00", 230, 671, 55),
  ]);

  assert.equal(records.length, 2);
  assert.equal(records[0].occurredAt, "2026-10-15T00:00");
  assert.equal(records[0].amount, 2500);
  assert.equal(records[0].currency, "INR");
  assert.match(records[0].merchant, /Cafe Aurora/);
  assert.equal(records[1].occurredAt, "2026-10-16T00:00");
  assert.equal(records[1].amount, 850);
});

test("reports when a PDF contains no readable transaction dates", () => {
  assert.throws(
    () => parseTransactionPdfTextItems([{ str: "Statement summary only" }]),
    /searchable PDF or export the statement as CSV/
  );
});

test("selects transaction amount instead of balance when columns are labeled", () => {
  const item = (str, x, y, width) => ({
    str,
    width,
    transform: [1, 0, 0, 1, x, y],
  });
  const records = parseTransactionPdfTextItems([
    item("Date", 10, 720, 24),
    item("Description", 80, 720, 55),
    item("Amount", 210, 720, 40),
    item("Balance", 310, 720, 42),
    item("Statement period 01 Oct 2026 to 31 Oct 2026", 10, 700, 210),
    item("Opening balance INR 18,000.00", 10, 680, 190),
    item("15 Oct 2026", 10, 650, 58),
    item("UPI transfer", 80, 650, 60),
    item("INR 2,500.00", 210, 650, 65),
    item("INR 18,000.00", 310, 650, 70),
  ]);

  assert.equal(records.length, 1);
  assert.equal(records[0].amount, 2500);
  assert.equal(records[0].remarks, "");
});

test("skips date-bearing statement summary lines without a transaction amount", () => {
  const records = parseTransactionPdfTextItems([
    {
      str: "Statement period 01 Oct 2026 to 31 Oct 2026",
      width: 220,
      transform: [1, 0, 0, 1, 10, 690],
    },
    {
      str: "15 Oct 2026 Cafe Aurora INR 250.00",
      width: 220,
      transform: [1, 0, 0, 1, 10, 660],
    },
  ]);

  assert.equal(records.length, 1);
  assert.match(records[0].merchant, /Cafe Aurora/);
});
