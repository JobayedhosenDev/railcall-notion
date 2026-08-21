"""Handlers for the workspace/notion RailCall module.

Every function defined here corresponds 1-to-1 with a command declared in module.json.
Returns clean dict payloads that get minted into Ed25519 tamper-evident RailCall receipts.
"""

import os
import sys
from typing import Any, Dict, List, Optional

# Ensure project directory is on sys.path for relative/absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from utils.notion_client import NotionClient, NotionAPIError
from utils.formatters import build_properties_dict, build_block_object, create_rich_text


def _get_client(context: Optional[Dict[str, Any]] = None) -> NotionClient:
    """Helper to initialize client using context API key if provided, else env var."""
    api_key = None
    if context and isinstance(context, dict):
        api_key = context.get("api_key") or context.get("NOTION_API_KEY")
    return NotionClient(api_key=api_key)


# =====================================================================
# READ COMMANDS (side_effects: "none")
# =====================================================================

def search(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Search workspace pages and databases by query string.
    
    inputs:
        query (str, optional): Search query term
        filter_value (str, optional): 'page' or 'database'
        sort_direction (str, optional): 'ascending' or 'descending'
        page_size (int, optional): Max results (1-100, default: 20)
    """
    client = _get_client(context)
    payload: Dict[str, Any] = {
        "page_size": min(inputs.get("page_size", 20), 100)
    }
    
    if inputs.get("query"):
        payload["query"] = inputs["query"]
        
    if inputs.get("filter_value"):
        payload["filter"] = {
            "value": inputs["filter_value"],
            "property": "object"
        }
        
    if inputs.get("sort_direction"):
        payload["sort"] = {
            "direction": inputs["sort_direction"],
            "timestamp": "last_edited_time"
        }

    res = client.request("POST", "search", payload=payload)
    
    results = []
    for item in res.get("results", []):
        obj_type = item.get("object")
        item_id = item.get("id")
        url = item.get("url")
        
        title_str = ""
        if obj_type == "page":
            props = item.get("properties", {})
            for p_val in props.values():
                if p_val.get("id") == "title" and p_val.get("title"):
                    title_str = "".join([t.get("plain_text", "") for t in p_val["title"]])
                    break
        elif obj_type == "database":
            title_objs = item.get("title", [])
            title_str = "".join([t.get("plain_text", "") for t in title_objs])

        results.append({
            "id": item_id,
            "object": obj_type,
            "title": title_str or "Untitled",
            "url": url,
            "last_edited_time": item.get("last_edited_time")
        })

    return {
        "count": len(results),
        "has_more": res.get("has_more", False),
        "next_cursor": res.get("next_cursor"),
        "results": results
    }


def get_page(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Retrieve metadata and properties for a given page ID."""
    client = _get_client(context)
    page_id = inputs["page_id"].strip()
    
    res = client.request("GET", f"pages/{page_id}")
    
    # Simple summary title extractor
    props = res.get("properties", {})
    title = ""
    for p_name, p_val in props.items():
        if p_val.get("type") == "title":
            title = "".join([t.get("plain_text", "") for t in p_val.get("title", [])])
            break

    return {
        "id": res.get("id"),
        "title": title or "Untitled",
        "url": res.get("url"),
        "created_time": res.get("created_time"),
        "last_edited_time": res.get("last_edited_time"),
        "archived": res.get("archived", False),
        "icon": res.get("icon"),
        "properties": props
    }


def query_database(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Query database with filters and sorts."""
    client = _get_client(context)
    database_id = inputs["database_id"].strip()
    
    payload: Dict[str, Any] = {
        "page_size": min(inputs.get("page_size", 50), 100)
    }
    if inputs.get("filter"):
        payload["filter"] = inputs["filter"]
    if inputs.get("sorts"):
        payload["sorts"] = inputs["sorts"]

    res = client.request("POST", f"databases/{database_id}/query", payload=payload)
    
    records = []
    for page in res.get("results", []):
        props = page.get("properties", {})
        title_str = ""
        for p_val in props.values():
            if p_val.get("type") == "title":
                title_str = "".join([t.get("plain_text", "") for t in p_val.get("title", [])])
                break

        records.append({
            "id": page.get("id"),
            "title": title_str or "Untitled",
            "url": page.get("url"),
            "created_time": page.get("created_time"),
            "last_edited_time": page.get("last_edited_time"),
            "archived": page.get("archived", False),
            "properties": props
        })

    return {
        "database_id": database_id,
        "count": len(records),
        "has_more": res.get("has_more", False),
        "next_cursor": res.get("next_cursor"),
        "results": records
    }


def get_block_children(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Retrieve child content blocks of a page or parent block."""
    client = _get_client(context)
    block_id = inputs["block_id"].strip()
    page_size = min(inputs.get("page_size", 50), 100)
    
    res = client.request("GET", f"blocks/{block_id}/children?page_size={page_size}")
    
    blocks = []
    for b in res.get("results", []):
        b_type = b.get("type")
        b_content = b.get(b_type, {})
        text_content = ""
        if isinstance(b_content, dict) and "rich_text" in b_content:
            text_content = "".join([t.get("plain_text", "") for t in b_content.get("rich_text", [])])

        blocks.append({
            "id": b.get("id"),
            "type": b_type,
            "text": text_content,
            "has_children": b.get("has_children", False),
            "raw": b
        })

    return {
        "block_id": block_id,
        "count": len(blocks),
        "has_more": res.get("has_more", False),
        "next_cursor": res.get("next_cursor"),
        "blocks": blocks
    }


def get_database(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Retrieve database metadata and schema definition."""
    client = _get_client(context)
    database_id = inputs["database_id"].strip()
    
    res = client.request("GET", f"databases/{database_id}")
    
    title_str = "".join([t.get("plain_text", "") for t in res.get("title", [])])
    
    # Flatten schema definitions
    schema = {}
    for p_name, p_def in res.get("properties", {}).items():
        schema[p_name] = {
            "id": p_def.get("id"),
            "type": p_def.get("type")
        }

    return {
        "id": res.get("id"),
        "title": title_str or "Untitled Database",
        "url": res.get("url"),
        "created_time": res.get("created_time"),
        "schema": schema,
        "raw": res
    }


# =====================================================================
# WRITE / SIDE-EFFECT COMMANDS (side_effects: "external")
# Trigger RailCall Airlock Preview -> Approval -> Execution -> Receipt
# =====================================================================

def create_page(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new page in a database or parent page."""
    client = _get_client(context)
    
    parent_type = inputs["parent_type"]
    parent_id = inputs["parent_id"].strip()
    title = inputs["title"].strip()
    
    parent_payload = {parent_type: parent_id}
    properties_payload = build_properties_dict(title=title, properties=inputs.get("properties"))
    
    payload: Dict[str, Any] = {
        "parent": parent_payload,
        "properties": properties_payload
    }
    
    if inputs.get("icon_emoji"):
        payload["icon"] = {"type": "emoji", "emoji": inputs["icon_emoji"]}
        
    if inputs.get("cover_url"):
        payload["cover"] = {"type": "external", "external": {"url": inputs["cover_url"]}}
        
    if inputs.get("content_blocks"):
        payload["children"] = [build_block_object(b) for b in inputs["content_blocks"]]

    res = client.request("POST", "pages", payload=payload)
    
    return {
        "success": True,
        "page_id": res.get("id"),
        "url": res.get("url"),
        "title": title,
        "created_time": res.get("created_time"),
        "message": f"Page '{title}' created successfully."
    }


def update_page(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Update title, properties, or archived state of an existing page."""
    client = _get_client(context)
    page_id = inputs["page_id"].strip()
    
    payload: Dict[str, Any] = {}
    
    if "title" in inputs or "properties" in inputs:
        payload["properties"] = build_properties_dict(
            title=inputs.get("title"),
            properties=inputs.get("properties")
        )
        
    if inputs.get("icon_emoji"):
        payload["icon"] = {"type": "emoji", "emoji": inputs["icon_emoji"]}
        
    if "archived" in inputs:
        payload["archived"] = inputs["archived"]

    res = client.request("PATCH", f"pages/{page_id}", payload=payload)
    
    return {
        "success": True,
        "page_id": res.get("id"),
        "url": res.get("url"),
        "last_edited_time": res.get("last_edited_time"),
        "archived": res.get("archived", False),
        "message": f"Page '{page_id}' updated successfully."
    }


def append_blocks(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Append content blocks to a parent block or page."""
    client = _get_client(context)
    block_id = inputs["block_id"].strip()
    raw_blocks = inputs["blocks"]
    
    formatted_children = [build_block_object(b) for b in raw_blocks]
    payload = {"children": formatted_children}

    res = client.request("PATCH", f"blocks/{block_id}/children", payload=payload)
    
    appended = res.get("results", [])
    return {
        "success": True,
        "block_id": block_id,
        "appended_count": len(appended),
        "appended_ids": [b.get("id") for b in appended],
        "message": f"Appended {len(appended)} content blocks to parent '{block_id}'."
    }


def update_block(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Update text or state of an existing content block."""
    client = _get_client(context)
    block_id = inputs["block_id"].strip()
    block_type = inputs.get("type", "paragraph")
    text = inputs.get("text", "")
    
    block_update: Dict[str, Any] = {}
    if text:
        block_update["rich_text"] = create_rich_text(text)
    if "checked" in inputs and block_type == "to_do":
        block_update["checked"] = inputs["checked"]

    payload = {
        block_type: block_update
    }

    res = client.request("PATCH", f"blocks/{block_id}", payload=payload)
    
    return {
        "success": True,
        "block_id": res.get("id"),
        "type": block_type,
        "last_edited_time": res.get("last_edited_time"),
        "message": f"Block '{block_id}' updated successfully."
    }


def archive_page(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Archive (soft-delete) or restore a page."""
    client = _get_client(context)
    page_id = inputs["page_id"].strip()
    should_archive = inputs.get("archive", True)
    
    payload = {"archived": should_archive}
    res = client.request("PATCH", f"pages/{page_id}", payload=payload)
    
    status_str = "archived" if should_archive else "restored"
    return {
        "success": True,
        "page_id": res.get("id"),
        "archived": res.get("archived", True),
        "message": f"Page '{page_id}' has been {status_str}."
    }
