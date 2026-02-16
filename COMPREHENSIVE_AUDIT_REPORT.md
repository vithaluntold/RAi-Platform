# RAi Platform — Comprehensive System Audit Report

> **Scope**: Every model, schema, service, API endpoint, and frontend UI file in the workflow/assignment system and all supporting subsystems.
> **Method**: Full source-code reading of every file — no inference or guessing.

---

## Table of Contents

1. [Data Model Hierarchy](#1-data-model-hierarchy)
2. [Service Methods & Business Logic](#2-service-methods--business-logic)
3. [API Endpoints](#3-api-endpoints)
4. [Schema Validation](#4-schema-validation)
5. [Auto-Progression Logic](#5-auto-progression-logic)
6. [Canvas Visualization](#6-canvas-visualization)
7. [AI Agent Integration](#7-ai-agent-integration)
8. [Assignment Lifecycle](#8-assignment-lifecycle)
9. [Project / Kanban Features](#9-project--kanban-features)
10. [Client & Contact Management](#10-client--contact-management)
11. [Notification & Reminder Systems](#11-notification--reminder-systems)
12. [Authentication & Authorization](#12-authentication--authorization)
13. [Frontend UI Capabilities](#13-frontend-ui-capabilities)
14. [Identified Bugs, Gaps & Risks](#14-identified-bugs-gaps--risks)
15. [Summary Statistics](#15-summary-statistics)

---

## 1. Data Model Hierarchy

The system implements a **template → instance** pattern. Workflow templates are designed once; assignments clone them into independent, trackable instances.

### 1.1 Workflow Templates (4 tables)

#### `workflows`

| Column | Type | Constraints |
| -------- | ------ | ------------- |
| `id` | UUID PK | `uuid4()` default |
| `organization_id` | UUID | nullable |
| `name` | String(255) | not null |
| `description` | String(1000) | nullable |
| `status` | Enum(`draft`, `active`, `archived`) | default `draft` |
| `custom_metadata` | JSON | nullable |
| `created_by` | UUID | nullable |
| `created_at` | DateTime | server default `now()` |
| `updated_at` | DateTime | auto-update |

- **Index**: `idx_workflows_org_status` on `(organization_id, status)`

#### `workflow_stages`

| Column | Type | Constraints |
| -------- | ------ | ------------- |
| `id` | UUID PK | |
| `workflow_id` | UUID | not null (no FK constraint) |
| `name` | String(255) | not null |
| `description` | String(1000) | nullable |
| `position` | Integer | not null |
| `custom_metadata` | JSON | nullable |
| `created_at` / `updated_at` | DateTime | |

- **Indexes**: `idx_workflow_stages_workflow`, `idx_workflow_stages_position`

#### `workflow_steps`

| Column | Type | Constraints |
| -------- | ------ | ------------- |
| `id` | UUID PK | |
| `stage_id` | UUID | not null (no FK constraint) |
| `name` | String(255) | not null |
| `description` | String(1000) | nullable |
| `position` | Integer | not null |
| `custom_metadata` | JSON | nullable |
| `created_at` / `updated_at` | DateTime | |

#### `workflow_tasks`

| Column | Type | Constraints |
| -------- | ------ | ------------- |
| `id` | UUID PK | |
| `step_id` | UUID | not null (no FK constraint) |
| `name` | String(255) | not null |
| `description` | String(1000) | nullable |
| `position` | Integer | not null |
| `custom_metadata` | JSON | nullable |
| `created_at` / `updated_at` | DateTime | |

**Key observation**: Template tables use **no foreign key constraints** — all references are lightweight UUID pointers. Deletion is handled at the service layer, not via cascades.

---

### 1.2 Assignment Instances (4 tables)

#### `workflow_assignments`

| Column | Type | Constraints |
| -------- | ------ | ------------- |
| `id` | UUID PK | |
| `workflow_id` | UUID | not null (no FK) |
| `client_id` | UUID FK | → `clients.id` |
| `organization_id` | UUID | nullable |
| `status` | Enum(`draft`, `active`, `in_progress`, `completed`, `on_hold`, `cancelled`) | default `draft` |
| `assigned_by` | UUID | nullable |
| `notes` | String(1000) | nullable |
| `due_date` | DateTime | nullable |
| `start_date` | DateTime | nullable |
| `priority` | Enum(`low`, `medium`, `high`, `urgent`) | default `medium` |
| `custom_metadata` | JSON | nullable |
| `created_at` / `updated_at` | DateTime | |

> **BUG**: No `name` column exists, but notification_service references `assignment.name`. See §14.

#### `assignment_workflow_stages`

| Column | Type | Constraints |
| -------- | ------ | ------------- |
| `id` | UUID PK | |
| `assignment_id` | UUID | not null (no FK) |
| `template_stage_id` | UUID | nullable — link back to original template stage |
| `name` | String(255) | not null |
| `description` | String(1000) | nullable |
| `order` | Integer | not null |
| `status` | Enum(`not_started`, `in_progress`, `completed`) | default `not_started` |
| `start_date` | DateTime | nullable |
| `completed_date` | DateTime | nullable |
| `assigned_to` | UUID | nullable |
| `custom_metadata` | JSON | nullable |
| `created_at` / `updated_at` | DateTime | |

#### `assignment_workflow_steps`

| Column | Type | Constraints |
| -------- | ------ | ------------- |
| `id` | UUID PK | |
| `stage_id` | UUID | not null (no FK) |
| `template_step_id` | UUID | nullable |
| `name` | String(255) | not null |
| `description` | String(1000) | nullable |
| `order` | Integer | not null |
| `status` | Enum (reuses `StageStatus`: `not_started`, `in_progress`, `completed`) | default `not_started` |
| `assigned_to` | UUID | nullable |
| `due_date` | DateTime | nullable |
| `completed_date` | DateTime | nullable |
| `custom_metadata` | JSON | nullable |
| `created_at` / `updated_at` | DateTime | |

#### `assignment_workflow_tasks`

| Column | Type | Constraints |
| -------- | ------ | ------------- |
| `id` | UUID PK | |
| `step_id` | UUID | not null (no FK) |
| `template_task_id` | UUID | nullable |
| `name` | String(255) | not null |
| `description` | String(1000) | nullable |
| `order` | Integer | not null |
| `status` | Enum(`not_started`, `in_progress`, `completed`, `blocked`) | default `not_started` |
| `assigned_to` | UUID | nullable |
| `due_date` | DateTime | nullable |
| `completed_date` | DateTime | nullable |
| `estimated_hours` | Numeric(10,2) | nullable |
| `actual_hours` | Numeric(10,2) | nullable |
| `custom_metadata` | JSON | nullable |
| `created_at` / `updated_at` | DateTime | |

**Key enrichment over templates**: Assignment instances gain `status`, `assigned_to`, `due_date`, `completed_date`, `estimated_hours`, `actual_hours` — fields needed for tracking work.

---

### 1.3 Agent Models (4 tables)

#### `agents`

| Column | Type | Constraints |
| -------- | ------ | ------------- |
| `id` | UUID PK | |
| `organization_id` | UUID | nullable |
| `name` | String(255) | not null |
| `description` | String(1000) | nullable |
| `agent_type` | Enum(`document_intelligence`, `search`, `extraction`, `validation`, `custom`) | not null |
| `backend_provider` | String(100) | default `"azure"` |
| `backend_config` | JSON | nullable — stores API keys, endpoints |
| `capabilities` | JSON | nullable |
| `input_schema` | JSON | nullable |
| `output_schema` | JSON | nullable |
| `status` | Enum(`active`, `inactive`, `deprecated`) | default `active` |
| `is_system` | Boolean | default `False` |
| `created_by` | UUID | nullable |
| `created_at` / `updated_at` | DateTime | |

#### `workflow_task_agents` (template-level)

| Column | Type |
| -------- | ------ |
| `id` | UUID PK |
| `task_id` | UUID — points to `workflow_tasks.id` |
| `agent_id` | UUID — points to `agents.id` |
| `position` | Integer |
| `is_required` | Boolean (default `False`) |
| `task_config` | JSON |
| `instructions` | String(2000) |
| `created_at` / `updated_at` | DateTime |

#### `assignment_task_agents` (instance-level)

| Column | Type |
| -------- | ------ |
| `id` | UUID PK |
| `task_id` | UUID — points to `assignment_workflow_tasks.id` |
| `agent_id` | UUID |
| `template_agent_id` | UUID — points back to `workflow_task_agents.id` |
| `order` | Integer |
| `status` | Enum(`pending`, `ready`, `running`, `completed`, `failed`, `skipped`) |
| `is_required` | Boolean |
| `task_config` | JSON |
| `instructions` | String(2000) |
| `assigned_by` | UUID |
| `last_execution_id` | UUID |
| `last_run_at` | DateTime |
| `created_at` / `updated_at` | DateTime |

#### `agent_executions`

| Column | Type |
| -------- | ------ |
| `id` | UUID PK |
| `assignment_task_agent_id` | UUID |
| `agent_id` | UUID |
| `task_id` | UUID |
| `triggered_by` | UUID |
| `status` | Enum(`queued`, `running`, `completed`, `failed`, `cancelled`, `timed_out`) |
| `input_data` | JSON |
| `output_data` | JSON |
| `error_message` | String(2000) |
| `error_details` | JSON |
| `started_at` / `completed_at` | DateTime |
| `duration_seconds` | Numeric(10,2) |
| `backend_provider` | String(100) |
| `created_at` / `updated_at` | DateTime |

---

### 1.4 Supporting Models

#### `users`

| Column | Type | Notes |
| -------- | ------ | ------- |
| `id` | UUID PK | |
| `first_name` / `last_name` | String(100) | |
| `email` | String(255), unique | |
| `hashed_password` | String(255), nullable | null for AD/Keycloak users |
| `role` | Enum `UserRole` (`ADMIN`, `MANAGER`, `ENDUSER`, `CLIENT`) | default `ENDUSER` |
| `is_active` | Boolean | default `True` |
| `auth_provider` | Enum (`LOCAL`, `AD`, `KEYCLOAK`) | default `LOCAL` |
| `ad_username` | String(255), unique, nullable | |
| `keycloak_sub` | String(255), unique, nullable | |
| `created_at` / `updated_at` | DateTime | |

#### `clients`

| Column | Type |
| -------- | ------ |
| `id` | UUID PK |
| `organization_id` | UUID |
| `name` | String(255), not null |
| `industry` | String(255) |
| `status` | Enum(`active`, `inactive`, `prospect`, `archived`) |
| `email/phone/website` | String |
| `address/city/state/country/postal_code` | String |
| `tax_id` | String(100) |
| `notes` | String(2000) |
| `created_by` | UUID |

#### `contacts`

| Column | Type |
| -------- | ------ |
| `id` | UUID PK |
| `organization_id` | UUID |
| `first_name/last_name` | String(100) |
| `email/phone/mobile` | String |
| `designation/department` | String |
| `status` | Enum(`active`, `inactive`, `archived`) |
| `notes` | String(2000) |
| `created_by` | UUID |

#### `client_contacts` (M2M join)

- FK `client_id` → `clients.id` (CASCADE delete)
- FK `contact_id` → `contacts.id` (CASCADE delete)
- `role` (String 100), `is_primary` (Boolean)
- UniqueConstraint on `(client_id, contact_id)`

#### `projects`

| Column | Type |
| -------- | ------ |
| `id` | UUID PK |
| `organization_id` | UUID |
| `name` | String(255), not null |
| `description` | String(2000) |
| `client_id` | UUID FK → `clients.id` |
| `status` | Enum(`planning`, `active`, `review`, `completed`, `archived`) |
| `priority` | Enum(`low`, `medium`, `high`, `urgent`) |
| `owner_id` | UUID |
| `manager_ids` | ARRAY(UUID) — PostgreSQL native array |
| `resource_folder_id/output_folder_id` | UUID |
| `start_date/due_date` | DateTime |
| `visibility` | Enum(`private`, `team`, `organization`) |
| `custom_metadata` | JSON |

#### `project_collaborators`

- `project_id` + `user_id` (UniqueConstraint)
- `role` Enum: `owner`, `editor`, `viewer`, `commenter`
- `joined_at` DateTime

#### `project_tasks` (Kanban cards)

| Column | Type |
| -------- | ------ |
| `id` | UUID PK |
| `project_id` | UUID |
| `title` | String(500), not null |
| `description` | String(2000) |
| `status` | Enum(`todo`, `in_progress`, `review`, `completed`) |
| `priority` | Enum(`low`, `medium`, `high`, `urgent`) |
| `assignee_id` | UUID |
| `due_date` | DateTime |
| `position` | Integer — for drag-reorder within column |
| `estimated_hours/actual_hours` | Numeric(10,2) |
| `resource_folder_id/output_folder_id` | UUID |
| `custom_metadata` | JSON |

#### `notifications`

- `user_id` FK → `users.id` (CASCADE)
- `type` Enum: `task_completed`, `step_completed`, `stage_completed`, `assignment_completed`, `task_assigned`, `task_created`, `general`
- `title/message(Text)/link`
- `is_read` Boolean, `email_sent` Boolean

#### `notification_settings` (Admin Outlook config)

- `outlook_email/client_id/client_secret/tenant_id`
- `is_enabled` Boolean

#### `user_notification_preferences`

- `user_id` FK unique → `users.id`
- `email_enabled/in_app_enabled` Boolean
- `updated_by` FK

#### `reminders`

- `user_id` FK → `users.id` (CASCADE)
- `entity_type` Enum: `assignment`, `stage`, `step`, `task`
- `entity_id/entity_name`
- `reminder_type` Enum: `auto_due_date`, `manual`
- `offset_label` Enum: `3_days_before`, `1_day_before`, `on_due_date`, `1_day_overdue`
- `title/message(Text)/link`
- `remind_at` DateTime
- `status` Enum: `pending`, `sent`, `snoozed`, `dismissed`
- `sent_at/snoozed_until/dismissed_at` DateTime
- `snooze_count` Integer
- `created_by` FK

---

## 2. Service Methods & Business Logic

### 2.1 WorkflowService (429 lines)

| Method | Signature | Logic |
| -------- | ----------- | ------- |
| `create_workflow` | `(db, name, description, org_id, created_by)` | Creates with status `draft`, position auto-set |
| `get_workflow` | `(db, workflow_id)` | Single lookup by ID |
| `list_workflows` | `(db, org_id)` | Filter by `organization_id` or return all |
| `update_workflow` | `(db, workflow_id, data: dict)` | Partial update via `setattr` loop |
| `delete_workflow` | `(db, workflow_id)` | Deletes workflow + all child stages/steps/tasks in single transaction |
| `create_stage` | `(db, workflow_id, name, description)` | Auto-calculates `position` as `max(position) + 1` |
| `list_stages` | `(db, workflow_id)` | Ordered by `position` |
| `update_stage` | `(db, stage_id, data)` | Partial update |
| `delete_stage` | `(db, stage_id)` | Cascades: deletes all child steps → tasks |
| `reorder_stages` | `(db, workflow_id, stage_ids)` | Validates all IDs exist, sets `position` by list index |
| `create_step` | `(db, stage_id, name, description)` | Auto-position |
| `list_steps` | `(db, stage_id)` | Ordered by `position` |
| `update_step` | `(db, step_id, data)` | Partial update |
| `delete_step` | `(db, step_id)` | Cascades: deletes all child tasks |
| `create_task` | `(db, step_id, name, description)` | Auto-position |
| `list_tasks` | `(db, step_id)` | Ordered by `position` |
| `update_task` | `(db, task_id, data)` | Partial update |
| `delete_task` | `(db, task_id)` | Direct delete |
| `get_workflow_hierarchy` | `(db, workflow_id)` | Returns full nested structure: workflow → stages → steps → tasks → agents |

**Cascade deletion pattern**: Service layer manually queries and deletes children before parent. No DB-level cascades on template tables.

---

### 2.2 AssignmentService (757 lines) — Core Business Logic

| Method | Signature | Logic |
| -------- | ----------- | ------- |
| `activate_assignment` | `(db, assignment)` | **Deep clone**: copies all template stages → steps → tasks → agents into assignment instance tables. Sets assignment status to `active`. |
| `get_assignment_hierarchy` | `(db, assignment_id)` | Multi-join query returning full nested hierarchy with progress %, agents, and counts |
| `calculate_progress` | `(db, assignment_id)` | `(completed_tasks / total_tasks) * 100`, rounded to int |
| `get_assignments_paginated` | `(db, org_id, status, priority, client_id, page, limit)` | Paginated list with client name join, progress calculation per item |
| `update_task_status` | `(db, assignment_id, task_id, data)` | Updates task, sets `completed_date` on completion, triggers `_propagate_status_upward` + sends notifications |
| `_propagate_status_upward` | `(db, task)` | **Auto-progression chain**: task complete → check if all sibling tasks complete → mark step complete → check all sibling steps → mark stage complete → check all stages → mark assignment complete. Issues notifications at each level. |
| `update_step_status` | `(db, assignment_id, step_id, data)` | If step set to `completed`, auto-completes all child tasks. If set to `not_started`, resets all child tasks. Then propagates up to stage/assignment. |
| `update_stage_status` | `(db, assignment_id, stage_id, data)` | If stage set to `completed`, auto-completes all child steps/tasks. If set to `not_started`, resets all. Then propagates up to assignment. |

**Activation deep-clone flow**:

```text

Template:  Workflow → Stages → Steps → Tasks → WorkflowTaskAgents
                                          ↓ (clone)
Instance:  Assignment → AssignmentStages → AssignmentSteps → AssignmentTasks → AssignmentTaskAgents

```

Each cloned entity preserves `template_*_id` for traceability back to the original.

---

### 2.3 AgentService (406 lines, 4 service classes)

| Class | Key Methods |
| ------- | ------------- |
| **AgentService** | `create_agent`, `get_agent`, `list_agents`, `update_agent`, `delete_agent` |
| **WorkflowTaskAgentService** | `attach_agent_to_task` (template), `list_agents_for_task`, `update_task_agent`, `remove_agent_from_task` |
| **AssignmentTaskAgentService** | `clone_agents_from_template` (used during activation), `assign_agent_to_task`, `list_agents_for_task`, `update_task_agent`, `remove_agent_from_task` |
| **AgentExecutionService** | `create_execution`, `start_execution`, `complete_execution` (computes duration), `fail_execution`, `list_executions`, `get_execution` |

**Agent clone during activation**: `clone_agents_from_template(db, template_task_id, assignment_task_id)` queries all `WorkflowTaskAgent` records for the template task, creates corresponding `AssignmentTaskAgent` records with `template_agent_id` preserved, status set to `pending`.

---

### 2.4 ProjectService (287 lines)

| Method | Logic |
| -------- | ------- |
| `get_project_tasks_grouped` | Returns tasks grouped by status column: `{todo: [...], in_progress: [...], review: [...], completed: [...]}` |
| `move_task` | Updates `status` and `position`, re-indexes siblings for clean ordering |
| `get_project_stats` | Counts tasks by status, calculates completion % |
| `get_projects_paginated` | Paginated with stats (task counts per project) |
| `check_project_access` | Role hierarchy: `owner > editor > viewer > commenter`. Returns boolean. |
| `add_collaborator` | Upsert-safe via `merge()` |

---

### 2.5 ClientService (176 lines)

| Method | Logic |
| -------- | ------- |
| `create_client` | Standard create |
| `get_client` | By ID |
| `get_clients` | With `contact_count` subquery, search by name/email, filter by status |
| `update_client` | Partial update |
| `delete_client` | Hard delete |
| `link_contact` | Creates `ClientContact` M2M entry |
| `unlink_contact` | Removes M2M entry |
| `get_client_contacts` | Returns contacts with role/is_primary enrichment |
| `get_client_name` | Lightweight name-only lookup |

---

### 2.6 ContactService (151 lines)

| Method | Logic |
| -------- | ------- |
| `create_contact` | Standard create |
| `get_contact` | By ID |
| `get_contacts` | Search by first/last name or email, filter by status |
| `update_contact` | Partial update |
| `delete_contact` | Hard delete |
| `get_contact_with_clients` | Returns contact + associated clients via M2M join |

---

### 2.7 NotificationService (413 lines)

| Method | Logic |
| -------- | ------- |
| `create_notification` | Checks user `in_app_enabled` preference; only creates if true |
| `get_user_notifications` | Paginated, optional `unread_only` filter |
| `get_unread_count` | COUNT where `is_read = False` |
| `mark_as_read` / `mark_all_as_read` | Bulk update |
| `send_email_notification` | Uses **Microsoft Graph API** via OAuth2 client credentials flow to send via Outlook. Fetches token from Azure AD, posts to `/users/{email}/sendMail`. |
| `notify_task_completed` | Notifies `assignment.assigned_by` user |
| `notify_step_completed` | Notifies `assignment.assigned_by` |
| `notify_stage_completed` | Notifies `assignment.assigned_by` |
| `notify_assignment_completed` | Notifies `assignment.assigned_by` |
| `notify_task_assigned` | Notifies `task.assigned_to` |
| `notify_task_created` | Notifies `task.assigned_to` |
| `dispatch_pending_emails` | Batch processes unsent email notifications |
| `get_settings` / `upsert_settings` | Admin Outlook config CRUD |
| `get_user_preference` / `update_user_preference` | Per-user email/in-app toggles |
| `get_all_user_preferences` | Admin view |

---

### 2.8 ReminderService (362 lines)

| Method | Logic |
| -------- | ------- |
| `create_manual_reminder` | User-created reminder with `reminder_type = manual` |
| `generate_due_date_reminders` | **Idempotent**: creates 4 reminders per entity (`3_days_before`, `1_day_before`, `on_due_date`, `1_day_overdue`). Skips duplicates via `offset_label` check. |
| `remove_auto_reminders_for_entity` | Deletes auto-generated reminders when due dates change |
| `process_pending_reminders` | **Background scheduler**: queries `status=pending AND remind_at <= now()`, creates in-app notification for each, marks as `sent`. Returns count. |
| `snooze_reminder` | Sets `status = snoozed`, then `status = pending` with new `remind_at = snooze_until`. Increments `snooze_count`. |
| `dismiss_reminder` | Sets `status = dismissed`, records `dismissed_at` |
| `get_user_reminders` | Paginated, optional status filter |
| `get_reminder_counts` | Returns `{pending, overdue}` where overdue = `pending AND remind_at < now()` |
| `update_reminder` / `delete_reminder` | CRUD with ownership check |
| `get_reminder_by_id` | With ownership validation |

**Background scheduler**: In `main.py`, an `asyncio.create_task(_reminder_loop())` runs every 60 seconds, calling `ReminderService.process_pending_reminders`.

---

## 3. API Endpoints

### 3.1 Workflows (`/api/v1/workflows`)

| Method | Path | Auth | Description |
| -------- | ------ | ------ | ------------- |
| `POST` | `/` | Active user | Create workflow |
| `GET` | `/` | Active user | List workflows (optional `organization_id` query) |
| `GET` | `/{id}` | Active user | Get workflow hierarchy (full nested) |
| `PATCH` | `/{id}` | Active user | Update workflow |
| `DELETE` | `/{id}` | Active user | Delete workflow + all children |
| `POST` | `/{id}/stages` | Active user | Add stage |
| `GET` | `/{id}/stages` | Active user | List stages |
| `PATCH` | `/stages/{id}` | Active user | Update stage |
| `DELETE` | `/stages/{id}` | Active user | Delete stage + children |
| `PUT` | `/{id}/stages/reorder` | Active user | Reorder stages |
| `POST` | `/stages/{id}/steps` | Active user | Add step |
| `GET` | `/stages/{id}/steps` | Active user | List steps |
| `PATCH` | `/steps/{id}` | Active user | Update step |
| `DELETE` | `/steps/{id}` | Active user | Delete step + children |
| `POST` | `/steps/{id}/tasks` | Active user | Add task |
| `GET` | `/steps/{id}/tasks` | Active user | List tasks |
| `PATCH` | `/tasks/{id}` | Active user | Update task |
| `DELETE` | `/tasks/{id}` | Active user | Delete task |

### 3.2 Assignments (`/api/v1/assignments`)

| Method | Path | Auth | Description |
| -------- | ------ | ------ | ------------- |
| `GET` | `/` | Active user | Paginated list with progress %, client name, filters |
| `POST` | `/` | Active user | Create draft assignment |
| `GET` | `/{id}` | Active user | Full hierarchy (stages→steps→tasks→agents) |
| `PATCH` | `/{id}` | Active user | Update assignment. **If status changes to `active`**, triggers `activate_assignment` (deep clone). Also generates due-date reminders if `due_date` is set. |
| `PATCH` | `/{id}/tasks/{task_id}` | Active user | Update task status (triggers auto-progression) |
| `PATCH` | `/{id}/steps/{step_id}` | Active user | Update step status (cascades to tasks, propagates up) |
| `PATCH` | `/{id}/stages/{stage_id}` | Active user | Update stage status (cascades to steps/tasks, propagates up) |

### 3.3 Canvas (`/api/v1/canvas`)

| Method | Path | Description |
| -------- | ------ | ------------- |
| `GET` | `/workflows/{id}` | Template canvas: generates positioned nodes (stages left-to-right, 340px spacing) + edges. Each node includes nested `steps[]` with `tasks[]` and `agents[]`. |
| `GET` | `/assignments/{id}` | Assignment canvas: same layout but with status overlays, progress %, completed/task counts, agent status. |
| `GET` | `/workflows/{id}/stats` | Template stats: stage/step/task/agent counts. |
| `PATCH` | `/assignments/{id}/nodes` | Update node status from canvas UI. Accepts `{node_id, node_type, status}`. Routes to task/step/stage update service. |

### 3.4 Agents (`/api/v1/agents`)

| Method | Path | Description |
| -------- | ------ | ------------- |
| `POST` | `/` | Create agent |
| `GET` | `/` | List agents (filter by `organization_id`, `agent_type`, `status`) |
| `GET` | `/{id}` | Get agent |
| `PATCH` | `/{id}` | Update agent |
| `DELETE` | `/{id}` | Delete agent |
| `POST` | `/workflow-tasks/{task_id}/agents` | Attach agent to template task |
| `GET` | `/workflow-tasks/{task_id}/agents` | List agents on template task |
| `PATCH` | `/workflow-task-agents/{wta_id}` | Update template attachment |
| `DELETE` | `/workflow-task-agents/{wta_id}` | Remove from template task |
| `POST` | `/assignment-tasks/{task_id}/agents` | Assign agent to instance task |
| `GET` | `/assignment-tasks/{task_id}/agents` | List agents on instance task |
| `PATCH` | `/assignment-task-agents/{ata_id}` | Update instance attachment |
| `DELETE` | `/assignment-task-agents/{ata_id}` | Remove from instance task |
| `POST` | `/assignment-task-agents/{ata_id}/execute` | Trigger agent execution (creates execution record, marks `running`) |
| `GET` | `/assignment-task-agents/{ata_id}/executions` | Execution history |
| `GET` | `/executions/{execution_id}` | Single execution detail |

### 3.5 Projects (`/api/v1/projects`)

| Method | Path | Description |
| -------- | ------ | ------------- |
| `GET` | `/` | Paginated list with stats |
| `POST` | `/` | Create project + auto-add creator as `owner` collaborator |
| `GET` | `/{id}/kanban` | Kanban view: tasks grouped by status column |
| `POST` | `/{id}/tasks` | Create task |
| `PATCH` | `/tasks/{id}` | Update task |
| `PATCH` | `/tasks/{id}/move` | Move task between columns / reorder |
| `DELETE` | `/{id}/tasks/{id}` | Delete task |
| `POST` | `/{id}/collaborators` | Add collaborator |

### 3.6 Clients (`/api/v1/clients`)

| Method | Path | Description |
| -------- | ------ | ------------- |
| `GET` | `/` | List with contact counts, search, status filter |
| `POST` | `/` | Create client |
| `GET` | `/{id}` | Get client |
| `PATCH` | `/{id}` | Update client |
| `DELETE` | `/{id}` | Delete client |
| `POST` | `/{id}/contacts` | Link contact to client |
| `DELETE` | `/{id}/contacts/{contact_id}` | Unlink contact |
| `GET` | `/{id}/contacts` | List client's contacts |

### 3.7 Contacts (`/api/v1/contacts`)

| Method | Path | Description |
| -------- | ------ | ------------- |
| `GET` | `/` | List with search, status filter |
| `POST` | `/` | Create |
| `GET` | `/{id}` | Get |
| `PATCH` | `/{id}` | Update |
| `DELETE` | `/{id}` | Delete |

### 3.8 Documents (`/api/v1/documents`)

| Method | Path | Description |
| -------- | ------ | ------------- |
| `POST` | `/upload` | File upload to disk (`uploads/` dir). Returns filename, content_type, location. |

### 3.9 Notifications (`/api/v1/notifications`)

| Method | Path | Auth | Description |
| -------- | ------ | ------ | ------------- |
| `GET` | `/` | User | Get notifications (paginated, optional `unread_only`) |
| `GET` | `/count` | User | Unread + total count |
| `PATCH` | `/read` | User | Mark specific IDs as read |
| `PATCH` | `/read-all` | User | Mark all as read |
| `GET` | `/preferences` | User | Get my email/in-app prefs |
| `PATCH` | `/preferences` | User | Update my prefs |
| `GET` | `/settings` | Admin | Get Outlook config |
| `POST` | `/settings` | Admin | Create/update Outlook config |
| `PATCH` | `/settings` | Admin | Partial update Outlook config |
| `GET` | `/admin/user-preferences` | Admin | View all users' prefs |
| `PATCH` | `/admin/user-preferences` | Admin | Override a user's prefs |

### 3.10 Reminders (`/api/v1/reminders`)

| Method | Path | Auth | Description |
| -------- | ------ | ------ | ------------- |
| `GET` | `/` | User | List my reminders (optional status filter) |
| `GET` | `/counts` | User | Pending + overdue counts |
| `POST` | `/` | User | Create manual reminder |
| `GET` | `/{id}` | User | Get single |
| `PATCH` | `/{id}` | User | Update |
| `POST` | `/{id}/snooze` | User | Snooze to new time |
| `POST` | `/{id}/dismiss` | User | Dismiss permanently |
| `DELETE` | `/{id}` | User | Hard delete |

### 3.11 Users (`/api/v1/users`)

| Method | Path | Auth | Description |
| -------- | ------ | ------ | ------------- |
| `POST` | `/onboard` | Admin | Create single user |
| `POST` | `/onboard/bulk` | Admin | Bulk create via CSV upload |

### 3.12 Dashboard (`/api/v1/dashboard`)

| Method | Path | Auth | Description |
| -------- | ------ | ------ | ------------- |
| `GET` | `/stats` | Admin | Returns `{total_users, active_workflows: 5, documents_processed: 120, storage_used: "1.2 GB"}` — **NOTE: mostly hardcoded values** |

---

## 4. Schema Validation

### 4.1 Workflow Schemas

| Schema | Fields | Notes |
| -------- | -------- | ------- |
| `WorkflowCreate` | `name` (required), `description`, `organization_id` | |
| `WorkflowUpdate` | `name`, `description`, `status` | All optional |
| `WorkflowResponse` | `id, name, description, status, organization_id, custom_metadata, created_by, created_at, updated_at` | `from_attributes = True` |
| `StageCreate` | `name` (required), `description` | |
| `StageUpdate` | `name`, `description` | |
| `StageResponse` | `id, workflow_id, name, description, position, custom_metadata, created_at, updated_at` | |
| `StepCreate/Update/Response` | Similar pattern | |
| `TaskCreate/Update/Response` | Similar pattern | |
| `TaskWithAgents` | Extends task with `agents: list[WorkflowTaskAgentResponse]` | |
| `StepWithTasks` | Step + `tasks: list[TaskWithAgents]` | |
| `StageWithSteps` | Stage + `steps: list[StepWithTasks]` | |
| `WorkflowWithHierarchy` | Workflow + `stages: list[StageWithSteps]` | Full nested response |

### 4.2 Assignment Schemas

| Schema | Fields | Notes |
| -------- | -------- | ------- |
| `AssignmentCreate` | `workflow_id` (required), `client_id` (required), `priority`, `notes`, `due_date`, `start_date`, `organization_id` | |
| `AssignmentUpdate` | `status`, `priority`, `notes`, `due_date`, `start_date` | All optional |
| `AssignmentTaskUpdate` | `status`, `assigned_to`, `due_date`, `actual_hours` | |
| `AssignmentStepUpdate` | `status`, `assigned_to`, `due_date` | |
| `AssignmentStageUpdate` | `status`, `assigned_to` | |
| `AssignmentTaskResponse` | All task fields + `agents: list[AssignmentTaskAgentResponse]` | |
| `AssignmentStepResponse` | All step fields + `tasks: list[AssignmentTaskResponse]` | |
| `AssignmentStageResponse` | All stage fields + `steps: list[AssignmentStepResponse]` | |
| `AssignmentResponse` | Full + `stages`, `progress`, `client_name` | |
| `AssignmentListItem` | Summary: `id, workflow_id, client_id, client_name, status, priority, progress, due_date, created_at` | |
| `AssignmentListResponse` | `data: list[AssignmentListItem]`, `pagination: {total, page, limit, pages}` | |

### 4.3 Agent Schemas

| Schema | Fields |
| -------- | -------- |
| `AgentCreate` | `name, description, agent_type, backend_provider, backend_config, capabilities, input_schema, output_schema, organization_id` |
| `AgentUpdate` | All optional |
| `AgentResponse` | Full model fields |
| `WorkflowTaskAgentCreate` | `agent_id, position, is_required, task_config, instructions` |
| `WorkflowTaskAgentResponse` | Full fields + `agent_name, agent_type` |
| `AssignmentTaskAgentCreate` | `agent_id, order, is_required, task_config, instructions` |
| `AssignmentTaskAgentResponse` | Full fields + `agent_name, agent_type, status, last_run_at` |
| `AgentExecutionCreate` | `input_data, triggered_by` |
| `AgentExecutionResponse` | Full execution fields |

### 4.4 Project Schemas

| Schema | Key Fields |
| -------- | ------------ |
| `ProjectCreate` | `name, description, client_id, priority, owner_id, manager_ids, start_date, due_date, visibility, organization_id` |
| `ProjectTaskCreate` | `title, description, status, priority, assignee_id, due_date, position, estimated_hours` |
| `ProjectTaskMove` | `status, position` |
| `ProjectWithStatsResponse` | Project + `task_stats: {todo, in_progress, review, completed, total}, completion_percentage` |
| `ProjectKanbanResponse` | `project: ProjectResponse, columns: {todo, in_progress, review, completed}` |

### 4.5 Notification Schemas

| Schema | Fields |
| -------- | -------- |
| `NotificationResponse` | `id, user_id, type, title, message, link, is_read, email_sent, created_at` |
| `NotificationMarkRead` | `notification_ids: list[UUID]` |
| `NotificationCountResponse` | `unread_count, total_count` |
| `NotificationSettingCreate` | `outlook_email, outlook_client_id, outlook_client_secret, outlook_tenant_id, is_enabled` |
| `UserNotificationPreferenceUpdate` | `email_enabled, in_app_enabled` |
| `AdminUserPreferenceUpdate` | `user_id + email_enabled, in_app_enabled` |

### 4.6 Reminder Schemas

| Schema | Fields |
| -------- | -------- |
| `ReminderCreate` | `entity_type, entity_id, entity_name, title, message, remind_at, link` |
| `ReminderSnooze` | `snooze_until: datetime` |
| `ReminderUpdate` | `title, message, remind_at, link` (all optional) |
| `ReminderResponse` | Full model fields |
| `ReminderCountResponse` | `pending: int, overdue: int` |

---

## 5. Auto-Progression Logic

The system implements a **bottom-up cascading completion** pattern in `AssignmentService._propagate_status_upward`:

```text

Task marked "completed"
    │
    ├── Check: Are ALL sibling tasks in this step "completed"?
    │     YES → Mark Step "completed" + set completed_date
    │     │
    │     ├── Check: Are ALL sibling steps in this stage "completed"?
    │     │     YES → Mark Stage "completed" + set completed_date
    │     │     │
    │     │     ├── Check: Are ALL stages in this assignment "completed"?
    │     │     │     YES → Mark Assignment "completed"
    │     │     │           → Send assignment_completed notification
    │     │     │     NO  → (do nothing)
    │     │     │
    │     │     └── Send stage_completed notification
    │     │
    │     │     NO → (do nothing)
    │     │
    │     └── Send step_completed notification
    │
    │     NO → (do nothing)
    │
    └── Send task_completed notification

```

**Top-down cascade** (step/stage updates):

- Setting a **step to `completed`** → auto-completes all child tasks that are not yet completed
- Setting a **stage to `completed`** → auto-completes all child steps → all child tasks
- Setting to `not_started` → resets all children to `not_started`
- Each downstream update also sets `completed_date` or clears it

**Notification trigger points**:

- `task_completed` → notifies `assignment.assigned_by`
- `step_completed` → notifies `assignment.assigned_by`
- `stage_completed` → notifies `assignment.assigned_by`
- `assignment_completed` → notifies `assignment.assigned_by`

---

## 6. Canvas Visualization

### 6.1 Backend Canvas API

The canvas endpoint (`/api/v1/canvas`) transforms the hierarchical data into a graph structure:

**Node positioning algorithm**:

- Stages are laid out **left-to-right** with `x = index * 340`, `y = 50`
- Each stage node is 280px wide × variable height
- Steps and tasks are **nested inside** the stage node data (not separate nodes)

**Edge generation**:

- Sequential stage-to-stage edges: `stage[0] → stage[1] → stage[2] → ...`
- Each edge has `animated = True` if the source stage is `in_progress` or `completed`

**Assignment canvas enrichment**:

- Adds `status`, `progress` (formatted as "X%"), `completedCount`, `taskCount` per stage
- Includes agent data on tasks with `agent_name`, `agent_type`, `status`

### 6.2 Frontend Canvas Implementation

The canvas is a **custom SVG-based renderer** (no React Flow):

**Features**:

- **Zoom**: Mouse wheel, min 0.3×, max 2.0×
- **Pan**: Click-and-drag on canvas background
- **Fit-to-screen**: Auto-calculates bounding box and centers with padding
- **Node expansion**: Click `+`/`-` to expand stages → show steps → show tasks
- **Stage height calculation**: Dynamic based on expanded children count
- **Edges**: Cubic Bezier curves with animated dashed lines for active edges
- **Status colors**: `not_started` = gray, `in_progress` = amber, `completed` = emerald, `blocked` = red
- **Agent visualization**: Color-coded dots on tasks (purple = doc intelligence, cyan = search, amber = extraction, teal = validation)
- **Details panel**: Right sidebar showing name, status, progress, agents, with **status update buttons** (assignment mode only)
- **Legend**: Bottom bar showing status colors + interaction hints

**Status update from canvas**: PATCH request to `/api/v1/canvas/assignments/{id}/nodes` with `{node_id, node_type, status}` — routes to the appropriate service method on the backend.

---

## 7. AI Agent Integration

### 7.1 Architecture

```text

Agent (definition) ──attach──→ WorkflowTaskAgent (template binding)
                                       │
                               ╭───────┴──── (clone on activation) ──────╮
                               │                                         │
                    AssignmentTaskAgent (instance binding)                │
                               │                                         │
                    AgentExecution (run history)                          │

```

### 7.2 Agent Types & Their Purpose

| Type | Intended Use |
| ------ | ------------- |
| `document_intelligence` | Azure Document Intelligence / OCR |
| `search` | AI-powered search across documents |
| `extraction` | Data extraction from unstructured content |
| `validation` | Automated validation / compliance checking |
| `custom` | User-defined agent logic |

### 7.3 Execution Flow

1. User clicks "Run" on an agent in the assignment detail page
2. Frontend POSTs to `/agents/assignment-task-agents/{ata_id}/execute`
3. Backend creates `AgentExecution` record with status `queued`
4. Immediately transitions to `running` status
5. **Actual AI execution is NOT implemented** — the endpoint creates and starts the record but no backend processing occurs
6. User must manually call complete/fail endpoints to update status

### 7.4 Agent Configuration

- `backend_config` (JSON): Stores provider-specific config (API keys, endpoints)
- `task_config` (JSON): Per-task configuration overriding agent defaults
- `instructions` (String 2000): Natural language instructions for this agent on this specific task
- `is_required` (Boolean): If true, implies task cannot complete without agent running (not enforced in code)

> **GAP**: `is_required` is stored but never enforced — tasks can be marked completed without running required agents.

---

## 8. Assignment Lifecycle

```text

              ┌─────────┐
              │  CREATE  │ (status = draft)
              └────┬─────┘
                   │
              ┌────▼─────┐
              │   DRAFT   │ ← Can set client, priority, dates, notes
              └────┬─────┘
                   │ PATCH status → "active"
              ┌────▼─────┐
              │ ACTIVATE  │ ← Deep-clones template hierarchy + agents
              └────┬─────┘    Creates assignment stages/steps/tasks/agents
                   │          Generates due-date reminders if due_date set
              ┌────▼──────┐
              │   ACTIVE   │
              └────┬──────┘
                   │ First task status update
              ┌────▼──────────┐
              │  IN_PROGRESS   │
              └────┬──────────┘
                   │ All tasks completed (auto-progression)
              ┌────▼──────────┐
              │   COMPLETED    │ ← Notification sent
              └───────────────┘

  Side states: ON_HOLD, CANCELLED (set manually via PATCH)

```

**Key behaviors**:

- Draft assignments have **no** cloned hierarchy — the template is referenced but not copied
- Activation is a **one-time** operation; re-activating has no guard (potential double-clone issue)
- Progress is calculated as `completed_tasks / total_tasks * 100`
- Paginated list returns each assignment with real-time progress %

---

## 9. Project / Kanban Features

### 9.1 Data Model

Projects are **independent of workflows/assignments**. They have their own task system (`project_tasks`) designed for Kanban-style tracking.

### 9.2 Kanban Columns

| Column | Status Value |
| -------- | ------------- |
| To Do | `todo` |
| In Progress | `in_progress` |
| Review | `review` |
| Completed | `completed` |

### 9.3 Features

- **Drag-and-drop reorder**: `PATCH /tasks/{id}/move` with `{status, position}` — re-indexes sibling cards
- **Collaborators**: Multiple users per project with role hierarchy (owner > editor > viewer > commenter)
- **Stats**: Auto-calculated task counts and completion % per project
- **Priority**: 4 levels matching assignment priority
- **Time tracking**: `estimated_hours` and `actual_hours` per task
- **Folder references**: `resource_folder_id` and `output_folder_id` for document organization (not implemented beyond storage)

### 9.4 Access Control

`check_project_access(db, project_id, user_id, required_role)` checks:

1. Is user the project `owner_id`? → full access
2. Is user in `manager_ids` array? → manager access
3. Is user a collaborator with sufficient role? → based on role hierarchy

---

## 10. Client & Contact Management

### 10.1 Architecture

```text

Client ←──M2M──→ Contact
  │                  (via client_contacts join table)
  │
  ├── Has many Assignments (via client_id FK)
  └── Has many Projects (via client_id FK)

```

### 10.2 Client Features

- CRUD with search (name/email) and status filter
- Contact count displayed in list view (subquery)
- Link/unlink contacts with role and `is_primary` flag
- Cascade delete of `client_contacts` on client or contact deletion
- `get_client_name()` for lightweight lookups (used by assignment list)

### 10.3 Contact Features

- CRUD with search (first/last name, email) and status filter
- View contact with all associated clients
- Shared across multiple clients via M2M

---

## 11. Notification & Reminder Systems

### 11.1 Notifications

**Trigger Points** (all from `AssignmentService` auto-progression):

- Task completed → `notify_task_completed`
- Step completed → `notify_step_completed`
- Stage completed → `notify_stage_completed`
- Assignment completed → `notify_assignment_completed`
- Task assigned → `notify_task_assigned` (not currently triggered from any code path)
- Task created → `notify_task_created` (not currently triggered from any code path)

**Delivery channels**:

1. **In-app**: Stored in `notifications` table, surfaced via API
2. **Email**: Via Microsoft Graph API (Outlook) — requires admin configuration of OAuth2 credentials

**User preferences**: Per-user toggle for `email_enabled` and `in_app_enabled`. Notifications respect these preferences.

### 11.2 Reminders

**Types**:

- `auto_due_date`: Auto-generated when assignment gets a `due_date` during activation
- `manual`: User-created for any entity

**Auto-generated offsets** (4 per entity):

- 3 days before due date
- 1 day before due date
- On due date
- 1 day after due date (overdue)

**Background processing**: Every 60 seconds, `process_pending_reminders` checks for pending reminders where `remind_at <= now()`, creates an in-app notification for each, and marks them as `sent`.

**Snooze/dismiss lifecycle**:

- Snooze: `snoozed → pending` (with new `remind_at`), `snooze_count++`
- Dismiss: `status = dismissed`, terminal state

---

## 12. Authentication & Authorization

### 12.1 Auth Providers

| Provider | Flow |
| ---------- | ------ |
| `LOCAL` | Email + password, `bcrypt` hash, JWT token |
| `AD` | Active Directory username + password via `requests.post` to AD endpoint, JWT issued on success |
| `KEYCLOAK` | Keycloak SubjectID stored, token validation delegated |

### 12.2 JWT Tokens

- Algorithm: Configurable via `settings.ALGORITHM` (default HS256)
- Payload: `{"sub": user_id, "exp": expiry}`
- Extracted via `OAuth2PasswordBearer(tokenUrl="...")`

### 12.3 Role-Based Access

| Role | Permissions |
| ------ | ------------- |
| `ADMIN` | All endpoints, user management, notification settings |
| `MANAGER` | Standard endpoints, project management |
| `ENDUSER` | Standard endpoints |
| `CLIENT` | TBD — role exists but no client-specific restrictions implemented |

**Dependency helpers**:

- `get_current_active_user` — any authenticated active user
- `get_current_active_admin` — admin only
- `require_roles(*roles)` — factory for custom role checks

### 12.4 Observations

- Most workflow/assignment endpoints only require `get_current_active_user` — **no organization-level isolation** is enforced (any user can access any workflow/assignment)
- No multi-tenancy enforcement in queries despite `organization_id` being present on models

---

## 13. Frontend UI Capabilities

### 13.1 Application Shell

- **Sidebar** (`Sidebar.tsx`, 242 lines): 12 navigation items — Dashboard, Assignments, Projects, Clients, Contacts, Users, Documents, Roles, Workflow, Agents, Notifications, Reminders
- **Auth context** (`AuthContext.tsx`): React context wrapping `useAuth` hook for login/logout/user state
- **API client** (`lib/index.ts`): `apiCall<T>()` wrapper with JWT bearer injection, base URL resolution

### 13.2 Workflow Builder (`workflow/page.tsx`, 1043 lines)

**List view**:

- Search workflows by name
- Filter by status: all / draft / active / archived
- Stats cards: Total, Draft, Active, Archived counts
- Toggle workflow status (draft ↔ active)
- Delete workflow with confirmation
- Create workflow modal

**Detail/hierarchy view**:

- Full stage → step → task tree displayed as columns
- Drag-and-drop stage reorder
- Inline add/delete for stages, steps, tasks
- Agent badges on tasks showing type and required flag
- Agent attach/detach via modal with agent picker, instructions field, required checkbox
- Edit workflow name/description
- Toggle workflow status

### 13.3 Assignment List (`AssignmentList.tsx`, 507 lines)

- Paginated table: Status, Client, Priority, Progress bar, Due Date, Actions
- Filter by status (6 options) and priority (4 options)
- Create assignment modal with workflow picker, client picker, priority selector, date pickers, notes
- Progress bar with color coding (green at 100%, blue at 50%+, gray below)
- Actions: View (detail page), Canvas (canvas visualization)

### 13.4 Assignment Detail (`assignments/[id]/page.tsx`, 488 lines)

- Summary cards: Client, Progress, Due Date, Stages count
- Accordion-style stage expansion (first stage expanded by default)
- Stages → steps → tasks hierarchy view
- Task checkbox toggle (completed ↔ not_started)
- Agent badges on tasks with:
  - Type-specific emoji icons (📄 🔍 ⛏️ ✅ 🤖)
  - Status pills (pending/ready/running/completed/failed/skipped)
  - Run button (▶️) to trigger execution
  - Click badge → execution history modal
- Execution history modal: status, duration, timestamps, error messages, output JSON (expandable)

### 13.5 Canvas (`canvas/[type]/[id]/page.tsx`, 795 lines)

- Full SVG canvas with zoom/pan
- Works for both workflow templates and assignment instances
- Stage nodes with steps/tasks drill-down
- Status-colored nodes and edges
- Agent dots on tasks
- Details sidebar with status update buttons (assignment mode)
- Legend bar with interaction hints

### 13.6 Documents (`documents/page.tsx`, 196 lines)

**Entirely static/mock** — hardcoded array of 8 sample documents. Upload dropzone UI exists but is not connected to the backend upload endpoint. No API calls are made.

### 13.7 API Config (`lib/api-config.ts`, 82 lines)

Comprehensive endpoint mapping covering all 14 API domains (auth, users, documents, workflows, projects, assignments, clients, contacts, agents, dashboard, notifications, reminders). Uses `NEXT_PUBLIC_API_URL` env var with localhost:8000 fallback.

---

## 14. Identified Bugs, Gaps & Risks

### 14.1 Critical Bugs

| # | Location | Issue | Impact |
| --- | ---------- | ------- | -------- |
| 1 | `notification_service.py` lines ~200-260 | References `assignment.name` but `WorkflowAssignment` model has **no `name` column** | **Runtime AttributeError** on any completed task/step/stage/assignment. The notification system would crash entirely. |
| 2 | `notification_service.py` ~line 275 | References `assignment.assigned_to` but model has no such column (only `assigned_by`) | **Runtime AttributeError** when assignment completes |
| 3 | `assignment_service.py` + `assignments.py` | No guard against **double activation** — if PATCH sets status to `active` twice, the deep clone runs again, duplicating all stages/steps/tasks/agents | **Data corruption** — duplicate hierarchy records |

### 14.2 Functional Gaps

| # | Area | Gap |
| --- | ------ | ----- |
| 4 | Agent execution | `is_required` flag on agents is stored but **never enforced** — tasks can be marked completed without running required agents |
| 5 | Agent execution | No actual AI backend integration — `execute` endpoint creates a record but **no processing runs**. Status must be manually updated. |
| 6 | Multi-tenancy | `organization_id` exists on models but **no row-level filtering** is applied in queries. Any authenticated user can access any organization's data. |
| 7 | Dashboard stats | `/dashboard/stats` returns **hardcoded values** for `active_workflows`, `documents_processed`, `storage_used` |
| 8 | Documents page | Frontend documents page is **entirely static mock data** with no API integration |
| 9 | Task `assigned_to` | `notify_task_assigned` and `notify_task_created` are defined but **never called** from any code path |
| 10 | Auto-reminders | `generate_due_date_reminders` is called for the assignment entity but **not for individual stages/steps/tasks** that may have their own `due_date` |
| 11 | Workflow delete | No soft-delete — deletions are permanent with no archive/undo capability |

### 14.3 Schema/Type Mismatches

| # | Location | Issue |
| --- | ---------- | ------- |
| 12 | Assignment task status | Backend model uses lowercase enum (`not_started`, `completed`) but frontend checks for both `'completed'` and `'COMPLETED'` — suggests inconsistent casing at some point |
| 13 | Canvas node status | Canvas API normalizes status to lowercase but original assignment models store lowercase; the frontend's `getStatusStyle` function handles both cases defensively |
| 14 | `AssignmentListItem` schema | Includes `workflow_id` and `client_id` but **no workflow name** — the list view cannot show which template an assignment is based on |

### 14.4 Security Concerns

| # | Area | Issue |
| --- | ------ | ------- |
| 15 | Authorization | Most endpoints only check `is_active` — no ownership or organization-level scoping. Any active user can read/modify any workflow, assignment, client, etc. |
| 16 | File upload | `/documents/upload` saves files to disk with original filename — no sanitization, no virus scanning, no size limit at the API level |
| 17 | Reminder/Notification | Ownership checks are present in reminder endpoints but **absent in notification mark-as-read** — bulk ID parameter could mark other users' notifications |
| 18 | User onboarding | CSV bulk onboard silently skips invalid rows with no error reporting |

### 14.5 Performance Considerations

| # | Area | Issue |
| --- | ------ | ------- |
| 19 | Assignment hierarchy | `get_assignment_hierarchy` builds the full nested response via multiple sequential queries — no eager loading or joins used. For large workflows, this could be slow. |
| 20 | Progress calculation | `calculate_progress` is called per-item in paginated list — N+1 query pattern |
| 21 | Template cascade delete | `delete_workflow` runs separate DELETE queries for each level (stages, steps, tasks) instead of using a single cascaded operation |
| 22 | Background scheduler | Reminder loop runs every 60s in the main process with synchronous DB calls — could block the event loop under load |

---

## 15. Summary Statistics

| Metric | Count |
| -------- | ------- |
| **Database tables** | 18 |
| **SQLAlchemy models** | 18 |
| **Pydantic schemas** | ~50 |
| **Service classes** | 10 (across 10 files) |
| **Service methods** | ~80 |
| **API endpoints** | ~75 |
| **API router modules** | 14 |
| **Frontend pages/components** | 8 major (+ Sidebar, AuthContext) |
| **Enum types** | 15 |
| **Alembic migrations** | 9 |
| **Lines of backend code** | ~5,000+ |
| **Lines of frontend code** | ~3,500+ |

### Enum Value Reference

| Enum | Values |
| ------ | -------- |
| `WorkflowStatus` | `draft`, `active`, `archived` |
| `AssignmentStatus` | `draft`, `active`, `in_progress`, `completed`, `on_hold`, `cancelled` |
| `StageStatus` (assignment) | `not_started`, `in_progress`, `completed` |
| `TaskStatus` (assignment) | `not_started`, `in_progress`, `completed`, `blocked` |
| `Priority` | `low`, `medium`, `high`, `urgent` |
| `AgentType` | `document_intelligence`, `search`, `extraction`, `validation`, `custom` |
| `AgentStatus` | `active`, `inactive`, `deprecated` |
| `AssignmentTaskAgentStatus` | `pending`, `ready`, `running`, `completed`, `failed`, `skipped` |
| `ExecutionStatus` | `queued`, `running`, `completed`, `failed`, `cancelled`, `timed_out` |
| `UserRole` | `ADMIN`, `MANAGER`, `ENDUSER`, `CLIENT` |
| `AuthProvider` | `LOCAL`, `AD`, `KEYCLOAK` |
| `ClientStatus` | `active`, `inactive`, `prospect`, `archived` |
| `ContactStatus` | `active`, `inactive`, `archived` |
| `ProjectStatus` | `planning`, `active`, `review`, `completed`, `archived` |
| `ProjectTaskStatus` | `todo`, `in_progress`, `review`, `completed` |
| `ProjectVisibility` | `private`, `team`, `organization` |
| `CollaboratorRole` | `owner`, `editor`, `viewer`, `commenter` |
| `NotificationType` | `task_completed`, `step_completed`, `stage_completed`, `assignment_completed`, `task_assigned`, `task_created`, `general` |
| `ReminderEntityType` | `assignment`, `stage`, `step`, `task` |
| `ReminderType` | `auto_due_date`, `manual` |
| `ReminderOffsetLabel` | `3_days_before`, `1_day_before`, `on_due_date`, `1_day_overdue` |
| `ReminderStatus` | `pending`, `sent`, `snoozed`, `dismissed` |

---

*Report generated by exhaustive source-code review of every file in the RAi Platform codebase.*
