# Spec-Driven Development

This directory anchors Claude Code's context for multi-step features.

## Workflow
1. **Plan**: Write a spec in `plans/` describing the feature, approach, and affected files
2. **Activate**: Move it to `in-progress/` when implementation begins
3. **Execute**: Claude reads the active spec before writing any code
4. **Archive**: Move to `executed/` when complete

## Rules
- Only ONE spec in `in-progress/` at a time
- Specs survive `/compact` (they're files, not chat context)
- Include: goal, affected files, interface changes, acceptance criteria
- Do NOT delete specs — archive them for history

## Template
```
# Feature: [name]
## Goal
[What and why]
## Affected Files
- [ ] file1.py — what changes
- [ ] file2.py — what changes
## Interface Changes
[Any signature/schema/contract changes]
## Acceptance Criteria
- [ ] criterion 1
- [ ] criterion 2
```
