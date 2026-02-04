## 2024-05-22 - [WeatherService API Latency]
**Learning:** `WeatherService` was fetching from Open-Meteo on every request, which is a significant bottleneck for dashboard performance.
**Action:** Always check for caching on external API calls, especially those used in high-traffic views like dashboards.

## 2024-06-03 - [SchedulerService Event Loop Blocking]
**Learning:** `SchedulerService.get_system_health` used blocking `requests.get` inside an async function, causing the entire event loop to freeze during network delays.
**Action:** Use `httpx` for all network calls within `async def` methods to ensure non-blocking execution.
