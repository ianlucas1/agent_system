import re
from pathlib import Path
import sys

"""build_prompts.py – generate roadmap_prompts.md
Usage:
    python scripts/build_prompts.py > roadmap_prompts.md

The script parses consolidated_development_roadmap.md and emits a markdown
file where each section is a **stand-alone prompt** for a fresh Cursor IDE
chat-agent.
"""

# --- 1. Locate source roadmap -------------------------------------------------
roadmap_path = Path(__file__).resolve().parent.parent / "consolidated_development_roadmap.md"
if not roadmap_path.exists():
    sys.stderr.write("❌  consolidated_development_roadmap.md not found.\n")
    sys.exit(1)

roadmap_text = roadmap_path.read_text(encoding="utf-8")

# --- 2. Regex helpers ---------------------------------------------------------
TASK_HDR_RE = re.compile(r"^###\s*(\d+)\s+(.+?)\s+→\s+branch\s+`([^`]+)`", re.MULTILINE)
SUBTASK_RE = re.compile(r"^\*\s+\*\*(\d+\.\d+)\*\*\s+(.*)$", re.MULTILINE)
COMMIT_RE = re.compile(r"git commit -m\s+\"([^\"]+)\"")

# --- 3. Extract tasks ---------------------------------------------------------

tasks = []  # list[(num, title, branch, subtasks:str list, commit_msg:str)]
for m in TASK_HDR_RE.finditer(roadmap_text):
    num, title, branch = m.group(1), m.group(2).strip(), m.group(3).strip()
    start = m.end()
    next_match = TASK_HDR_RE.search(roadmap_text, start)
    end = next_match.start() if next_match else len(roadmap_text)
    section = roadmap_text[start:end]

    # Sub-steps
    subtasks = [sm.group(0).lstrip("* ").strip() for sm in SUBTASK_RE.finditer(section)]

    # Commit message (best-effort)
    commit_match = COMMIT_RE.search(section)
    if commit_match:
        commit_msg = commit_match.group(1)
    else:
        # Fallback sensible default
        safe_title = re.sub(r"[^A-Za-z0-9\- ]", "", title).strip().replace(" ", "-")
        commit_msg = f"task-{num}: {safe_title.lower()}"

    tasks.append((num, title, branch, subtasks, commit_msg))

# --- 4. Templates -------------------------------------------------------------
HEADER = """<!--
⚠️  THIS FILE IS AUTO-GENERATED. DO NOT EDIT BY HAND.
Run:  python scripts/build_prompts.py > roadmap_prompts.md
-->

# Roadmap Prompts

Each section below is a stand-alone prompt that can be copy-pasted into a new
Cursor IDE chat session. Begin with Task 1 and proceed sequentially. A fresh
agent instance should be used for every task to avoid context bloat.
"""

CLI_SNIP = """```bash
git add -A
git commit -m \"{commit_msg}\"
git push --set-upstream origin {branch}
gh pr create --base main --head {branch} --draft --fill
gh pr ready <PR_NUMBER>
gh pr checks <PR_NUMBER> --watch
printf \"y\\n\" | gh pr merge <PR_NUMBER> --merge --delete-branch
git checkout main
git pull --ff-only origin main
git branch -d {branch}
```"""

DEBRIEF_TMPL = """```markdown
## Debrief for Task {num}

- Task Completed: Task {num}: {title} (branch `{branch}`)
- Summary of Changes: <fill>
- Key Files Modified/Created: <fill>
- Commit SHA: <fill>
- PR Link: <fill>
- Tag (if applicable): <fill>
- Current Git Status: <fill>
- Next Task Information: <fill>
- Potential Issues or Notes for Next Agent: <fill>
```"""

# --- 5. Render ----------------------------------------------------------------

out_lines = [HEADER]
for num, title, branch, substeps, commit_msg in tasks:
    out_lines.append(f"## Task {num}: {title} (branch `{branch}`)\n")
    out_lines.append(
        "You are a **Cursor IDE chat agent**. Your sole mission is to execute this task and **not stop** until the entire checklist is satisfied.\n"
    )

    # Inputs
    out_lines.append("### Inputs required\n")
    out_lines.append(f"- Section `### {num}` of `consolidated_development_roadmap.md`.\n")
    out_lines.append("- Any existing project files referenced below. If a required file is missing, ask the user to attach it before proceeding.\n")

    # Steps
    out_lines.append("### Steps to perform\n")
    out_lines.append(f"- git checkout -b {branch}")

    contains_precommit = False
    if substeps:
        for step in substeps:
            cleaned = step.replace("**", "").strip()
            if "pre-commit" in cleaned:
                contains_precommit = True
            out_lines.append(f"- {cleaned}")
    else:
        out_lines.append("- Follow the sub-steps in the roadmap section.")

    # Append safety guard for pre-commit if needed
    if contains_precommit:
        out_lines.append("- If `pre-commit` is not available, run `pip install pre-commit && pre-commit install` then retry the previous step.")

    out_lines.append("")

    # Checklist
    out_lines.append("### Do-Not-Stop-Until checklist\n")
    out_lines.append("- All code / docs edits are applied.\n")
    out_lines.append("- Quality gates pass: `ruff`, `pytest -q`, etc.\n")
    out_lines.append("- GitHub workflow executed (see snippet below).\n")
    out_lines.append("- Debrief block posted in this chat using the template.\n")

    # CLI snippet & Debrief
    out_lines.append("### GitHub CLI workflow (copy/paste)\n")
    out_lines.append(CLI_SNIP.format(commit_msg=commit_msg, branch=branch))

    out_lines.append("### Debrief template\n")
    out_lines.append(DEBRIEF_TMPL.format(num=num, title=title, branch=branch))

    # Persistence instructions
    out_lines.append("### Persistence actions\n")
    out_lines.append(
        f"After you paste the debrief above, also **append** `Task {num}` to `agent_workspace/roadmap_progress.txt` (create the file if it does not exist).\n"
    )
    out_lines.append(
        f"Save the same debrief block to `agent_workspace/debrief_task_{num}.md` and append a link (or the block itself) to `agent_workspace/debrief_index.md` so future agents have a chronological ledger.\n"
    )

    # Final success sentinel
    out_lines.append(
        "When **everything** above is complete, reply only with:\n```success: Task "
        + num
        + " complete```\n\n---\n"
    )

print("\n".join(out_lines)) 