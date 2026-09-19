#!/usr/bin/env python3
"""
ChatGPT → Claude Migration Engine (Phase 2)
============================================
Reads the Phase 1 organized_chats/ output and produces a complete
Claude-ready migration package in organized_claude/.

Usage:
    python3 migrate_to_claude.py /path/to/organized_chats

Or with options:
    python3 migrate_to_claude.py /path/to/organized_chats --output ./organized_claude --max-projects 15

Requirements:
    None beyond Python 3.10+ standard library.
    (Phase 1's ijson dependency is NOT needed here.)

This script handles the mechanical work:
    - RFL scoring (Recency, Frequency, Length)
    - Topic clustering from conversation metadata
    - Project folder creation and file sorting
    - Project index with scores and summary cards
    - Potential skills list with scheduled task recommendations
    - Random Stuff catch-all project

Claude (in Cowork) handles the judgment work after this script runs:
    - Memoir extraction (USER_MEMOIR.md, MEMORY_PASTE.md)
    - PROJECT_INSTRUCTIONS.md for each project
    - MIGRATION_GUIDE.md (personalized)
    - ARCHITECTURE_MAP.md
    - COWORK_TASKS.md / CODE_WORKFLOWS.md recommendations
"""

import re
import sys
import math
import shutil
import argparse
from pathlib import Path
from datetime import datetime, date
from collections import defaultdict, Counter


# ─── Constants ───────────────────────────────────────────────────────────────

# RFL weights
W_RECENCY = 0.40
W_FREQUENCY = 0.35
W_LENGTH = 0.25

# Scoring thresholds
STRONG_THRESHOLD = 7.0
MODERATE_THRESHOLD = 4.0

# Target project count range
DEFAULT_MIN_PROJECTS = 5
DEFAULT_MAX_PROJECTS = 15

# Default catch-all projects always recommended
DEFAULT_PROJECTS = [
    ("Random Stuff", "Quick questions, one-off tasks, and conversations that don't fit elsewhere."),
]

STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "must", "need", "this",
    "that", "these", "those", "it", "its", "new", "chat", "get",
    "started", "start", "process", "steps", "guide", "help", "request",
    "overview", "setup", "creation", "create", "summary", "explanation",
    "query", "question", "from", "by", "how", "what", "why", "branch",
    "my", "your", "i", "me", "we", "our", "about", "more", "also",
    "just", "only", "very", "some", "all", "any", "each", "every",
    "both", "other", "into", "out", "up", "down", "no", "not", "so",
    "if", "then", "use", "using", "used", "make", "made", "making",
    "like", "well", "back", "still", "here", "there", "when", "where",
    "which", "who", "whom", "their", "them", "than", "too", "now",
    "way", "first", "one", "two", "three", "based", "via", "per",
    "etc", "vs", "top", "best", "key", "main", "next", "last",
}


# ─── Metadata Parser ────────────────────────────────────────────────────────

# Regex to parse the metadata block written by Phase 1
META_PATTERN = re.compile(
    r"^## (.+?)(?:\s+\(model:\s*(.+?)\))?\s*$\n"
    r"- Date:\s*(.+?)\s*$\n"
    r"- Words:\s*([\d,]+)\s*$\n"
    r"- Source:\s*(.+?)\s*$\n"
    r"- Group:\s*(.+?)\s*$\n"
    r"- Gizmo ID:\s*(.+?)\s*$\n"
    r"- Messages:\s*(\d+)\s*$",
    re.MULTILINE,
)

# Simpler fallback for conversations that might not have full metadata
TITLE_PATTERN = re.compile(r"^## (.+?)(?:\s+\(model:\s*.+?\))?\s*$", re.MULTILINE)


def parse_conversation_metadata(text: str) -> list[dict]:
    """Extract all conversation metadata blocks from a Phase 1 output file."""
    results = []
    for match in META_PATTERN.finditer(text):
        title = match.group(1).strip()
        model = match.group(2) or ""
        date_str = match.group(3).strip()
        words = int(match.group(4).replace(",", ""))
        source = match.group(5).strip()
        group = match.group(6).strip()
        gizmo_id = match.group(7).strip()
        messages = int(match.group(8))

        # Parse date
        conv_date = None
        try:
            conv_date = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
        except Exception:
            pass

        results.append({
            "title": title,
            "model": model,
            "date": conv_date,
            "date_str": date_str,
            "words": words,
            "source": source,
            "group": group,
            "gizmo_id": gizmo_id if gizmo_id != "none" else None,
            "messages": messages,
        })
    return results


def scan_phase1_output(organized_chats: Path) -> list[dict]:
    """Scan all markdown files in organized_chats/ and extract conversation metadata."""
    all_convos = []
    for md_file in sorted(organized_chats.rglob("*.md")):
        if md_file.name.startswith("INDEX") or md_file.name.startswith("_"):
            continue
        try:
            text = md_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        convos = parse_conversation_metadata(text)
        for c in convos:
            c["source_file"] = md_file
            # Determine which subfolder this came from
            rel = md_file.relative_to(organized_chats)
            parts = rel.parts
            if len(parts) >= 3 and parts[1] == "Projects":
                c["phase1_project"] = parts[2]  # folder name
            elif len(parts) >= 3 and parts[1] == "Custom_GPTs":
                c["phase1_gpt"] = parts[2]  # folder name
            else:
                c["phase1_project"] = None
                c["phase1_gpt"] = None
        all_convos.extend(convos)
    return all_convos


# ─── RFL Scoring ─────────────────────────────────────────────────────────────

def score_recency(most_recent_date: date, reference_date: date) -> float:
    """Score 0-10 based on how recent the most recent conversation is."""
    days_ago = (reference_date - most_recent_date).days
    if days_ago < 0:
        days_ago = 0
    if days_ago <= 30:
        return 10.0
    elif days_ago <= 60:
        return 9.0
    elif days_ago <= 90:
        return 8.0
    elif days_ago <= 120:
        return 7.0
    elif days_ago <= 150:
        return 6.0
    elif days_ago <= 180:
        return 5.0
    elif days_ago <= 270:
        return 4.0
    elif days_ago <= 365:
        return 3.0
    elif days_ago <= 540:
        return 2.0
    elif days_ago <= 730:
        return 1.5
    else:
        return 1.0


def score_frequency(num_conversations: int) -> float:
    """Score 0-10 based on conversation count."""
    if num_conversations >= 20:
        return 10.0
    elif num_conversations >= 15:
        return 9.0
    elif num_conversations >= 10:
        return 8.0
    elif num_conversations >= 7:
        return 7.0
    elif num_conversations >= 5:
        return 6.0
    elif num_conversations >= 4:
        return 5.0
    elif num_conversations >= 3:
        return 4.0
    elif num_conversations >= 2:
        return 2.0
    else:
        return 1.0


def score_length(avg_words: float) -> float:
    """Score 0-10 based on average conversation word count."""
    if avg_words >= 5000:
        return 10.0
    elif avg_words >= 3000:
        return 8.0
    elif avg_words >= 2000:
        return 7.0
    elif avg_words >= 1000:
        return 5.0
    elif avg_words >= 500:
        return 3.0
    elif avg_words >= 200:
        return 2.0
    else:
        return 1.0


def calculate_rfl(convos: list[dict], reference_date: date) -> dict:
    """Calculate RFL score for a group of conversations."""
    if not convos:
        return {"score": 0, "recency": 0, "frequency": 0, "length": 0}

    dates = [c["date"] for c in convos if c.get("date")]
    most_recent = max(dates) if dates else date(2020, 1, 1)
    oldest = min(dates) if dates else most_recent

    num_convos = len(convos)
    total_words = sum(c.get("words", 0) for c in convos)
    avg_words = total_words / num_convos if num_convos > 0 else 0

    r = score_recency(most_recent, reference_date)
    f = score_frequency(num_convos)
    l = score_length(avg_words)

    score = (r * W_RECENCY) + (f * W_FREQUENCY) + (l * W_LENGTH)

    return {
        "score": round(score, 1),
        "recency": round(r, 1),
        "frequency": round(f, 1),
        "length": round(l, 1),
        "num_conversations": num_convos,
        "total_words": total_words,
        "avg_words": round(avg_words),
        "most_recent": most_recent.isoformat() if most_recent else None,
        "oldest": oldest.isoformat() if oldest else None,
    }


# ─── Topic Clustering ───────────────────────────────────────────────────────

def extract_keywords(title: str) -> set[str]:
    """Extract meaningful keywords from a conversation title."""
    words = re.findall(r"[a-zA-Z]+", title.lower())
    return {w for w in words if w not in STOP_WORDS and len(w) > 2}


def cluster_conversations(convos: list[dict]) -> dict[str, list[dict]]:
    """
    Group conversations into topic clusters based on keyword overlap.
    Returns {cluster_name: [convos]}.
    """
    # Step 1: Build keyword index
    keyword_to_convos = defaultdict(list)
    for c in convos:
        keywords = extract_keywords(c.get("title", ""))
        for kw in keywords:
            keyword_to_convos[kw].append(c)

    # Step 2: Find keyword groups (keywords that co-occur frequently)
    # Use the most frequent keywords as cluster anchors
    keyword_freq = Counter()
    for c in convos:
        keywords = extract_keywords(c.get("title", ""))
        for kw in keywords:
            keyword_freq[kw] += 1

    # Only consider keywords that appear in 3+ conversations
    significant_keywords = {kw for kw, count in keyword_freq.items() if count >= 3}

    # Step 3: Assign each conversation to its best cluster
    # Build clusters around the most frequent keywords
    assigned = set()
    clusters = {}

    # Sort keywords by frequency (highest first)
    sorted_keywords = sorted(significant_keywords, key=lambda k: -keyword_freq[k])

    for anchor_kw in sorted_keywords:
        if keyword_freq[anchor_kw] < 3:
            continue

        # Find all unassigned conversations that have this keyword
        cluster_convos = []
        for c in keyword_to_convos[anchor_kw]:
            c_id = id(c)
            if c_id not in assigned:
                cluster_convos.append(c)
                assigned.add(c_id)

        if len(cluster_convos) >= 2:
            # Name the cluster from the most common keywords in this group
            cluster_keywords = Counter()
            for c in cluster_convos:
                for kw in extract_keywords(c.get("title", "")):
                    if kw in significant_keywords:
                        cluster_keywords[kw] += 1
            top_words = [w.capitalize() for w, _ in cluster_keywords.most_common(3)]
            name = " ".join(top_words) if top_words else anchor_kw.capitalize()
            clusters[name] = cluster_convos

    # Collect unassigned conversations
    unassigned = [c for c in convos if id(c) not in assigned]

    return clusters, unassigned


def merge_overlapping_clusters(
    clusters: dict[str, list[dict]],
    max_projects: int,
) -> dict[str, list[dict]]:
    """
    If we have too many clusters, merge the smallest/most-similar ones.
    Uses keyword overlap between cluster names to find merge candidates.
    """
    if len(clusters) <= max_projects:
        return clusters

    # Iteratively merge the two most similar small clusters
    while len(clusters) > max_projects:
        # Find the smallest cluster
        smallest_name = min(clusters.keys(), key=lambda k: len(clusters[k]))
        smallest_convos = clusters[smallest_name]

        # Find the most similar other cluster (by keyword overlap in titles)
        smallest_keywords = Counter()
        for c in smallest_convos:
            for kw in extract_keywords(c.get("title", "")):
                smallest_keywords[kw] += 1

        best_match = None
        best_overlap = -1
        for name, convos in clusters.items():
            if name == smallest_name:
                continue
            other_keywords = Counter()
            for c in convos:
                for kw in extract_keywords(c.get("title", "")):
                    other_keywords[kw] += 1
            # Calculate overlap
            overlap = sum((smallest_keywords & other_keywords).values())
            if overlap > best_overlap:
                best_overlap = overlap
                best_match = name

        if best_match is None:
            break

        # Merge smallest into best_match
        clusters[best_match].extend(clusters.pop(smallest_name))

        # Rename the merged cluster based on combined keywords
        combined_keywords = Counter()
        for c in clusters[best_match]:
            for kw in extract_keywords(c.get("title", "")):
                combined_keywords[kw] += 1
        top_words = [w.capitalize() for w, _ in combined_keywords.most_common(3)]
        new_name = " ".join(top_words)
        if new_name != best_match:
            clusters[new_name] = clusters.pop(best_match)

    return clusters


# ─── Skills List Generator ──────────────────────────────────────────────────

def analyze_potential_skills(
    gpt_groups: dict[str, list[dict]],
    all_convos: list[dict],
) -> list[dict]:
    """
    Analyze Custom GPT groups and recurring conversation patterns
    to identify potential Claude skills.
    """
    skills = []

    # Custom GPTs with 5+ conversations
    for gpt_folder, convos in gpt_groups.items():
        if len(convos) < 5:
            continue

        # Analyze conversation patterns
        total_words = sum(c.get("words", 0) for c in convos)
        dates = [c["date"] for c in convos if c.get("date")]
        most_recent = max(dates) if dates else None
        oldest = min(dates) if dates else None

        # Check if it looks like a recurring task (regular intervals)
        is_recurring = False
        if dates and len(dates) >= 5:
            sorted_dates = sorted(dates)
            gaps = [(sorted_dates[i+1] - sorted_dates[i]).days for i in range(len(sorted_dates)-1)]
            avg_gap = sum(gaps) / len(gaps) if gaps else 999
            if avg_gap < 30:  # Used at least monthly
                is_recurring = True

        # Determine if it should be a scheduled task
        is_scheduled = is_recurring and len(convos) >= 10

        # Extract what the GPT seems to do from titles
        title_keywords = Counter()
        for c in convos:
            for kw in extract_keywords(c.get("title", "")):
                title_keywords[kw] += 1
        top_keywords = [w for w, _ in title_keywords.most_common(5)]

        skills.append({
            "name": gpt_folder,
            "source": "Custom GPT",
            "conversations": len(convos),
            "total_words": total_words,
            "keywords": top_keywords,
            "most_recent": most_recent.isoformat() if most_recent else "unknown",
            "oldest": oldest.isoformat() if oldest else "unknown",
            "is_recurring": is_recurring,
            "recommend_scheduled_task": is_scheduled,
            "sample_titles": [c["title"] for c in convos[:5]],
        })

    # Sort by conversation count descending
    skills.sort(key=lambda s: -s["conversations"])
    return skills


# ─── Output Generators ───────────────────────────────────────────────────────

def safe_folder_name(name: str) -> str:
    clean = re.sub(r"[^\w\s-]", "", name)
    clean = re.sub(r"[\s_]+", "_", clean).strip("_")
    return clean[:60] or "Unnamed"


def generate_project_index(
    scored_projects: list[dict],
    output_path: Path,
):
    """Generate _project_index.md with summary cards for every recommended project."""
    lines = ["# Project Index\n"]
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    lines.append(f"Total recommended projects: {len(scored_projects)}\n")
    lines.append("---\n")

    for proj in scored_projects:
        score = proj["rfl"]["score"]
        strength = "STRONG" if score >= STRONG_THRESHOLD else "MODERATE" if score >= MODERATE_THRESHOLD else "OPTIONAL"
        lines.append(f"## {proj['name']} (Score: {score})")
        lines.append(f"- **Recommendation:** {strength}")
        lines.append(f"- **Conversations:** {proj['rfl']['num_conversations']}")
        lines.append(f"- **Total words:** {proj['rfl']['total_words']:,}")
        lines.append(f"- **Date range:** {proj['rfl']['oldest']} — {proj['rfl']['most_recent']}")
        lines.append(f"- **Recency:** {proj['rfl']['recency']}/10 | **Frequency:** {proj['rfl']['frequency']}/10 | **Length:** {proj['rfl']['length']}/10")

        if proj.get("sources"):
            lines.append(f"- **Sources:** {proj['sources']}")

        # Key themes from keywords
        if proj.get("keywords"):
            lines.append(f"- **Key themes:** {', '.join(proj['keywords'])}")

        lines.append("")
        # Sample titles
        lines.append("**Sample conversations:**")
        for title in proj.get("sample_titles", [])[:5]:
            lines.append(f"  - {title}")
        lines.append("\n---\n")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def generate_skills_index(skills: list[dict], output_path: Path):
    """Generate _skills_index.md listing potential skills to build."""
    lines = ["# Potential Skills\n"]
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    lines.append("These are Custom GPTs from your ChatGPT history that could be rebuilt as Claude skills.")
    lines.append("Each one was used frequently enough to suggest a repeatable workflow.\n")
    lines.append("---\n")

    for skill in skills:
        scheduled_tag = " **[SCHEDULED TASK]**" if skill["recommend_scheduled_task"] else ""
        recurring_tag = " (recurring pattern detected)" if skill["is_recurring"] and not skill["recommend_scheduled_task"] else ""

        lines.append(f"## {skill['name']}{scheduled_tag}")
        lines.append(f"- **Source:** {skill['source']}")
        lines.append(f"- **Conversations:** {skill['conversations']}")
        lines.append(f"- **Total words:** {skill['total_words']:,}")
        lines.append(f"- **Active period:** {skill['oldest']} — {skill['most_recent']}")
        lines.append(f"- **Keywords:** {', '.join(skill['keywords'])}")

        if skill["recommend_scheduled_task"]:
            lines.append(f"- **Recommendation:** Create as a **scheduled Cowork task**. This GPT was used {skill['conversations']} times with a regular recurring pattern, suggesting it handles a routine workflow.")
        elif skill["is_recurring"]:
            lines.append(f"- **Recommendation:** Strong candidate for a reusable skill or prompt template.{recurring_tag}")
        else:
            lines.append(f"- **Recommendation:** Consider recreating as a skill if you still need this workflow.")

        lines.append("")
        lines.append("**Sample conversations:**")
        for title in skill["sample_titles"][:5]:
            lines.append(f"  - {title}")
        lines.append("\n---\n")

    if not skills:
        lines.append("*No Custom GPTs with 5+ conversations were found. No skill recommendations to make.*\n")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def generate_phase2_instructions(output_path: Path, scored_projects: list[dict]):
    """
    Generate _CLAUDE_TASKS.md — instructions for Claude to complete
    the judgment-based parts of Phase 2 during the Cowork session.
    """
    project_names = [p["name"] for p in scored_projects]

    lines = ["# Phase 2: Claude Tasks\n"]
    lines.append("These tasks require Claude's judgment and should be completed in the Cowork session")
    lines.append("after the mechanical Phase 2 script has run.\n")
    lines.append("---\n")

    lines.append("## Task 1: Write PROJECT_INSTRUCTIONS.md for Each Project\n")
    lines.append("For each project folder in `projects/`, read the conversation files inside it")
    lines.append("and write a `PROJECT_INSTRUCTIONS.md` that contains:")
    lines.append("- A 2-3 sentence description of what this project is about")
    lines.append("- Recommended custom instructions the user should paste into their Claude Project settings")
    lines.append("- Key terminology and frameworks used in conversations")
    lines.append("- Suggested tone and style based on how the user communicated in these conversations\n")
    lines.append(f"Projects to process: {', '.join(project_names)}\n")
    lines.append("---\n")

    lines.append("## Task 2: Write the Memoir (USER_MEMOIR.md + MEMORY_PASTE.md)\n")
    lines.append("Read conversation files ONLY from the scored projects (not the archive).")
    lines.append("Focus on the highest-scoring projects first.\n")
    lines.append("**USER_MEMOIR.md** should cover:")
    lines.append("- Identity and evolution: who the person was when they started, major phases, current state")
    lines.append("- Thinking patterns: how they approach problems, recurring frameworks, obsessions")
    lines.append("- Emotional anchors: breakthroughs, frustrations, pride points")
    lines.append("- Relationship with AI: usage evolution, trust level, preferences")
    lines.append("- Extract direct quotes that reveal thinking patterns")
    lines.append("- Extract specific numbers they track (revenue, subscribers, etc.)")
    lines.append("- Extract named frameworks with exact terminology")
    lines.append("- Filter for repetition: topics in 3+ conversations carry more weight\n")
    lines.append("**MEMORY_PASTE.md** should be:")
    lines.append("- 2,000-4,000 words maximum")
    lines.append("- Written in third person ('User is...', 'User prefers...')")
    lines.append("- Prioritizes current state over historical detail")
    lines.append("- Formatted for direct paste into Claude Settings > Memory\n")
    lines.append("---\n")

    lines.append("## Task 3: Write MIGRATION_GUIDE.md\n")
    lines.append("Personalized step-by-step instructions for this specific user:")
    lines.append(f"- List the exact {len(scored_projects)} projects to create, in order of priority (highest RFL score first)")
    lines.append("- For each project: what to name it, what files to upload, what custom instructions to set")
    lines.append("- How to paste MEMORY_PASTE.md into Claude memory settings")
    lines.append("- Where to find their archived conversations (organized_chats/) if they need them later")
    lines.append("- Tips for their first week using the new Claude setup\n")
    lines.append("---\n")

    lines.append("## Task 4: Write ARCHITECTURE_MAP.md\n")
    lines.append("Visual overview using markdown showing:")
    lines.append("- All recommended projects in a list with their scores")
    lines.append("- The CCC Framework: which surfaces (Chat, Cowork, Code) each project maps to")
    lines.append("- Memory architecture: Layer 1 (synthesis), Layer 2 (knowledge bases), Layer 3 (skills)")
    lines.append("- Quick reference card for model selection (Sonnet vs Opus)\n")
    lines.append("---\n")

    lines.append("## Task 5: Write COWORK_TASKS.md\n")
    lines.append("Look for repetitive task patterns across the conversation history.")
    lines.append("For each one found, recommend a Cowork automation with:")
    lines.append("- What the task is")
    lines.append("- How often it was done")
    lines.append("- What a Cowork automation would look like")
    lines.append("- Estimated time saved\n")

    output_path.write_text("\n".join(lines), encoding="utf-8")


# ─── Main Pipeline ───────────────────────────────────────────────────────────

def run_migration(organized_chats: Path, output_dir: Path, max_projects: int):
    """Main Phase 2 pipeline."""
    print(f"Phase 2: Migration Engine")
    print(f"Reading Phase 1 output: {organized_chats}")
    print()

    # ── Step 1: Scan all Phase 1 output ──────────────────────────────────
    all_convos = scan_phase1_output(organized_chats)
    print(f"Found {len(all_convos):,} conversations with metadata")

    if not all_convos:
        print("No conversation metadata found. Make sure Phase 1 has run first.")
        print("Looking for files in:", organized_chats)
        sys.exit(1)

    # Reference date for recency scoring
    dates = [c["date"] for c in all_convos if c.get("date")]
    reference_date = max(dates) if dates else date.today()
    print(f"Reference date (most recent conversation): {reference_date}")

    # ── Step 2: Separate already-grouped vs loose conversations ──────────
    # Conversations already in Projects/ or Custom_GPTs/ from Phase 1
    project_convos = defaultdict(list)  # project_folder -> convos
    gpt_convos = defaultdict(list)      # gpt_folder -> convos
    loose_convos = []                   # regular conversations

    for c in all_convos:
        if c.get("phase1_project"):
            project_convos[c["phase1_project"]].append(c)
        elif c.get("phase1_gpt"):
            gpt_convos[c["phase1_gpt"]].append(c)
        else:
            loose_convos.append(c)

    print(f"\nExisting ChatGPT Projects: {len(project_convos)}")
    print(f"Custom GPTs: {len(gpt_convos)}")
    print(f"Loose conversations: {len(loose_convos):,}")

    # ── Step 3: Score existing projects (auto-qualify per design) ─────────
    scored_projects = []

    # Existing ChatGPT Projects → auto-qualify
    for folder_name, convos in project_convos.items():
        rfl = calculate_rfl(convos, reference_date)
        keywords = Counter()
        for c in convos:
            for kw in extract_keywords(c.get("title", "")):
                keywords[kw] += 1
        top_kw = [w for w, _ in keywords.most_common(5)]

        scored_projects.append({
            "name": folder_name.replace("_", " "),
            "folder": folder_name,
            "rfl": rfl,
            "convos": convos,
            "sources": f"ChatGPT Project ({len(convos)} conversations)",
            "keywords": top_kw,
            "sample_titles": [c["title"] for c in convos[:5]],
            "auto_qualified": True,
        })

    print(f"\nAuto-qualified from existing Projects: {len(scored_projects)}")

    # ── Step 4: Cluster loose conversations into topics ──────────────────
    print(f"\nClustering {len(loose_convos):,} loose conversations...")
    clusters, unassigned = cluster_conversations(loose_convos)
    print(f"Found {len(clusters)} topic clusters, {len(unassigned):,} unclustered")

    # Score each cluster
    for cluster_name, convos in clusters.items():
        rfl = calculate_rfl(convos, reference_date)

        # Only recommend clusters that meet minimum threshold
        if rfl["score"] < MODERATE_THRESHOLD and len(convos) < 3:
            unassigned.extend(convos)
            continue

        keywords = Counter()
        for c in convos:
            for kw in extract_keywords(c.get("title", "")):
                keywords[kw] += 1
        top_kw = [w for w, _ in keywords.most_common(5)]

        scored_projects.append({
            "name": cluster_name,
            "folder": safe_folder_name(cluster_name),
            "rfl": rfl,
            "convos": convos,
            "sources": f"Clustered from {len(convos)} loose conversations",
            "keywords": top_kw,
            "sample_titles": [c["title"] for c in convos[:5]],
            "auto_qualified": False,
        })

    # ── Step 5: Merge if too many projects ───────────────────────────────
    # Separate auto-qualified (can't merge those) from scored
    auto_projects = [p for p in scored_projects if p.get("auto_qualified")]
    scored_only = [p for p in scored_projects if not p.get("auto_qualified")]

    # Sort scored by RFL score descending
    scored_only.sort(key=lambda p: -p["rfl"]["score"])

    # If total exceeds max, trim the lowest-scoring non-auto projects
    available_slots = max_projects - len(auto_projects) - len(DEFAULT_PROJECTS)
    if available_slots < 0:
        available_slots = 0

    if len(scored_only) > available_slots:
        # Move excess to unassigned
        excess = scored_only[available_slots:]
        for p in excess:
            unassigned.extend(p["convos"])
        scored_only = scored_only[:available_slots]

    # Combine
    final_projects = auto_projects + scored_only
    final_projects.sort(key=lambda p: -p["rfl"]["score"])

    print(f"\nFinal project recommendations: {len(final_projects)} + {len(DEFAULT_PROJECTS)} defaults")
    for p in final_projects:
        auto_tag = " [auto-qualified]" if p.get("auto_qualified") else ""
        print(f"  {p['rfl']['score']:5.1f}  {p['name'][:40]:40s}  ({p['rfl']['num_conversations']} convos){auto_tag}")

    # ── Step 6: Build output folder structure ────────────────────────────
    print(f"\nBuilding output: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create project folders and copy conversation files
    projects_dir = output_dir / "projects"
    projects_dir.mkdir(exist_ok=True)

    for proj in final_projects:
        folder = projects_dir / safe_folder_name(proj["name"])
        folder.mkdir(exist_ok=True)

        # Copy source files into project folder
        source_files = set()
        for c in proj["convos"]:
            sf = c.get("source_file")
            if sf and sf.exists():
                source_files.add(sf)

        for sf in source_files:
            dest = folder / sf.name
            if not dest.exists():
                shutil.copy2(sf, dest)

    # Random Stuff folder with unassigned conversations info
    random_dir = projects_dir / "Random_Stuff"
    random_dir.mkdir(exist_ok=True)

    # Write a note about unassigned conversations
    if unassigned:
        random_lines = [
            "# Random Stuff\n",
            f"This folder catches {len(unassigned):,} conversations that didn't cluster into a specific project.",
            "These are typically one-off questions, quick lookups, or exploratory chats.\n",
            "The original files are in your `organized_chats/` archive if you need them.\n",
            "---\n",
            "## Sample conversations in this bucket:\n",
        ]
        for c in unassigned[:30]:
            random_lines.append(f"- {c.get('date_str', 'unknown')}: {c['title']}")
        if len(unassigned) > 30:
            random_lines.append(f"\n... and {len(unassigned) - 30:,} more")
        (random_dir / "README.md").write_text("\n".join(random_lines), encoding="utf-8")

        # Copy source files for unassigned (group by month)
        unassigned_files = set()
        for c in unassigned:
            sf = c.get("source_file")
            if sf and sf.exists():
                unassigned_files.add(sf)
        for sf in unassigned_files:
            dest = random_dir / sf.name
            if not dest.exists():
                shutil.copy2(sf, dest)

    # Create memoir directory (placeholder for Claude to fill)
    memoir_dir = output_dir / "memoir"
    memoir_dir.mkdir(exist_ok=True)
    (memoir_dir / "USER_MEMOIR.md").write_text(
        "# User Memoir\n\n*This file will be written by Claude during the Cowork session.*\n",
        encoding="utf-8",
    )
    (memoir_dir / "MEMORY_PASTE.md").write_text(
        "# Memory Paste\n\n*This file will be written by Claude during the Cowork session.*\n"
        "*It should be 2,000-4,000 words, formatted for direct paste into Claude Settings > Memory.*\n",
        encoding="utf-8",
    )

    # Create skills directory
    skills_dir = output_dir / "skills"
    skills_dir.mkdir(exist_ok=True)

    # Create recommendations directory (placeholder)
    rec_dir = output_dir / "recommendations"
    rec_dir.mkdir(exist_ok=True)

    # ── Step 7: Generate index files ─────────────────────────────────────
    # Project index with scores
    generate_project_index(final_projects, projects_dir / "_project_index.md")
    print(f"  Written: projects/_project_index.md")

    # Skills analysis
    skills = analyze_potential_skills(gpt_convos, all_convos)
    generate_skills_index(skills, skills_dir / "_skills_index.md")
    print(f"  Written: skills/_skills_index.md ({len(skills)} potential skills)")

    # Claude task instructions
    generate_phase2_instructions(output_dir / "_CLAUDE_TASKS.md", final_projects)
    print(f"  Written: _CLAUDE_TASKS.md")

    # ── Summary ──────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"Phase 2 mechanical work complete!")
    print(f"  Projects recommended: {len(final_projects)} + {len(DEFAULT_PROJECTS)} defaults")
    print(f"  Potential skills identified: {len(skills)}")
    scheduled_count = sum(1 for s in skills if s["recommend_scheduled_task"])
    if scheduled_count:
        print(f"  Recommended as scheduled tasks: {scheduled_count}")
    print(f"  Conversations in Random Stuff: {len(unassigned):,}")
    print(f"  Output: {output_dir}")
    print(f"\nNext: Claude should read _CLAUDE_TASKS.md and complete the judgment tasks.")
    print(f"{'='*60}")


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Phase 2: Build Claude migration package from organized chat exports.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 migrate_to_claude.py ./organized_chats
  python3 migrate_to_claude.py ./organized_chats --output ./organized_claude
  python3 migrate_to_claude.py ./organized_chats --max-projects 12
        """,
    )
    parser.add_argument(
        "input_folder",
        type=Path,
        help="Path to the organized_chats/ folder from Phase 1",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Output folder (default: organized_claude/ next to input)",
    )
    parser.add_argument(
        "--max-projects", "-p",
        type=int,
        default=DEFAULT_MAX_PROJECTS,
        help=f"Maximum number of recommended projects (default: {DEFAULT_MAX_PROJECTS})",
    )

    args = parser.parse_args()
    input_folder = args.input_folder.expanduser().resolve()
    output_folder = (args.output or input_folder.parent / "organized_claude").expanduser().resolve()
    max_projects = args.max_projects

    if not input_folder.exists():
        print(f"Input folder not found: {input_folder}")
        sys.exit(1)

    run_migration(input_folder, output_folder, max_projects)


if __name__ == "__main__":
    main()
