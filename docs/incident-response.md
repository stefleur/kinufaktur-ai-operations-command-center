# Incident response

Start Compose, run `make demo-incident`, then inspect the operations dashboard. The evidence collector starts with a healthy workflow, injects an isolated dependency fault, sends a new workflow request, verifies HTTP 503, retrieves its automatically created incident, checks correlated traces/logs/alert and tool records, and verifies both HTTP health and a recovered workflow.

Agent decision loop: observe health + correlated telemetry + metrics; recognize the deliberately faulted dependency; select reset_demo_dependency or escalate; execute at most one idempotent reset; verify /health; persist resolution or human-required status. All tool starts and results appear in the timeline. There is no unrestricted command execution, runtime LLM, production administration or claim of general-purpose diagnosis. The deterministic policy is the reproducible offline agent implementation.

Unknown failures should be investigated by a human through the recorded trace. Do not expose demo mode to unauthenticated public traffic. Demo controls are disabled unless DEMO_MODE=true. After repairing infrastructure, rerun the user workflow; unresolved incidents are preserved rather than silently marked successful. Back up both data volumes before migrations. Never use docker compose down -v unless explicitly deleting synthetic demo data.
