"""
Database settings (task W3): read from .env, everyday login ollaa_user, no default password,
and never the administrator login postgres. Nothing here connects to the database.
"""
import pytest

import config
from etl.db_writer import DBWriter

SAFE = {
    "host": "localhost",
    "port": 5432,
    "database": "ollaa",
    "user": "ollaa_user",
    "password": "made-up-test-password",
}


def test_settings_file_is_in_the_top_project_folder():
    assert config.ENV_FILE.name == ".env"
    assert (config.ENV_FILE.parent / ".env.example").exists()


def test_no_default_password_and_everyday_login(monkeypatch):
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    monkeypatch.delenv("DB_USER", raising=False)
    db = config.DatabaseConfig()
    assert db.password == ""
    assert db.user == "ollaa_user"


def test_settings_come_from_the_environment(monkeypatch):
    monkeypatch.setenv("DB_USER", "ollaa_user")
    monkeypatch.setenv("DB_PASSWORD", SAFE["password"])
    monkeypatch.setenv("DB_PORT", "5433")
    db = config.DatabaseConfig()
    assert (db.user, db.password, db.port) == ("ollaa_user", SAFE["password"], 5433)


def test_refuses_without_password():
    writer = DBWriter(db_config={**SAFE, "password": ""})
    with pytest.raises(RuntimeError, match="DB_PASSWORD is missing"):
        writer._get_connection_params()


def test_refuses_administrator_login_without_showing_password():
    writer = DBWriter(db_config={**SAFE, "user": "postgres"})
    with pytest.raises(RuntimeError, match="ollaa_user") as error:
        writer._get_connection_params()
    assert SAFE["password"] not in str(error.value)


def test_everyday_login_accepted():
    assert DBWriter(db_config=SAFE)._get_connection_params()["user"] == "ollaa_user"


def test_scheduler_start_stops_without_password(caplog):
    # init_database is the first step of every scheduler start; it must refuse cleanly.
    writer = DBWriter(db_config={**SAFE, "password": ""})
    assert writer.init_database() is False
    assert "DB_PASSWORD is missing" in caplog.text
