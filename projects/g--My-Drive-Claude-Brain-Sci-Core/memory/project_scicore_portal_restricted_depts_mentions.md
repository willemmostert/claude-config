---
name: project-scicore-portal-restricted-depts-mentions
description: "Sci-Core portal additions from 2026-10-01 — restricted departments (Campaigns, Athlete Management, Ambassadors), @mention emails via Resend, and Willem's two profiles"
metadata:
  node_type: memory
  type: project
  originSessionId: 458dc4f4-da6a-4a39-a99a-31c53971ae18
  modified: 2026-10-01T10:43:08.742Z
---

Follow-on to [[project-scicore-portal-instore-build]] (same repo, `C:\Users\info\Developer\gotwurkwebsite`, deploys from `main`). Shipped 2026-10-01, last commit `335c6eb`.

- **Restricted departments** (`RESTRICTED_DEPARTMENTS` in `src/lib/access.ts`): `campaigns`, `athlete_management`, `ambassadors`. Owners/admins do NOT get in by role; only `service_provider` (GotWurk staff = Willem's info@ account) or profiles with the key in `profiles.departments`. To add a department: `DEPARTMENTS` in `management-types.ts`, `RESTRICTED_DEPARTMENTS`, a Sidebar link, and a route folder using `ComingSoonPage`. Access is granted by Willem running SQL in the Supabase editor (`array_append(departments, ...)`); Claude's own prod DB reads/writes and Vercel secret writes were blocked by the permission classifier.
- Access as set: Elizma Ferreira = campaigns + ambassadors; Kyla Oosthuizen = marketing, members_club + athlete_management. All three departments are still "Coming soon" shells (comments + calendar + deliverables placeholders).
- **Willem has two profiles**: info@willemmostert.com (service_provider, no customer_id — his main one) and willemmostert21@gmail.com (client owner). The @mention picker includes service_provider profiles and shows the email beside duplicate names.
- **@mention emails** (`src/lib/mention-email.ts`, called from `addPageComment` via `after()`): uses Resend. Needs `RESEND_API_KEY` and `MENTION_EMAIL_FROM` (verified-domain sender) in Vercel; Willem said he added them but whether the email actually arrived was never confirmed. His Resend key was pasted into chat — rotation unconfirmed, like the Supabase one.
- EOD report window is now 16:00–18:00 SAST; pending rows self-correct on load.

**Why:** Willem wants Campaigns/Athlete/Ambassadors closed to everyone but named people.
**How to apply:** Before adding departments or touching mentions, re-read `access.ts` and `department/actions.ts`; verify deploy state rather than trusting this.
