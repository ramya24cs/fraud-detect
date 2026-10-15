"""Idempotently store Member 1 final-test metrics on xgb-cost-v1.

Usage (from repository root, with DATABASE_URL configured):

    python -m backend.scripts.seed_xgb_cost_v1_metrics

Does not create duplicate registry rows or change the active model flag.
"""

from backend.app.db.session import SessionLocal
from backend.app.services.model_registry_service import (
    XGB_COST_V1_METRICS,
    ensure_xgb_cost_v1_metrics,
)


def main() -> None:
    db = SessionLocal()
    try:
        model = ensure_xgb_cost_v1_metrics(db)
        print(
            f"updated version={model.version} "
            f"active={model.active} "
            f"metrics={model.metrics_json}"
        )
        assert model.metrics_json == XGB_COST_V1_METRICS
    finally:
        db.close()


if __name__ == "__main__":
    main()
