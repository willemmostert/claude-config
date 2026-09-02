---
name: feedback-gmail-base64-attachment-limit
description: "Manually retyping a large base64 blob between reading an encoded file and calling an attachment tool silently corrupts it - verify with a hash before trusting it, or skip the attachment"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5137aabc-9146-44d1-91a5-103bfc70496c
  modified: 2026-09-02T13:19:53.955Z
---

Do not manually copy a large base64-encoded file (e.g. a generated .docx, ~10KB+ raw / ~14KB+ base64) from a Read tool result into another tool's inline `content` parameter (e.g. Gmail's `create_draft` attachments) and assume it arrived intact.

**Why:** Tried this once for a ~14KB base64 Word doc attachment — the Gmail API rejected it with "Base64 decoding failed." Verified the root cause directly: wrote the exact string I intended to send to a separate file and diffed it byte-for-byte against the original source file with `sha256sum`/`cmp`. The hashes did not match — my retyped copy was 278 characters longer and diverged partway through, meaning the act of reproducing a long, structureless (non-natural-language) string as part of generating a tool call silently introduced corruption. This is a real failure mode, not a one-off fluke — long random-looking strings are exactly the kind of content a model can drop or duplicate characters in without any visible sign of doing so.

**How to apply:** Before trusting any tool call that requires manually transcribing a large encoded blob (base64, hex, etc.) from one tool's output into another tool's input:
1. Prefer a path that avoids the manual transcription entirely — a Drive link, a tool that accepts a file path, or a smaller/leaner file that keeps the encoded string short enough to reproduce reliably (rough rule of thumb: under ~1-2KB is fairly safe, several KB+ is risky).
2. If transcription is unavoidable, verify before treating it as sent: write your reproduced string to a local file via Bash/Write and compare its hash (`sha256sum`) against the original source file. Do not skip this just because the tool call "succeeded" syntactically — the corruption only surfaces as a decode error on the receiving end, or worse, silently as a corrupted file the recipient can't open.
3. If verification fails or isn't practical, don't force it — fall back to leaving the attachment out and telling the user exactly where the file is saved so they can attach it manually in their own client. That's what happened for the [[project_blu_horizon]] disclosure-doc email: the Gmail draft was created without the attachment, with a note in the body telling Willem which file to attach before sending.
