from typing import Any, List, Dict, Optional
import anyio
import click
import os
from pathlib import Path
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from mcp.server.lowlevel import Server
import mcp.types as types

# 加载.env文件中的环境变量
load_dotenv()

class SlackClient:
    """Slack API客户端封装类"""
    
    def __init__(self, token: str):
        """初始化Slack客户端
        
        Args:
            token: Slack API令牌
        """
        self.client = WebClient(token=token)
    
    async def get_channel_users(self, channel_id: str) -> List[Dict[str, Any]]:
        """获取指定频道的用户列表
        
        Args:
            channel_id: Slack频道ID
            
        Returns:
            用户列表,每个用户包含id、name等信息
        """
        try:
            # 获取频道成员ID列表
            response = self.client.conversations_members(channel=channel_id)
            member_ids = response["members"]
            
            # 获取每个成员的详细信息
            users = []
            for user_id in member_ids:
                user_info = self.client.users_info(user=user_id)
                if user_info["ok"]:
                    user = user_info["user"]
                    users.append({
                        "id": user["id"],
                        "name": user["name"],
                        "real_name": user.get("real_name", ""),
                        "display_name": user.get("profile", {}).get("display_name", ""),
                        "email": user.get("profile", {}).get("email", ""),
                        "is_bot": user.get("is_bot", False)
                    })
            
            return users
        except SlackApiError as e:
            raise ValueError(f"获取频道用户失败: {e.response['error']}")
    
    async def get_thread_messages(self, channel_id: str, thread_ts: str) -> List[Dict[str, Any]]:
        """获取指定线程的聊天记录
        
        Args:
            channel_id: Slack频道ID
            thread_ts: 线程时间戳ID
            
        Returns:
            消息列表,每条消息包含用户、文本、时间戳等信息
        """
        try:
            # 获取线程消息
            response = self.client.conversations_replies(
                channel=channel_id,
                ts=thread_ts
            )
            
            messages = []
            for msg in response["messages"]:
                # 获取发送消息的用户信息
                user_info = None
                if "user" in msg:
                    try:
                        user_info = self.client.users_info(user=msg["user"])["user"]
                    except SlackApiError:
                        pass
                
                message = {
                    "ts": msg["ts"],
                    "text": msg["text"],
                    "user_id": msg.get("user", ""),
                    "user_name": user_info["name"] if user_info else "Unknown",
                    "is_bot": user_info.get("is_bot", False) if user_info else False,
                    "thread_ts": msg.get("thread_ts", ""),
                    "reply_count": msg.get("reply_count", 0),
                    "reactions": msg.get("reactions", [])
                }
                messages.append(message)
            
            return messages
        except SlackApiError as e:
            raise ValueError(f"获取线程消息失败: {e.response['error']}")

    async def get_conversation_history(self, channel_id: str, limit: int = 100, cursor: str = None) -> Dict[str, Any]:
        """获取指定频道的对话历史记录
        
        Args:
            channel_id: Slack频道ID
            limit: 返回的消息数量上限,默认100条
            cursor: 分页游标,用于获取更多消息
            
        Returns:
            包含消息列表和下一页游标的字典
        """
        try:
            # 构建API请求参数
            params = {
                "channel": channel_id,
                "limit": limit
            }
            
            if cursor:
                params["cursor"] = cursor
                
            # 获取频道历史消息
            response = self.client.conversations_history(**params)
            messages = []
            for msg in response["messages"]:
                # 获取发送消息的用户信息
                user_info = None
                if "user" in msg:
                    try:
                        user_info = self.client.users_info(user=msg["user"])["user"]
                    except SlackApiError:
                        pass
                
                message = {
                    "ts": msg["ts"],
                    "text": msg["text"],
                    "user_id": msg.get("user", ""),
                    "user_name": user_info["name"] if user_info else "Unknown",
                    "is_bot": user_info.get("is_bot", False) if user_info else False,
                    "thread_ts": msg.get("thread_ts", ""),
                    "reply_count": msg.get("reply_count", 0),
                    "reactions": msg.get("reactions", [])
                }
                messages.append(message)
            
            # 返回消息列表和下一页游标（如果有）
            result = {
                "messages": messages,
                "has_more": response.get("has_more", False)
            }
            
            if response.get("response_metadata") and response["response_metadata"].get("next_cursor"):
                result["next_cursor"] = response["response_metadata"]["next_cursor"]
            
            return result
        except SlackApiError as e:
            raise ValueError(f"获取频道历史消息失败: {e.response['error']}")

@click.command()
@click.option("--port", default=8000, help="服务监听端口")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="传输类型",
)
@click.option("--token", default=None, help="Slack API令牌（可选,如未提供则使用环境变量TOKEN）")
def main(port: int, transport: str, token: str = None) -> int:
    """Slack MCP服务主入口"""
    # 如果命令行未提供token,则使用环境变量中的TOKEN
    if token is None:
        token = os.getenv("TOKEN")
        if not token:
            raise ValueError("未提供Slack API令牌,请通过--token参数或在.env文件中设置TOKEN环境变量")
    
    app = Server("slack")
    slack_client = SlackClient(token)

    @app.call_tool()
    async def slack_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        if name == "get_channel_users":
            try:
                users = await slack_client.get_channel_users(arguments["channel_id"])
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
        elif name == "get_thread_messages":
            try:
                messages = await slack_client.get_thread_messages(
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
        elif name == "get_conversation_history":
            try:
                # 获取必需参数
                channel_id = arguments["channel_id"]
                
                # 获取可选参数,如果未提供则使用默认值
                limit = arguments.get("limit", 100)
                cursor = arguments.get("cursor", None)
                
                result = await slack_client.get_conversation_history(
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
        raise ValueError(f"未知工具: {name}")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
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

    if transport == "sse":
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route

        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )

        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        import uvicorn

        uvicorn.run(starlette_app, host="0.0.0.0", port=port)
    else:
        from mcp.server.stdio import stdio_server

        async def arun():
            async with stdio_server() as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )

        anyio.run(arun)

    return 0

if __name__ == "__main__":
    main()