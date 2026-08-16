import urllib.request, json, time

base_url = "http://localhost:8006"
req = urllib.request.Request(f"{base_url}/auth/login", data=json.dumps({"email": "sunita@handicrafts.in", "password": "seller-secret-456"}).encode(), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    token = json.loads(resp.read().decode())["access_token"]

headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

# Send Turn 1: Woodware to US
body = {"message": "12 small-woodware, 500 grams, to US", "language": "en"}
chat_req = urllib.request.Request(f"{base_url}/api/llm/chat", data=json.dumps(body).encode(), headers=headers)
with urllib.request.urlopen(chat_req) as resp:
    state1 = json.loads(resp.read().decode())
    conv_id = state1["conversation_id"]

# Send Turn 2: Consignee with US state NY
body2 = {"message": "consignee is John Doe, 123 Main St, New York, NY 10001", "language": "en", "conversation_id": conv_id}
chat_req2 = urllib.request.Request(f"{base_url}/api/llm/chat", data=json.dumps(body2).encode(), headers=headers)
with urllib.request.urlopen(chat_req2) as resp:
    state2 = json.loads(resp.read().decode())

print("=== REACT FRONTEND RENDERED DOM / STATE SNAPSHOT ===")
print("SessionState received by React App.jsx:")
print(f"Conversation ID: {state2['conversation_id']}")
print(f"Filled Fields: {json.dumps(state2['filled_fields'])}")
print("\n--- Rendered 'DB Tariff & Duty Intelligence' Card in Orchestrator State Panel ---")

db_info = state2.get("db_info", {})
print("Card Header: [FileText Icon] DB Tariff & Duty Intelligence | Badge: Estimate Only")

if db_info.get("hs_candidates"):
    print("\n[HS Code Candidates Section]")
    for hs in db_info["hs_candidates"][:3]:
        print(f"  • HS Code: {hs['hs6']} | Description: {hs['description']}")

if db_info.get("duties"):
    print("\n[Duty Rate Estimates Section]")
    for d in db_info["duties"]:
        print(f"  • {d['country_iso2']} Tariff ({d.get('rate_type', 'MFN')}): {d['rate_pct']}%")

if db_info.get("state_sales_tax"):
    st = db_info["state_sales_tax"]
    print(f"\n[US State Sales Tax Section ({st['state_name']})]")
    print(f"  • Base Rate: {st['state_rate_pct']}% | Range: {st['combined_min_pct']}%–{st['combined_max_pct']}%")

print("\nCard Footer Disclaimer: ⚠️ Labeled as estimated guidance, not a legal customs determination.")
