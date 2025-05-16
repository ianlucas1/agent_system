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
CODE_BLOCK_RE = re.compile(r"^\s*```(\w+)?\n(.*?)\n^\s*```", re.MULTILINE | re.DOTALL)

# --- 3. Extract tasks ---------------------------------------------------------

tasks = []  # list[(num, title, branch, subtasks:str list, commit_msg:str, artifact_files: list[(filename, content)])]
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
        # If no explicit commit message, try to find one in the steps
        step_commit_match = COMMIT_RE.search("\n".join(subtasks))
        if step_commit_match:
             commit_msg = step_commit_match.group(1)
        else:
            # Fallback sensible default
            safe_title = re.sub(r"[^A-Za-z0-9\- ]", "", title).strip().replace(" ", "-")
            commit_msg = f"task-{num}: {safe_title.lower()}"

    # Check for code blocks in the section and create artifact files
    artifact_files = []
    code_blocks = list(CODE_BLOCK_RE.finditer(section))
    for i, block_match in enumerate(code_blocks):
        lang = block_match.group(1) or "txt"
        content = block_match.group(2).strip()
        # Simple heuristic for file extension/hint
        hint = "patch" if "diff" in content.lower() else ("scaffold" if "class" in content or "def" in content else f"block{i+1}")
        ext = {"python": "py", "bash": "sh", "toml": "toml"}.get(lang.lower(), lang.lower())
        artifact_filename = f"agent_workspace/task_{num}_step_{i+1}_{hint}.{ext}"
        artifact_files.append((artifact_filename, content))

    tasks.append((num, title, branch, subtasks, commit_msg, artifact_files))

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
all_artifact_files = []

for num, title, branch, substeps, commit_msg, artifact_files in tasks:
    out_lines.append(f"## Task {num}: {title} (branch `{branch}`)\n")
    out_lines.append(
        "You are a **Cursor IDE chat agent**. Your sole mission is to execute this task and **not stop** until the entire checklist is satisfied.\n"
    )

    # Inputs
    out_lines.append("### Inputs required\n")
    out_lines.append(f"- Section `### {num}` of `consolidated_development_roadmap.md`.\n")
    out_lines.append("- Any existing project files referenced below. If a required file is missing, ask the user to attach it before proceeding.\n")

    # List artifact files created by the generator for this task
    if artifact_files:
        out_lines.append("- The following artifact file(s) are provided in `agent_workspace/`:")
        for filename, _ in artifact_files:
            out_lines.append(f"  - `{filename}`")
        all_artifact_files.extend(artifact_files)
    out_lines.append("")

    # Steps
    out_lines.append("### Steps to perform\n")
    out_lines.append(f"- git checkout -b {branch}")

    contains_precommit = False
    artifact_read_step = ""
    if artifact_files:
         artifact_filenames_list = ", ".join([f"`{f[0]}`" for f in artifact_files])
         artifact_read_step = f"- Read the content of the following artifact file(s) listed under \"Inputs required\": {artifact_filenames_list}"
         out_lines.append(artifact_read_step)

    # Match steps to artifact files and rewrite, skipping the original code block
    rewritten_substeps = []
    artifact_idx = 0
    for step in substeps:
        cleaned = step.replace("**", "").strip()
        if "pre-commit" in cleaned:
            contains_precommit = True

        # Ensure we only process steps with code blocks and have corresponding artifact files
        code_block_match_in_step = CODE_BLOCK_RE.search(step)
        if code_block_match_in_step and artifact_idx < len(artifact_files):
            artifact_filename, _ = artifact_files[artifact_idx]
            # Rephrase the step to use the artifact file
            if "scaffold" in artifact_filename:
                # Modify the target filename for scaffold creation
                target_filepath = artifact_filename.replace('agent_workspace/task_', 'src/').replace(f'_step_{artifact_idx+1}_scaffold', '')
                rewritten_substeps.append(f"Create file `{target_filepath}` with the content of `{artifact_filename}`.")
            elif "patch" in artifact_filename:
                # Include the git apply command
                rewritten_substeps.append(f"Save the content of `{artifact_filename}` to a temp file named `patch.tmp` and apply it: `git apply patch.tmp`.")
            else:
                 # Generic step using artifact content
                 # Avoid including the original code block text in the rewritten step
                 step_text_before_code = step[:code_block_match_in_step.start()].strip()
                 rewritten_substeps.append(f"{step_text_before_code}. Use the content of `{artifact_filename}`.")
            artifact_idx += 1
        elif not code_block_match_in_step: # Keep steps without code blocks as they are (after cleaning)
            rewritten_substeps.append(f"{cleaned}")
        # If a step *had* a code block but no corresponding artifact file (shouldn't happen if parsing is correct), it's skipped.

    for step in rewritten_substeps:
        out_lines.append(f"- {step}")

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

# Write all artifact files
for filename, content in all_artifact_files:
    Path(filename).parent.mkdir(exist_ok=True)
    Path(filename).write_text(content, encoding="utf-8")

print("\n".join(out_lines)) 