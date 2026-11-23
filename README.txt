Townlight Data 0.2.0 is packaged with Windows beta 1.9.3.1. Windows 1.9.2.1 does not include Data. See the [GitHub release](https://github.com/townlight/townlight/releases/tag/townlight-windows-v1.9.3.1).

Townlight Data

Townlight Data is the Townlight open-data preparation module. Version 0.2.0 ships the local package, FastAPI runtime, deterministic helper functions, optional database-backed publication workpapers, bearer-token protection for persisted retrieval, tests, release gates, public documentation, and browser-verified sample UI for preparing municipal datasets before human-approved publication.

Shipping in v0.2.0

- Dataset field normalization for CKAN-friendly names, date/time hints, and geospatial-review notes.
- Data-dictionary draft generation from source schema metadata.
- CKAN/open-data package metadata drafts with license and redaction blockers.
- Optional SQLAlchemy-backed CKAN package and publication-plan workpaper records through CIVICDATA_PUBLICATION_DB_URL.
- Bearer-token protection for persisted CKAN package and publication-plan retrieval through CIVICDATA_AUTH_TOKEN_ROLES.
- PII/exemption preflight review that blocks readiness until staff review clears findings.
- Records-retention archive bundle checklist support.
- Scheduled publication planning checklists that require human approval.
- FastAPI endpoints, health check, static public UI, and release verification scripts.

Not shipped yet

- Live CKAN publication or API writeback.
- BI dashboards or dashboard hosting.
- Data warehouse storage or long-term operational data storage beyond archive-bundle planning.
- Autonomous redaction or automatic exemption decisions.
- External connector runtime, approval queues, or Townlight Records exemption-engine integration.
- Staff SSO and role-based publication approvals. v0.2.0 protects persisted retrieval only; broader workflow auth comes later.

Install and run locally

Townlight Data v0.2.0 is pinned to townlight-core==1.3.0.dev2.

    python -m venv .venv
    . .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
    python -m pip install -e ".[dev]"
    python -m uvicorn townlight_data.main:app --host 127.0.0.1 --port 8137

Open http://127.0.0.1:8137/civicdata for the browser sample and http://127.0.0.1:8137/docs for FastAPI docs.

Set CIVICDATA_PUBLICATION_DB_URL to persist CKAN package drafts and publication plans. Set CIVICDATA_AUTH_TOKEN_ROLES to a JSON token-to-role map before exposing persisted retrieval. Without the database variable, Townlight Data remains deterministic and stateless. Without the auth variable, persisted retrieval endpoints return actionable 503 guidance. With auth configured, anonymous callers receive 401 and callers without an allowed role receive 403.

API surface

- GET / reports current product state and boundaries.
- GET /health reports civicdata and civiccore versions.
- GET /civicdata renders the public sample page.
- POST /api/v1/civicdata/normalize normalizes field metadata.
- POST /api/v1/civicdata/data-dictionary drafts data-dictionary entries.
- POST /api/v1/civicdata/ckan-package drafts CKAN package metadata.
- GET /api/v1/civicdata/ckan-package/{package_id} retrieves a persisted CKAN package draft when both persistence and retrieval auth are configured.
- POST /api/v1/civicdata/redaction-review flags PII/exemption review needs.
- POST /api/v1/civicdata/archive-bundle prepares records-retention archive checklists.
- POST /api/v1/civicdata/publication-plan prepares human-approved publication checklists.
- GET /api/v1/civicdata/publication-plan/{plan_id} retrieves a persisted publication plan when both persistence and retrieval auth are configured.

Verification

    python -m pytest -q
    bash scripts/verify-docs.sh
    python scripts/check-civiccore-placeholder-imports.py
    python -m ruff check .
    bash scripts/verify-release.sh

Licensing

Code: AGPL-3.0-only, with the TownLight Public Institution Exception for qualifying deployments. See LICENSE and LICENSE-EXCEPTION.md. Documentation is CC BY 4.0 unless otherwise noted. Townlight Data is designed for local municipal operation and does not require outbound runtime calls in the default profile.

Windows staff workflow

In Townlight Data 0.2.0 candidate on Windows Suite full profile, existing Contracts grants let staff select signed agreements and preview only contract ID, title, vendor, start/expiration. An admin explicitly confirms the actual SHA-256 preview before an unattended queue sends to the configured resident Portal. Status states cover selection, hash confirmation, queueing, acknowledgement, correction, and withdrawal. No public link appears until the receiving portal acknowledges. Public outputs include CSV, JSON, and dictionary. Corrections proceed through a new review; withdrawal removes anonymous downloads when delivered. Legacy standalone workpaper APIs remain separate.
