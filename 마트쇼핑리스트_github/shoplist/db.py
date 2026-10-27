"""SQLite 저장소.

- DB 경로는 환경 변수 SHOPLIST_DB, 없으면 프로젝트 폴더의 shoplist.db
- 모든 SQL은 ? 파라미터 바인딩을 쓴다
- Streamlit을 import하지 않는다
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from .models import CATEGORIES

DEFAULT_DB = Path(__file__).resolve().parent.parent / "shoplist.db"
FIELDS = ("name", "category", "quantity", "price", "memo")

# 분류 목록은 models.CATEGORIES의 고정 상수에서 가져옴 (사용자 입력이 아니라 SQL에 넣어도 안전)
_CATEGORY_SQL = ", ".join(f"'{key}'" for key in CATEGORIES)
SCHEMA = f"""
CREATE TABLE IF NOT EXISTS items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    category    TEXT    NOT NULL CHECK (category IN ({_CATEGORY_SQL})),
    quantity    INTEGER NOT NULL DEFAULT 1 CHECK (quantity BETWEEN 1 AND 99),
    price       INTEGER CHECK (price IS NULL OR price >= 0),
    memo        TEXT    NOT NULL DEFAULT '',
    checked     INTEGER NOT NULL DEFAULT 0 CHECK (checked IN (0, 1)),
    created_at  TEXT    NOT NULL,
    updated_at  TEXT    NOT NULL
)
"""


def db_path() -> Path:
    return Path(os.environ.get("SHOPLIST_DB") or DEFAULT_DB)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """DB 파일과 테이블이 없으면 만든다. (배포 서버는 빈 상태에서 시작)"""
    with closing(_connect()) as conn, conn:
        conn.execute(SCHEMA)


def _row(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    item = dict(row)
    item["checked"] = bool(item["checked"])
    return item


def list_items() -> list[dict]:
    with closing(_connect()) as conn:
        return [_row(r) for r in conn.execute("SELECT * FROM items ORDER BY id")]


def get_item(item_id: int) -> dict | None:
    with closing(_connect()) as conn:
        return _row(conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone())


def _insert(conn: sqlite3.Connection, item: dict) -> int:
    now = _now()
    cur = conn.execute(
        "INSERT INTO items (name, category, quantity, price, memo, checked, created_at, updated_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            item["name"], item["category"], item["quantity"],
            item.get("price"), item.get("memo") or "", int(bool(item.get("checked"))), now, now,
        ),
    )
    return cur.lastrowid


def add_item(**item) -> int:
    with closing(_connect()) as conn, conn:
        return _insert(conn, item)


def add_many(items: list[dict]) -> int:
    with closing(_connect()) as conn, conn:
        for item in items:
            _insert(conn, item)
    return len(items)


def replace_all(items: list[dict]) -> int:
    """모든 아이템을 지우고 새 목록으로 바꾼다. (한 트랜잭션 → 중간에 실패하면 원래대로)"""
    with closing(_connect()) as conn, conn:
        conn.execute("DELETE FROM items")
        for item in items:
            _insert(conn, item)
    return len(items)


def update_item(item_id: int, **fields) -> bool:
    cols = [f for f in FIELDS if f in fields]
    if not cols:
        return False
    sets = ", ".join(f"{c} = ?" for c in cols)  # 열 이름은 FIELDS에서만 옴
    values = [fields[c] for c in cols]
    with closing(_connect()) as conn, conn:
        cur = conn.execute(
            f"UPDATE items SET {sets}, updated_at = ? WHERE id = ?",
            (*values, _now(), item_id),
        )
        return cur.rowcount == 1


def set_checked(item_id: int, checked: bool) -> bool:
    with closing(_connect()) as conn, conn:
        cur = conn.execute(
            "UPDATE items SET checked = ?, updated_at = ? WHERE id = ?",
            (int(bool(checked)), _now(), item_id),
        )
        return cur.rowcount == 1


def delete_item(item_id: int) -> bool:
    with closing(_connect()) as conn, conn:
        return conn.execute("DELETE FROM items WHERE id = ?", (item_id,)).rowcount == 1


def delete_checked() -> int:
    with closing(_connect()) as conn, conn:
        return conn.execute("DELETE FROM items WHERE checked = 1").rowcount
