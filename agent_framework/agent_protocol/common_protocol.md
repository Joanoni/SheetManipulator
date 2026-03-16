# Roo Code Agent Protocol - Common Rules

## Initialization & Context
Before writing any code or modifying any files, you MUST perform the following initialization steps:

1. Read the `README.md` located in the root directory to understand the project's high-level purpose.
2. Read all files inside the `agent_framework/` directory to understand the systemic rules, current state, and architectural decisions.
3. **CRITICAL RULE:** All implementation MUST be placed exclusively inside the `src/` directory. Do not create source code files in the root or in the `agent_framework/` folder.

---

# Agent Operating Modes

The Roo Code agent operates in two distinct modes:

## Planning Mode

Planning Mode is responsible for converting high-level planning documents into structured executable tasks.

In this mode the agent:

- Reads planning documents from `agent_framework/task_planning/`
- Interprets features, improvements, and problems
- Decomposes them into atomic tasks
- Generates new phases and tasks inside `agent_framework/tasks/`
- Copies referenced images into task directories

Planning Mode **does NOT execute tasks**.

Rules for Planning Mode are defined in:

```
agent_framework/agent_protocol/planning_mode.md
```

---

## Execution Mode

Execution Mode is responsible for implementing the previously generated tasks.

In this mode the agent:

- Navigates tasks sequentially
- Implements requirements
- Writes attempt reports
- Updates project documentation
- Updates decision logs
- Commits changes to git

Execution Mode **does NOT generate tasks**.

Rules for Execution Mode are defined in:

```
agent_framework/agent_protocol/execution_mode.md
```

---

# Ecosystem File Dictionary

You will interact with the following core files. Understand their objectives and maintain their expected structures:

* **`agent_framework/core_rules.md`**
  * **[Objective]**: Defines systemic constraints, architectural boundaries, and global patterns that must not be violated.
  * **[Expected Structure]**: Markdown list of constitutional rules for the project.

* **`agent_framework/decision_log.md`**
  * **[Objective]**: Architectural Decision Records (ADRs). Tracks why specific technical choices were made and alternatives rejected.
  * **[Expected Structure]**: Markdown entries typically containing Context, Decision, and Consequences.

* **`agent_framework/project_state.md`**
  * **[Objective]**: High-level tracking of the overall progress across project phases.
  * **[Expected Structure]**: Markdown with phase checklists or status markers.

* **`agent_framework/tasks/README.md`**
  * **[Objective]**: General guide and overview for the atomic task execution framework.
  * **[Expected Structure]**: Markdown document explaining the directory structure and general flow.

* **`agent_framework/tasks/[ID]_phase/[ID]_task/status.json`**
  * **[Objective]**: Tracks the current execution state of a specific atomic task.

  Expected template:

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

* **`agent_framework/tasks/[ID]_phase/[ID]_task/task_definition.md`**
  * **[Objective]**: The full technical specification and acceptance criteria for a specific task.

* **`agent_framework/task_planning/`**
  * **[Objective]**: Contains high-level descriptions of features, improvements, or problems that must be converted into structured tasks.

* **`README.md`** (Root)
  * **[Objective]**: Main project documentation and entry point for developers.