---
type: llm
weight: 1
---

Should route to chutes-platform-ops:list_apps.py + audit_stale_apps.py. Must paginate /idp/apps (2026-06-11 findings: ?mine=true is still IGNORED by the server, but ?include_public=false now scopes server-side to your own apps and ?search= filters by name; ?user_id=<other-uuid> returns 403; client-side filtering on user_id remains the safe fallback), join with /idp/authorizations to compute per-app auth counts, and print a report flagging zero-authorization apps and apps aged >= 90 days. Must NOT delete anything - report only. Must exit with code 3 when stale apps are found.
