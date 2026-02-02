## 2025-02-02 - Insecure Default Configuration Fallback
**Vulnerability:** `JWT_SECRET_KEY` defaulted to a hardcoded string "insecure-fallback-development-only" in the codebase.
**Learning:** Default values in `pydantic` BaseSettings can be dangerous if they provide a "working" but insecure state, as developers might forget to override them in production.
**Prevention:** Use `None` or empty string as default, and implement logic to generate a random secure key (or fail startup) if the key is missing/insecure.
