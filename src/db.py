"""
Simple async SQLite helper for deals.

Copyright (c) 2025 @killerbesto
All Rights Reserved.
"""
from __future__ import annotations

import aiosqlite
from typing import Optional, Dict, Any
import datetime

DB_PATH = "deals.db"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS deals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    initiator_id INTEGER NOT NULL,
    initiator_role TEXT,
    target_id INTEGER NOT NULL,
    target_role TEXT,
    amount TEXT,
    currency TEXT,
    inr_rate TEXT,
    payment_method TEXT,
    network TEXT,
    token_symbol TEXT,
    surcharge_usdt REAL DEFAULT 0,
    expected_total_usdt REAL,
    status TEXT NOT NULL,
    group_chat_id INTEGER,
    usdt_address TEXT,
    fee TEXT,
    tx_hash TEXT,
    tx_link TEXT,
    deposit_amount TEXT,
    deposit_network TEXT,
    invite_link TEXT,
    confirm_initiator INTEGER DEFAULT 0,
    confirm_target INTEGER DEFAULT 0,
    completed_initiator INTEGER DEFAULT 0,
    completed_target INTEGER DEFAULT 0,
    created_at TEXT,
    accepted_at TEXT,
    paid_at TEXT,
    fiat_sent_at TEXT,
    fiat_received_at TEXT,
    released_at TEXT,
    closed_at TEXT
);
"""

CREATE_GROUPS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS groups (
    chat_id INTEGER PRIMARY KEY,
    name TEXT,
    is_occupied INTEGER DEFAULT 0,
    current_deal_id INTEGER,
    created_at TEXT
);
"""


async def init_db(path: str = DB_PATH) -> None:
    async with aiosqlite.connect(path) as db:
        await db.execute(CREATE_TABLE_SQL)
        await db.execute(CREATE_GROUPS_TABLE_SQL)
        await db.commit()


async def add_group_to_pool(chat_id: int, name: str = "", path: str = DB_PATH) -> None:
    created_at = datetime.datetime.utcnow().isoformat()
    async with aiosqlite.connect(path) as db:
        # Use INSERT OR REPLACE to reset group status if already exists
        await db.execute(
            "INSERT OR REPLACE INTO groups (chat_id, name, is_occupied, current_deal_id, created_at) VALUES (?, ?, 0, NULL, ?)",
            (chat_id, name, created_at),
        )
        await db.commit()


async def get_free_group(path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM groups WHERE is_occupied = 0 LIMIT 1")
        row = await cur.fetchone()
        return dict(row) if row else None


async def occupy_group(chat_id: int, deal_id: int, path: str = DB_PATH) -> None:
    async with aiosqlite.connect(path) as db:
        await db.execute("UPDATE groups SET is_occupied = 1, current_deal_id = ? WHERE chat_id = ?", (deal_id, chat_id))
        await db.commit()


async def release_group(chat_id: int, path: str = DB_PATH) -> None:
    async with aiosqlite.connect(path) as db:
        await db.execute("UPDATE groups SET is_occupied = 0, current_deal_id = NULL WHERE chat_id = ?", (chat_id,))
        await db.commit()


async def create_deal(
    initiator_id: int,
    target_id: int,
    initiator_role: Optional[str] = None,
    amount: Optional[str] = None,
    currency: Optional[str] = None,
    inr_rate: Optional[str] = None,
    payment_method: Optional[str] = None,
    group_chat_id: Optional[int] = None,
    usdt_address: Optional[str] = None,
    fee: Optional[str] = None,
    invite_link: Optional[str] = None,
    path: str = DB_PATH
) -> int:
    created_at = datetime.datetime.utcnow().isoformat()
    # determine target role (opposite of initiator)
    target_role = "seller" if initiator_role == "buyer" else "buyer" if initiator_role == "seller" else None
    
    async with aiosqlite.connect(path) as db:
        cur = await db.execute(
            "INSERT INTO deals (initiator_id, initiator_role, target_id, target_role, amount, currency, inr_rate, payment_method, status, group_chat_id, usdt_address, fee, invite_link, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (initiator_id, initiator_role, target_id, target_role, amount, currency, inr_rate, payment_method, "pending", group_chat_id, usdt_address, fee, invite_link, created_at),
        )
        await db.commit()
        return cur.lastrowid


async def get_deal(deal_id: int, path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM deals WHERE id = ?", (deal_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_active_deal_for_user(user_id: int, path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM deals WHERE (initiator_id = ? OR target_id = ?) AND status = ?", (user_id, user_id, "accepted"))
        row = await cur.fetchone()
        return dict(row) if row else None


async def update_deal_status(deal_id: int, status: str, path: str = DB_PATH) -> None:
    ts_field = None
    ts = datetime.datetime.utcnow().isoformat()
    if status == "accepted":
        ts_field = "accepted_at"
    elif status == "paid":
        ts_field = "paid_at"
    elif status == "fiat_sent":
        ts_field = "fiat_sent_at"
    elif status == "fiat_received":
        ts_field = "fiat_received_at"
    elif status == "released":
        ts_field = "released_at"
    elif status == "closed":
        ts_field = "closed_at"

    async with aiosqlite.connect(path) as db:
        if ts_field:
            await db.execute(f"UPDATE deals SET status = ?, {ts_field} = ? WHERE id = ?", (status, ts, deal_id))
        else:
            await db.execute("UPDATE deals SET status = ? WHERE id = ?", (status, deal_id))
        await db.commit()


async def update_deal(deal_id: int, path: str = DB_PATH, **kwargs) -> None:
    """Update deal with arbitrary fields."""
    if not kwargs:
        return
    
    fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
    values = list(kwargs.values()) + [deal_id]
    
    async with aiosqlite.connect(path) as db:
        await db.execute(f"UPDATE deals SET {fields} WHERE id = ?", values)
        await db.commit()


async def update_deal_tx(deal_id: int, tx_hash: str, deposit_amount: str, deposit_network: str, path: str = DB_PATH) -> None:
    async with aiosqlite.connect(path) as db:
        await db.execute("UPDATE deals SET tx_hash = ?, deposit_amount = ?, deposit_network = ? WHERE id = ?", (tx_hash, deposit_amount, deposit_network, deal_id))
        await db.commit()


async def get_deal_by_group(group_chat_id: int, path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM deals WHERE group_chat_id = ? AND status NOT IN ('closed', 'rejected') ORDER BY created_at DESC LIMIT 1", (group_chat_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def list_deals_for_user(user_id: int, path: str = DB_PATH):
    async with aiosqlite.connect(path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM deals WHERE initiator_id = ? OR target_id = ? ORDER BY created_at DESC", (user_id, user_id))
        rows = await cur.fetchall()
        return [dict(r) for r in rows]
