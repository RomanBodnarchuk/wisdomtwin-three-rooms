import os
import pytest
from cryptography.fernet import Fernet

os.environ["WISDOMTWIN_ENV"] = "test"
os.environ["HOST"] = "127.0.0.1"
os.environ["WISDOMTWIN_USE_FIXTURES"] = "1"
os.environ["WISDOMTWIN_AUTH_DISABLED"] = "1"
os.environ["SLACK_CLIENT_ID"] = "local-test-client"
os.environ["SLACK_CONNECTOR_ENABLED"] = "true"
os.environ["GMAIL_CONNECTOR_ENABLED"] = "false"
os.environ["DRIVE_CONNECTOR_ENABLED"] = "false"
os.environ.pop("REDIS_URL", None)
os.environ.pop("OPENAI_API_KEY", None)
os.environ.pop("DATABASE_URL", None)
os.environ.pop("PUBLIC_BASE_URL", None)
os.environ.pop("RAILWAY_PUBLIC_URL", None)


@pytest.fixture(autouse=True)
def isolated_security_state(tmp_path, monkeypatch):
    from store import actor_subject, reset_store

    monkeypatch.setenv("WISDOMTWIN_AUTH_DB", str(tmp_path / "synthetic-auth.sqlite3"))
    monkeypatch.setenv("CONNECTOR_TOKEN_KEY", Fernet.generate_key().decode())
    actor = actor_subject.set("local")
    reset_store()
    yield
    reset_store()
    actor_subject.reset(actor)
