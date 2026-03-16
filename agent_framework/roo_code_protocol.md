# Roo Code Autonomous Protocol

## Phase 0: Initialization & Context
Before writing any code or modifying any files, you MUST perform the following initialization steps:
1. Read the `README.md` located in the root directory to understand the project's high-level purpose.
2. Read all files inside the `agent_framework/` directory to understand the systemic rules, current state, and architectural decisions.
3. **CRITICAL RULE:** All implementation MUST be placed exclusively inside the `src/` directory. Do not create source code files in the root or in the `agent_framework/` folder.

## Phase 1: Ecosystem File Dictionary
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

* **`src/tasks/README.md`**
  * **[Objective]**: General guide and overview for the atomic task execution framework.
  * **[Expected Structure]**: Markdown document explaining the directory structure and general flow.

* **`src/tasks/[ID]_phase/[ID]_task/status.json`**
  * **[Objective]**: Tracks the current execution state of a specific atomic task.
  * **[Expected Structure]**: A JSON object containing at least a `"status"` key. Valid values are usually `"pending"`, `"in_progress"`, `"completed"`, or `"failed"`.

* **`src/tasks/[ID]_phase/[ID]_task/task_definition.md`**
  * **[Objective]**: The full technical specification and acceptance criteria for a specific task.
  * **[Expected Structure]**: Markdown document with context, requirements, and expected outputs.

* **`README.md`** (Root)
  * **[Objective]**: Main project documentation, tech stack overview, and entry point for developers.
  * **[Expected Structure]**: Standard Markdown documentation format.

## Phase 2: The Autonomous Execution Loop
You must follow this finite-state machine workflow strictly to implement the SheetManipulator project. Do not skip steps.

1. Navigate sequentially through the task directories located in `src/tasks/` (starting from the earliest phase/task up to the final one). Read the files inside the current task's directory.    
    1.1. If the `status.json` file has the status `"completed"`, move to the next sequential task directory and restart from Step 1.    
    1.2. If the `status.json` file has a status other than `"completed"`, count the number of files ending with `_report.md` in the current task's directory.        
        1.2.1. If there are exactly 3 `_report.md` files:
            1.2.1.1. Update the `status.json` file status to `"failed"`.
            1.2.1.2. Output a terminal warning stating: "Task attempts exhausted. Halting execution."
            1.2.1.3. Stop the agent execution immediately.            
        1.2.2. If there are between 0 and 2 `_report.md` files:
            1.2.2.1. Update the `status.json` file status to `"in_progress"`.
            1.2.2.2. Create a new file named `attempt_[N]_report.md` (where N is the current attempt number: 1, 2, or 3) containing a checklist of activities required to fulfill the `task_definition.md`.
            1.2.2.3. Implement the requirements defined in the checklist. As each activity is completed, check it off inside the `attempt_[N]_report.md` file.
            1.2.2.4. Create a python script inside `src/tests/` strictly focused on validating the acceptance criteria of the current task.
            1.2.2.5. Execute the created test script via the terminal.
            1.2.2.6. Update the `attempt_[N]_report.md` with a summary of what was done, what was tested, and the exact terminal execution log/result (success or failure).
            1.2.2.7. If the test script FAILS:
                1.2.2.7.1. Finalize the `attempt_[N]_report.md` with an analysis of why the failure occurred.
                1.2.2.7.2. Loop back to Step 1 to initiate the next attempt (which will create a new report).
            1.2.2.8. If the test script SUCCEEDS:
                1.2.2.8.1. Update the `status.json` file status to `"completed"`.
                1.2.2.8.2. Update `agent_framework/project_state.md` to reflect the newly completed task, maintaining its current format.
                1.2.2.8.3. Update `agent_framework/decision_log.md` with any architectural or technical decisions made during this implementation, maintaining its current format.
                1.2.2.8.4. Check if any updates are needed in `agent_framework/core_rules.md` based on new patterns established.
                    1.2.2.8.4.1. If updates are needed, modify `agent_framework/core_rules.md` maintaining its current format.
                1.2.2.8.5. Execute git commands: `git add .`, `git commit -m "feat: completed task [Task Name/Number]"` and `git push`.
                1.2.2.8.6. Loop back to Step 1 to proceed to the next task.