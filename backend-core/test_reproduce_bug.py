import urllib.request, json

base_url = "http://localhost:8006"
req = urllib.request.Request(f"{base_url}/auth/login", data=json.dumps({"email": "sunita@handicrafts.in", "password": "seller-secret-456"}).encode(), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    token = json.loads(resp.read().decode())["access_token"]

headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

turns = [
    "12 Jute Bags to Germany of ₹15000",   # Turn 1: product, qty, destination, value
    "500g",                                   # Turn 2: weight (must NOT steal value)
    "John Doe, 123 Berlin Str, Germany",      # Turn 3: consignee → should reach step:ready
]

conv_id = None

for i, text in enumerate(turns):
    print(f"--- TURN {i+1} ---")
    print(f"User Message: {text}")
    body = {"message": text, "language": "en"}
    if conv_id:
        body["conversation_id"] = conv_id
    r = urllib.request.Request(f"{base_url}/api/llm/chat", data=json.dumps(body).encode(), headers=headers)
    with urllib.request.urlopen(r) as resp:
        res = json.loads(resp.read().decode())
        conv_id = res.get("conversation_id")
        print(f"Current Step: {res['current_step']}")
        print(f"Filled Fields: {json.dumps(res['filled_fields'])}")
        print(f"Pending Fields: {res['pending_fields']}")
        print(f"Assistant Reply: {res['history'][-1]['content']}\n")
