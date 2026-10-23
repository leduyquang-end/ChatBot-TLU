import sqlite3
from types import SimpleNamespace

import pytest

from src.shared.common.errors import ConfigError
from src.shared.database import connect, db_connection, get_connection
from src.shared.database import connection as connection_mod


def test_connect_tao_file_va_query_duoc(tmp_path):
    url = f"sqlite:///{tmp_path / 'sub' / 'app.db'}"
    conn = connect(url)
    conn.execute("CREATE TABLE demo (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute("INSERT INTO demo (name) VALUES (?)", ("tieng viet",))
    conn.commit()
    row = conn.execute("SELECT name FROM demo").fetchone()
    assert row["name"] == "tieng viet"
    conn.close()
    assert (tmp_path / "sub" / "app.db").is_file()


def test_connect_bat_foreign_keys(tmp_path):
    conn = connect(f"sqlite:///{tmp_path / 'fk.db'}")
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    conn.close()


def test_memory_duoc_ho_tro():
    conn = connect("sqlite:///:memory:")
    conn.execute("CREATE TABLE x (id INTEGER)")
    conn.close()


def test_connect_file_o_thu_muc_hien_tai(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    conn = connect("sqlite:///app.db")
    conn.execute("CREATE TABLE x (id INTEGER)")
    conn.close()
    assert (tmp_path / "app.db").is_file()


def test_dialect_khac_nem_config_error():
    with pytest.raises(ConfigError, match="mysql"):
        connect("mysql://localhost/db")


def test_url_sai_nem_config_error():
    with pytest.raises(ConfigError):
        connect("khong-phai-url")
    with pytest.raises(ConfigError, match="thiếu đường dẫn"):
        connect("sqlite:///")


def test_get_connection_dung_settings(monkeypatch, tmp_path):
    monkeypatch.setattr(
        connection_mod,
        "get_settings",
        lambda: SimpleNamespace(
            database_url=f"sqlite:///{tmp_path / 'via-settings.db'}"
        ),
    )
    conn = get_connection()
    conn.execute("SELECT 1")
    conn.close()
    assert (tmp_path / "via-settings.db").is_file()


def test_db_connection_tu_dong_dong(monkeypatch, tmp_path):
    monkeypatch.setattr(
        connection_mod,
        "get_settings",
        lambda: SimpleNamespace(database_url=f"sqlite:///{tmp_path / 'ctx.db'}"),
    )
    with db_connection() as conn:
        conn.execute("CREATE TABLE t (id INTEGER)")
    with pytest.raises(sqlite3.ProgrammingError):
        conn.execute("SELECT 1")
