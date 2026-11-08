import requests
import secrets
import os
import sys
import json

_BASE            = os.path.dirname(__file__)
_ROOT            = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(_BASE)
_CREDENTIALS     = os.path.join(_ROOT, "credentials.json")
_REQUEST         = os.path.join(_ROOT, "Offsets", "request.json")
_TOKEN_URL       = "https://nebula.starbreeze.com/iam/v3/oauth/token"


# ── Internal ──────────────────────────────────────────────────────────────────

def _load_request():
    """Return the full request.json dict, or {} on error."""
    try:
        with open(_REQUEST) as f:
            return json.load(f)
    except Exception:
        return {}


def _save_request(data):
    os.makedirs(os.path.dirname(_REQUEST), exist_ok=True)
    with open(_REQUEST, "w") as f:
        json.dump(data, f, indent=4)


# ── Public API ────────────────────────────────────────────────────────────────

def login(username, password):
    """Authenticate and persist the token + resolved URLs. Returns (user_id, access_token)."""
    rng = ''.join(secrets.choice(
        'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    ) for _ in range(32))

    data = _load_request()

    # token_header must carry Basic auth for the OAuth endpoint.
    # If it's missing or was overwritten with a Bearer token, fall back to the
    # known PD3 client credential so login always works.
    _BASIC = "Basic MGIzYmZkZjVhMjVmNDUyZmJkMzNhMzYxMzNhMmRlYWI6"
    stored_auth = data.get("token_header", {}).get("Authorization", "")
    token_headers = data.get("token_header", {}).copy()
    if not stored_auth or stored_auth.startswith("Bearer"):
        token_headers["Authorization"] = _BASIC

    try:
        resp = requests.post(_TOKEN_URL, headers=token_headers, data={
            "username":   username,
            "password":   password,
            "grant_type": "password",
            "client_id":  rng,
            "extend_exp": "true",
        }, timeout=30)
        resp.raise_for_status()
        body         = resp.json()
        user_id      = body.get("user_id", "")
        access_token = body.get("access_token", "")
    except requests.HTTPError as e:
        print(f"Login HTTP error: {e}")
        return None, None
    except Exception as e:
        print(f"Login error: {e}")
        return None, None

    # Only update the API-call headers with the Bearer token.
    # Never touch token_header — it must keep the Basic auth for future logins.
    bearer = f"Bearer {access_token}"
    if "headers" in data:
        data["headers"]["Authorization"] = bearer
    if "token_header_with_token" in data:
        data["token_header_with_token"]["Authorization"] = bearer

    # Substitute {user_id} placeholder in buy URLs
    ubp = data.get("url_buy_products", {})
    for key in ("url", "url_upgrade"):
        if key in ubp:
            ubp[key] = ubp[key].replace("{user_id}", user_id)

    _save_request(data)
    return user_id, access_token


def manage_credentials(username, password, remember_me):
    """Save credentials to disk when remember_me is True, delete otherwise."""
    if remember_me:
        with open(_CREDENTIALS, "w") as f:
            json.dump({"username": username, "password": password}, f)
    else:
        if os.path.exists(_CREDENTIALS):
            os.remove(_CREDENTIALS)


def load_credentials():
    """Return (username, password) from saved credentials, or (None, None)."""
    try:
        with open(_CREDENTIALS) as f:
            c = json.load(f)
        return c.get("username") or None, c.get("password") or None
    except Exception:
        return None, None


# ── Auto-login on import ──────────────────────────────────────────────────────

def _auto_login():
    username, password = load_credentials()
    if username and password:
        print("Loaded credentials. Attempting to login...")
        user_id, token = login(username, password)
        print("Login successful!" if (user_id and token) else "Login failed.")
    else:
        print("No credentials found. Please log in and save your credentials.")

_auto_login()
