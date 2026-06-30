"""
conftest.py – Shared pytest fixtures for the Endurance CRM test suite.

Fixture tiers:
  ① Unit-test fixtures  – pure Python mocks, no Docker, no network.
  ② Integration fixtures – real Postgres container via pytest-docker.

Usage:
  - Unit tests import from tier ①.
  - Integration tests use the `pg_supervisor` and `api_client_real` fixtures
    from tier ②, which require Docker to be running.

Marks:
  - pytest.mark.integration  →  requires Docker + real Postgres.
  - All other tests run without any infrastructure.
"""

import time
import pytest
import psycopg2
from unittest.mock import MagicMock, patch


# ============================================================================
# Constants
# ============================================================================

CLINIC_ID       = "test_clinic"
ADMIN_GROUP     = "TEST_ADMIN_GROUP"
DASHBOARD_WH    = "https://example.com/webhook"
PATIENT_PHONE   = "+919876543210"

# Postgres settings used in the real container
POSTGRES_DB     = "crm_test_db"
POSTGRES_USER   = "test_admin"
POSTGRES_PASS   = "test_password"
POSTGRES_PORT   = 5433          # Avoid clashing with any local PG on 5432


# ============================================================================
# ① Unit-test fixtures  (no Docker required)
# ============================================================================

@pytest.fixture
def triage():
    from agents.triage_profiler import TriageProfiler
    return TriageProfiler(clinic_id=CLINIC_ID)


@pytest.fixture
def hitl():
    from agents.hitl_manager import HITLManager
    return HITLManager(admin_whatsapp_group=ADMIN_GROUP, dashboard_webhook=DASHBOARD_WH)


@pytest.fixture
def kaizen():
    from agents.kaizen_optimizer import KaizenExpert
    return KaizenExpert(clinic_id=CLINIC_ID)


@pytest.fixture
def booking_executor():
    """BookingExecutor with a fully mocked Google Calendar service."""
    from agents.executor_booking import BookingExecutor
    ex = BookingExecutor(clinic_id=CLINIC_ID)
    mock_service = MagicMock()
    ex._service  = mock_service
    ex._creds    = MagicMock()
    return ex


@pytest.fixture
def mock_db_conn():
    """Returns (mock_conn, mock_cursor) for use in unit tests."""
    mock_conn   = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__  = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__  = MagicMock(return_value=False)
    mock_cursor.fetchone.return_value = None
    return mock_conn, mock_cursor


@pytest.fixture
def supervisor(mock_db_conn):
    """SovereignSupervisor with all DB calls mocked (unit-test tier)."""
    mock_conn, mock_cursor = mock_db_conn
    with patch("agents.supervisor.psycopg2.connect", return_value=mock_conn):
        from agents.supervisor import SovereignSupervisor
        sup = SovereignSupervisor(
            clinic_id=CLINIC_ID,
            admin_group=ADMIN_GROUP,
            dashboard_webhook=DASHBOARD_WH,
        )
        sup._mock_conn   = mock_conn
        sup._mock_cursor = mock_cursor
        return sup


# ============================================================================
# ② Integration fixtures  (requires Docker)
# ============================================================================

# ── docker_compose_file ──────────────────────────────────────────────────────
# pytest-docker looks for this fixture to find the compose file.
@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    """Points pytest-docker at our dedicated integration compose file."""
    import os
    return os.path.join(str(pytestconfig.rootdir), "tests", "docker-compose.test.yml")


# ── postgres_service ─────────────────────────────────────────────────────────
def _is_postgres_ready(host: str, port: int, user: str, password: str, dbname: str) -> bool:
    """Probes Postgres until it accepts connections."""
    try:
        conn = psycopg2.connect(
            host=host, port=port,
            user=user, password=password, dbname=dbname,
            connect_timeout=2,
        )
        conn.close()
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def postgres_service(docker_services):
    """
    Starts a real Postgres container and waits until it's ready.
    Returns the (host, port) tuple.
    """
    host = "localhost"
    docker_services.wait_until_responsive(
        timeout=60.0,
        pause=1.0,
        check=lambda: _is_postgres_ready(
            host, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASS, POSTGRES_DB
        ),
    )
    return host, POSTGRES_PORT


@pytest.fixture(scope="function")
def pg_conn(postgres_service):
    """
    Yields a fresh psycopg2 connection to the real test Postgres.
    Rolls back after each test so the DB is clean for the next one.
    """
    host, port = postgres_service
    conn = psycopg2.connect(
        host=host, port=port,
        user=POSTGRES_USER, password=POSTGRES_PASS, dbname=POSTGRES_DB,
    )
    conn.autocommit = False
    yield conn
    conn.rollback()
    conn.close()


@pytest.fixture(scope="function")
def pg_supervisor(postgres_service):
    """
    SovereignSupervisor wired to the REAL Postgres test container.
    Used exclusively in integration tests.
    """
    host, port = postgres_service
    from agents.supervisor import SovereignSupervisor

    sup = SovereignSupervisor(
        clinic_id=CLINIC_ID,
        admin_group=ADMIN_GROUP,
        dashboard_webhook=DASHBOARD_WH,
    )
    # Override the db_config to point at the test container
    sup.db_config = {
        "dbname":   POSTGRES_DB,
        "user":     POSTGRES_USER,
        "password": POSTGRES_PASS,
        "host":     host,
        "port":     port,
    }
    # Re-run table creation against the real DB
    sup._ensure_state_table()
    yield sup

    # Teardown: drop all rows written during this test
    conn = psycopg2.connect(**sup.db_config)
    with conn.cursor() as cur:
        cur.execute("DELETE FROM session_state WHERE clinic_id = %s;", (CLINIC_ID,))
    conn.commit()
    conn.close()


@pytest.fixture(scope="module")
def api_client_real(postgres_service):
    """
    FastAPI TestClient backed by a real Postgres supervisor.
    Scope is 'module' to keep the container warm across the integration test module.
    """
    host, port = postgres_service
    from fastapi.testclient import TestClient
    from agents.supervisor import SovereignSupervisor
    import main

    sup = SovereignSupervisor(
        clinic_id=CLINIC_ID,
        admin_group=ADMIN_GROUP,
        dashboard_webhook=DASHBOARD_WH,
    )
    sup.db_config = {
        "dbname":   POSTGRES_DB,
        "user":     POSTGRES_USER,
        "password": POSTGRES_PASS,
        "host":     host,
        "port":     port,
    }
    sup._ensure_state_table()
    main.supervisor = sup
    return TestClient(main.app, raise_server_exceptions=False)
