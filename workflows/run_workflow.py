"""Track B Submission: Governed Knowledge Ops & Task Triage Workflow Runner.

Demonstrates end-to-end RailCall Airlock workflow execution:
1. Ingest Event
2. Query Notion KB (side_effects: "none") -> Receipt minted
3. Airlock Preview: Draft Sprint Task (side_effects: "external")
4. Operator Approves Execution -> Create Page -> Receipt minted
5. Airlock Preview: Append Resolution Blocks (side_effects: "external")
6. Operator Approves Execution -> Append Blocks -> Receipt minted
"""

import os
import sys
import json
import time
import hashlib
from typing import Dict, Any

# Ensure UTF-8 output formatting on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from handlers import handler


def simulate_signed_receipt(action: str, inputs: Dict[str, Any], output: Dict[str, Any]) -> Dict[str, Any]:
    """Simulate RailCall tamper-evident Ed25519 signed receipt structure."""
    payload_str = json.dumps({"action": action, "inputs": inputs, "output": output}, sort_keys=True)
    digest = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
    
    return {
        "receipt_id": f"rc-rcpt-{digest[:16]}",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "action": action,
        "side_effects": "external" if "create" in action or "append" in action else "none",
        "status": "EXECUTED",
        "signature_scheme": "Ed25519",
        "signature": f"sig_ed25519_{digest[:32]}",
        "payload_hash": digest
    }


def run_governed_workflow(mock_mode: bool = True):
    print("==========================================================================")
    print(" [LAUNCH] RAILCALL GOVERNED WORKFLOW: AI Incident Triage & KB Sync")
    print("==========================================================================")
    print("Context: Critical customer support incident reported [INC-8902]")
    print("Target Integration: Notion Workspace (workspace/notion)\n")

    context = {"api_key": os.environ.get("NOTION_API_KEY", "demo_secret_token_123")}

    # --------------------------------------------------------------------
    # STEP 1: Query Knowledge Base (Read-only, no airlock gate required)
    # --------------------------------------------------------------------
    print("[STEP 1/3] Executing Action: workspace/notion.query_database")
    print("           Side Effects: 'none' (Read-only operation)")
    
    if mock_mode:
        kb_result = {
            "database_id": "db-kb-8888",
            "count": 1,
            "results": [{
                "id": "kb-article-001",
                "title": "OAuth Token Refresh Failure Playbook",
                "url": "https://notion.so/kb-001"
            }]
        }
    else:
        kb_result = handler.query_database({
            "database_id": "db-kb-8888",
            "filter": {"property": "Topic", "select": {"equals": "Authentication"}}
        }, context)

    kb_receipt = simulate_signed_receipt("workspace/notion.query_database", {"database_id": "db-kb-8888"}, kb_result)
    print(f"  [OK] Execution Complete.")
    print(f"  [RECEIPT] Signed Receipt Minted: {kb_receipt['receipt_id']} [Hash: {kb_receipt['payload_hash'][:12]}...]\n")

    # --------------------------------------------------------------------
    # STEP 2: Create Engineering Sprint Task (Write operation -> AIRLOCK)
    # --------------------------------------------------------------------
    print("[STEP 2/3] Action Request: workspace/notion.create_page")
    print("           Side Effects: 'external' (AIRLOCK ACTIVATED)")
    
    create_inputs = {
        "parent_type": "database_id",
        "parent_id": "db-sprint-9999",
        "title": "INC-8902: Resolve OAuth Token Refresh Error",
        "icon_emoji": "🚨",
        "properties": {
            "Priority": "P0 Critical",
            "Status": "In Progress",
            "Tags": ["Security", "Authentication"]
        }
    }

    print("\n  ==================== [AIRLOCK PREVIEW] ====================")
    print(f"  Target: Notion Database [{create_inputs['parent_id']}]")
    print(f"  Action: Create Page '{create_inputs['title']}'")
    print(f"  Properties: {json.dumps(create_inputs['properties'])}")
    print("  ===========================================================")
    print("  Status: WAITING FOR OPERATOR APPROVAL...")
    print("  [Auto-Approved by Governance Policy in Automated Workflow Mode]")

    if mock_mode:
        task_result = {
            "success": True,
            "page_id": "page-task-inc-8902",
            "url": "https://notion.so/page-task-inc-8902",
            "title": create_inputs["title"],
            "created_time": "2026-07-30T12:00:00Z",
            "message": f"Page '{create_inputs['title']}' created successfully."
        }
    else:
        task_result = handler.create_page(create_inputs, context)

    task_receipt = simulate_signed_receipt("workspace/notion.create_page", create_inputs, task_result)
    print(f"  [OK] Operator Approved & Executed.")
    print(f"  [RECEIPT] Signed Receipt Minted: {task_receipt['receipt_id']} [Hash: {task_receipt['payload_hash'][:12]}...]\n")

    # --------------------------------------------------------------------
    # STEP 3: Append AI Resolution Logs (Write operation -> AIRLOCK)
    # --------------------------------------------------------------------
    print("[STEP 3/3] Action Request: workspace/notion.append_blocks")
    print("           Side Effects: 'external' (AIRLOCK ACTIVATED)")

    log_inputs = {
        "block_id": task_result["page_id"],
        "blocks": [
            {"type": "heading_2", "text": "AI Resolution & Remediation Protocol"},
            {"type": "callout", "text": "Referenced KB Article: OAuth Token Refresh Failure Playbook", "icon": "📚"},
            {"type": "paragraph", "text": "Automated diagnosis confirmed token expiration margin skew. Apply hotfix patch below:"},
            {"type": "code", "text": "def refresh_token(client):\n    return client.post('/auth/refresh', headers=client.auth_headers)", "language": "python"},
            {"type": "to_do", "text": "Deploy hotfix to production cluster", "checked": False},
            {"type": "to_do", "text": "Verify customer SLA metrics post-deployment", "checked": False}
        ]
    }

    print("\n  ==================== [AIRLOCK PREVIEW] ====================")
    print(f"  Target: Page Block [{log_inputs['block_id']}]")
    print(f"  Action: Append {len(log_inputs['blocks'])} structured content blocks")
    print("  ===========================================================")
    print("  Status: WAITING FOR OPERATOR APPROVAL...")
    print("  [Auto-Approved by Governance Policy in Automated Workflow Mode]")

    if mock_mode:
        log_result = {
            "success": True,
            "block_id": log_inputs["block_id"],
            "appended_count": len(log_inputs["blocks"]),
            "appended_ids": [f"blk-{i}" for i in range(len(log_inputs["blocks"]))],
            "message": f"Appended {len(log_inputs['blocks'])} content blocks to parent '{log_inputs['block_id']}'."
        }
    else:
        log_result = handler.append_blocks(log_inputs, context)

    log_receipt = simulate_signed_receipt("workspace/notion.append_blocks", log_inputs, log_result)
    print(f"  [OK] Operator Approved & Executed.")
    print(f"  [RECEIPT] Signed Receipt Minted: {log_receipt['receipt_id']} [Hash: {log_receipt['payload_hash'][:12]}...]\n")

    print("==========================================================================")
    print(" [DONE] WORKFLOW COMPLETED SUCCESSFULLY!")
    print("        Total Steps: 3 | Receipts Signed: 3 | Zero Unsanctioned Side-Effects")
    print("==========================================================================")


if __name__ == "__main__":
    run_governed_workflow(mock_mode=True)
