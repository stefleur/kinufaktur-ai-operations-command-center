"""Actual PostgreSQL/container restart persistence check, synthetic records only."""
import json, urllib.request, subprocess, time
base = "http://localhost:8000"
def get(path):
    with urllib.request.urlopen(base+path, timeout=5) as response: return json.load(response)
req = urllib.request.Request(base+"/tasks", data=json.dumps({"title":"Synthetic restart evidence","description":"Synthetic persistence check","category":"Other","priority":"Low","status":"incoming"}).encode(), headers={"Content-Type":"application/json"})
with urllib.request.urlopen(req, timeout=5) as response: task=json.load(response)
incidents = {row["id"] for row in get("/ops/overview")["incidents"]}
subprocess.run(["docker", "compose", "restart", "backend", "postgres"], check=True)
for attempt in range(40):
    try:
        assert get("/health")["status"] == "healthy"
        break
    except Exception:
        if attempt == 39: raise
        time.sleep(1)
assert get("/tasks/"+task["id"])["title"] == task["title"]
assert incidents.issubset({row["id"] for row in get("/ops/overview")["incidents"]})
with urllib.request.urlopen(urllib.request.Request(base+"/tasks/"+task["id"], method="DELETE"), timeout=5): pass
print("PostgreSQL task and telemetry incident persistence across container restarts verified")
