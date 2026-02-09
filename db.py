import sqlite3
import datetime
import json
import os

# Check if DATABASE_URL is set (for PostgreSQL on Heroku/Render)
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Use PostgreSQL
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    # Fix for Heroku DATABASE_URL (postgres:// -> postgresql://)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    DB_TYPE = 'postgresql'
else:
    # Use SQLite (for local development)
    conn = sqlite3.connect("bot.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    DB_TYPE = 'sqlite'


def execute_query(query, params=None):
    """Execute query with proper placeholder conversion for PostgreSQL/SQLite"""
    if DB_TYPE == 'postgresql' and params:
        # Convert ? to %s for PostgreSQL
        query = query.replace('?', '%s')
    cursor.execute(query, params or ())


def execute_insert_or_replace(table, key_col, key_val, data_dict):
    """Insert or replace/update a row"""
    cols = ', '.join(data_dict.keys())
    placeholders = ', '.join(['?' for _ in data_dict])
    values = tuple(data_dict.values())
    
    if DB_TYPE == 'postgresql':
        # PostgreSQL: ON CONFLICT DO UPDATE
        updates = ', '.join([f"{k} = EXCLUDED.{k}" for k in data_dict.keys() if k != key_col])
        query = f"""
            INSERT INTO {table} ({cols}) VALUES ({placeholders})
            ON CONFLICT ({key_col}) DO UPDATE SET {updates}
        """
        query = query.replace('?', '%s')
    else:
        # SQLite: INSERT OR REPLACE
        query = f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({placeholders})"
    
    cursor.execute(query, values)
    conn.commit()


def execute_insert_or_ignore(table, data_dict):
    """Insert or ignore if exists"""
    cols = ', '.join(data_dict.keys())
    placeholders = ', '.join(['?' for _ in data_dict])
    values = tuple(data_dict.values())
    
    if DB_TYPE == 'postgresql':
        # Get primary key column (assume first column)
        first_col = list(data_dict.keys())[0]
        query = f"""
            INSERT INTO {table} ({cols}) VALUES ({placeholders})
            ON CONFLICT ({first_col}) DO NOTHING
        """
        query = query.replace('?', '%s')
    else:
        query = f"INSERT OR IGNORE INTO {table} ({cols}) VALUES ({placeholders})"
    
    cursor.execute(query, values)
    conn.commit()


def init_db():
    if DB_TYPE == 'postgresql':
        # PostgreSQL syntax
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                available INTEGER DEFAULT 0,
                reserved INTEGER DEFAULT 0,
                referral_balance INTEGER DEFAULT 0,
                referrer_id BIGINT DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                description TEXT,
                price INTEGER,
                status TEXT DEFAULT 'pending',
                proof_file_id TEXT,
                admin_data TEXT,
                error_note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                reserved_until TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS withdrawals (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                method TEXT,
                data TEXT,
                amount INTEGER,
                status TEXT DEFAULT 'pending',
                receipt_file_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id SERIAL PRIMARY KEY,
                referrer_id BIGINT,
                referred_id BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id BIGINT PRIMARY KEY
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS withdrawal_methods (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE,
                min_amount INTEGER DEFAULT 0,
                fee INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
    else:
        # SQLite syntax
        cursor.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                available INTEGER DEFAULT 0,
                reserved INTEGER DEFAULT 0,
                referral_balance INTEGER DEFAULT 0,
                referrer_id INTEGER DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                description TEXT,
                price INTEGER,
                status TEXT DEFAULT 'pending',
                proof_file_id TEXT,
                admin_data TEXT,
                error_note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                reserved_until TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS withdrawals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                method TEXT,
                data TEXT,
                amount INTEGER,
                status TEXT DEFAULT 'pending',
                receipt_file_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referred_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );

            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY
            );

            CREATE TABLE IF NOT EXISTS withdrawal_methods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                min_amount INTEGER DEFAULT 0,
                fee INTEGER DEFAULT 0
            );
        ''')
    
    # Add columns if they don't exist (for existing databases)
    if DB_TYPE == 'sqlite':
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0")
            conn.commit()
        except Exception:
            pass
        
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN first_name TEXT")
            conn.commit()
        except Exception:
            pass
        
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN last_name TEXT")
            conn.commit()
        except Exception:
            pass
    
    conn.commit()

    # Default settings
    defaults = {
        "task_price": "10",
        "referral_reward": "2",
        "min_withdrawal": "50",
        "bot_active": "1",
        "tutorial_video_id": "",
        "channel_id": "@gmailfarmermax",
        "leaderboard_min_referrals": "10",
        "leaderboard_min_tasks": "20",
    }
    for k, v in defaults.items():
        if DB_TYPE == 'postgresql':
            execute_query("""
                INSERT INTO settings (key, value) VALUES (?, ?)
                ON CONFLICT (key) DO NOTHING
            """, (k, v))
        else:
            execute_query("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

    # Default withdrawal methods
    default_methods = [
        ("Vodafone Cash", 50, 0),
        ("InstaPay", 50, 0),
        ("Binance Pay", 50, 0),
    ]
    for name, min_amt, fee in default_methods:
        if DB_TYPE == 'postgresql':
            execute_query("""
                INSERT INTO withdrawal_methods (name, min_amount, fee) VALUES (?, ?, ?)
                ON CONFLICT (name) DO NOTHING
            """, (name, min_amt, fee))
        else:
            execute_query("INSERT OR IGNORE INTO withdrawal_methods (name, min_amount, fee) VALUES (?, ?, ?)",
                          (name, min_amt, fee))
    conn.commit()


# ---- Settings ----
def get_setting(key):
    execute_query("SELECT value FROM settings WHERE key=?", (key,))
    row = cursor.fetchone()
    return row["value"] if row else None


def set_setting(key, value):
    execute_insert_or_replace('settings', 'key', key, {'key': key, 'value': str(value)})


# ---- Users ----
def add_user(user_id, username, referrer_id=0, first_name=None, last_name=None):
    # Try to insert with new columns first
    try:
        if DB_TYPE == 'postgresql':
            execute_query("""
                INSERT INTO users (id, username, first_name, last_name, referrer_id) 
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (id) DO UPDATE SET 
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name
            """, (user_id, username, first_name, last_name, referrer_id))
        else:
            cursor.execute(
                "INSERT OR IGNORE INTO users (id, username, first_name, last_name, referrer_id) VALUES (?, ?, ?, ?, ?)",
                (user_id, username, first_name, last_name, referrer_id)
            )
            # Update existing user's name if they already exist
            cursor.execute(
                "UPDATE users SET username=?, first_name=?, last_name=? WHERE id=?",
                (username, first_name, last_name, user_id)
            )
    except Exception:
        # Fallback to old schema without first_name and last_name
        if DB_TYPE == 'postgresql':
            execute_query("""
                INSERT INTO users (id, username, referrer_id) VALUES (?, ?, ?)
                ON CONFLICT (id) DO UPDATE SET username = EXCLUDED.username
            """, (user_id, username, referrer_id))
        else:
            cursor.execute(
                "INSERT OR IGNORE INTO users (id, username, referrer_id) VALUES (?, ?, ?)",
                (user_id, username, referrer_id)
            )
            # Update existing user
            cursor.execute(
                "UPDATE users SET username=? WHERE id=?",
                (username, user_id)
            )
    conn.commit()


def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    return cursor.fetchone()


def get_all_users():
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()


def get_user_count():
    cursor.execute("SELECT COUNT(*) as cnt FROM users")
    return cursor.fetchone()["cnt"]


def get_active_user_count():
    """Users who have at least one task"""
    cursor.execute("SELECT COUNT(DISTINCT user_id) as cnt FROM tasks")
    return cursor.fetchone()["cnt"]


def get_total_balances():
    cursor.execute("SELECT COALESCE(SUM(available),0) as avail, COALESCE(SUM(reserved),0) as res, COALESCE(SUM(referral_balance),0) as ref FROM users")
    return cursor.fetchone()


def update_user_balance(user_id, available=None, reserved=None, referral_balance=None):
    user = get_user(user_id)
    if not user:
        return
    if available is not None:
        cursor.execute("UPDATE users SET available=? WHERE id=?", (available, user_id))
    if reserved is not None:
        cursor.execute("UPDATE users SET reserved=? WHERE id=?", (reserved, user_id))
    if referral_balance is not None:
        cursor.execute("UPDATE users SET referral_balance=? WHERE id=?", (referral_balance, user_id))
    conn.commit()


def add_to_reserved(user_id, amount):
    cursor.execute("UPDATE users SET reserved = reserved + ? WHERE id=?", (amount, user_id))
    conn.commit()


def add_to_available(user_id, amount):
    cursor.execute("UPDATE users SET available = available + ? WHERE id=?", (amount, user_id))
    conn.commit()


def add_to_referral_balance(user_id, amount):
    cursor.execute("UPDATE users SET referral_balance = referral_balance + ? WHERE id=?", (amount, user_id))
    conn.commit()


def clear_user_balance(user_id):
    cursor.execute("UPDATE users SET available=0, reserved=0, referral_balance=0 WHERE id=?", (user_id,))
    conn.commit()


def move_reserved_to_available(user_id, amount):
    cursor.execute("UPDATE users SET reserved = reserved - ?, available = available + ? WHERE id=?",
                   (amount, amount, user_id))
    conn.commit()


# ---- Tasks ----
def create_task(user_id, price):
    cursor.execute("INSERT INTO tasks (user_id, price, description) VALUES (?, ?, ?)",
                   (user_id, price, "مهمة جديدة"))
    conn.commit()
    return cursor.lastrowid


def get_task(task_id):
    cursor.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
    return cursor.fetchone()


def get_user_tasks(user_id):
    cursor.execute("SELECT * FROM tasks WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    return cursor.fetchall()


def get_pending_tasks():
    """Tasks waiting for admin to send data or review"""
    cursor.execute("SELECT * FROM tasks WHERE status IN ('pending', 'proof_submitted', 'error_resubmitted') ORDER BY created_at ASC")
    return cursor.fetchall()


def update_task_status(task_id, status):
    cursor.execute("UPDATE tasks SET status=? WHERE id=?", (status, task_id))
    conn.commit()


def update_task_admin_data(task_id, data):
    cursor.execute("UPDATE tasks SET admin_data=?, status='data_sent' WHERE id=?", (data, task_id))
    conn.commit()


def update_task_proof(task_id, file_id):
    cursor.execute("UPDATE tasks SET proof_file_id=?, status='proof_submitted' WHERE id=?", (file_id, task_id))
    conn.commit()


def update_task_error_resubmit(task_id, file_id):
    cursor.execute("UPDATE tasks SET proof_file_id=?, status='error_resubmitted' WHERE id=?", (file_id, task_id))
    conn.commit()


def approve_task(task_id):
    now = datetime.datetime.now()
    reserved_until = now + datetime.timedelta(hours=48)
    cursor.execute("UPDATE tasks SET status='approved', completed_at=?, reserved_until=? WHERE id=?",
                   (now.isoformat(), reserved_until.isoformat(), task_id))
    conn.commit()


def reject_task(task_id):
    cursor.execute("UPDATE tasks SET status='rejected' WHERE id=?", (task_id,))
    conn.commit()


def cancel_task(task_id):
    cursor.execute("UPDATE tasks SET status='cancelled' WHERE id=?", (task_id,))
    conn.commit()


def set_task_error(task_id, note):
    cursor.execute("UPDATE tasks SET status='error', error_note=? WHERE id=?", (note, task_id))
    conn.commit()


def get_tasks_ready_to_release():
    """Tasks where 48h have passed and status is approved"""
    now = datetime.datetime.now().isoformat()
    cursor.execute("SELECT * FROM tasks WHERE status='approved' AND reserved_until <= ?", (now,))
    return cursor.fetchall()


def get_user_task_stats(user_id):
    cursor.execute("SELECT COUNT(*) as total FROM tasks WHERE user_id=?", (user_id,))
    total = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) as approved FROM tasks WHERE user_id=? AND status='approved'", (user_id,))
    approved = cursor.fetchone()["approved"]
    cursor.execute("SELECT COUNT(*) as released FROM tasks WHERE user_id=? AND status='released'", (user_id,))
    released = cursor.fetchone()["released"]
    cursor.execute("SELECT COUNT(*) as rejected FROM tasks WHERE user_id=? AND status='rejected'", (user_id,))
    rejected = cursor.fetchone()["rejected"]
    return {"total": total, "approved": approved + released, "rejected": rejected}


def release_task(task_id):
    cursor.execute("UPDATE tasks SET status='released' WHERE id=?", (task_id,))
    conn.commit()


def get_reserved_tasks():
    """Tasks that are approved but not yet released (48h not passed or waiting admin)"""
    cursor.execute("SELECT * FROM tasks WHERE status='approved' ORDER BY reserved_until ASC")
    return cursor.fetchall()


def get_reserved_tasks_by_user(user_id):
    """Get all reserved tasks for a specific user"""
    cursor.execute("SELECT * FROM tasks WHERE status='approved' AND user_id=? ORDER BY reserved_until ASC", (user_id,))
    return cursor.fetchall()


# ---- Withdrawals ----
def create_withdrawal(user_id, method, data, amount):
    cursor.execute("INSERT INTO withdrawals (user_id, method, data, amount) VALUES (?, ?, ?, ?)",
                   (user_id, method, data, amount))
    conn.commit()
    return cursor.lastrowid


def get_withdrawal(wid):
    cursor.execute("SELECT * FROM withdrawals WHERE id=?", (wid,))
    return cursor.fetchone()


def get_pending_withdrawals():
    cursor.execute("SELECT * FROM withdrawals WHERE status='pending' ORDER BY created_at ASC")
    return cursor.fetchall()


def get_user_withdrawals(user_id):
    cursor.execute("SELECT * FROM withdrawals WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    return cursor.fetchall()


def approve_withdrawal(wid):
    cursor.execute("UPDATE withdrawals SET status='approved' WHERE id=?", (wid,))
    conn.commit()


def reject_withdrawal(wid):
    w = get_withdrawal(wid)
    if w:
        # Return balance to user
        add_to_available(w["user_id"], w["amount"])
        cursor.execute("UPDATE withdrawals SET status='rejected' WHERE id=?", (wid,))
        conn.commit()


def set_withdrawal_receipt(wid, file_id):
    cursor.execute("UPDATE withdrawals SET receipt_file_id=? WHERE id=?", (file_id, wid))
    conn.commit()


# ---- Referrals ----
def add_referral(referrer_id, referred_id):
    execute_query("SELECT * FROM referrals WHERE referrer_id=? AND referred_id=?", (referrer_id, referred_id))
    if not cursor.fetchone():
        execute_query("INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)", (referrer_id, referred_id))
        conn.commit()


def get_referral_count(user_id):
    execute_query("SELECT COUNT(*) as cnt FROM referrals WHERE referrer_id=?", (user_id,))
    return cursor.fetchone()["cnt"]


def get_user_referrals(user_id):
    """Get all referrals for a user"""
    execute_query("SELECT * FROM referrals WHERE referrer_id=? ORDER BY created_at DESC", (user_id,))
    return cursor.fetchall()


def get_referral_completed_tasks(referrer_id):
    """Count tasks completed by referred users"""
    cursor.execute("""
        SELECT COUNT(*) as cnt FROM tasks t
        JOIN referrals r ON t.user_id = r.referred_id
        WHERE r.referrer_id = ? AND t.status IN ('approved', 'released')
    """, (referrer_id,))
    return cursor.fetchone()["cnt"]


def get_leaderboard():
    """Get referral leaderboard sorted by referral count"""
    cursor.execute("""
        SELECT r.referrer_id, u.username, COUNT(r.referred_id) as ref_count,
        (SELECT COUNT(*) FROM tasks t2 JOIN referrals r2 ON t2.user_id = r2.referred_id
         WHERE r2.referrer_id = r.referrer_id AND t2.status IN ('approved','released')) as task_count
        FROM referrals r
        JOIN users u ON r.referrer_id = u.id
        GROUP BY r.referrer_id
        ORDER BY ref_count DESC
    """)
    return cursor.fetchall()


# ---- Admins ----
def add_admin(admin_id):
    if DB_TYPE == 'postgresql':
        execute_query("INSERT INTO admins (id) VALUES (?) ON CONFLICT (id) DO NOTHING", (admin_id,))
    else:
        cursor.execute("INSERT OR IGNORE INTO admins (id) VALUES (?)", (admin_id,))
    conn.commit()


def remove_admin(admin_id):
    cursor.execute("DELETE FROM admins WHERE id=?", (admin_id,))
    conn.commit()


def get_admins():
    cursor.execute("SELECT id FROM admins")
    return [row["id"] for row in cursor.fetchall()]


def is_admin(user_id, main_admin_id):
    if user_id == main_admin_id:
        return True
    cursor.execute("SELECT id FROM admins WHERE id=?", (user_id,))
    return cursor.fetchone() is not None


# ---- Withdrawal Methods ----
def get_withdrawal_methods():
    cursor.execute("SELECT * FROM withdrawal_methods")
    return cursor.fetchall()


def get_withdrawal_method(name):
    execute_query("SELECT * FROM withdrawal_methods WHERE name=?", (name,))
    return cursor.fetchone()


def add_withdrawal_method(name, min_amount=0, fee=0):
    execute_insert_or_ignore('withdrawal_methods', {'name': name, 'min_amount': min_amount, 'fee': fee})


def update_withdrawal_method_min(name, min_amount):
    execute_query("UPDATE withdrawal_methods SET min_amount=? WHERE name=?", (min_amount, name))
    conn.commit()


def update_withdrawal_method_fee(name, fee):
    execute_query("UPDATE withdrawal_methods SET fee=? WHERE name=?", (fee, name))
    conn.commit()


# ---- Ban/Unban Users ----
def ban_user(user_id):
    cursor.execute("UPDATE users SET is_banned=1 WHERE id=?", (user_id,))
    conn.commit()


def unban_user(user_id):
    cursor.execute("UPDATE users SET is_banned=0 WHERE id=?", (user_id,))
    conn.commit()


def is_user_banned(user_id):
    cursor.execute("SELECT is_banned FROM users WHERE id=?", (user_id,))
    row = cursor.fetchone()
    return row["is_banned"] == 1 if row else False


# ---- Get all user IDs ----
def get_all_user_ids():
    cursor.execute("SELECT id FROM users")
    return [row["id"] for row in cursor.fetchall()]


# ---- Get incomplete tasks ----
def get_incomplete_tasks():
    """Tasks that are not completed (pending, data_sent, proof_submitted, error, error_resubmitted)"""
    cursor.execute("SELECT * FROM tasks WHERE status IN ('pending', 'data_sent', 'proof_submitted', 'error', 'error_resubmitted') ORDER BY created_at DESC")
    return cursor.fetchall()
