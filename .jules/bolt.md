## 2024-05-22 - [WeatherService API Latency]
**Learning:** `WeatherService` was fetching from Open-Meteo on every request, which is a significant bottleneck for dashboard performance.
**Action:** Always check for caching on external API calls, especially those used in high-traffic views like dashboards.

## 2024-06-03 - [SchedulerService Event Loop Blocking]
**Learning:** `SchedulerService.get_system_health` used blocking `requests.get` inside an async function, causing the entire event loop to freeze during network delays.
**Action:** Use `httpx` for all network calls within `async def` methods to ensure non-blocking execution.

## 2024-06-18 - [Missing Database Index on Activity Log]
**Learning:** The `SystemActivity` table was missing an index on `timestamp`, causing the activity feed query (`ORDER BY timestamp DESC`) to perform a full table scan. This became a bottleneck as logs grew.
**Action:** Always index columns used in `ORDER BY` or `WHERE` clauses for high-frequency queries.
