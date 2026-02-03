## 2024-05-22 - [WeatherService API Latency]
**Learning:** `WeatherService` was fetching from Open-Meteo on every request, which is a significant bottleneck for dashboard performance.
**Action:** Always check for caching on external API calls, especially those used in high-traffic views like dashboards.

## 2026-02-03 - [Blocking IO in Async Service]
**Learning:** `SchedulerService` was using blocking `requests.get` inside an `async def`, which freezes the event loop for the duration of the request.
**Action:** Use `httpx` or other async libraries for external API calls within async functions.
