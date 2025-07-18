#!/usr/bin/env python3
"""
Focused test for messaging system endpoints
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://4b869601-8f24-43a7-86e2-890808928b40.preview.emergentagent.com/api"
TIMEOUT = 30

def test_messaging_system():
    """Test the messaging system endpoints"""
    session = requests.Session()
    session.timeout = TIMEOUT
    
    print("🚀 Testing Messaging System...")
    
    # Step 1: Register and login a user
    timestamp = int(time.time())
    user_data = {
        "email": f"msgtest{timestamp}@skillswap.com",
        "username": f"msgtest{timestamp}",
        "password": "MsgTest123!",
        "first_name": "Message",
        "last_name": "Tester",
        "role": "both"
    }
    
    print("1. Registering user...")
    reg_response = session.post(f"{BASE_URL}/auth/register", json=user_data)
    if reg_response.status_code != 200:
        print(f"❌ Registration failed: {reg_response.status_code}")
        print(reg_response.text)
        return
    
    auth_data = reg_response.json()
    token = auth_data.get("access_token")
    user_id = auth_data.get("user", {}).get("id")
    
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ User registered: {user_id}")
    
    # Step 2: Test get conversations (should be empty initially)
    print("2. Testing get conversations...")
    conv_response = session.get(f"{BASE_URL}/messages/conversations", headers=headers)
    if conv_response.status_code == 200:
        conversations = conv_response.json()
        print(f"✅ Get conversations: {len(conversations)} conversations")
    else:
        print(f"❌ Get conversations failed: {conv_response.status_code}")
        print(conv_response.text)
        return
    
    # Step 3: Create a second user for conversation
    print("3. Creating second user...")
    user2_data = {
        "email": f"msgtest2_{timestamp}@skillswap.com",
        "username": f"msgtest2_{timestamp}",
        "password": "MsgTest123!",
        "first_name": "Message",
        "last_name": "Recipient",
        "role": "both"
    }
    
    reg2_response = session.post(f"{BASE_URL}/auth/register", json=user2_data)
    if reg2_response.status_code != 200:
        print(f"❌ Second user registration failed: {reg2_response.status_code}")
        return
    
    user2_data_response = reg2_response.json()
    user2_id = user2_data_response.get("user", {}).get("id")
    print(f"✅ Second user created: {user2_id}")
    
    # Step 4: Create conversation
    print("4. Creating conversation...")
    participants = [user_id, user2_id]
    conv_create_response = session.post(f"{BASE_URL}/messages/conversations", json=participants, headers=headers)
    if conv_create_response.status_code == 200:
        conversation = conv_create_response.json()
        conversation_id = conversation.get("id")
        print(f"✅ Conversation created: {conversation_id}")
    else:
        print(f"❌ Create conversation failed: {conv_create_response.status_code}")
        print(conv_create_response.text)
        return
    
    # Step 5: Send a message
    print("5. Sending message...")
    message_data = {
        "recipient_id": user2_id,
        "content": "Hello! This is a test message from the messaging system.",
        "message_type": "text"
    }
    
    send_response = session.post(f"{BASE_URL}/messages/send", json=message_data, headers=headers)
    if send_response.status_code == 200:
        message = send_response.json()
        message_id = message.get("id")
        print(f"✅ Message sent: {message_id}")
    else:
        print(f"❌ Send message failed: {send_response.status_code}")
        print(send_response.text)
        return
    
    # Step 6: Get conversation messages
    print("6. Getting conversation messages...")
    messages_response = session.get(f"{BASE_URL}/messages/conversations/{conversation_id}/messages", headers=headers)
    if messages_response.status_code == 200:
        messages = messages_response.json()
        print(f"✅ Retrieved {len(messages)} messages")
    else:
        print(f"❌ Get messages failed: {messages_response.status_code}")
        print(messages_response.text)
    
    # Step 7: Test unread count
    print("7. Testing unread count...")
    unread_response = session.get(f"{BASE_URL}/messages/unread-count", headers=headers)
    if unread_response.status_code == 200:
        unread_data = unread_response.json()
        print(f"✅ Unread count: {unread_data.get('unread_count')}")
    else:
        print(f"❌ Get unread count failed: {unread_response.status_code}")
        print(unread_response.text)
    
    # Step 8: Test online users
    print("8. Testing online users...")
    online_response = session.get(f"{BASE_URL}/messages/online-users", headers=headers)
    if online_response.status_code == 200:
        online_data = online_response.json()
        print(f"✅ Online users: {len(online_data.get('online_users', []))}")
    else:
        print(f"❌ Get online users failed: {online_response.status_code}")
        print(online_response.text)
    
    print("\n🎉 Messaging system test completed!")

if __name__ == "__main__":
    test_messaging_system()