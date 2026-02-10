## 2024-05-22 - [WeatherService API Latency]
**Learning:** `WeatherService` was fetching from Open-Meteo on every request, which is a significant bottleneck for dashboard performance.
**Action:** Always check for caching on external API calls, especially those used in high-traffic views like dashboards.

## 2024-06-03 - [SchedulerService Event Loop Blocking]
**Learning:** `SchedulerService.get_system_health` used blocking `requests.get` inside an async function, causing the entire event loop to freeze during network delays.
**Action:** Use `httpx` for all network calls within `async def` methods to ensure non-blocking execution.

## 2026-02-05 - [Event Loop Blocking in Service Layer]
**Learning:** `SchedulerService.get_dashboard_stats` was defined as `async def` but performed heavy synchronous database and service calls, effectively blocking the asyncio event loop for the duration of the request.
**Action:** Identify `async def` functions that don't await anything but do heavy work. Refactor them to run in a thread pool using `loop.run_in_executor(None, sync_func)` to keep the application responsive.
## 2024-06-18 - [Missing Database Index on Activity Log]
**Learning:** The `SystemActivity` table was missing an index on `timestamp`, causing the activity feed query (`ORDER BY timestamp DESC`) to perform a full table scan. This became a bottleneck as logs grew.
**Action:** Always index columns used in `ORDER BY` or `WHERE` clauses for high-frequency queries.
