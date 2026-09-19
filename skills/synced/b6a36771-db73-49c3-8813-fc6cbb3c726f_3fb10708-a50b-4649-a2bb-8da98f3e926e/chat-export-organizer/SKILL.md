---
name: chat-export-organizer
description: >
  Organize exported conversation data from ChatGPT and Claude into date-sorted,
  browsable files, then build a complete Claude migration package with project
  recommendations, memoir, and setup instructions. Use this skill whenever the user
  wants to process, organize, parse, sort, or split AI chat exports — including
  conversations.json, chat.html, or any data export folder from OpenAI/ChatGPT or
  Anthropic/Claude. Triggers include: "organize my chats", "sort my conversations",
  "parse my ChatGPT export", "break up my conversations file", "split conversations
  by date", "export organizer", "chat history organizer", "process my AI export data",
  "migrate from ChatGPT", "migrate to Claude", "import my ChatGPT data", or any
  mention of conversations.json or chat.html from ChatGPT/Claude in the context of
  organizing, parsing, or splitting. Also trigger when users mention moving conversation
  data between platforms or preparing chat exports for upload to tools like NotebookLM,
  Google Docs, or any knowledge base.
---

# Chat Export Organizer + Migration Engine

Two-phase pipeline:
- **Phase 1:** Organize raw exports into clean, date-sorted, project-grouped files
- **Phase 2:** Score, cluster, and build a complete Claude migration package

## What To Do When This Skill Triggers

### Step 0: Install dependency

```bash
pip install ijson --break-system-packages -q
```

### Step 1: Find the files

Check in this order:

**A) User uploaded file(s)** — gather paths from uploads directory.
**B) User has a folder selected** — look inside it for export files.
**C) No files visible** — ask the user to upload or select a folder.

### Step 2: Run Phase 1

```bash
python3 <SKILL_DIR>/scripts/organize_chats.py <input> --output <output>/organized_chats
```

Accepts individual files OR folders. Auto-detects ChatGPT vs Claude.

### Step 3: Run Phase 2

```bash
python3 <SKILL_DIR>/scripts/migrate_to_claude.py <output>/organized_chats --output <output>/organized_claude
```

This produces the mechanical migration package: scored projects, folder structure, skills list, and placeholder files.

### Step 4: Complete the judgment tasks

After Phase 2 finishes, read `<output>/organized_claude/_CLAUDE_TASKS.md`. It contains specific instructions for the 5 judgment tasks that require Claude's analysis:

1. **PROJECT_INSTRUCTIONS.md** for each project folder
2. **USER_MEMOIR.md** + **MEMORY_PASTE.md** (memoir extraction)
3. **MIGRATION_GUIDE.md** (personalized setup guide)
4. **ARCHITECTURE_MAP.md** (visual overview)
5. **COWORK_TASKS.md** (automation recommendations)

Read conversation files from the highest-scoring projects first. For the memoir, ONLY use conversations from the scored projects — not the full archive.

### Step 5: Present results

Tell the user:
- How many projects were recommended (with scores)
- How many potential skills were identified
- Where to find the migration guide
- Link to the output folders

---

## Output Structure

### Phase 1: organized_chats/

```
organized_chats/
├── INDEX.md
├── ChatGPT/
│   ├── 2023-01_ChatGPT.md          ← Regular conversations by month
│   ├── ...
│   ├── Projects/
│   │   ├── Bible_Word_Study/        ← Inferred project names
│   │   └── ...
│   └── Custom_GPTs/
│       ├── Title_Ideas/             ← Inferred GPT names
│       └── ...
└── Claude/
    └── ...
```

### Phase 2: organized_claude/

```
organized_claude/
├── _CLAUDE_TASKS.md               ← Instructions for Claude's judgment tasks
├── memoir/
│   ├── USER_MEMOIR.md             ← Written by Claude
│   └── MEMORY_PASTE.md           ← Written by Claude (2-4K words, paste into memory)
├── projects/
│   ├── _project_index.md          ← Summary cards with RFL scores
│   ├── Bible_Word_Study/          ← One folder per recommended project
│   │   ├── PROJECT_INSTRUCTIONS.md ← Written by Claude
│   │   └── [conversation files]
│   ├── Content_Strategy/
│   │   └── ...
│   ├── Random_Stuff/              ← Catch-all for unclustered conversations
│   │   └── README.md
│   └── ...
├── skills/
│   └── _skills_index.md           ← Potential skills + scheduled task recommendations
└── recommendations/
    ├── COWORK_TASKS.md            ← Written by Claude
    └── MIGRATION_GUIDE.md         ← Written by Claude
```

---

## How Phase 2 Scoring Works

### RFL Score (Recency, Frequency, Length)

Each topic cluster is scored on three dimensions:

| Factor | Weight | Scoring |
|--------|--------|---------|
| Recency | 40% | Days since last conversation. <30 days = 10, <90 = 8, <180 = 5, >2yr = 1 |
| Frequency | 35% | Number of conversations. 20+ = 10, 10+ = 8, 5+ = 6, 3+ = 4 |
| Length | 25% | Average words per conversation. 5000+ = 10, 3000+ = 8, 1000+ = 5 |

**Score 7-10:** Strong project candidate. Auto-recommended.
**Score 4-6:** Moderate candidate. Created but marked optional.
**Below 4:** Stays in archive. Goes to Random Stuff if unclustered.

**Hard rules that override the score:**
- Existing ChatGPT Projects auto-qualify regardless of score
- Custom GPTs with 5+ conversations get a skill recommendation
- Single conversations never create a project
- Minimum 3 conversations to calculate a score

**Self-calibrating:** Target is 5-15 projects. If scoring produces more than the max, lower-scored clusters get trimmed. If fewer than 5, the threshold stays as-is.

### Topic Clustering

Loose conversations (not in a Project or GPT) are clustered by keyword overlap in titles. The algorithm:
1. Extracts meaningful keywords from each title
2. Groups by co-occurring keywords (minimum 3 conversations per cluster)
3. Names each cluster from its top 3 keywords
4. Merges overlapping clusters if total exceeds max-projects

---

## Skills Detection

Custom GPTs with 5+ conversations are analyzed for:
- **Recurring pattern:** Used at regular intervals (monthly or more) → recommend as **scheduled Cowork task**
- **Heavy usage:** 10+ conversations → strong skill candidate
- **Keywords:** Extracted from conversation titles to describe what the GPT did

The `_skills_index.md` lists each potential skill with a recommendation on whether it should be a regular skill or a scheduled task.
