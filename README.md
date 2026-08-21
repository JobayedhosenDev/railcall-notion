# RailCall Notion Integration Module & Governed Workflow

> **RailCall Marketplace Contest 2026Q3 Entry**
> - **Track A Submission:** Best Module (`workspace/notion`)
> - **Track B Submission:** Best Governed Workflow (`workflows/lead_kb_triage_workflow.json` & `workflows/run_workflow.py`)
> - **Contest Tag:** `contest:2026Q3`

---

## Overview

**Notion for RailCall** brings local-first, governed AI automation to Notion workspaces. Every database query, page update, block append, and task creation goes through RailCall's **Airlock Protocol** (`preview -> approve -> execute -> signed receipt`).

Whether you are building autonomous AI incident response agents, customer support knowledge base syncers, or automated engineering sprint managers, **workspace/notion** provides full governance with Ed25519 tamper-evident audit trails.

---

## Features & Coverage (10 Complete Actions)

The module exposes **10 complete, production-ready commands** split strictly by side-effect safety:

### Read Operations (`side_effects: "none"`)
| Command | Description |
| :--- | :--- |
| `search` | Workspace-wide text search across pages and databases with filters and sorting. |
| `get_page` | Retrieve metadata, properties, and URL for a specific page UUID. |
| `query_database` | Query database items with structured filter conditions, sorting, and pagination. |
| `get_block_children` | Retrieve child content blocks (paragraphs, headings, callouts, lists) of a page/block. |
| `get_database` | Retrieve database schema definitions, property types, and option values. |

### Write / Update Operations (`side_effects: "external"` - AIRLOCK GATED)
| Command | Description |
| :--- | :--- |
| `create_page` | Create new pages inside databases or child pages with icon, cover, and body blocks. |
| `update_page` | Update page titles, select/multi-select properties, checkboxes, or archive status. |
| `append_blocks` | Append structured content (headings, callouts, code blocks, to-dos) to pages. |
| `update_block` | Edit content or toggle checked state of specific blocks. |
| `archive_page` | Archive (soft-delete) or restore pages and database items. |

---

## Quickstart (Under 5 Minutes)

### 1. Prerequisites & Installation

Ensure you have RailCall CLI installed:
```bash
curl -fsSL https://railcall.ai/install.sh | bash
```

Clone or copy this module directory to your workstation:
```bash
cd railcall-notion
```

### 2. Set Up Notion API Credentials

Obtain an Internal Integration Token from [Notion Integrations](https://www.notion.so/my-integrations):
```bash
export NOTION_API_KEY="secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### 3. Install Module Locally

```bash
railcall module install --from-path .
```

---

## Command Usage Examples

### 1. Workspace Search (`search`)
```bash
railcall run workspace/notion.search \
  --query="Authentication Playbook" \
  --filter_value="page" \
  --page_size=5
```
*Response & Receipt:* Returns matching pages and mints a read receipt (`side_effects: "none"`).

### 2. Query Database (`query_database`)
```bash
railcall run workspace/notion.query_database \
  --database_id="c0a80112-8888-4900-a000-123456789abc" \
  --filter='{"property": "Status", "select": {"equals": "In Progress"}}'
```

### 3. Create Sprint Task (`create_page`) - AIRLOCK PROTECTED
```bash
railcall run workspace/notion.create_page \
  --parent_type="database_id" \
  --parent_id="c0a80112-8888-4900-a000-123456789abc" \
  --title="INC-8902: Resolve OAuth Expiration Skew" \
  --icon_emoji="🚨" \
  --properties='{"Priority": "P0 Critical", "Status": "In Progress"}'
```
*Airlock Behavior:*
1. **Preview:** RailCall prints the exact database target, title, and property diff.
2. **Approval:** Operator reviews and approves execution.
3. **Execution:** Notion REST API invoked.
4. **Receipt:** Ed25519-signed receipt saved to `~/.railcall/receipts/`.

### 4. Append AI Resolution Protocol (`append_blocks`)
```bash
railcall run workspace/notion.append_blocks \
  --block_id="page-uuid-123" \
  --blocks='[{"type": "heading_2", "text": "Root Cause Analysis"}, {"type": "callout", "text": "Token refresh window was insufficient.", "icon": "💡"}]'
```

---

## Track B: Governed Workflow Demo

Run the included end-to-end incident triage and knowledge sync workflow:

```bash
python workflows/run_workflow.py
```

### Workflow Execution Flow:
```
[Event Ingest] -> [Step 1: Query KB DB (Read)] -> [Step 2: Airlock Preview -> Operator Approve -> Create Task] -> [Step 3: Airlock Preview -> Operator Approve -> Append Logs] -> [3 Signed Receipts Minted]
```

---

## Trust Surface & Security Audit

- **Zero Secret Leakage:** Authentication headers rely exclusively on `NOTION_API_KEY`. Tokens are stripped from logs, exceptions, and receipts.
- **Rate Limit Resilience:** Built-in exponential backoff for HTTP 429 and 5xx response codes.
- **Air-Gapped Local Execution:** Written in 100% pure Python using standard library (`urllib`). Zero vulnerable external dependencies.
- **Side-Effects Isolation:** Read-only queries execute instantly; write actions force human operator verification through the RailCall Airlock.

---

## Running Unit Tests

Run the complete test suite:
```bash
python -m unittest discover -s tests -p "test_*.py"
```

Expected output:
```text
..........
----------------------------------------------------------------------
Ran 10 tests in 0.002s

OK
```

---

## Marketplace Publishing

To publish this module to the RailCall Marketplace:

```bash
railcall market login your@email.com
railcall market publisher init your-handle
railcall market publisher register
railcall market publish .
```

---

## License

Distributed under the MIT License. See `LICENSE` for details.
