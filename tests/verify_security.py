import html
import unittest
from unittest.mock import MagicMock
import sys
from pathlib import Path

# Add project root to sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Mock streamlit before importing theme
sys.modules['streamlit'] = MagicMock()
import core.theme as theme

class TestSecurityFix(unittest.TestCase):
    def test_html_escape_logic(self):
        payload = "<script>alert('xss')</script>"
        # html.escape by default escapes quotes as well in recent python versions
        escaped_payload = html.escape(payload)

        self.assertIn("&lt;script&gt;", escaped_payload)
        self.assertNotIn("<script>", escaped_payload)

    def test_theme_functions_escaping(self):
        # We need to check if theme functions call st.markdown with escaped strings
        # Since we mocked streamlit, we can check the calls to st.markdown

        import streamlit as st

        payload = "<script>alert('xss')</script>"

        # Test page_header
        theme.page_header(payload, payload)
        call_args = st.markdown.call_args[0][0]
        self.assertIn("&lt;script&gt;", call_args)
        self.assertNotIn("<script>", call_args)

        # Test section_header
        st.markdown.reset_mock()
        theme.section_header(payload, payload)
        call_args = st.markdown.call_args[0][0]
        self.assertIn("&lt;script&gt;", call_args)
        self.assertNotIn("<script>", call_args)

        # Test chat_message
        st.markdown.reset_mock()
        theme.chat_message(payload, payload, payload)
        call_args = st.markdown.call_args[0][0]
        self.assertIn("&lt;script&gt;", call_args)
        self.assertNotIn("<script>", call_args)

        # Test agent_message
        st.markdown.reset_mock()
        theme.agent_message(payload, payload, payload)
        call_args = st.markdown.call_args[0][0]
        self.assertIn("&lt;script&gt;", call_args)
        self.assertNotIn("<script>", call_args)

        # Test metric_card
        st.markdown.reset_mock()
        theme.metric_card(payload, payload, payload)
        call_args = st.markdown.call_args[0][0]
        self.assertIn("&lt;script&gt;", call_args)
        self.assertNotIn("<script>", call_args)

        # Test typing_indicator
        st.markdown.reset_mock()
        theme.typing_indicator(payload, payload)
        call_args = st.markdown.call_args[0][0]
        self.assertIn("&lt;script&gt;", call_args)
        self.assertNotIn("<script>", call_args)

        # Test step_indicator
        st.markdown.reset_mock()
        theme.step_indicator([payload])
        call_args = st.markdown.call_args[0][0]
        self.assertIn("&lt;script&gt;", call_args)
        self.assertNotIn("<script>", call_args)

if __name__ == "__main__":
    unittest.main()
