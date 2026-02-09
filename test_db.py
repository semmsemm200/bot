#!/usr/bin/env python3
"""
Test database connection and basic operations
"""

import db

print("=" * 50)
print("Testing Database Connection")
print("=" * 50)

# Test 1: Initialize database
print("\n1. Initializing database...")
try:
    db.init_db()
    print("✅ Database initialized successfully")
except Exception as e:
    print(f"❌ Error initializing database: {e}")
    exit(1)

# Test 2: Get settings
print("\n2. Testing settings...")
try:
    task_price = db.get_setting("task_price")
    print(f"✅ Task price: {task_price}")
except Exception as e:
    print(f"❌ Error getting setting: {e}")

# Test 3: Add test user
print("\n3. Testing user operations...")
try:
    test_user_id = 123456789
    db.add_user(test_user_id, "test_user", 0, "Test", "User")
    print(f"✅ User added successfully")
    
    user = db.get_user(test_user_id)
    if user:
        print(f"✅ User retrieved: {dict(user)}")
    else:
        print("⚠️ User not found")
except Exception as e:
    print(f"❌ Error with user operations: {e}")

# Test 4: Get user count
print("\n4. Testing user count...")
try:
    count = db.get_user_count()
    print(f"✅ Total users: {count}")
except Exception as e:
    print(f"❌ Error getting user count: {e}")

# Test 5: Get all users
print("\n5. Testing get all users...")
try:
    users = db.get_all_users()
    print(f"✅ Retrieved {len(users)} users")
except Exception as e:
    print(f"❌ Error getting all users: {e}")

# Test 6: Test balance operations
print("\n6. Testing balance operations...")
try:
    db.add_to_available(test_user_id, 100)
    print("✅ Added 100 to available balance")
    
    user = db.get_user(test_user_id)
    if user:
        print(f"✅ New balance: {user['available']}")
except Exception as e:
    print(f"❌ Error with balance operations: {e}")

# Test 7: Test task operations
print("\n7. Testing task operations...")
try:
    task_id = db.create_task(test_user_id, 10)
    if task_id:
        print(f"✅ Task created with ID: {task_id}")
        
        task = db.get_task(task_id)
        if task:
            print(f"✅ Task retrieved: #{task['id']} - Status: {task['status']}")
    else:
        print("⚠️ Task creation returned None")
except Exception as e:
    print(f"❌ Error with task operations: {e}")

# Test 8: Test withdrawal methods
print("\n8. Testing withdrawal methods...")
try:
    methods = db.get_withdrawal_methods()
    print(f"✅ Retrieved {len(methods)} withdrawal methods")
    for m in methods:
        print(f"   - {m['name']}: min {m['min_amount']}, fee {m['fee']}")
except Exception as e:
    print(f"❌ Error getting withdrawal methods: {e}")

print("\n" + "=" * 50)
print("Database Test Complete!")
print("=" * 50)
print("\nIf all tests passed, the database is working correctly.")
print("You can now run the bot with: python bot.py")
