## 2025-02-02 - Insecure Default Configuration Fallback
**Vulnerability:** `JWT_SECRET_KEY` defaulted to a hardcoded string "insecure-fallback-development-only" in the codebase.
**Learning:** Default values in `pydantic` BaseSettings can be dangerous if they provide a "working" but insecure state, as developers might forget to override them in production.
**Prevention:** Use `None` or empty string as default, and implement logic to generate a random secure key (or fail startup) if the key is missing/insecure.

## 2026-02-04 - [System Control Endpoint Restricted]
**Vulnerability:** The `/control/{action}` endpoint allowed unauthenticated execution of system scripts via `subprocess` from any network location.
**Learning:** Sensitive administrative actions (shutdown/boot) were exposed without IP restrictions or authentication.
**Prevention:** Implemented `verify_local_request` dependency to strictly enforce localhost access (127.0.0.1, ::1) for critical system routes.
