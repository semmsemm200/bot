"""
Debug helper for referral rewards
"""

def log_referral_check(task_id, user_id, user_data):
    """Log referral check details"""
    print(f"=" * 60)
    print(f"[REFERRAL DEBUG] Task #{task_id}")
    print(f"[REFERRAL DEBUG] User ID: {user_id}")
    if user_data:
        print(f"[REFERRAL DEBUG] User found: YES")
        print(f"[REFERRAL DEBUG] Referrer ID: {user_data.get('referrer_id', 'N/A')}")
        print(f"[REFERRAL DEBUG] Username: {user_data.get('username', 'N/A')}")
    else:
        print(f"[REFERRAL DEBUG] User found: NO")
    print(f"=" * 60)

def log_referral_reward(referrer_id, reward_amount):
    """Log referral reward addition"""
    print(f"[REFERRAL DEBUG] Adding {reward_amount} EGP to referrer {referrer_id}")

def log_referral_notification(referrer_id, success, error=None):
    """Log referral notification result"""
    if success:
        print(f"[REFERRAL DEBUG] Notification sent to referrer {referrer_id}")
    else:
        print(f"[REFERRAL DEBUG] Failed to notify referrer {referrer_id}: {error}")
