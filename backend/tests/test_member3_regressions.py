
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from backend.app.api.deps import require_roles
from backend.app.main import app
from backend.app.schemas.auth import UserRegister


def test_registration_schema_does_not_expose_role():
    user = UserRegister(
        email="operator@example.com",
        password="Test-Password-123!",
        role="ADMIN",
    )

    assert "role" not in UserRegister.model_fields
    assert not hasattr(user, "role")


def test_admin_route_dependency_rejects_operator():
    check_admin = require_roles("ADMIN")
    operator = SimpleNamespace(role="OPERATOR")

    with pytest.raises(HTTPException) as exc_info:
        check_admin(current_user=operator)

    assert exc_info.value.status_code == 403


def test_admin_route_dependency_accepts_admin():
    check_admin = require_roles("ADMIN")
    admin = SimpleNamespace(role="ADMIN")

    assert check_admin(current_user=admin) is admin


def test_member3_api_routes_are_registered():
    paths = app.openapi()["paths"]

    expected_routes = {
        "/auth/register",
        "/auth/login",
        "/auth/token",
        "/transactions/predict",
        "/transactions/{transaction_id}",
        "/review-queue",
        "/feedback",
        "/dashboard/summary",
        "/dashboard/cost",
        "/models/current",
        "/models",
        "/models/register",
        "/models/activate",
        "/audit-logs",
    }

    assert expected_routes.issubset(paths.keys())
