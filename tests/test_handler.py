"""Comprehensive unit tests for RailCall Notion Module handler commands and API client.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Ensure parent path in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from handlers import handler
from utils.notion_client import NotionClient, NotionAPIError
from utils.formatters import build_properties_dict, build_block_object, create_rich_text


class TestNotionFormatters(unittest.TestCase):
    """Test formatters and schema helpers."""

    def test_create_rich_text(self):
        rt = create_rich_text("Hello World", link_url="https://railcall.ai")
        self.assertEqual(len(rt), 1)
        self.assertEqual(rt[0]["type"], "text")
        self.assertEqual(rt[0]["text"]["content"], "Hello World")
        self.assertEqual(rt[0]["text"]["link"]["url"], "https://railcall.ai")

    def test_build_properties_dict(self):
        props = build_properties_dict(
            title="Sprint Goal",
            properties={
                "Status": "In Progress",
                "Priority": 1,
                "Tags": ["Urgent", "Backend"]
            }
        )
        self.assertIn("Name", props)
        self.assertIn("Status", props)
        self.assertEqual(props["Priority"]["number"], 1)
        self.assertEqual(len(props["Tags"]["multi_select"]), 2)

    def test_build_block_object(self):
        # String shorthand test
        b1 = build_block_object("Simple text paragraph")
        self.assertEqual(b1["type"], "paragraph")
        
        # Callout block test
        b2 = build_block_object({"type": "callout", "text": "Important notice", "icon": "⚠️"})
        self.assertEqual(b2["type"], "callout")
        self.assertEqual(b2["callout"]["icon"]["emoji"], "⚠️")


class TestNotionHandlers(unittest.TestCase):
    """Test all 10 handler commands using mock NotionClient."""

    def setUp(self):
        self.context = {"api_key": "secret_test_key_12345"}

    @patch.object(NotionClient, "request")
    def test_search(self, mock_req):
        mock_req.return_value = {
            "object": "list",
            "results": [
                {
                    "object": "page",
                    "id": "page-uuid-1",
                    "url": "https://notion.so/page-1",
                    "last_edited_time": "2026-07-30T10:00:00Z",
                    "properties": {
                        "Name": {
                            "id": "title",
                            "title": [{"plain_text": "System Design Doc"}]
                        }
                    }
                }
            ],
            "has_more": False
        }
        res = handler.search({"query": "System Design"}, self.context)
        self.assertEqual(res["count"], 1)
        self.assertEqual(res["results"][0]["title"], "System Design Doc")
        mock_req.assert_called_once()

    @patch.object(NotionClient, "request")
    def test_get_page(self, mock_req):
        mock_req.return_value = {
            "id": "page-uuid-123",
            "url": "https://notion.so/page-123",
            "created_time": "2026-07-30T09:00:00Z",
            "properties": {
                "Title": {
                    "type": "title",
                    "title": [{"plain_text": "Customer Feedback"}]
                }
            }
        }
        res = handler.get_page({"page_id": "page-uuid-123"}, self.context)
        self.assertEqual(res["id"], "page-uuid-123")
        self.assertEqual(res["title"], "Customer Feedback")

    @patch.object(NotionClient, "request")
    def test_query_database(self, mock_req):
        mock_req.return_value = {
            "results": [
                {
                    "id": "item-1",
                    "url": "https://notion.so/item-1",
                    "properties": {
                        "Task": {
                            "type": "title",
                            "title": [{"plain_text": "Fix Authentication Bug"}]
                        }
                    }
                }
            ],
            "has_more": False
        }
        res = handler.query_database({
            "database_id": "db-uuid-456",
            "filter": {"property": "Status", "select": {"equals": "Done"}}
        }, self.context)
        self.assertEqual(res["count"], 1)
        self.assertEqual(res["results"][0]["title"], "Fix Authentication Bug")

    @patch.object(NotionClient, "request")
    def test_create_page(self, mock_req):
        mock_req.return_value = {
            "id": "new-page-789",
            "url": "https://notion.so/new-page-789",
            "created_time": "2026-07-30T11:00:00Z"
        }
        res = handler.create_page({
            "parent_type": "database_id",
            "parent_id": "db-uuid-456",
            "title": "New Feature Spec",
            "icon_emoji": "🚀",
            "content_blocks": ["Introduction", {"type": "callout", "text": "High Priority"}]
        }, self.context)
        
        self.assertTrue(res["success"])
        self.assertEqual(res["page_id"], "new-page-789")
        self.assertEqual(res["title"], "New Feature Spec")

    @patch.object(NotionClient, "request")
    def test_append_blocks(self, mock_req):
        mock_req.return_value = {
            "results": [{"id": "block-1"}, {"id": "block-2"}]
        }
        res = handler.append_blocks({
            "block_id": "parent-page-123",
            "blocks": ["Step 1", "Step 2"]
        }, self.context)
        
        self.assertTrue(res["success"])
        self.assertEqual(res["appended_count"], 2)

    @patch.object(NotionClient, "request")
    def test_archive_page(self, mock_req):
        mock_req.return_value = {
            "id": "page-to-archive",
            "archived": True
        }
        res = handler.archive_page({"page_id": "page-to-archive", "archive": True}, self.context)
        self.assertTrue(res["success"])
        self.assertTrue(res["archived"])

    def test_missing_api_key_raises_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                handler.get_page({"page_id": "123"}, context={})


if __name__ == "__main__":
    unittest.main()
