---
name: calculate-web-rules
description: Enforce the mandatory development and delivery rules for the calculate web project. Use when Codex is working in F:\AI Project\calculate web and must classify a request as investigation, modification, or new work; limit changes to the allowed scope; avoid forbidden edits; and format the response with full file paths, line ranges, before/after code, and a closing summary table.
---

# Calculate Web Rules

## Overview

Apply the project-specific rules in `../CODEX_RULES.md` before inspecting, modifying, or adding files in this repository.
Treat `../CODEX_RULES.md` as the source of truth if this skill summary and the rules file ever diverge.

## Required Workflow

1. Read `../CODEX_RULES.md` at the start of every task in this repository.
2. Declare the task type at the beginning of the response:
   - Use the investigation task label from `../CODEX_RULES.md` for report-only work.
   - Use the modification task label from `../CODEX_RULES.md` for edits to existing code.
   - Use the new-work task label from `../CODEX_RULES.md` when creating files or features.
3. Check the hard restrictions before editing:
   - Do not modify logic marked as completed and excluded from repeat changes in `../CODEX_RULES.md`.
   - Do not delete any existing field or interface; only add or extend.
   - Do not modify `.docx` Word template files.
   - Do not change more than 3 files in a single task. Split the work if needed.
4. Apply the technical rules while implementing:
   - Add an inline specification/source comment for every hardcoded structural calculation constant.
   - Keep new frontend inputs visually consistent with nearby inputs.
   - Give every new frontend field a default value.
   - Fetch allowed values and limits from the backend instead of hardcoding calculation results in the frontend.
   - Use the `/api/v1/` route prefix for every new backend API.
   - Add `Field(description="...")` to every new Pydantic field.
   - Move section-parameter lookup logic into a dedicated function instead of hardcoding it inside checking functions.
5. End every completed task with the required summary table.

## Output Rules

### Investigation Tasks

- Do not edit files.
- Output a report that identifies the issue, likely cause, affected files, and a recommended next step.

### Modification Tasks

For each changed file, provide:

1. Full file path
2. Changed line range
3. Before code in a fenced code block
4. After code in a fenced code block
5. One-sentence summary of what changed and why

### New Work Tasks

- State every new file path and explain its purpose.
- If existing files are also modified, include the full modification-task format for those files.

## Required Closing Table

Always end with the exact table format defined in `../CODEX_RULES.md`.

If needed, copy the header row directly from that file to avoid drift.

## Quick Checks

- If the requested work would touch more than 3 files, stop and split the work into smaller batches.
- If a request conflicts with the rules, explain the conflict and propose a compliant alternative.
- If a structural calculation constant is added without a citation comment, fix it before finishing.
