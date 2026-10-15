# Member 4 API integration contract

Base URL (existing Render service):
`https://cost-sensitive-fraud-detection.onrender.com`

All protected endpoints require:
`Authorization: Bearer <access_token>`

Obtain a token via `POST /auth/login` or `POST /auth/token`.
Public registration creates an `OPERATOR` account.

Roles in this repository: `ADMIN`, `OPERATOR`.

---

## Authentication

### `POST /auth/register`
- Auth: none
- Body: `{ "email": "string", "password": "string (>=8)" }`
- Success: `201` `{ "id", "email", "role": "OPERATOR" }`

### `POST /auth/login`
- Auth: none
- Body: `{ "email", "password" }`
- Success: `200` `{ "access_token", "token_type": "bearer", "expires_in" }`
- Errors: `401` invalid credentials

---

## Model monitoring

### `GET /models/current`
- Auth: any authenticated user (`OPERATOR` or `ADMIN`)
- Success: `200`

```json
{
  "id": "uuid",
  "version": "xgb-cost-v1",
  "artifact_path": "xgboost_baseline.joblib",
  "trained_at": "2026-10-10T00:00:00Z",
  "metrics_json": {
    "precision": 0.8125,
    "recall": 0.75,
    "f1_score": 0.78,
    "pr_auc": 0.768924,
    "roc_auc": 0.978265
  },
  "active": true
}
```

Frontend metric mapping (all under `metrics_json`):

| UI label | JSON field |
|----------|------------|
| Precision | `metrics_json.precision` |
| Recall | `metrics_json.recall` |
| F1 score | `metrics_json.f1_score` |
| PR-AUC | `metrics_json.pr_auc` |
| ROC-AUC | `metrics_json.roc_auc` |
| Active version | `version` |

Errors: `401` missing/invalid token; `404` no active model.

### `GET /models`
- Auth: `OPERATOR` or `ADMIN` (read-only history)
- Query: `limit` (1–200, default 50), `offset` (>=0)
- Success: `200`

```json
{
  "items": [
    {
      "id": "uuid",
      "version": "xgb-cost-v1",
      "artifact_path": "xgboost_baseline.joblib",
      "trained_at": "2026-10-10T00:00:00Z",
      "metrics_json": { "precision": 0.8125, "recall": 0.75, "f1_score": 0.78, "pr_auc": 0.768924, "roc_auc": 0.978265 },
      "active": true
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

Errors: `401` unauthenticated; `403` if role is neither OPERATOR nor ADMIN; `422` bad pagination.

### Admin-only (not for operator UI)
- `POST /models/register` — `ADMIN` only
- `POST /models/activate` — `ADMIN` only

Inference/prediction responses use `model_version: "xgb-cost-v1"`, matching the active registry version.

---

## Feedback

### `POST /feedback`
- Auth: authenticated `OPERATOR` or `ADMIN`
- Body:

```json
{
  "transaction_id": "uuid",
  "operator_decision": "CONFIRMED_FRAUD | CONFIRMED_GENUINE | DISPUTED | INCONCLUSIVE",
  "reason_code": "string",
  "comment": "optional string"
}
```

- Success: `201`

```json
{
  "id": "uuid",
  "transaction_id": "uuid",
  "user_id": "uuid",
  "decision": "CONFIRMED_GENUINE",
  "reason_code": "MANUAL_REVIEW",
  "comment": null,
  "created_at": "2026-10-13T00:00:00Z"
}
```

Errors: `401`; `404` unknown transaction; `409` no prediction yet; `422` validation.

### `GET /feedback`
- Auth: authenticated `OPERATOR` or `ADMIN`
- Query: `limit`, `offset`, optional `transaction_id`
- Success: `200`

```json
{
  "items": [ { "id", "transaction_id", "user_id", "decision", "reason_code", "comment", "created_at" } ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

Errors: `401` unauthenticated.

---

## Related endpoints used by monitoring / review UI

| Method | Path | Auth |
|--------|------|------|
| GET | `/review-queue` | authenticated |
| POST | `/transactions/predict` | authenticated |
| GET | `/dashboard/summary` | authenticated |
| GET | `/health` | none |
