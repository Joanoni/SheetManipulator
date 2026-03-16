# Roo Code Agent Protocol - Planning Mode

## Task Planning Processing

The agent MUST process planning files located in:

```
agent_framework/task_planning/
```

These files contain high-level feature descriptions, improvements, or problems discovered in the tool that require implementation.

---

## Planning File Interpretation

Planning files may include:

- Feature specifications
- Bug reports
- Improvements
- Architectural changes
- References to supporting images

Images placed in the same directory may be referenced directly inside the planning text by filename.

Example reference inside planning files:

```
See screenshot: error_case_01.png
```

---

## Planning Processing Procedure

When planning files exist inside `agent_framework/task_planning/`, the agent MUST:

1. Read all `.md` files inside `agent_framework/task_planning/`.
2. Interpret the described work items.
3. Decompose them into atomic implementation tasks.
4. Organize the generated tasks into new phases inside:

```
agent_framework/tasks/
```

---

## Phase Creation Rules

1. New phases MUST follow the existing sequential numbering pattern:

```
001_phase
002_phase
003_phase
```

2. Tasks inside phases MUST follow sequential numbering:

```
001_task
002_task
003_task
```

3. Tasks MUST respect dependency ordering when generated.

---

## Task Generation Structure

For each generated task, the agent MUST create:

```
agent_framework/tasks/[ID_PHASE]_phase/[ID_TASK]_task/
```

Containing:

- `task_definition.md`
- `status.json`

And optionally:

- `images/`

---

## status.json Initialization

The `status.json` MUST follow this template:

```json
{
  "task_id": "[ID_TASK]",
  "phase": "[ID_PHASE]_phase",
  "title": "[TITLE]",
  "status": "pending",
  "started_at": null,
  "completed_at": null,
  "assigned_to": "AI Agent",
  "priority": "[PRIORITY]"
}
```

---

## Planning Image Handling

Planning files may reference images placed inside:

```
agent_framework/task_planning/
```

When a planning file references images, the agent MUST:

1. Detect all referenced image filenames inside the planning document.
2. Verify the files exist in `agent_framework/task_planning/`.
3. Create an `images/` directory inside the generated task folder:

```
agent_framework/tasks/[ID_PHASE]_phase/[ID_TASK]_task/images/
```

4. Copy the referenced images into that directory.
5. Preserve original filenames.
6. Do NOT modify the image files.

---

## Planning File Lifecycle

After processing a planning file:

1. Move the processed file to:

```
agent_framework/task_planning/processed/
```

2. Do NOT delete planning files.

Image files MUST remain untouched in the original planning directory.

---

## Planning Execution Termination Rule

After all planning files have been processed and converted into tasks:

1. The agent MUST stop execution.
2. The agent MUST NOT start task execution.
3. Output a terminal message:

```
Task planning processing completed. New tasks generated successfully.
Autonomous execution loop not started.
```