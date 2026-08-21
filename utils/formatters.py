"""Notion API payload formatting utilities for RailCall Notion Module.

Converts simple Python data types and dicts into Notion's formal API schemas
for properties, rich text objects, and block children.
"""

from typing import Any, Dict, List, Union, Optional


def create_rich_text(text: str, link_url: Optional[str] = None) -> List[Dict[str, Any]]:
    """Build a Notion rich text array from a string."""
    if not text:
        return []
    text_obj: Dict[str, Any] = {"content": text}
    if link_url:
        text_obj["link"] = {"url": link_url}
    return [{
        "type": "text",
        "text": text_obj
    }]


def format_property_value(val: Any) -> Dict[str, Any]:
    """Dynamically infer Notion property payload from Python data type."""
    if isinstance(val, dict):
        # Already structured as Notion property (e.g. {"select": {"name": "In Progress"}})
        return val
    
    if isinstance(val, bool):
        return {"checkbox": val}
    
    if isinstance(val, (int, float)):
        return {"number": val}
    
    if isinstance(val, str):
        # Default string handling as rich_text
        return {"rich_text": create_rich_text(val)}
    
    if isinstance(val, list):
        # List of strings converted to multi_select
        if val and isinstance(val[0], str):
            return {"multi_select": [{"name": item} for item in val]}
    
    return {"rich_text": create_rich_text(str(val))}


def build_properties_dict(title: Optional[str] = None, properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Construct a full properties dictionary for page creation or update."""
    result: Dict[str, Any] = {}
    
    if title is not None:
        result["Name"] = {
            "title": create_rich_text(title)
        }
        result["title"] = {
            "title": create_rich_text(title)
        }
    
    if properties:
        for key, val in properties.items():
            if key.lower() in ["title", "name"] and title is not None:
                continue  # Avoid duplicating title
            result[key] = format_property_value(val)
            
    return result


def build_block_object(block_item: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Convert string or dict into a valid Notion block child object."""
    if isinstance(block_item, str):
        # Convenient string shorthand -> paragraph block
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": create_rich_text(block_item)
            }
        }
    
    if isinstance(block_item, dict):
        if "object" in block_item and "type" in block_item:
            # Already a formal Notion block object
            return block_item
        
        block_type = block_item.get("type", "paragraph")
        text = block_item.get("text", "")
        
        if block_type in ["paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item", "numbered_list_item", "quote"]:
            return {
                "object": "block",
                "type": block_type,
                block_type: {
                    "rich_text": create_rich_text(text)
                }
            }
        
        if block_type == "callout":
            emoji = block_item.get("icon", "💡")
            return {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": create_rich_text(text),
                    "icon": {"type": "emoji", "emoji": emoji}
                }
            }
        
        if block_type == "to_do":
            checked = block_item.get("checked", False)
            return {
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": create_rich_text(text),
                    "checked": checked
                }
            }
        
        if block_type == "code":
            language = block_item.get("language", "json")
            return {
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": create_rich_text(text),
                    "language": language
                }
            }

    # Fallback paragraph
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": create_rich_text(str(block_item))
        }
    }
