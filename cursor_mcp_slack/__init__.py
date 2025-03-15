"""
Cursor MCP Slack 工具包

这个包提供了与Slack集成的MCP工具，允许通过MCP协议与Slack API交互。
"""

from cursor_mcp_slack.slack_client import SlackClient
from cursor_mcp_slack.slack_tools import SlackTools
from cursor_mcp_slack.server import setup_server

__all__ = ["SlackClient", "SlackTools", "setup_server"]

__version__ = "0.1.0" 