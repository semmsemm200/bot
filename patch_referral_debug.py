"""
Monkey patch to add debug logging to referral functions
Import this at the start of bot.py
"""
import db

# Save original function
_original_add_to_referral_balance = db.add_to_referral_balance

def patched_add_to_referral_balance(user_id, amount):
    """Patched version with debug logging"""
    print(f"[REFERRAL] Adding {amount} EGP to user {user_id} referral balance")
    result = _original_add_to_referral_balance(user_id, amount)
    print(f"[REFERRAL] Successfully added to user {user_id}")
    return result

# Apply patch
db.add_to_referral_balance = patched_add_to_referral_balance
print("[REFERRAL DEBUG] Monkey patch applied successfully!")
