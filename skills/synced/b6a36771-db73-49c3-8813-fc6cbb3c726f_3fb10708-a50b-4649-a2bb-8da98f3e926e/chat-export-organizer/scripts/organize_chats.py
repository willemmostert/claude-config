#!/usr/bin/env python3
"""
Chat Export Organizer
=====================
Takes exported conversation data from ChatGPT and/or Claude and organizes
it into date-based, project-grouped files that are easy to browse, search,
and upload to any AI tool.

Usage:
    python3 organize_chats.py /path/to/export/folder
    python3 organize_chats.py conversations.json
    python3 organize_chats.py chatgpt.json claude.json --output ./organized_chats

Requirements:
    pip install ijson

Supports:
    - ChatGPT conversations.json (mapping/tree structure, with Projects & Custom GPTs)
    - ChatGPT chat.html (embedded JSON)
    - Claude conversations.json (chat_messages structure)
    - Any mix of the above in one folder
"""

import os
import re
import sys
import json
import codecs
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter

try:
    import ijson
except ImportError:
    print("Missing dependency. Install it with:")
    print("  pip install ijson")
    sys.exit(1)


# ─── Constants ───────────────────────────────────────────────────────────────

WORD_RE = re.compile(r"\S+")
ROLE_LABEL = {"user": "User", "assistant": "Assistant"}
DEFAULT_MAX_WORDS = 400_000

# Words to ignore when inferring project/GPT names from titles
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


# ─── Utilities ───────────────────────────────────────────────────────────────

def word_count(text: str) -> int:
    return len(WORD_RE.findall(text))


def normalize_role(raw) -> str | None:
    if not raw:
        return None
    s = str(raw).strip().lower()
    if s in ("user", "human", "person", "customer"):
        return "user"
    if s in ("assistant", "ai", "model", "claude", "bot", "chatgpt"):
        return "assistant"
    return None


def normalize_text(s: str) -> str:
    s = s.lstrip("\ufeff").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def epoch_to_month(ts) -> str | None:
    try:
        return datetime.fromtimestamp(float(ts)).strftime("%Y-%m")
    except Exception:
        return None


def epoch_to_datetime_str(ts) -> str | None:
    try:
        return datetime.fromtimestamp(float(ts)).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return None


def iso_to_month(s: str) -> str | None:
    if not isinstance(s, str) or len(s) < 7:
        return None
    return s[:7]


def safe_folder_name(name: str) -> str:
    """Convert a string into a filesystem-safe folder name."""
    # Replace non-alphanumeric chars with underscores, collapse multiples
    clean = re.sub(r"[^\w\s-]", "", name)
    clean = re.sub(r"[\s_]+", "_", clean).strip("_")
    return clean[:60] or "Unnamed"


# ─── Name Inference ──────────────────────────────────────────────────────────

def infer_group_name(titles: list[str], max_words: int = 3) -> str:
    """
    Given conversation titles from the same project/GPT, infer a short
    descriptive name (2-3 words) by finding the most common meaningful
    words across all titles.
    """
    word_freq = Counter()
    valid_titles = [t for t in titles if t and t != "(untitled)" and t != "New chat"]

    if not valid_titles:
        return "Unnamed"

    for title in valid_titles:
        words = re.findall(r"[a-zA-Z]+", title.lower())
        # Deduplicate within each title so one long title doesn't dominate
        unique_words = set(w for w in words if w not in STOP_WORDS and len(w) > 2)
        for w in unique_words:
            word_freq[w] += 1

    if not word_freq:
        return "Unnamed"

    # Pick top words that appear in a meaningful portion of titles
    threshold = max(2, len(valid_titles) * 0.15)
    candidates = [(w, c) for w, c in word_freq.most_common(20) if c >= threshold]

    if not candidates:
        candidates = word_freq.most_common(max_words)

    name_words = [w.capitalize() for w, _ in candidates[:max_words]]
    return " ".join(name_words) if name_words else "Unnamed"


# ─── ChatGPT Extraction ─────────────────────────────────────────────────────

def chatgpt_get_text(message: dict) -> str:
    content = message.get("content")
    if isinstance(content, dict):
        parts = content.get("parts")
        if isinstance(parts, list):
            out = []
            for x in parts:
                if isinstance(x, str) and x.strip():
                    out.append(x.strip())
                elif isinstance(x, dict):
                    t = x.get("text")
                    if isinstance(t, str) and t.strip():
                        out.append(t.strip())
            return "\n".join(out).strip()
        t = content.get("text")
        return t.strip() if isinstance(t, str) else ""
    return content.strip() if isinstance(content, str) else ""


def chatgpt_walk_active_branch(conv: dict) -> list[tuple]:
    """
    Walk the conversation tree from current_node back to root,
    then reverse for chronological order. Only gets the active branch.
    """
    mapping = conv.get("mapping")
    if not isinstance(mapping, dict):
        return []

    current_node = conv.get("current_node")
    if not current_node or current_node not in mapping:
        return chatgpt_extract_all_sorted(mapping)

    path = []
    node_id = current_node
    visited = set()
    while node_id and node_id in mapping and node_id not in visited:
        visited.add(node_id)
        node = mapping[node_id]
        if not node:
            break
        msg = node.get("message")
        if msg and isinstance(msg, dict):
            author = msg.get("author") or {}
            role = normalize_role(author.get("role") if isinstance(author, dict) else None)
            if role in ("user", "assistant"):
                text = chatgpt_get_text(msg)
                if text:
                    ts = msg.get("create_time") or 0
                    try:
                        ts = float(ts)
                    except (TypeError, ValueError):
                        ts = 0.0
                    path.append((ts, role, text))
        node_id = node.get("parent")

    path.reverse()
    return path


def chatgpt_extract_all_sorted(mapping: dict) -> list[tuple]:
    out = []
    for node in mapping.values():
        if not node:
            continue
        msg = node.get("message")
        if not isinstance(msg, dict):
            continue
        author = msg.get("author") or {}
        role = normalize_role(author.get("role") if isinstance(author, dict) else None)
        if role not in ("user", "assistant"):
            continue
        text = chatgpt_get_text(msg)
        if not text:
            continue
        ts = msg.get("create_time") or 0
        try:
            ts = float(ts)
        except (TypeError, ValueError):
            ts = 0.0
        out.append((ts, role, text))
    out.sort(key=lambda x: x[0])
    return out


def extract_chatgpt_conversation(conv: dict) -> dict:
    title = conv.get("title") or "Untitled"
    create_time = conv.get("create_time")
    month = epoch_to_month(create_time) if create_time else None
    date_str = epoch_to_datetime_str(create_time) if create_time else None
    messages = chatgpt_walk_active_branch(conv)
    model = conv.get("default_model_slug") or ""

    # Grouping metadata
    gizmo_id = conv.get("gizmo_id") or None
    gizmo_type = conv.get("gizmo_type") or None

    # Determine group: project, custom_gpt, or regular
    if gizmo_type == "snorlax" and gizmo_id:
        group = "project"
    elif gizmo_type == "gpt" and gizmo_id:
        group = "custom_gpt"
    else:
        group = "regular"

    return {
        "platform": "ChatGPT",
        "title": title,
        "month": month,
        "date_str": date_str,
        "model": model,
        "messages": messages,
        "group": group,
        "gizmo_id": gizmo_id,
    }


# ─── Claude Extraction ──────────────────────────────────────────────────────

def extract_claude_conversation(conv: dict) -> dict:
    title = conv.get("name") or "Untitled"
    created_at = conv.get("created_at") or ""
    month = iso_to_month(created_at)
    date_str = created_at[:16].replace("T", " ") if len(created_at) >= 16 else None

    chat_messages = conv.get("chat_messages") or []
    messages = []
    for m in chat_messages:
        if not isinstance(m, dict):
            continue
        role = normalize_role(m.get("sender"))
        if role not in ("user", "assistant"):
            continue
        text_parts = []
        content = m.get("content")
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    t = block.get("text", "").strip()
                    if t:
                        text_parts.append(t)
        text = "\n".join(text_parts).strip()
        if not text:
            text = (m.get("text") or "").strip()
        if not text:
            continue
        messages.append((0, role, text))

    return {
        "platform": "Claude",
        "title": title,
        "month": month,
        "date_str": date_str,
        "model": "",
        "messages": messages,
        "group": "regular",
        "gizmo_id": None,
    }


# ─── Format Detection ───────────────────────────────────────────────────────

def detect_format(path: Path) -> str | None:
    try:
        sample = path.read_bytes()[:65536]
    except Exception:
        return None

    if sample.startswith(codecs.BOM_UTF8):
        sample = sample[len(codecs.BOM_UTF8):]

    text = sample.decode("utf-8", errors="ignore").lstrip()

    if text.startswith("<") and "var jsonData" in text[:5000]:
        return "chatgpt_html"
    if text.startswith("<"):
        return "html_other"

    if text.startswith("["):
        try:
            with path.open("rb") as f:
                for item in ijson.items(f, "item"):
                    if isinstance(item, dict):
                        if "mapping" in item:
                            return "chatgpt_json"
                        if "chat_messages" in item:
                            return "claude_json"
                        return "unknown_json"
                    break
        except Exception:
            return "unknown_json"

    return None


# ─── Streaming Parsers ───────────────────────────────────────────────────────

def stream_chatgpt_json(path: Path):
    with path.open("rb") as f:
        try:
            for conv in ijson.items(f, "item"):
                if isinstance(conv, dict) and "mapping" in conv:
                    yield extract_chatgpt_conversation(conv)
        except ijson.common.IncompleteJSONError:
            pass


def stream_chatgpt_html(path: Path):
    with path.open("rb") as f:
        raw = f.read(100_000)
        idx = raw.find(b"var jsonData = ")
        if idx < 0:
            return
        json_offset = idx + len(b"var jsonData = ")

    with path.open("rb") as f:
        f.seek(json_offset)
        try:
            for conv in ijson.items(f, "item"):
                if isinstance(conv, dict) and "mapping" in conv:
                    yield extract_chatgpt_conversation(conv)
        except ijson.common.IncompleteJSONError:
            pass


def stream_claude_json(path: Path):
    with path.open("rb") as f:
        try:
            for conv in ijson.items(f, "item"):
                if isinstance(conv, dict) and "chat_messages" in conv:
                    yield extract_claude_conversation(conv)
        except ijson.common.IncompleteJSONError:
            pass


# ─── File Writer ─────────────────────────────────────────────────────────────

def format_conversation(conv: dict) -> str:
    lines = []
    title = conv["title"]
    date_str = conv["date_str"] or "Unknown date"
    model = conv["model"]
    platform = conv["platform"]
    group = conv["group"]
    gizmo_id = conv.get("gizmo_id")
    messages = conv["messages"]

    # Calculate word count and message count
    total_words = sum(word_count(text) for _, _, text in messages)
    message_count = len(messages)

    # Format header with metadata
    header = f"## {title}  (model: {model})" if model else f"## {title}"
    lines.append(header)

    # Add structured metadata
    lines.append(f"- Date: {date_str}")
    lines.append(f"- Words: {total_words:,}")
    lines.append(f"- Source: {platform}")
    lines.append(f"- Group: {group}")
    gizmo_str = gizmo_id if gizmo_id else "none"
    lines.append(f"- Gizmo ID: {gizmo_str}")
    lines.append(f"- Messages: {message_count}")
    lines.append("")

    for ts, role, text in messages:
        label = ROLE_LABEL.get(role, role)
        lines.append(f"**{label}:**\n")
        lines.append(normalize_text(text))
        lines.append("")

    lines.append("---\n")
    return "\n".join(lines)


def write_conversations_to_files(
    convos: list[dict],
    label: str,
    output_dir: Path,
    max_words: int,
    max_bytes: int = 29_000_000,
) -> dict:
    """
    Write conversations to files, grouped by month, splitting large months.
    Checks byte size before writing and splits if necessary.
    Returns stats dict.
    """
    stats = {"files": 0, "conversations": 0}
    if not convos:
        return stats

    output_dir.mkdir(parents=True, exist_ok=True)

    # Group by month
    by_month: dict[str, list] = defaultdict(list)
    for conv in convos:
        month = conv.get("month") or "unknown"
        by_month[month].append(conv)

    stats["conversations"] = len(convos)

    for month in sorted(by_month.keys()):
        month_convos = by_month[month]
        part = 1
        current_words = 0
        current_lines = []

        def flush(part_num):
            if not current_lines:
                return
            suffix = f"_part{part_num}" if part_num > 1 else ""
            filename = f"{month}_{label}{suffix}.md"
            filepath = output_dir / filename
            header = f"# {label} — {month}" + (f" (Part {part_num})" if suffix else "") + "\n\n"
            content = header + "\n".join(current_lines)
            content_bytes = content.encode("utf-8")

            # Check byte size and split if necessary
            if len(content_bytes) > max_bytes:
                # Split the lines to stay under max_bytes
                sub_part = 1
                sub_lines = []
                sub_bytes = len(header.encode("utf-8"))

                for line_block in current_lines:
                    line_bytes = (line_block + "\n").encode("utf-8")
                    if sub_bytes > 0 and sub_bytes + line_bytes > max_bytes:
                        # Write current sub-part
                        sub_suffix = f"_part{part_num}_sub{sub_part}"
                        sub_filename = f"{month}_{label}{sub_suffix}.md"
                        sub_filepath = output_dir / sub_filename
                        sub_content = header + "\n".join(sub_lines)
                        sub_filepath.write_text(sub_content, encoding="utf-8")
                        stats["files"] += 1

                        sub_part += 1
                        sub_lines = []
                        sub_bytes = len(header.encode("utf-8"))

                    sub_lines.append(line_block)
                    sub_bytes += len(line_bytes)

                # Write final sub-part
                if sub_lines:
                    sub_suffix = f"_part{part_num}_sub{sub_part}"
                    sub_filename = f"{month}_{label}{sub_suffix}.md"
                    sub_filepath = output_dir / sub_filename
                    sub_content = header + "\n".join(sub_lines)
                    sub_filepath.write_text(sub_content, encoding="utf-8")
                    stats["files"] += 1
            else:
                filepath.write_text(content, encoding="utf-8")
                stats["files"] += 1

        for conv in month_convos:
            block = format_conversation(conv)
            block_words = word_count(block)
            if current_words > 0 and current_words + block_words > max_words:
                flush(part)
                part += 1
                current_words = 0
                current_lines = []
            current_lines.append(block)
            current_words += block_words

        flush(part)

    return stats


# ─── Main Processing ─────────────────────────────────────────────────────────

def discover_files(folder: Path) -> list[tuple[Path, str]]:
    results = []
    for p in sorted(folder.iterdir()):
        if not p.is_file():
            continue
        if p.suffix.lower() not in (".json", ".html", ".htm"):
            continue
        if p.name.startswith("."):
            continue
        fmt = detect_format(p)
        if fmt and fmt in ("chatgpt_json", "chatgpt_html", "claude_json"):
            results.append((p, fmt))
    return results


def run_pipeline(files: list[tuple[Path, str]], output_dir: Path, max_words: int, max_bytes: int = 29_000_000):
    """Core pipeline: parse files → group → infer names → write output."""
    if not files:
        print("No supported export files found.")
        sys.exit(1)

    print(f"Found {len(files)} export file(s):\n")
    for p, fmt in files:
        size_mb = p.stat().st_size / (1024 * 1024)
        print(f"  {p.name:40s}  {size_mb:>8.1f} MB  [{fmt}]")
    print()

    # ── Pass 1: Parse all conversations ──────────────────────────────────
    all_convos = []
    for path, fmt in files:
        print(f"Processing: {path.name} ...", end=" ", flush=True)
        count = 0
        if fmt == "chatgpt_json":
            stream = stream_chatgpt_json(path)
        elif fmt == "chatgpt_html":
            stream = stream_chatgpt_html(path)
        elif fmt == "claude_json":
            stream = stream_claude_json(path)
        else:
            continue

        for conv in stream:
            if not conv.get("month") or not conv["messages"]:
                continue
            all_convos.append(conv)
            count += 1

        print(f"{count:,} conversations")

    print(f"\nTotal usable conversations: {len(all_convos):,}")

    # ── Pass 2: Separate by platform and group ───────────────────────────
    chatgpt_projects: dict[str, list] = defaultdict(list)   # gizmo_id -> convos
    chatgpt_gpts: dict[str, list] = defaultdict(list)       # gizmo_id -> convos
    chatgpt_regular: list = []
    claude_regular: list = []

    for conv in all_convos:
        if conv["platform"] == "Claude":
            claude_regular.append(conv)
        elif conv["group"] == "project":
            chatgpt_projects[conv["gizmo_id"]].append(conv)
        elif conv["group"] == "custom_gpt":
            chatgpt_gpts[conv["gizmo_id"]].append(conv)
        else:
            chatgpt_regular.append(conv)

    # ── Pass 3: Infer names for projects and GPTs ────────────────────────
    def dedupe_names(name_map: dict[str, str]) -> dict[str, str]:
        """Ensure no two groups map to the same folder name."""
        folder_counts: dict[str, int] = defaultdict(int)
        result = {}
        # Process in order of most conversations first (so the biggest group gets the clean name)
        for gid in name_map:
            name = name_map[gid]
            folder = safe_folder_name(name)
            folder_counts[folder] += 1
            if folder_counts[folder] > 1:
                result[gid] = f"{name} {folder_counts[folder]}"
            else:
                result[gid] = name
        return result

    project_names = {}
    for gid, convos in chatgpt_projects.items():
        titles = [c["title"] for c in convos]
        inferred = infer_group_name(titles)
        project_names[gid] = inferred
    project_names = dedupe_names(project_names)

    gpt_names = {}
    for gid, convos in chatgpt_gpts.items():
        titles = [c["title"] for c in convos]
        inferred = infer_group_name(titles)
        gpt_names[gid] = inferred
    gpt_names = dedupe_names(gpt_names)

    # Print what we found
    if chatgpt_projects:
        print(f"\nChatGPT Projects found: {len(chatgpt_projects)}")
        for gid in sorted(chatgpt_projects.keys(), key=lambda k: -len(chatgpt_projects[k])):
            convos = chatgpt_projects[gid]
            name = project_names[gid]
            print(f"  {name:30s}  ({len(convos)} conversations)")

    if chatgpt_gpts:
        print(f"\nCustom GPTs found: {len(chatgpt_gpts)}")
        for gid in sorted(chatgpt_gpts.keys(), key=lambda k: -len(chatgpt_gpts[k]))[:20]:
            convos = chatgpt_gpts[gid]
            name = gpt_names[gid]
            print(f"  {name:30s}  ({len(convos)} conversations)")
        if len(chatgpt_gpts) > 20:
            print(f"  ... and {len(chatgpt_gpts) - 20} more")

    # ── Pass 4: Write everything ─────────────────────────────────────────
    output_dir.mkdir(parents=True, exist_ok=True)
    total_stats = {"files": 0, "conversations": 0}

    # ChatGPT regular conversations → organized_chats/ChatGPT/
    if chatgpt_regular:
        print(f"\nWriting ChatGPT regular conversations...")
        s = write_conversations_to_files(
            chatgpt_regular, "ChatGPT", output_dir / "ChatGPT", max_words, max_bytes
        )
        total_stats["files"] += s["files"]
        total_stats["conversations"] += s["conversations"]
        print(f"  {s['files']} files ({s['conversations']:,} conversations)")

    # ChatGPT Projects → organized_chats/ChatGPT/Projects/<InferredName>/
    if chatgpt_projects:
        print(f"\nWriting ChatGPT Projects...")
        for gid, convos in chatgpt_projects.items():
            name = project_names[gid]
            folder_name = safe_folder_name(name)
            project_dir = output_dir / "ChatGPT" / "Projects" / folder_name
            s = write_conversations_to_files(convos, name, project_dir, max_words, max_bytes)
            total_stats["files"] += s["files"]
            total_stats["conversations"] += s["conversations"]
            print(f"  {name}: {s['files']} files ({s['conversations']:,} conversations)")

    # ChatGPT Custom GPTs → organized_chats/ChatGPT/Custom_GPTs/<InferredName>/
    if chatgpt_gpts:
        print(f"\nWriting Custom GPTs...")
        for gid, convos in chatgpt_gpts.items():
            name = gpt_names[gid]
            folder_name = safe_folder_name(name)
            gpt_dir = output_dir / "ChatGPT" / "Custom_GPTs" / folder_name
            s = write_conversations_to_files(convos, name, gpt_dir, max_words, max_bytes)
            total_stats["files"] += s["files"]
            total_stats["conversations"] += s["conversations"]
            print(f"  {name}: {s['files']} files ({s['conversations']:,} conversations)")

    # Claude → organized_chats/Claude/
    if claude_regular:
        print(f"\nWriting Claude conversations...")
        s = write_conversations_to_files(
            claude_regular, "Claude", output_dir / "Claude", max_words, max_bytes
        )
        total_stats["files"] += s["files"]
        total_stats["conversations"] += s["conversations"]
        print(f"  {s['files']} files ({s['conversations']:,} conversations)")

    # ── Write INDEX.md ───────────────────────────────────────────────────
    index_path = output_dir / "INDEX.md"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("# Organized Chat Export\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")

        if chatgpt_regular or chatgpt_projects or chatgpt_gpts:
            f.write("## ChatGPT\n\n")

            if chatgpt_regular:
                total_words = sum(
                    sum(word_count(t) for _, _, t in c["messages"]) for c in chatgpt_regular
                )
                f.write(f"**Regular conversations:** {len(chatgpt_regular):,} conversations (~{total_words:,} words)\n\n")

            if chatgpt_projects:
                f.write(f"**Projects:** {len(chatgpt_projects)} projects\n\n")
                for gid in sorted(chatgpt_projects.keys(), key=lambda k: -len(chatgpt_projects[k])):
                    convos = chatgpt_projects[gid]
                    name = project_names[gid]
                    total_words = sum(
                        sum(word_count(t) for _, _, t in c["messages"]) for c in convos
                    )
                    f.write(f"- **{name}**: {len(convos)} conversations (~{total_words:,} words)\n")
                f.write("\n")

            if chatgpt_gpts:
                f.write(f"**Custom GPTs:** {len(chatgpt_gpts)} GPTs\n\n")
                for gid in sorted(chatgpt_gpts.keys(), key=lambda k: -len(chatgpt_gpts[k])):
                    convos = chatgpt_gpts[gid]
                    name = gpt_names[gid]
                    f.write(f"- **{name}**: {len(convos)} conversations\n")
                f.write("\n")

        if claude_regular:
            f.write("## Claude\n\n")
            total_words = sum(
                sum(word_count(t) for _, _, t in c["messages"]) for c in claude_regular
            )
            f.write(f"**Conversations:** {len(claude_regular):,} (~{total_words:,} words)\n\n")

    print(f"\n{'='*60}")
    print(f"Done! {total_stats['files']} files, {total_stats['conversations']:,} conversations")
    print(f"Output: {output_dir}")
    print(f"Index:  {index_path}")
    print(f"{'='*60}")


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Organize ChatGPT and Claude exports into date-based, project-grouped files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Point at a folder containing export files
  python3 organize_chats.py ~/Downloads/ChatGPT_Data

  # Point at individual file(s) directly
  python3 organize_chats.py conversations.json
  python3 organize_chats.py chatgpt.json claude.json

  # Custom output location
  python3 organize_chats.py ~/Downloads/ChatGPT_Data --output ~/Documents/organized_chats

  # Custom word limit per file
  python3 organize_chats.py ~/Downloads/ChatGPT_Data --max-words 300000
        """,
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="Path(s) to export folder(s) or individual file(s) (conversations.json, chat.html, etc.)",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Output folder (default: ./organized_chats next to input)",
    )
    parser.add_argument(
        "--max-words", "-m",
        type=int,
        default=DEFAULT_MAX_WORDS,
        help=f"Max words per output file before splitting (default: {DEFAULT_MAX_WORDS:,})",
    )
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=29_000_000,
        help=f"Max bytes per output file before splitting (default: 29,000,000)",
    )

    args = parser.parse_args()
    max_words = args.max_words
    max_bytes = args.max_bytes
    inputs = [p.expanduser().resolve() for p in args.inputs]

    folders = [p for p in inputs if p.is_dir()]
    individual_files = [p for p in inputs if p.is_file()]
    missing = [p for p in inputs if not p.exists()]

    if missing:
        for p in missing:
            print(f"Not found: {p}")
        if not folders and not individual_files:
            sys.exit(1)

    # Determine output directory
    if args.output:
        output_folder = args.output.expanduser().resolve()
    elif folders:
        output_folder = folders[0] / "organized_chats"
    elif individual_files:
        output_folder = individual_files[0].parent / "organized_chats"
    else:
        output_folder = Path.cwd() / "organized_chats"

    # Collect all parseable files
    all_files = []
    for f in individual_files:
        fmt = detect_format(f)
        if fmt and fmt in ("chatgpt_json", "chatgpt_html", "claude_json"):
            all_files.append((f, fmt))
        else:
            print(f"Skipping (unrecognized format): {f.name}")

    for folder in folders:
        print(f"Scanning: {folder}")
        all_files.extend(discover_files(folder))

    run_pipeline(all_files, output_folder, max_words, max_bytes)


if __name__ == "__main__":
    main()
