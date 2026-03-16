# Roo Code Agent Protocol - Execution Mode

## The Autonomous Execution Loop

You must follow this finite-state machine workflow strictly to implement the SheetManipulator project. Do not skip steps.

1. Navigate sequentially through the task directories located in `agent_framework/tasks/` (starting from the earliest phase/task up to the final one). Read the files inside the current task's directory.

    1.1. If the `status.json` file has the status `"completed"`, move to the next sequential task directory and restart from Step 1.

    1.2. If the `status.json` file has a status other than `"completed"`, count the number of files ending with `_report.md` in the current task's directory.

        1.2.1. If there are exactly 3 `_report.md` files:

            1.2.1.1. Update the `status.json` file status to `"failed"`.

            1.2.1.2. Output a terminal warning stating:

```
Task attempts exhausted. Halting execution.
```

            1.2.1.3. Stop the agent execution immediately.

        1.2.2. If there are between 0 and 2 `_report.md` files:

            1.2.2.1. Update the `status.json` file status to `"in_progress"`.

            1.2.2.2. Create a new file named `attempt_[N]_report.md`.

            1.2.2.3. Read the `task_definition.md` and create a checklist of activities required to fulfill the task.

            1.2.2.4. Implement the requirements defined in the checklist.

            1.2.2.5. As each activity is completed, mark it as completed inside `attempt_[N]_report.md`.

            1.2.2.6. Update the `attempt_[N]_report.md` with a summary of what was implemented and any important technical notes.

            1.2.2.7. Review the checklist to verify if all task requirements were satisfied.

            1.2.2.8. If the task implementation is incomplete or incorrect:

                1.2.2.8.1. Finalize the `attempt_[N]_report.md` with an analysis explaining what remains unresolved.

                1.2.2.8.2. Loop back to Step 1 to initiate the next attempt.

            1.2.2.9. If all checklist items and task requirements are satisfied:

                1.2.2.9.1. Update the `status.json` file status to `"completed"`.

                1.2.2.9.2. Update `agent_framework/project_state.md`.

                1.2.2.9.3. Update `agent_framework/decision_log.md`.

                1.2.2.9.4. Update the root `README.md` with the implemented feature.

                1.2.2.9.5. Check if updates are needed in `agent_framework/core_rules.md`.

                1.2.2.9.6. Execute git commands:

```
git add .
git commit -m "feat: completed task [Task Name/Number]"
git push
```

                1.2.2.9.7. Loop back to Step 1 to proceed to the next task.