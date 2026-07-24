# Content OS — Phase 1 (MVP) Build Plan

## Context

The user wants a full "Content Operating System" for Instagram/TikTok/YouTube Shorts/X/Threads content production, running on top of Notion, with API-driven automation (Notion API, Google Drive API, Claude/OpenAI), built in Node/TypeScript so it can later be triggered from n8n. The full spec (25+ Notion databases, shot-list generator, script builder, Drive integration, analytics, AI coach, templates, calendars, future RAG/vector search) is too large to build and verify in one pass.

The user chose an **MVP-first** sequencing: get Inbox → Inspiration Database → AI analysis → Content Library working end-to-end first, then layer in Shot Lists, Scripts, Drive, Analytics, Templates, Calendars, etc. in later phases. They confirmed:
- Metadata scraping: integrate a **paid scraper (Apify)** from day one for Instagram/TikTok metrics (not just free oEmbed), behind a swappable `MetadataProvider` interface.
- AI provider: default to **Claude**, with OpenAI supported as a swappable alternate behind an `AIProvider` interface.
- They already have Notion/Google/AI API credentials — these go in a local `.env` file the user fills in themselves; I never ask for or handle raw keys in chat.

The working directory (`g:\My Drive\Claude Brain\Content OS`) is currently empty — this is a greenfield build, not a modification of existing code. No exploration of existing code was needed.

This plan covers **Deliverable 1 (OS.md) + Phase 1 MVP** of the user's requested 12-step deliverable order. Phases 2+ (Shot Lists, Scripts, Drive integration, Editing/Publishing Queues, Analytics, Templates, Calendars, AI Coach chat, transcripts/RAG/vector search) are documented in OS.md's roadmap but **not built** in this pass — they get their own future plan/build passes.

## Architecture Decisions

- **Provider interfaces everywhere**: `MetadataProvider`, `AIProvider` are TypeScript interfaces with swappable implementations selected via env config — no hardcoded vendor lock-in, matches the "avoid hardcoding / config files / future expansion" requirement.
- **Inbox = Inspiration DB with a Status property**, not two separate databases. A pasted URL becomes a page with `Status: New`; the pipeline advances it through `Analyzing → Analyzed → Promoted → Archived`. This avoids duplicate data entry and matches how Notion databases are actually used (single source of truth, filtered views for "Inbox").
- **Trigger-agnostic core logic**: the actual pipeline (`ingestInspiration(url)`) is a plain function, called by (a) a CLI command for manual testing, and (b) a polling watcher for the "just paste and it processes" experience. This is the seam where an n8n workflow (Notion trigger → HTTP call) drops in later without touching pipeline code.
- **Schema evolution note for Content Library**: Phase 2 DBs (Shot Lists, Scripts, Drive Assets) don't exist yet, so Content Library can't have real Notion `relation` properties to them yet. Phase 1 adds plain placeholder properties (rich_text/url) for those slots; Phase 2's provisioning script upgrades them to true relations. This is documented explicitly in OS.md so it isn't a surprise later.
- **Metadata reality check documented up front**: Instagram/TikTok require Apify actor runs (cost + rate limits) for engagement metrics; YouTube uses the official Data API v3; X/Threads fall back to oEmbed/manual entry since neither has a reliable free metrics API. This is written into OS.md as an explicit limitation, not glossed over.

## Deliverables in this pass

### 1. `OS.md` (master blueprint, written first, before any code)
Sections: Vision & principles · System architecture diagram (textual) · Full folder structure · Complete Notion database map for ALL 25+ databases from the spec, tagged by phase (Phase 1 built now / Phase 2 / Phase 3 / Phase 4) · Database relationship diagram · Data flow (paste → parse → AI analyze → write-back → promote to project → production → publish → analyze) · Automation flow (polling now, n8n later) · API integration layer design (the 4 interfaces) · Naming conventions · Environment variable reference · Future expansion roadmap (Whisper transcripts, frame extraction, AI thumbnails, trend prediction, competitor tracking, RAG/vector DB, MCP/agent workflows, team collab, mobile/desktop). This is the authoritative reference for every future phase, not just Phase 1.

### 2. Project scaffold
`package.json` (TypeScript, `@notionhq/client`, `@anthropic-ai/sdk`, `openai`, `commander`, `dotenv`, `zod` for env validation, `vitest` for tests), `tsconfig.json`, `.env.example`, `.gitignore`, `README.md`.

### 3. Config & types layer
- `src/config/env.ts` — loads and validates all env vars with `zod` (fails fast with a clear message if something required is missing), single source of truth for config.
- `src/types/*.ts` — `Platform`, `InspirationRecord`, `NormalizedMetadata`, `AIAnalysisResult` types shared across layers.

### 4. Notion layer (`src/notion/`)
- `client.ts` — thin wrapper around `@notionhq/client`.
- `schemas/*.schema.ts` — property schema definitions for Inspiration, Creators, Content Pillars, Content Library, expressed as data (not hardcoded API calls) so the provisioning script and future migrations both read from the same source.
- `provision.ts` — idempotent script: creates the 4 Phase-1 databases as children of `NOTION_PARENT_PAGE_ID` if they don't already exist (checks by title first), sets up relations between them.
- `repositories/*Repo.ts` — CRUD helpers per database (create page, query by status, update properties, append AI-analysis blocks to page body).

### 5. Metadata layer (`src/metadata/`)
- `urlParser.ts` — detects platform from a pasted URL (Instagram/TikTok/YouTube/X/Threads).
- `MetadataProvider.ts` — interface: `fetchMetadata(url): Promise<NormalizedMetadata>`.
- `providers/oembedProvider.ts` — YouTube + X, free oEmbed.
- `providers/apifyProvider.ts` — Instagram + TikTok via Apify actor runs (actor IDs configurable via env, not hardcoded).
- `resolveMetadata.ts` — picks the right provider per platform, normalizes output, marks fields that couldn't be fetched as `null` (surfaced as empty Notion properties for manual fill, never fabricated).

### 6. AI layer (`src/ai/`)
- `AIProvider.ts` — interface: `analyzeContent(metadata): Promise<AIAnalysisResult>`.
- `providers/claudeProvider.ts` (default, selected via `AI_PROVIDER=claude`) and `providers/openaiProvider.ts` (alternate).
- `prompts/analysis.prompt.ts` — structured-output prompt covering every AI analysis field from the spec (summary, why it performed well, hook breakdown, psychology, story structure, editing breakdown, retention techniques, visual pacing, suggested improvements, remake/improve guidance, etc.), returned as validated JSON.

### 7. Workflow + CLI (`src/workflows/`, `src/cli/`)
- `ingestInspiration.ts` — the core pipeline: create/find Notion page → resolve metadata → write metadata properties → run AI analysis → append analysis blocks to page body → set `Status: Analyzed`.
- `watchInbox.ts` — polls the Inspiration DB on an interval (`WATCH_INTERVAL_SECONDS`) for `Status: New` pages and runs the pipeline on each — this is what makes "paste a URL into Notion and it just works" true without touching a terminal each time.
- `cli/index.ts` — `content-os provision`, `content-os ingest <url>`, `content-os watch` commands (Commander-based).

### 8. Docs
- `docs/INSTALL.md` — step-by-step: create a Notion internal integration and share a parent page with it, get an Apify token + confirm/duplicate the Instagram & TikTok actors, get a YouTube Data API key, get an Anthropic and/or OpenAI key, fill `.env`, run `npm run provision`, run `npm run watch`.
- `docs/DEVELOPER.md` — architecture explanation, how to add a new `MetadataProvider` or `AIProvider`, how the schema-as-data pattern works for adding new databases later.
- `docs/ROADMAP.md` — the full Phase 2/3/4 plan pulled from OS.md, so future work has a checklist to pick up from.

### 9. Minimal tests (`tests/`)
`urlParser` platform-detection tests and `resolveMetadata` normalization tests using `vitest` — no live API calls, pure logic checks that run without any credentials.

## Verification

1. `npm install && npm run build` — TypeScript compiles clean.
2. `npm test` — unit tests pass without needing any real API keys.
3. User fills in their own `.env` from `.env.example` (I never see or request the actual key values).
4. `npm run provision` — user runs this themselves against their real Notion workspace; verify by checking the 4 databases appear correctly nested under their parent page with correct properties/relations.
5. `npm run ingest -- "<a real Instagram/TikTok/YouTube URL>"` — user runs this themselves; verify a Notion page is created with metadata populated and AI analysis blocks appended.
6. `npm run watch` — paste a new URL directly into the Notion Inbox view, confirm it gets picked up and processed within one polling interval.

Not built in this pass (documented in OS.md roadmap for later): Shot List Generator, Script Builder, Google Drive folder automation, Editing/Publishing Queues, Analytics tracking, Content Calendar, Templates, AI Coach chat interface, Audio/B-Roll libraries, transcripts/Whisper, frame extraction, RAG/vector search, n8n webhook receiver, team/mobile/desktop features.
