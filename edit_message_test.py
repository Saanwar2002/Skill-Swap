#!/usr/bin/env python3
"""
Test just the edit message functionality
"""

import requests
import json
import time

# Configuration
BASE_URL = "https://285f26f8-1ec5-4b4e-8222-f75d2caf99e6.preview.emergentagent.com/api"
TIMEOUT = 30

def test_edit_message():
    """Test the edit message endpoint"""
    session = requests.Session()
    session.timeout = TIMEOUT
    
    print("🚀 Testing Edit Message...")
    
    # Step 1: Register and login a user
    timestamp = int(time.time())
    user_data = {
        "email": f"editest{timestamp}@skillswap.com",
        "username": f"editest{timestamp}",
        "password": "EditTest123!",
        "first_name": "Edit",
        "last_name": "Tester",
        "role": "both"
    }
    
    print("1. Registering user...")
    reg_response = session.post(f"{BASE_URL}/auth/register", json=user_data)
    if reg_response.status_code != 200:
        print(f"❌ Registration failed: {reg_response.status_code}")
        return
    
    auth_data = reg_response.json()
    token = auth_data.get("access_token")
    user_id = auth_data.get("user", {}).get("id")
    
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ User registered: {user_id}")
    
    # Step 2: Create a second user for conversation
    print("2. Creating second user...")
    user2_data = {
        "email": f"editest2_{timestamp}@skillswap.com",
        "username": f"editest2_{timestamp}",
        "password": "EditTest123!",
        "first_name": "Edit",
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
    
    # Step 3: Send a message to edit
    print("3. Sending message to edit...")
    message_data = {
        "recipient_id": user2_id,
        "content": "This message will be edited.",
        "message_type": "text"
    }
    
    send_response = session.post(f"{BASE_URL}/messages/send", json=message_data, headers=headers)
    if send_response.status_code != 200:
        print(f"❌ Send message failed: {send_response.status_code}")
        print(send_response.text)
        return
    
    message = send_response.json()
    message_id = message.get("id")
    print(f"✅ Message sent: {message_id}")
    
    # Step 4: Edit the message
    print("4. Editing message...")
    edit_response = session.put(
        f"{BASE_URL}/messages/messages/{message_id}/edit",
        headers=headers,
        params={"new_content": "This message has been edited successfully! The content is now updated."}
    )
    
    if edit_response.status_code == 200:
        edit_data = edit_response.json()
        print(f"✅ Message edited: {edit_data.get('message')}")
    else:
        print(f"❌ Edit message failed: {edit_response.status_code}")
        print(edit_response.text)
    
    print("\n🎉 Edit message test completed!")

if __name__ == "__main__":
    test_edit_message()