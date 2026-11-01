import json, urllib.request, uuid, os
base = os.getenv("API_URL", "http://localhost:8000")
def request(path, method="GET", data=None):
    req = urllib.request.Request(base+path, data=json.dumps(data).encode() if data else None, method=method, headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=10) as response: return json.load(response)
assert request("/health")["status"] == "healthy"
task = request("/tasks", "POST", {"title":"Synthetic smoke " + uuid.uuid4().hex[:8],"description":"Synthetic smoke check","category":"Other","priority":"Low","status":"incoming"})
assert request("/tasks/"+task["id"])["title"] == task["title"]
request("/tasks/"+task["id"], "DELETE")
print("Health and persistent task CRUD smoke passed")
