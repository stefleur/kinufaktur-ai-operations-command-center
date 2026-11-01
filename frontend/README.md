# Operations Command Center frontend

React/Vite business operations dashboard and persistent task workspace. Configure `VITE_API_BASE_URL` for the independent backend; default is `http://localhost:8000`. No fallback contacts the original submission. Build base defaults to `/`.

From this directory: `npm ci`, `npm run test:ci`, `npm run build`. For development run `npm run dev`. See the repository README for the one-command complete stack.

Operations overview displays live backend health, request/error/latency/workflow metrics, alerts, incident timelines, trace spans and sanitized structured logs. Task workspace retains inherited CRUD. Fault injection requires backend demo mode. Requests carry unique W3C traceparent and X-Request-ID headers through the shared HTTP client.
