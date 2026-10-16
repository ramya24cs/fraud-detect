const HEADER_ALIASES = {
  amount: [
    "amount",
    "transactionamount",
    "transactionvalue",
    "value",
    "debit",
    "debitamount",
    "withdrawal",
    "withdrawalamount",
  ],
  credit: ["credit", "deposit", "creditamount"],
  date: [
    "date",
    "transactiondate",
    "datetime",
    "transactiondatetime",
    "valuedate",
    "time",
  ],
  currency: ["currency", "currencycode"],
  merchant: [
    "merchant",
    "description",
    "details",
    "narration",
    "narrative",
    "particulars",
    "recipient",
    "payee",
    "beneficiary",
    "counterparty",
  ],
  type: ["type", "transactiontype", "paymenttype"],
  channel: ["channel", "paymentchannel", "method", "mode"],
  reference: ["reference", "referenceid", "transactionid", "id"],
  location: ["location", "city", "region"],
  remarks: ["remarks", "note", "notes"],
};

const DEFAULT_RECORD = {
  amount: "",
  currency: "INR",
  occurredAt: "",
  type: "Other / Unknown",
  merchant: "",
  channel: "Other",
  reference: "",
  location: "",
  remarks: "",
};

export async function isTransactionPdf(file) {
  if (
    file.type?.toLowerCase() === "application/pdf" ||
    /\.pdf(?:$|[ .(])/i.test(file.name ?? "")
  ) {
    return true;
  }

  const signature = new TextDecoder().decode(
    await file.slice(0, 5).arrayBuffer()
  );
  return signature === "%PDF-";
}

function detectCsvDelimiter(text) {
  const firstLine = text.split(/\r\n|\n|\r/, 1)[0] ?? "";
  const counts = new Map([
    [",", 0],
    [";", 0],
    ["\t", 0],
  ]);
  let quoted = false;

  for (let index = 0; index < firstLine.length; index += 1) {
    const character = firstLine[index];
    if (character === '"' && firstLine[index + 1] === '"' && quoted) {
      index += 1;
    } else if (character === '"') {
      quoted = !quoted;
    } else if (!quoted && counts.has(character)) {
      counts.set(character, counts.get(character) + 1);
    }
  }

  return [...counts.entries()].sort((left, right) => right[1] - left[1])[0][0];
}

function parseCsvRows(text, delimiter) {
  const rows = [];
  let row = [];
  let cell = "";
  let quoted = false;

  for (let index = 0; index < text.length; index += 1) {
    const character = text[index];
    if (quoted) {
      if (character === '"' && text[index + 1] === '"') {
        cell += '"';
        index += 1;
      } else if (character === '"') {
        quoted = false;
      } else {
        cell += character;
      }
    } else if (character === '"' && cell.length === 0) {
      quoted = true;
    } else if (character === delimiter) {
      row.push(cell.trim());
      cell = "";
    } else if (character === "\n" || character === "\r") {
      if (character === "\r" && text[index + 1] === "\n") index += 1;
      row.push(cell.trim());
      if (row.some((value) => value !== "")) rows.push(row);
      row = [];
      cell = "";
    } else {
      cell += character;
    }
  }

  if (quoted) {
    throw new Error("The CSV has an unterminated quoted field.");
  }

  row.push(cell.trim());
  if (row.some((value) => value !== "")) rows.push(row);
  return rows;
}

function parseAmount(value) {
  if (value === undefined || value === null) return "";
  const text = String(value).trim();
  if (!text) return "";

  const negative = /^\(.*\)$/.test(text) || /^\s*-/.test(text);
  const normalized = text
    .replace(/[₹$€£]/g, "")
    .replace(/\b[A-Z]{3}\b|Rs\.?/gi, "")
    .replace(/[(),\s]/g, "");
  const number = Number(normalized);
  return Number.isFinite(number) && number > 0 && !negative ? number : "";
}

function toLocalDateTime(year, month, day, hour = 0, minute = 0, second = 0) {
  const date = new Date(year, month - 1, day, hour, minute, second);
  if (
    date.getFullYear() !== year ||
    date.getMonth() !== month - 1 ||
    date.getDate() !== day
  ) {
    return "";
  }
  const pad = (value) => String(value).padStart(2, "0");
  return `${year}-${pad(month)}-${pad(day)}T${pad(hour)}:${pad(minute)}`;
}

export function parseTransactionDate(value) {
  const text = String(value ?? "").trim();
  if (!text) return "";

  if (/^\d{4}-\d{1,2}-\d{1,2}T.*(?:Z|[+-]\d{2}:?\d{2})$/i.test(text)) {
    const zonedDate = new Date(text);
    if (Number.isNaN(zonedDate.getTime())) return "";
    const pad = (number) => String(number).padStart(2, "0");
    return `${zonedDate.getFullYear()}-${pad(
      zonedDate.getMonth() + 1
    )}-${pad(zonedDate.getDate())}T${pad(zonedDate.getHours())}:${pad(
      zonedDate.getMinutes()
    )}`;
  }

  const iso = text.match(
    /^(\d{4})-(\d{1,2})-(\d{1,2})(?:[T\s](\d{1,2}):(\d{2})(?::(\d{2}))?)?/
  );
  if (iso) {
    return toLocalDateTime(
      Number(iso[1]),
      Number(iso[2]),
      Number(iso[3]),
      Number(iso[4] ?? 0),
      Number(iso[5] ?? 0),
      Number(iso[6] ?? 0)
    );
  }

  const dayFirst = text.match(
    /^(\d{1,2})[/-](\d{1,2})[/-](\d{4})(?:[,\s]+(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(AM|PM)?)?/i
  );
  if (dayFirst) {
    let hour = Number(dayFirst[4] ?? 0);
    const meridiem = dayFirst[7]?.toUpperCase();
    if (meridiem === "PM" && hour < 12) hour += 12;
    if (meridiem === "AM" && hour === 12) hour = 0;
    return toLocalDateTime(
      Number(dayFirst[3]),
      Number(dayFirst[2]),
      Number(dayFirst[1]),
      hour,
      Number(dayFirst[5] ?? 0),
      Number(dayFirst[6] ?? 0)
    );
  }

  const monthNames =
    "jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?";
  const textualDate = text.match(
    new RegExp(
      `^(?:(\\d{1,2})[\\s/-]+(${monthNames})[\\s,/-]+(\\d{2,4})|(${monthNames})[\\s/-]+(\\d{1,2}),?[\\s/-]+(\\d{2,4}))(?:[,\\s]+(\\d{1,2}):(\\d{2})(?::(\\d{2}))?\\s*(AM|PM)?)?`,
      "i"
    )
  );
  if (textualDate) {
    const monthName = textualDate[2] ?? textualDate[4];
    const month = new Date(`${monthName} 1, 2000`).getMonth() + 1;
    let year = Number(textualDate[3] ?? textualDate[6]);
    if (year < 100) year += year < 50 ? 2000 : 1900;
    let hour = Number(textualDate[7] ?? 0);
    const meridiem = textualDate[10]?.toUpperCase();
    if (meridiem === "PM" && hour < 12) hour += 12;
    if (meridiem === "AM" && hour === 12) hour = 0;
    return toLocalDateTime(
      year,
      month,
      Number(textualDate[1] ?? textualDate[5]),
      hour,
      Number(textualDate[8] ?? 0),
      Number(textualDate[9] ?? 0)
    );
  }

  const parsed = new Date(text);
  if (Number.isNaN(parsed.getTime())) return "";
  const pad = (value) => String(value).padStart(2, "0");
  return `${parsed.getFullYear()}-${pad(parsed.getMonth() + 1)}-${pad(
    parsed.getDate()
  )}T${pad(parsed.getHours())}:${pad(parsed.getMinutes())}`;
}

function normalizeCurrency(value) {
  const text = String(value ?? "").trim().toUpperCase();
  if (["INR", "₹", "RS", "RS."].includes(text)) return "INR";
  if (["USD", "$"].includes(text)) return "USD";
  if (["EUR", "€"].includes(text)) return "EUR";
  if (["GBP", "£"].includes(text)) return "GBP";
  return /^[A-Z]{3}$/.test(text) ? text : "INR";
}

export function parseTransactionCsv(text) {
  const normalizedText = String(text)
    .replace(/^\uFEFF/, "")
    .replace(/\0/g, "");
  const rows = parseCsvRows(
    normalizedText,
    detectCsvDelimiter(normalizedText)
  );
  if (rows.length < 2) {
    throw new Error("The CSV must contain a header row and at least one transaction.");
  }

  const headers = rows[0].map((header) =>
    header.toLowerCase().replace(/[^a-z0-9]/g, "")
  );
  const columns = {};
  for (const [field, aliases] of Object.entries(HEADER_ALIASES)) {
    columns[field] = headers.findIndex((header) => aliases.includes(header));
  }

  if (columns.amount < 0 && columns.credit < 0) {
    throw new Error(
      "Could not find an amount column. Use a header such as Amount, Debit, Withdrawal, or Credit."
    );
  }
  if (columns.date < 0) {
    throw new Error(
      "Could not find a transaction date column. Use a header such as Date or Transaction Date."
    );
  }

  const cell = (row, column) => (column < 0 ? "" : row[column] ?? "");
  return rows.slice(1).map((row, index) => {
    const amount =
      parseAmount(cell(row, columns.amount)) ||
      parseAmount(cell(row, columns.credit));
    return {
      ...DEFAULT_RECORD,
      id: `csv-${index + 1}`,
      sourceRow: index + 2,
      amount,
      currency: normalizeCurrency(cell(row, columns.currency)),
      occurredAt: parseTransactionDate(cell(row, columns.date)),
      merchant: cell(row, columns.merchant).slice(0, 150),
      type: cell(row, columns.type).slice(0, 50) || DEFAULT_RECORD.type,
      channel: cell(row, columns.channel).slice(0, 50) || DEFAULT_RECORD.channel,
      reference: cell(row, columns.reference).slice(0, 100),
      location: cell(row, columns.location).slice(0, 150),
      remarks: cell(row, columns.remarks).slice(0, 500),
    };
  });
}

const PDF_DATE_PATTERN =
  /\b(?:\d{4}[/-]\d{1,2}[/-]\d{1,2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}[\s/-]+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[\s,/-]+\d{2,4}|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[\s/-]+\d{1,2},?[\s/-]+\d{2,4})(?:[,\s]+\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?)?/i;
const PDF_AMOUNT_PATTERN =
  /(?:₹|\b[A-Z]{3}\s*|Rs\.?)?\(?-?\d[\d,]*(?:\.\d{1,2})?\)?/gi;

const PDF_NON_TRANSACTION_PATTERN =
  /\b(?:statement\s+(?:period|date|summary)|opening\s+balance|closing\s+balance|brought\s+forward|carried\s+forward|total\s+(?:debits?|credits?|withdrawals?|deposits?)|page\s+\d+)\b/i;
const PDF_AMOUNT_HEADER_PATTERN =
  /\b(?:debit|withdrawal|withdrawn|paid\s+out|amount|transaction\s+amount|credit|deposit|paid\s+in)\b/i;
const PDF_PREFERRED_AMOUNT_HEADER_PATTERN =
  /\b(?:debit|withdrawal|withdrawn|paid\s+out|amount|transaction\s+amount)\b/i;
const PDF_EXCLUDED_AMOUNT_HEADER_PATTERN =
  /\b(?:balance|opening|closing|available|running)\b/i;

function formatPdfTextRow(items) {
  const orderedItems = [...items].sort((left, right) => left.x - right.x);
  return orderedItems
    .reduce((line, item, index) => {
      if (index === 0) return item.text;
      const previous = orderedItems[index - 1];
      const gap = item.x - (previous.x + previous.width);
      return `${line}${gap > 2 ? " " : ""}${item.text}`;
    }, "")
    .replace(/\s+/g, " ")
    .trim();
}

function findPdfAmountColumn(rows) {
  const headers = rows
    .map(({ items }) => {
      const text = formatPdfTextRow(items);
      if (PDF_DATE_PATTERN.test(text)) {
        PDF_DATE_PATTERN.lastIndex = 0;
        return null;
      }
      PDF_DATE_PATTERN.lastIndex = 0;
      return items
        .filter(
          (item) =>
            PDF_AMOUNT_HEADER_PATTERN.test(item.text) &&
            !PDF_EXCLUDED_AMOUNT_HEADER_PATTERN.test(item.text)
        )
        .map((item) => ({
          text: item.text,
          x: item.x + item.width / 2,
        }));
    })
    .flat()
    .filter(Boolean);

  const preferred = headers.find((header) =>
    PDF_PREFERRED_AMOUNT_HEADER_PATTERN.test(header.text)
  );
  return preferred?.x ?? headers[0]?.x ?? null;
}

function parsePdfTransactionLine(line, index, items, amountColumnX) {
  if (PDF_NON_TRANSACTION_PATTERN.test(line)) return null;
  const dateMatch = PDF_DATE_PATTERN.exec(line);
  PDF_DATE_PATTERN.lastIndex = 0;
  if (!dateMatch) return null;
  const occurredAt = parseTransactionDate(dateMatch[0]);
  if (!occurredAt) return null;
  const withoutDate = line.replace(dateMatch[0], " ");
  const candidateItems = items?.length
    ? items.map((item) => ({
        text: dateMatch[0]
          ? item.text.replace(dateMatch[0], " ")
          : item.text,
        x: item.x + item.width / 2,
      }))
    : [{ text: withoutDate, x: null }];
  const candidates = candidateItems
    .flatMap(({ text, x }) =>
      [...text.matchAll(PDF_AMOUNT_PATTERN)].map((match) => ({
        raw: match[0],
        amount: parseAmount(match[0]),
        x,
        strong:
          /[.,]|₹|\$|€|£|\b(?:INR|USD|EUR|GBP|Rs\.?)\b/i.test(match[0]),
      }))
    )
    .filter((candidate) => candidate.amount !== "");
  PDF_AMOUNT_PATTERN.lastIndex = 0;
  if (candidates.length === 0) return null;

  const strongCandidates = candidates.filter((candidate) => candidate.strong);
  const selectableCandidates =
    strongCandidates.length > 0 ? strongCandidates : candidates;
  const selectedCandidate =
    amountColumnX !== null
      ? [...selectableCandidates].sort(
          (left, right) =>
            Math.abs(left.x - amountColumnX) -
            Math.abs(right.x - amountColumnX)
        )[0]
      : selectableCandidates[0];
  const amount = selectedCandidate.amount;
  const merchant = withoutDate
    .replace(PDF_AMOUNT_PATTERN, " ")
    .replace(/[|•·]/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 150);
  PDF_AMOUNT_PATTERN.lastIndex = 0;
  const currencyCode = selectedCandidate?.raw.match(/\b([A-Z]{3})\b/)?.[1];
  const currencySymbol = selectedCandidate?.raw.match(/[₹$€£]/)?.[0];

  return {
    ...DEFAULT_RECORD,
    id: `pdf-${index + 1}`,
    sourceRow: index + 1,
    amount,
    currency: normalizeCurrency(currencyCode ?? currencySymbol),
    occurredAt,
    merchant,
    remarks: "",
  };
}

function groupPdfTextRows(items) {
  const lines = [];
  for (const item of items) {
    if (!item.str?.trim()) continue;
    const x = item.transform?.[4] ?? 0;
    const y = item.transform?.[5] ?? 0;
    let line = lines.find((candidate) => Math.abs(candidate.y - y) <= 3);
    if (!line) {
      line = { y, items: [] };
      lines.push(line);
    }
    line.items.push({ x, width: item.width ?? 0, text: item.str.trim() });
  }

  return lines.sort((left, right) => right.y - left.y);
}

export function parseTransactionPdfTextItems(items) {
  const rows = groupPdfTextRows(items);
  const amountColumnX = findPdfAmountColumn(rows);
  const records = parsePdfRows(rows, amountColumnX);
  if (records.length === 0) {
    throw new Error(
      "No transaction rows could be read. This PDF may be scanned or use an unsupported statement layout. Try a searchable PDF or export the statement as CSV."
    );
  }
  return records;
}

function parsePdfRows(rows, amountColumnX = null) {
  return rows
    .map(({ items }, index) =>
      parsePdfTransactionLine(
        formatPdfTextRow(items),
        index,
        items,
        amountColumnX
      )
    )
    .filter(Boolean);
}

function parsePdfLines(lines) {
  return lines
    .map((line, index) => parsePdfTransactionLine(line, index, null, null))
    .filter(Boolean);
}

function renderPdfPage(page) {
  const pageSize = page.getViewport({ scale: 1 });
  const scale = Math.min(2.2, 2200 / Math.max(pageSize.width, pageSize.height));
  const viewport = page.getViewport({ scale });
  const canvas = document.createElement("canvas");
  canvas.width = Math.ceil(viewport.width);
  canvas.height = Math.ceil(viewport.height);
  const context = canvas.getContext("2d");
  if (!context) {
    throw new Error("Could not prepare a page for scanned-PDF text recognition.");
  }
  return page.render({ canvasContext: context, viewport }).promise.then(() => canvas);
}

async function recognizePdfPages(document, onProgress) {
  let worker;
  try {
    const [tesseract, workerUrl] = await Promise.all([
      import("tesseract.js"),
      import("tesseract.js/dist/worker.min.js?url"),
    ]);
    const { createWorker } = tesseract.default ?? tesseract;
    worker = await createWorker("eng", undefined, {
      workerPath: workerUrl.default,
      logger: ({ status, progress }) => {
        if (status === "recognizing text") {
          onProgress?.(
            `Recognizing scanned statement (${Math.round(progress * 100)}%)`
          );
        } else if (status) {
          onProgress?.("Preparing OCR for scanned statement...");
        }
      },
    });
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error);
    throw new Error(
      `Could not start on-device OCR. Check the internet connection to load OCR resources and retry. ${detail}`,
      { cause: error }
    );
  }

  const lines = [];
  try {
    for (let pageNumber = 1; pageNumber <= document.numPages; pageNumber += 1) {
      onProgress?.(`Reading scanned PDF page ${pageNumber} of ${document.numPages}...`);
      const page = await document.getPage(pageNumber);
      const canvas = await renderPdfPage(page);
      try {
        let data;
        try {
          ({ data } = await worker.recognize(canvas, { rotateAuto: true }));
        } catch (error) {
          const detail = error instanceof Error ? error.message : String(error);
          throw new Error(
            `OCR could not read PDF page ${pageNumber}. ${detail}`,
            { cause: error }
          );
        }
        lines.push(
          ...data.text
            .split(/\r\n|\n|\r/)
            .map((line) => line.trim())
            .filter(Boolean)
        );
      } finally {
        canvas.width = 0;
        canvas.height = 0;
      }
    }
  } finally {
    await worker.terminate();
  }
  return lines;
}

export async function parseTransactionPdf(file, onProgress) {
  const isBrowser = typeof window !== "undefined";
  const pdfjs = isBrowser
    ? await import("pdfjs-dist")
    : await import("pdfjs-dist/legacy/build/pdf.mjs");
  if (isBrowser) {
    pdfjs.GlobalWorkerOptions.workerSrc = new URL(
      "pdfjs-dist/build/pdf.worker.min.mjs",
      import.meta.url
    ).toString();
  }
  const loadingTask = pdfjs.getDocument({
    data: await file.arrayBuffer(),
  });
  const document = await loadingTask.promise;
  if (document.numPages > 100) {
    await loadingTask.destroy();
    throw new Error("The PDF is limited to 100 pages.");
  }

  try {
    const textRecords = [];
    for (let pageNumber = 1; pageNumber <= document.numPages; pageNumber += 1) {
      const page = await document.getPage(pageNumber);
      const content = await page.getTextContent();
      const pageRows = groupPdfTextRows(content.items);
      textRecords.push(
        ...parsePdfRows(pageRows, findPdfAmountColumn(pageRows))
      );
    }

    const hasAssessableRows = (records) =>
      records.some(
        (record) =>
          Number.isFinite(Number(record.amount)) &&
          Number(record.amount) > 0 &&
          Boolean(record.occurredAt)
      );
    if (hasAssessableRows(textRecords)) {
      return textRecords.map((record, index) => ({
        ...record,
        id: `pdf-${index + 1}`,
        sourceRow: index + 1,
      }));
    }

    onProgress?.("No embedded text found. Starting on-device OCR...");
    const ocrLines = await recognizePdfPages(document, onProgress);
    const ocrRecords = parsePdfLines(ocrLines);
    if (!hasAssessableRows(ocrRecords)) {
      throw new Error(
        "No transaction rows could be identified after OCR. Check that the PDF is clear and includes transaction dates and amounts, or export it as CSV."
      );
    }
    return ocrRecords;
  } finally {
    await loadingTask.destroy();
  }
}
