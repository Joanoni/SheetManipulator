# ADSP FRAMEWORK DNA (v1.0.0)

<context>

This document establishes the primary semantic foundation for the Autonomous Development for Simple Projects (ADSP) framework. It defines the universal boundaries and state-management protocols that apply to all specialized agents.

</context>

---

## 🛡️ Operational Pillars
<rules>

| Pillar | Definition | Critical Constraint |
| :--- | :--- | :--- |
| **Source Code** | **MANDATORY Root** | All implementation logic **MUST** reside in the `src/` directory. |
| **Integrity** | Role Isolation | Agents **MUST NOT** perform actions or access data outside their assigned mode slug's scope. |
| **Blueprint** | **Single Source** | Use ONLY `.adsp/blueprints/blueprint.md`. No project-named subfolders. |
| **State** | Status Log Authority | The file `.adsp/status_log.md` is the absolute source of truth for project progression. |
| **Safety** | Transactional Code | Every modification to the `src/` directory must be treated as a reversible transaction via Git. |

</rules>

---

## 📁 Shared Semantic Map
<architecture>

* **Input Layer:** `.adsp/inbox/` (Raw user intent).
* **Strategic Layer:** `.adsp/blueprints/` (Conceptual map).
* **Technical Layer:** `.adsp/specs/` (Architectural design).
* **Execution Layer:** `.adsp/tasks/` (Atomic task units).
* **Global Registry:** `.adsp/status_log.md` (State tracking).

</architecture>

---

**CRITICAL:** Agents must synchronize the `status_log.md`, add, commit with message and push BEFORE concluding any session.