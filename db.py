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
    conn.autocommit = False  # Ensure we control transactions
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
    try:
        if DB_TYPE == 'postgresql' and params:
            # Convert ? to %s for PostgreSQL
            query = query.replace('?', '%s')
        cursor.execute(query, params or ())
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()  # Rollback on error
        raise e


def safe_fetchone(query, params=None):
    """Safely fetch one row with automatic rollback on error"""
    try:
        execute_query(query, params)
        return cursor.fetchone()
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        print(f"Error in safe_fetchone: {e}")
        return None


def safe_fetchall(query, params=None):
    """Safely fetch all rows with automatic rollback on error"""
    try:
        execute_query(query, params)
        return cursor.fetchall()
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        print(f"Error in safe_fetchall: {e}")
        return []


def execute_insert_or_replace(table, key_col, key_val, data_dict):
    """Insert or replace/update a row"""
    try:
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
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        raise e


def execute_insert_or_ignore(table, data_dict):
    """Insert or ignore if exists"""
    try:
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
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        raise e


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
    try:
        row = safe_fetchone("SELECT value FROM settings WHERE key=?", (key,))
        return row["value"] if row else None
    except Exception as e:
        print(f"Error getting setting {key}: {e}")
        return None


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
            conn.commit()
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
            conn.commit()
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        print(f"Error adding user (trying fallback): {e}")
        # Fallback to old schema without first_name and last_name
        try:
            if DB_TYPE == 'postgresql':
                execute_query("""
                    INSERT INTO users (id, username, referrer_id) VALUES (?, ?, ?)
                    ON CONFLICT (id) DO UPDATE SET username = EXCLUDED.username
                """, (user_id, username, referrer_id))
                conn.commit()
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
        except Exception as e2:
            if DB_TYPE == 'postgresql':
                conn.rollback()
            print(f"Error adding user (fallback failed): {e2}")


def get_user(user_id):
    try:
        return safe_fetchone("SELECT * FROM users WHERE id=?", (user_id,))
    except Exception as e:
        print(f"Error getting user {user_id}: {e}")
        return None


def get_all_users():
    try:
        return safe_fetchall("SELECT * FROM users")
    except Exception as e:
        print(f"Error getting all users: {e}")
        return []


def get_user_count():
    try:
        row = safe_fetchone("SELECT COUNT(*) as cnt FROM users")
        return row["cnt"] if row else 0
    except Exception as e:
        print(f"Error getting user count: {e}")
        return 0


def get_active_user_count():
    """Users who have at least one task"""
    try:
        row = safe_fetchone("SELECT COUNT(DISTINCT user_id) as cnt FROM tasks")
        return row["cnt"] if row else 0
    except Exception as e:
        print(f"Error getting active user count: {e}")
        return 0


def get_total_balances():
    try:
        row = safe_fetchone("SELECT COALESCE(SUM(available),0) as avail, COALESCE(SUM(reserved),0) as res, COALESCE(SUM(referral_balance),0) as ref FROM users")
        return row if row else {"avail": 0, "res": 0, "ref": 0}
    except Exception as e:
        print(f"Error getting total balances: {e}")
        return {"avail": 0, "res": 0, "ref": 0}


def update_user_balance(user_id, available=None, reserved=None, referral_balance=None):
    user = get_user(user_id)
    if not user:
        return
    try:
        if available is not None:
            execute_query("UPDATE users SET available=? WHERE id=?", (available, user_id))
        if reserved is not None:
            execute_query("UPDATE users SET reserved=? WHERE id=?", (reserved, user_id))
        if referral_balance is not None:
            execute_query("UPDATE users SET referral_balance=? WHERE id=?", (referral_balance, user_id))
        conn.commit()
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        print(f"Error updating user balance: {e}")


def add_to_reserved(user_id, amount):
    try:
        execute_query("UPDATE users SET reserved = reserved + ? WHERE id=?", (amount, user_id))
        conn.commit()
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        print(f"Error adding to reserved: {e}")


def add_to_available(user_id, amount):
    try:
        execute_query("UPDATE users SET available = available + ? WHERE id=?", (amount, user_id))
        conn.commit()
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        print(f"Error adding to available: {e}")


def add_to_referral_balance(user_id, amount):
    try:
        execute_query("UPDATE users SET referral_balance = referral_balance + ? WHERE id=?", (amount, user_id))
        conn.commit()
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        print(f"Error adding to referral balance: {e}")


def clear_user_balance(user_id):
    try:
        execute_query("UPDATE users SET available=0, reserved=0, referral_balance=0 WHERE id=?", (user_id,))
        conn.commit()
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        print(f"Error clearing user balance: {e}")


def move_reserved_to_available(user_id, amount):
    try:
        execute_query("UPDATE users SET reserved = reserved - ?, available = available + ? WHERE id=?",
                       (amount, amount, user_id))
        conn.commit()
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        print(f"Error moving reserved to available: {e}")


# ---- Tasks ----
def create_task(user_id, price):
    try:
        execute_query("INSERT INTO tasks (user_id, price, description) VALUES (?, ?, ?)",
                       (user_id, price, "مهمة جديدة"))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        print(f"Error creating task: {e}")
        return None


def get_task(task_id):
    try:
        return safe_fetchone("SELECT * FROM tasks WHERE id=?", (task_id,))
    except Exception as e:
        print(f"Error getting task {task_id}: {e}")
        return None


def get_user_tasks(user_id):
    try:
        return safe_fetchall("SELECT * FROM tasks WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    except Exception as e:
        print(f"Error getting user tasks: {e}")
        return []


def get_pending_tasks():
    """Tasks waiting for admin to send data or review"""
    try:
        return safe_fetchall("SELECT * FROM tasks WHERE status IN ('pending', 'proof_submitted', 'error_resubmitted') ORDER BY created_at ASC")
    except Exception as e:
        print(f"Error getting pending tasks: {e}")
        return []


def update_task_status(task_id, status):
    try:
        execute_query("UPDATE tasks SET status=? WHERE id=?", (status, task_id))
        conn.commit()
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        print(f"Error updating task status: {e}")


def update_task_admin_data(task_id, data):
    try:
        execute_query("UPDATE tasks SET admin_data=?, status='data_sent' WHERE id=?", (data, task_id))
        conn.commit()
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        print(f"Error updating task admin data: {e}")


def update_task_proof(task_id, file_id):
    try:
        execute_query("UPDATE tasks SET proof_file_id=?, status='proof_submitted' WHERE id=?", (file_id, task_id))
        conn.commit()
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        print(f"Error updating task proof: {e}")


def update_task_error_resubmit(task_id, file_id):
    try:
        execute_query("UPDATE tasks SET proof_file_id=?, status='error_resubmitted' WHERE id=?", (file_id, task_id))
        conn.commit()
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        print(f"Error updating task error resubmit: {e}")


def approve_task(task_id):
    try:
        now = datetime.datetime.now()
        reserved_until = now + datetime.timedelta(hours=48)
        execute_query("UPDATE tasks SET status='approved', completed_at=?, reserved_until=? WHERE id=?",
                       (now.isoformat(), reserved_until.isoformat(), task_id))
        conn.commit()
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        print(f"Error approving task: {e}")


def reject_task(task_id):
    try:
        execute_query("UPDATE tasks SET status='rejected' WHERE id=?", (task_id,))
        conn.commit()
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        print(f"Error rejecting task: {e}")


def cancel_task(task_id):
    try:
        execute_query("UPDATE tasks SET status='cancelled' WHERE id=?", (task_id,))
        conn.commit()
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        print(f"Error cancelling task: {e}")


def set_task_error(task_id, note):
    try:
        execute_query("UPDATE tasks SET status='error', error_note=? WHERE id=?", (note, task_id))
        conn.commit()
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        print(f"Error setting task error: {e}")


def get_tasks_ready_to_release():
    """Tasks where 48h have passed and status is approved"""
    try:
        now = datetime.datetime.now().isoformat()
        return safe_fetchall("SELECT * FROM tasks WHERE status='approved' AND reserved_until <= ?", (now,))
    except Exception as e:
        print(f"Error getting tasks ready to release: {e}")
        return []


def get_user_task_stats(user_id):
    try:
        row = safe_fetchone("SELECT COUNT(*) as total FROM tasks WHERE user_id=?", (user_id,))
        total = row["total"] if row else 0
        
        row = safe_fetchone("SELECT COUNT(*) as approved FROM tasks WHERE user_id=? AND status='approved'", (user_id,))
        approved = row["approved"] if row else 0
        
        row = safe_fetchone("SELECT COUNT(*) as released FROM tasks WHERE user_id=? AND status='released'", (user_id,))
        released = row["released"] if row else 0
        
        row = safe_fetchone("SELECT COUNT(*) as rejected FROM tasks WHERE user_id=? AND status='rejected'", (user_id,))
        rejected = row["rejected"] if row else 0
        
        return {"total": total, "approved": approved + released, "rejected": rejected}
    except Exception as e:
        print(f"Error getting user task stats: {e}")
        return {"total": 0, "approved": 0, "rejected": 0}


def release_task(task_id):
    try:
        execute_query("UPDATE tasks SET status='released' WHERE id=?", (task_id,))
        conn.commit()
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        print(f"Error releasing task: {e}")


def get_reserved_tasks():
    """Tasks that are approved but not yet released (48h not passed or waiting admin)"""
    try:
        return safe_fetchall("SELECT * FROM tasks WHERE status='approved' ORDER BY reserved_until ASC")
    except Exception as e:
        print(f"Error getting reserved tasks: {e}")
        return []


def get_reserved_tasks_by_user(user_id):
    """Get all reserved tasks for a specific user"""
    try:
        return safe_fetchall("SELECT * FROM tasks WHERE status='approved' AND user_id=? ORDER BY reserved_until ASC", (user_id,))
    except Exception as e:
        print(f"Error getting reserved tasks by user: {e}")
        return []


# ---- Withdrawals ----
def create_withdrawal(user_id, method, data, amount):
    try:
        execute_query("INSERT INTO withdrawals (user_id, method, data, amount) VALUES (?, ?, ?, ?)",
                       (user_id, method, data, amount))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        print(f"Error creating withdrawal: {e}")
        return None


def get_withdrawal(wid):
    try:
        return safe_fetchone("SELECT * FROM withdrawals WHERE id=?", (wid,))
    except Exception as e:
        print(f"Error getting withdrawal: {e}")
        return None


def get_pending_withdrawals():
    try:
        return safe_fetchall("SELECT * FROM withdrawals WHERE status='pending' ORDER BY created_at ASC")
    except Exception as e:
        print(f"Error getting pending withdrawals: {e}")
        return []


def get_user_withdrawals(user_id):
    try:
        return safe_fetchall("SELECT * FROM withdrawals WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    except Exception as e:
        print(f"Error getting user withdrawals: {e}")
        return []


def approve_withdrawal(wid):
    try:
        execute_query("UPDATE withdrawals SET status='approved' WHERE id=?", (wid,))
        conn.commit()
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        print(f"Error approving withdrawal: {e}")


def reject_withdrawal(wid):
    try:
        w = get_withdrawal(wid)
        if w:
            # Return balance to user
            add_to_available(w["user_id"], w["amount"])
            execute_query("UPDATE withdrawals SET status='rejected' WHERE id=?", (wid,))
            conn.commit()
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        print(f"Error rejecting withdrawal: {e}")


def set_withdrawal_receipt(wid, file_id):
    try:
        execute_query("UPDATE withdrawals SET receipt_file_id=? WHERE id=?", (file_id, wid))
        conn.commit()
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        print(f"Error setting withdrawal receipt: {e}")


# ---- Referrals ----
def add_referral(referrer_id, referred_id):
    try:
        row = safe_fetchone("SELECT * FROM referrals WHERE referrer_id=? AND referred_id=?", (referrer_id, referred_id))
        if not row:
            execute_query("INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)", (referrer_id, referred_id))
            conn.commit()
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        print(f"Error adding referral: {e}")


def get_referral_count(user_id):
    try:
        row = safe_fetchone("SELECT COUNT(*) as cnt FROM referrals WHERE referrer_id=?", (user_id,))
        return row["cnt"] if row else 0
    except Exception as e:
        print(f"Error getting referral count: {e}")
        return 0


def get_user_referrals(user_id):
    """Get all referrals for a user"""
    try:
        return safe_fetchall("SELECT * FROM referrals WHERE referrer_id=? ORDER BY created_at DESC", (user_id,))
    except Exception as e:
        print(f"Error getting user referrals: {e}")
        return []


def get_referral_completed_tasks(referrer_id):
    """Count tasks completed by referred users"""
    try:
        row = safe_fetchone("""
            SELECT COUNT(*) as cnt FROM tasks t
            JOIN referrals r ON t.user_id = r.referred_id
            WHERE r.referrer_id = ? AND t.status IN ('approved', 'released')
        """, (referrer_id,))
        return row["cnt"] if row else 0
    except Exception as e:
        print(f"Error getting referral completed tasks: {e}")
        return 0


def get_leaderboard():
    """Get referral leaderboard sorted by referral count"""
    try:
        return safe_fetchall("""
            SELECT r.referrer_id, u.username, COUNT(r.referred_id) as ref_count,
            (SELECT COUNT(*) FROM tasks t2 JOIN referrals r2 ON t2.user_id = r2.referred_id
             WHERE r2.referrer_id = r.referrer_id AND t2.status IN ('approved','released')) as task_count
            FROM referrals r
            JOIN users u ON r.referrer_id = u.id
            GROUP BY r.referrer_id
            ORDER BY ref_count DESC
        """)
    except Exception as e:
        print(f"Error getting leaderboard: {e}")
        return []


# ---- Admins ----
def add_admin(admin_id):
    try:
        if DB_TYPE == 'postgresql':
            execute_query("INSERT INTO admins (id) VALUES (?) ON CONFLICT (id) DO NOTHING", (admin_id,))
        else:
            cursor.execute("INSERT OR IGNORE INTO admins (id) VALUES (?)", (admin_id,))
        conn.commit()
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        print(f"Error adding admin: {e}")


def remove_admin(admin_id):
    try:
        execute_query("DELETE FROM admins WHERE id=?", (admin_id,))
        conn.commit()
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        print(f"Error removing admin: {e}")


def get_admins():
    try:
        rows = safe_fetchall("SELECT id FROM admins")
        return [row["id"] for row in rows]
    except Exception as e:
        print(f"Error getting admins: {e}")
        return []


def is_admin(user_id, main_admin_id):
    if user_id == main_admin_id:
        return True
    try:
        row = safe_fetchone("SELECT id FROM admins WHERE id=?", (user_id,))
        return row is not None
    except Exception as e:
        print(f"Error checking admin: {e}")
        return False


# ---- Withdrawal Methods ----
def get_withdrawal_methods():
    try:
        return safe_fetchall("SELECT * FROM withdrawal_methods")
    except Exception as e:
        print(f"Error getting withdrawal methods: {e}")
        return []


def get_withdrawal_method(name):
    try:
        return safe_fetchone("SELECT * FROM withdrawal_methods WHERE name=?", (name,))
    except Exception as e:
        print(f"Error getting withdrawal method: {e}")
        return None


def add_withdrawal_method(name, min_amount=0, fee=0):
    try:
        execute_insert_or_ignore('withdrawal_methods', {'name': name, 'min_amount': min_amount, 'fee': fee})
    except Exception as e:
        print(f"Error adding withdrawal method: {e}")


def update_withdrawal_method_min(name, min_amount):
    try:
        execute_query("UPDATE withdrawal_methods SET min_amount=? WHERE name=?", (min_amount, name))
        conn.commit()
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        print(f"Error updating withdrawal method min: {e}")


def update_withdrawal_method_fee(name, fee):
    try:
        execute_query("UPDATE withdrawal_methods SET fee=? WHERE name=?", (fee, name))
        conn.commit()
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        print(f"Error updating withdrawal method fee: {e}")


# ---- Ban/Unban Users ----
def ban_user(user_id):
    try:
        execute_query("UPDATE users SET is_banned=1 WHERE id=?", (user_id,))
        conn.commit()
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        print(f"Error banning user: {e}")


def unban_user(user_id):
    try:
        execute_query("UPDATE users SET is_banned=0 WHERE id=?", (user_id,))
        conn.commit()
    except Exception as e:
        if DB_TYPE == 'postgresql':
            conn.rollback()
        print(f"Error unbanning user: {e}")


def is_user_banned(user_id):
    try:
        row = safe_fetchone("SELECT is_banned FROM users WHERE id=?", (user_id,))
        return row["is_banned"] == 1 if row else False
    except Exception as e:
        print(f"Error checking if user is banned: {e}")
        return False


# ---- Get all user IDs ----
def get_all_user_ids():
    try:
        rows = safe_fetchall("SELECT id FROM users")
        return [row["id"] for row in rows]
    except Exception as e:
        print(f"Error getting all user IDs: {e}")
        return []


# ---- Get incomplete tasks ----
def get_incomplete_tasks():
    """Tasks that are not completed (pending, data_sent, proof_submitted, error, error_resubmitted)"""
    try:
        return safe_fetchall("SELECT * FROM tasks WHERE status IN ('pending', 'data_sent', 'proof_submitted', 'error', 'error_resubmitted') ORDER BY created_at DESC")
    except Exception as e:
        print(f"Error getting incomplete tasks: {e}")
        return []
