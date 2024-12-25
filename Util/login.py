import requests
import secrets
import os
import json

# File for storing credentials
credentials_file = "credentials.json"
request_file = "Offsets/request.json"

url_token = "https://nebula.starbreeze.com/iam/v3/oauth/token"

def load_token_headers():
    """Load token headers from request.json if it exists."""
    if os.path.exists(request_file):
        try:
            with open(request_file, "r") as f:
                data = json.load(f)
                return data.get("token_header", {}), data.get("token_header_with_token", {}), data.get("url_buy_products", {}), data.get("headers",{}), data.get("url_buy", {}), data.get("payload_money", {}) , data.get("payload_cstacks", {}), data.get("payload_cred" , {})
        except json.JSONDecodeError:
            print("Error: Invalid JSON in request file.")
            return {}, {}, {} ,{}, {}, {}, {}
    return {}, {}, {} ,{} , {} , {}, {}

def save_token_headers(access_token, user_id):
    """Saves the updated token headers and user_id to request.json."""
    # Ensure the Offsets folder exists
    os.makedirs("Offsets", exist_ok=True)

    # Load existing headers from request.json
    original_headers, _, url_buy_products, headers, url_buy , payload_money, payload_cstacks, payload_cred = load_token_headers()

    # Update the token header with the new access token
    updated_headers = original_headers.copy()
    updated_headers["Authorization"] = f"Bearer {access_token}"  # Use Bearer token format\
    headers["Authorization"] = f"Bearer {access_token}"

    # Update the url_buy_products with the actual user_id
    if "url" in url_buy_products:
        url_buy_products["url"] = url_buy_products["url"].replace("{user_id}", user_id)
        url_buy_products["url_upgrade"] = url_buy_products["url_upgrade"].replace("{user_id}", user_id)

    # Prepare the data to save in the JSON file
    data_to_save = {
        "token_header": original_headers,
        "token_header_with_token": updated_headers,
        "url_buy_products": url_buy_products,  # Now includes user_id in the URL
        "headers": headers,
        "url_buy" : url_buy,
        "payload_money" : payload_money,
        "payload_cstacks" : payload_cstacks,
        "payload_cred": payload_cred
    }

    # Save to request.json
    with open(request_file, "w") as f:
        json.dump(data_to_save, f, indent=4)

def login(username, password):
    """Handles the login process."""
    random_string = ''.join(secrets.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(32))
    data_token = {
        "username": username,
        "password": password,
        "grant_type": "password",
        "client_id": random_string,
        "extend_exp": "true"
    }

    # Load original token headers
    token_headers, _, _ , _, _, _, _, _ = load_token_headers()

    try:
        response = requests.post(url_token, headers=token_headers, data=data_token)
        response.raise_for_status()
        response_data = response.json()
        user_id = response_data.get("user_id", "")
        access_token = response_data.get("access_token", "")

        # Save updated token headers and user_id to request.json
        save_token_headers(access_token, user_id)

        return user_id, access_token
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred: {e}")
        return None, None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None

def manage_credentials(username, password, remember_me):
    """Save or load user credentials based on the 'remember me' checkbox."""
    if remember_me:
        credentials = {
            "username": username,
            "password": password
        }
        # Save username and password to a JSON file
        with open(credentials_file, "w") as f:
            json.dump(credentials, f)
    else:
        # Optionally clear stored credentials
        if os.path.exists(credentials_file):
            os.remove(credentials_file)

def load_credentials():
    """Load credentials from a JSON file if they exist."""
    if os.path.exists(credentials_file):
        try:
            with open(credentials_file, "r") as f:
                if os.path.getsize(credentials_file) > 0:  # Check if file is not empty
                    credentials = json.load(f)
                    username = credentials.get("username", "")
                    password = credentials.get("password", "")
                    return username, password
                else:
                    return None, None  # File is empty
        except json.JSONDecodeError:
            print("Error: Invalid JSON in credentials file.")
            return None, None
    return None, None

# Attempt to load stored credentials
username, password = load_credentials()

if username and password:
    print("Loaded credentials. Attempting to login...")
    user_id, access_token = login(username, password)
    if user_id and access_token:
        # print(f"Login successful! User ID: {user_id}, Access Token: {access_token}")
        print("Login successful!")
    else:
        print("Login failed.")
else:
    print("No credentials found. Please log in and save your credentials.")
