"""
Security and rate limiting module.

Copyright (c) 2025 @killerbesto
All Rights Reserved.
"""
from __future__ import annotations

import datetime
from typing import Optional, Dict, Any
import aiosqlite
from . import db

# Rate limiting constants
MAX_DEALS_PER_HOUR = 5
MAX_CANCELS_PER_HOUR = 3
DEAL_CREATION_COOLDOWN_SECONDS = 60  # 1 minute between deals
CANCEL_COOLDOWN_SECONDS = 300  # 5 minutes between cancels
ROLE_SWITCH_COOLDOWN_SECONDS = 10  # 10 seconds between role switches

# Input validation bounds
MIN_USDT_AMOUNT = 10.0
MAX_USDT_AMOUNT = 50000.0
MIN_INR_RATE = 50.0
MAX_INR_RATE = 200.0


async def log_activity(user_id: int, action_type: str, deal_id: Optional[int] = None, details: str = "", path: str = db.DB_PATH) -> None:
    """Log user activity for security monitoring."""
    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    async with aiosqlite.connect(path) as conn:
        await conn.execute(
            "INSERT INTO activity_logs (user_id, action_type, deal_id, details, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, action_type, deal_id, details, created_at)
        )
        await conn.commit()


async def check_rate_limit_deal_creation(user_id: int, path: str = db.DB_PATH) -> tuple[bool, str]:
    """
    Check if user can create a new deal.
    Returns: (allowed: bool, reason: str)
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    
    async with aiosqlite.connect(path) as conn:
        conn.row_factory = aiosqlite.Row
        
        # Get user cache data
        cur = await conn.execute(
            "SELECT last_deal_created_at, deal_count FROM user_cache WHERE user_id = ?",
            (user_id,)
        )
        row = await cur.fetchone()
        
        if row:
            # Check cooldown from last deal
            if row["last_deal_created_at"]:
                last_created = datetime.datetime.fromisoformat(row["last_deal_created_at"])
                seconds_since = (now - last_created).total_seconds()
                if seconds_since < DEAL_CREATION_COOLDOWN_SECONDS:
                    remaining = int(DEAL_CREATION_COOLDOWN_SECONDS - seconds_since)
                    return False, f"⏳ Please wait {remaining} seconds before creating another deal."
        
        # Check deals in last hour
        one_hour_ago = (now - datetime.timedelta(hours=1)).isoformat()
        cur = await conn.execute(
            "SELECT COUNT(*) as count FROM deals WHERE (initiator_id = ? OR target_id = ?) AND created_at > ?",
            (user_id, user_id, one_hour_ago)
        )
        result = await cur.fetchone()
        
        if result["count"] >= MAX_DEALS_PER_HOUR:
            return False, f"🚫 Rate limit exceeded. Maximum {MAX_DEALS_PER_HOUR} deals per hour. Please try again later."
    
    return True, ""


async def check_rate_limit_cancel(user_id: int, path: str = db.DB_PATH) -> tuple[bool, str]:
    """
    Check if user can cancel a deal.
    Returns: (allowed: bool, reason: str)
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    
    async with aiosqlite.connect(path) as conn:
        conn.row_factory = aiosqlite.Row
        
        # Get user cache data
        cur = await conn.execute(
            "SELECT last_deal_cancelled_at, cancel_count FROM user_cache WHERE user_id = ?",
            (user_id,)
        )
        row = await cur.fetchone()
        
        if row and row["last_deal_cancelled_at"]:
            last_cancelled = datetime.datetime.fromisoformat(row["last_deal_cancelled_at"])
            seconds_since = (now - last_cancelled).total_seconds()
            if seconds_since < CANCEL_COOLDOWN_SECONDS:
                remaining = int(CANCEL_COOLDOWN_SECONDS - seconds_since)
                return False, f"⏳ Please wait {remaining} seconds before cancelling another deal."
        
        # Check cancellations in last hour
        one_hour_ago = (now - datetime.timedelta(hours=1)).isoformat()
        cur = await conn.execute(
            "SELECT COUNT(*) as count FROM activity_logs WHERE user_id = ? AND action_type = 'DEAL_CANCELLED' AND created_at > ?",
            (user_id, one_hour_ago)
        )
        result = await cur.fetchone()
        
        if result["count"] >= MAX_CANCELS_PER_HOUR:
            return False, f"🚫 Too many cancellations. Maximum {MAX_CANCELS_PER_HOUR} per hour. Please try again later."
    
    return True, ""


async def check_rate_limit_role_switch(user_id: int, path: str = db.DB_PATH) -> tuple[bool, str]:
    """
    Check if user can switch roles (prevents rapid switching abuse).
    Returns: (allowed: bool, reason: str)
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    
    async with aiosqlite.connect(path) as conn:
        conn.row_factory = aiosqlite.Row
        
        # Get user cache data
        cur = await conn.execute(
            "SELECT last_role_switch_at FROM user_cache WHERE user_id = ?",
            (user_id,)
        )
        row = await cur.fetchone()
        
        if row and row["last_role_switch_at"]:
            last_switch = datetime.datetime.fromisoformat(row["last_role_switch_at"])
            seconds_since = (now - last_switch).total_seconds()
            if seconds_since < ROLE_SWITCH_COOLDOWN_SECONDS:
                remaining = int(ROLE_SWITCH_COOLDOWN_SECONDS - seconds_since)
                return False, f"⏳ Please wait {remaining} seconds before selecting a role."
    
    return True, ""


async def update_user_cache_deal_created(user_id: int, path: str = db.DB_PATH) -> None:
    """Update user cache when a deal is created."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    async with aiosqlite.connect(path) as conn:
        await conn.execute(
            """
            INSERT INTO user_cache (user_id, last_deal_created_at, deal_count, updated_at)
            VALUES (?, ?, 1, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                last_deal_created_at = ?,
                deal_count = deal_count + 1,
                updated_at = ?
            """,
            (user_id, now, now, now, now)
        )
        await conn.commit()


async def update_user_cache_deal_cancelled(user_id: int, path: str = db.DB_PATH) -> None:
    """Update user cache when a deal is cancelled."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    async with aiosqlite.connect(path) as conn:
        await conn.execute(
            """
            INSERT INTO user_cache (user_id, last_deal_cancelled_at, cancel_count, updated_at)
            VALUES (?, ?, 1, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                last_deal_cancelled_at = ?,
                cancel_count = cancel_count + 1,
                updated_at = ?
            """,
            (user_id, now, now, now, now)
        )
        await conn.commit()


async def update_user_cache_role_switch(user_id: int, path: str = db.DB_PATH) -> None:
    """Update user cache when a role is selected."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    async with aiosqlite.connect(path) as conn:
        await conn.execute(
            """
            INSERT INTO user_cache (user_id, last_role_switch_at, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                last_role_switch_at = ?,
                updated_at = ?
            """,
            (user_id, now, now, now, now)
        )
        await conn.commit()


async def update_user_display_cache(user_id: int, username: Optional[str], full_name: Optional[str], first_name: Optional[str], path: str = db.DB_PATH) -> None:
    """Cache user display information to reduce API calls."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    async with aiosqlite.connect(path) as conn:
        await conn.execute(
            """
            INSERT INTO user_cache (user_id, username, full_name, first_name, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = ?,
                full_name = ?,
                first_name = ?,
                updated_at = ?
            """,
            (user_id, username, full_name, first_name, now, username, full_name, first_name, now)
        )
        await conn.commit()


async def get_cached_user_display(user_id: int, path: str = db.DB_PATH) -> Optional[Dict[str, Any]]:
    """Get cached user display information."""
    async with aiosqlite.connect(path) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute(
            "SELECT username, full_name, first_name, updated_at FROM user_cache WHERE user_id = ?",
            (user_id,)
        )
        row = await cur.fetchone()
        if row:
            # Check if cache is fresh (less than 1 day old)
            updated_at = datetime.datetime.fromisoformat(row["updated_at"])
            age = datetime.datetime.now(datetime.timezone.utc) - updated_at
            if age.total_seconds() < 86400:  # 24 hours
                return dict(row)
        return None


def validate_usdt_amount(amount: float) -> tuple[bool, str]:
    """
    Validate USDT amount is within acceptable bounds.
    Returns: (valid: bool, error_message: str)
    """
    if amount < MIN_USDT_AMOUNT:
        return False, f"❌ Minimum amount is {MIN_USDT_AMOUNT} USDT"
    if amount > MAX_USDT_AMOUNT:
        return False, f"❌ Maximum amount is {MAX_USDT_AMOUNT} USDT"
    return True, ""


def validate_inr_rate(rate: float) -> tuple[bool, str]:
    """
    Validate INR rate is within acceptable bounds.
    Returns: (valid: bool, error_message: str)
    """
    if rate < MIN_INR_RATE:
        return False, f"❌ Rate too low. Minimum is ₹{MIN_INR_RATE}/USDT"
    if rate > MAX_INR_RATE:
        return False, f"❌ Rate too high. Maximum is ₹{MAX_INR_RATE}/USDT"
    return True, ""


async def detect_suspicious_activity(user_id: int, path: str = db.DB_PATH) -> Optional[str]:
    """
    Detect suspicious patterns in user activity.
    Returns: Warning message if suspicious activity detected, None otherwise.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    one_hour_ago = (now - datetime.timedelta(hours=1)).isoformat()
    
    async with aiosqlite.connect(path) as conn:
        conn.row_factory = aiosqlite.Row
        
        # Check for rapid role switching (more than 5 times in 1 hour)
        cur = await conn.execute(
            "SELECT COUNT(*) as count FROM activity_logs WHERE user_id = ? AND action_type = 'ROLE_SELECTED' AND created_at > ?",
            (user_id, one_hour_ago)
        )
        result = await cur.fetchone()
        if result["count"] >= 5:
            return "⚠️ SUSPICIOUS: Rapid role switching detected"
        
        # Check for high cancellation rate
        cur = await conn.execute(
            "SELECT cancel_count, deal_count FROM user_cache WHERE user_id = ?",
            (user_id,)
        )
        result = await cur.fetchone()
        if result and result["deal_count"] > 0:
            cancel_ratio = result["cancel_count"] / result["deal_count"]
            if cancel_ratio > 0.5 and result["deal_count"] >= 5:
                return f"⚠️ SUSPICIOUS: High cancellation rate ({result['cancel_count']}/{result['deal_count']})"
    
    return None
