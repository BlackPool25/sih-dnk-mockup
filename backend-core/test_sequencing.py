import urllib.request, json, time

time.sleep(6)
base_url = "http://localhost:8006"
req = urllib.request.Request(f"{base_url}/auth/login", data=json.dumps({"email": "sunita@handicrafts.in", "password": "seller-secret-456"}).encode(), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    token = json.loads(resp.read().decode())["access_token"]

headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

turns = [
    "12 wooden toys, 500 grams, to Germany",
    "consignee is John Doe, 123 Berlin Str",
    "value is 15000 INR",
    "product category is handloom-scarves-stoles",
    "Simulate Completing Order"
]

conv_id = None

for i, text in enumerate(turns):
    print(f"--- TURN {i+1} ---")
    print(f"User: {text}")
    
    body = {
        "message": text,
        "language": "en"
    }
    if conv_id:
        body["conversation_id"] = conv_id
    
    chat_req = urllib.request.Request(f"{base_url}/api/llm/chat", data=json.dumps(body).encode(), headers=headers)
    with urllib.request.urlopen(chat_req) as resp:
        res = json.loads(resp.read().decode())
        conv_id = res.get("conversation_id")
        print(f"Step: {res['current_step']}")
        print(f"Filled: {json.dumps(res['filled_fields'])}")
        print(f"Pending: {res['pending_fields']}")
        
        reply = res["history"][-1]["content"]
        print(f"Reply: {reply}\n")
        
        if "Simulate Completing Order" in text:
            print("--- SUBMITTING ORDER ---")
            ff = res["filled_fields"]
            order_payload = {
                "destination_country": ff.get("destination_country"),
                "value_minor": ff.get("value_minor"),
                "consignee": ff.get("consignee"),
                "net_weight_g": float(ff.get("weight_grams")),
                "gross_weight_g": float(round(ff.get("weight_grams") * 1.1)),
                "line_items": [
                    {
                        "description": ff.get("product_category", "Goods"),
                        "hsn_code": ff.get("hs_code", "0000"),
                        "quantity": ff.get("quantity", 1),
                        "unit_price_minor": int(ff.get("value_minor", 0) / max(ff.get("quantity", 1), 1)),
                        "total_minor": ff.get("value_minor")
                    }
                ],
                "currency": "INR"
            }
            order_req = urllib.request.Request(f"{base_url}/orders", data=json.dumps(order_payload).encode(), headers=headers)
            try:
                with urllib.request.urlopen(order_req) as o_resp:
                    print(f"Order Status: {o_resp.status}")
                    print(f"Order Response: {o_resp.read().decode()}")
            except Exception as e:
                print(f"Order Failed: {e}")
                if hasattr(e, 'read'):
                    print(e.read().decode())
