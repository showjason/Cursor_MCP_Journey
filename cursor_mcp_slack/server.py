import anyio
from mcp.server.lowlevel import Server

def setup_server(app: Server, port: int, transport_type: str) -> None:
    """设置并启动MCP服务器
    
    Args:
        app: MCP服务器实例
        port: 服务器监听端口
        transport_type: 传输类型，支持"stdio"或"sse"
    """
    if transport_type == "sse":
        _setup_sse_server(app, port)
    else:
        _setup_stdio_server(app)

def _setup_sse_server(app: Server, port: int) -> None:
    """设置并启动SSE服务器
    
    Args:
        app: MCP服务器实例
        port: 服务器监听端口
    """
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Mount, Route
    import uvicorn

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

    uvicorn.run(starlette_app, host="0.0.0.0", port=port)

def _setup_stdio_server(app: Server) -> None:
    """设置并启动标准输入输出服务器
    
    Args:
        app: MCP服务器实例
    """
    from mcp.server.stdio import stdio_server

    async def arun():
        async with stdio_server() as streams:
            await app.run(
                streams[0], streams[1], app.create_initialization_options()
            )

    anyio.run(arun) 