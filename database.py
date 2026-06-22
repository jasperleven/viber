import sqlite3
import logging
from datetime import datetime

DB_PATH = "/var/lib/viber_bot/deals.db"

def init_db():
    """Initialize database"""
    import os
    os.makedirs("/var/lib/viber_bot", exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deals (
            deal_id TEXT PRIMARY KEY,
            phone TEXT NOT NULL,
            name TEXT,
            stage TEXT,
            contract_signed_at TIMESTAMP,
            delivery_notified INTEGER DEFAULT 0,
            last_reminder_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    logging.info("Database initialized")

def upsert_deal(deal_id: str, phone: str, name: str, stage: str):
    """Insert or update deal"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    existing = cursor.execute(
        "SELECT deal_id FROM deals WHERE deal_id = ?", (deal_id,)
    ).fetchone()
    
    if existing:
        cursor.execute("""
            UPDATE deals SET phone=?, name=?, stage=? WHERE deal_id=?
        """, (phone, name, stage, deal_id))
    else:
        cursor.execute("""
            INSERT INTO deals (deal_id, phone, name, stage) VALUES (?, ?, ?, ?)
        """, (deal_id, phone, name, stage))
    
    conn.commit()
    conn.close()

def set_contract_signed(deal_id: str):
    """Mark deal as contract signed with timestamp"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE deals SET 
            stage='contract_signed',
            contract_signed_at=?,
            last_reminder_at=?
        WHERE deal_id=?
    """, (datetime.now(), datetime.now(), deal_id))
    conn.commit()
    conn.close()

def set_delivery_notified(deal_id: str):
    """Mark deal as delivery notified"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE deals SET stage='delivery', delivery_notified=1 WHERE deal_id=?
    """, (deal_id,))
    conn.commit()
    conn.close()

def set_docs_stage(deal_id: str):
    """Mark deal as waiting docs"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE deals SET stage='waiting_docs' WHERE deal_id=?
    """, (deal_id,))
    conn.commit()
    conn.close()

def get_deals_for_reminder(days: int) -> list:
    """Get deals that need weekly reminder"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    result = cursor.execute("""
        SELECT deal_id, phone, name, last_reminder_at FROM deals
        WHERE stage='contract_signed'
        AND delivery_notified=0
        AND (
            last_reminder_at IS NULL 
            OR (julianday('now') - julianday(last_reminder_at)) >= ?
        )
    """, (days,)).fetchall()
    
    conn.close()
    return result

def update_reminder_time(deal_id: str):
    """Update last reminder timestamp"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE deals SET last_reminder_at=? WHERE deal_id=?
    """, (datetime.now(), deal_id))
    conn.commit()
    conn.close()
