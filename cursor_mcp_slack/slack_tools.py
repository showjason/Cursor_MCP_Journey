from typing import Any, List, Dict, Optional
import mcp.types as types
from mcp.server.lowlevel import Server
from cursor_mcp_slack.slack_client import SlackClient

class SlackTools:
    """Slack工具集合类，用于管理和注册所有Slack相关工具"""
    
    def __init__(self, slack_client: SlackClient):
        """初始化Slack工具集
        
        Args:
            slack_client: Slack客户端实例
        """
        self.slack_client = slack_client
        self.tools_registry = {
            "get_channel_users": self._handle_get_channel_users,
            "get_thread_messages": self._handle_get_thread_messages,
            "get_conversation_history": self._handle_get_conversation_history
        }
        
    def register_tools(self, app: Server) -> None:
        """向MCP服务器注册所有Slack工具
        
        Args:
            app: MCP服务器实例
        """
        @app.call_tool()
        async def slack_tool(
            name: str, arguments: dict
        ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            if name in self.tools_registry:
                return await self.tools_registry[name](arguments)
            raise ValueError(f"未知工具: {name}")

        @app.list_tools()
        async def list_tools() -> list[types.Tool]:
            return self._get_tools_definitions()
    
    async def _handle_get_channel_users(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """处理获取频道用户列表的工具调用
        
        Args:
            arguments: 工具参数
            
        Returns:
            格式化的用户列表文本内容
        """
        try:
            users = await self.slack_client.get_channel_users(arguments["channel_id"])
            result = "频道用户列表:\n\n"
            for user in users:
                result += f"ID: {user['id']}\n"
                result += f"用户名: {user['name']}\n"
                result += f"真实姓名: {user['real_name']}\n"
                result += f"显示名称: {user['display_name']}\n"
                result += f"邮箱: {user['email']}\n"
                result += f"是否机器人: {'是' if user['is_bot'] else '否'}\n\n"
            return [types.TextContent(type="text", text=result)]
        except ValueError as e:
            return [types.TextContent(type="text", text=str(e))]
    
    async def _handle_get_thread_messages(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """处理获取线程消息的工具调用
        
        Args:
            arguments: 工具参数
            
        Returns:
            格式化的线程消息文本内容
        """
        try:
            messages = await self.slack_client.get_thread_messages(
                arguments["channel_id"], arguments["thread_ts"]
            )
            result = "线程消息记录:\n\n"
            for msg in messages:
                result += f"时间戳: {msg['ts']}\n"
                result += f"用户: {msg['user_name']} ({msg['user_id']})\n"
                result += f"内容: {msg['text']}\n"
                if msg.get("reactions"):
                    result += "反应: "
                    reactions = [f"{r['name']} ({r['count']})" for r in msg["reactions"]]
                    result += ", ".join(reactions) + "\n"
                result += "\n"
            return [types.TextContent(type="text", text=result)]
        except ValueError as e:
            return [types.TextContent(type="text", text=str(e))]
    
    async def _handle_get_conversation_history(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """处理获取频道对话历史的工具调用
        
        Args:
            arguments: 工具参数
            
        Returns:
            格式化的对话历史文本内容
        """
        try:
            # 获取必需参数
            channel_id = arguments["channel_id"]
            
            # 获取可选参数,如果未提供则使用默认值
            limit = arguments.get("limit", 100)
            cursor = arguments.get("cursor", None)
            
            result = await self.slack_client.get_conversation_history(
                channel_id, limit, cursor
            )
            messages = result["messages"]
            result_text = "频道对话历史记录:\n\n"
            for msg in messages:
                result_text += f"时间戳: {msg['ts']}\n"
                result_text += f"用户: {msg['user_name']} ({msg['user_id']})\n"
                result_text += f"内容: {msg['text']}\n"
                if msg.get("reactions"):
                    result_text += "反应: "
                    reactions = [f"{r['name']} ({r['count']})" for r in msg["reactions"]]
                    result_text += ", ".join(reactions) + "\n"
                result_text += "\n"
            
            # 添加分页信息
            if result.get("has_more"):
                result_text += "---\n"
                result_text += "还有更多消息。"
                if result.get("next_cursor"):
                    result_text += f"\n下一页游标: {result['next_cursor']}"
            
            return [types.TextContent(type="text", text=result_text)]
        except ValueError as e:
            return [types.TextContent(type="text", text=str(e))]
    
    def _get_tools_definitions(self) -> List[types.Tool]:
        """获取所有工具的定义
        
        Returns:
            工具定义列表
        """
        return [
            types.Tool(
                name="get_channel_users",
                description="获取指定Slack频道下的用户列表",
                inputSchema={
                    "type": "object",
                    "required": ["channel_id"],
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "Slack频道ID",
                        }
                    },
                },
            ),
            types.Tool(
                name="get_thread_messages",
                description="获取指定Slack频道中特定线程的聊天记录",
                inputSchema={
                    "type": "object",
                    "required": ["channel_id", "thread_ts"],
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "Slack频道ID",
                        },
                        "thread_ts": {
                            "type": "string",
                            "description": "线程的时间戳ID",
                        }
                    },
                },
            ),
            types.Tool(
                name="get_conversation_history",
                description="获取指定Slack频道的对话历史记录",
                inputSchema={
                    "type": "object",
                    "required": ["channel_id"],
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "Slack频道ID",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "返回的消息数量上限,默认100条",
                        },
                        "cursor": {
                            "type": "string",
                            "description": "分页游标,用于获取更多消息",
                        }
                    },
                },
            )
        ] 