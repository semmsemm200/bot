#!/usr/bin/env python3
"""
Test script to check referral system
"""
import db

print("=" * 60)
print("Testing Referral System")
print("=" * 60)

# Initialize database
db.init_db()

# Get all users
users = db.get_all_users()
print(f"\nTotal users: {len(users)}")

# Check users with referrer_id
users_with_referrer = []
for user in users:
    user_dict = dict(user)
    if user_dict.get('referrer_id') and user_dict['referrer_id'] != 0:
        users_with_referrer.append(user_dict)
        print(f"\n👤 User: {user_dict['id']}")
        print(f"   Username: {user_dict.get('username', 'N/A')}")
        print(f"   Referrer ID: {user_dict['referrer_id']}")
        print(f"   Referral Balance: {user_dict.get('referral_balance', 0)}")

print(f"\n📊 Users with referrer: {len(users_with_referrer)}")

# Check referral settings
ref_reward = db.get_setting("referral_reward")
print(f"\n💰 Referral reward setting: {ref_reward} EGP")

# Get all tasks
print("\n" + "=" * 60)
print("Checking Tasks")
print("=" * 60)

# For each user with referrer, check their tasks
for user_dict in users_with_referrer:
    user_id = user_dict['id']
    tasks = db.get_user_tasks(user_id)
    approved_tasks = [t for t in tasks if dict(t)['status'] in ('approved', 'released')]
    
    print(f"\n👤 User {user_id} (Referrer: {user_dict['referrer_id']})")
    print(f"   Total tasks: {len(tasks)}")
    print(f"   Approved tasks: {len(approved_tasks)}")
    
    if approved_tasks:
        print(f"   ✅ This user completed {len(approved_tasks)} tasks")
        print(f"   💡 Referrer {user_dict['referrer_id']} should have received {len(approved_tasks) * int(ref_reward)} EGP")
        
        # Check referrer's actual balance
        referrer = db.get_user(user_dict['referrer_id'])
        if referrer:
            referrer_dict = dict(referrer)
            print(f"   📊 Referrer's actual referral balance: {referrer_dict.get('referral_balance', 0)} EGP")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)
