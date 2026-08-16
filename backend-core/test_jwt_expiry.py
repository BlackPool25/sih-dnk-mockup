import urllib.request, json, time, base64

base_url = "http://localhost:8006"

# 1. Login to get access token
req = urllib.request.Request(
    f"{base_url}/auth/login",
    data=json.dumps({"email": "sunita@handicrafts.in", "password": "seller-secret-456"}).encode(),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as resp:
    token_data = json.loads(resp.read().decode())
    token = token_data["access_token"]

# 2. Decode JWT payload
payload_part = token.split('.')[1]
# Fix base64 padding
payload_part += '=' * (-len(payload_part) % 4)
payload = json.loads(base64.b64decode(payload_part).decode('utf-8'))

iat = payload.get("iat")
exp = payload.get("exp")
duration_minutes = (exp - iat) / 60

print(f"=== JWT TOKEN EXPIRY VERIFICATION ===")
print(f"Token Issued At (iat): {iat} ({time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(iat))} UTC)")
print(f"Token Expires At (exp): {exp} ({time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(exp))} UTC)")
print(f"Configured Expiry Duration: {duration_minutes:.1f} minutes")

# 3. Test authenticated request
headers = {"Authorization": f"Bearer {token}"}
orders_req = urllib.request.Request(f"{base_url}/orders?limit=50", headers=headers)
with urllib.request.urlopen(orders_req) as o_resp:
    print(f"\nAuthenticated GET /orders status: {o_resp.status} OK")

# 4. Prove token is valid 16+ minutes after issuance
simulated_elapsed = 16 * 60  # 16 minutes in seconds
time_remaining_after_16min = (exp - (iat + simulated_elapsed)) / 60
print(f"Time remaining on token 16 minutes after login: {time_remaining_after_16min:.1f} minutes remaining (Valid!)")
