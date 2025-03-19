from typing import Any, List, Dict, Optional
import click
import os
from dotenv import load_dotenv
from mcp.server.lowlevel import Server

# 导入重构后的模块
from cursor_mcp_slack.slack_client import SlackClient
from cursor_mcp_slack.slack_tools import SlackTools
from cursor_mcp_slack.server import setup_server

# 加载.env文件中的环境变量
load_dotenv()

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
    
    # 创建Slack客户端
    slack_client = SlackClient(token)
    
    # 创建MCP服务器
    app = Server("slack")
    
    # 设置Slack工具
    tools = SlackTools(slack_client)
    tools.register_tools(app)
    
    # 启动服务器
    setup_server(app, port, transport)

    return 0

if __name__ == "__main__":
    main()