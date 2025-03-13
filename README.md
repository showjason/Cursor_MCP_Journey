# Cursor MCP Slack Service

一个用于Cursor MCP的Slack服务集成，提供获取Slack频道用户列表和获取指定线程聊天记录的功能。

## 功能

- 获取指定Slack频道下的用户列表
- 获取指定Slack频道中特定线程的聊天记录
- 获取指定Slack频道中的聊天记录

## 使用方法

### 配置Slack API令牌

有两种方式配置Slack API令牌：

1. **环境变量方式**：
   - 复制项目根目录下的`.env.example`文件为`.env`
   - 在`.env`文件中设置您的Slack API令牌：
     ```
     TOKEN=xoxb-your-slack-token-here
     ```

2. **命令行参数方式**：
   - 在启动服务时通过`--token`参数提供令牌（此方式优先级更高）

### 作为Cursor MCP服务

1. 首先，获取Slack API令牌（需要有适当的权限）

2. 启动Slack MCP服务器：
```bash
# 使用命令行参数提供令牌
uv run slack --transport sse --port 8005 --token YOUR_SLACK_TOKEN

# 或者使用.env文件中配置的令牌
uv run slack --transport sse --port 8005
```

3. 在Cursor中，添加新的MCP服务器：
   - 名称：Slack
   - 类型：sse
   - 服务器URL：http://localhost:8085

该服务提供两个MCP工具：

1. `get_channel_users`: 获取指定Slack频道下的用户列表
   - 参数：`channel_id`（Slack频道ID）

2. `get_thread_messages`: 获取指定Slack频道中特定线程的聊天记录
   - 参数：
     - `channel_id`：Slack频道ID
     - `thread_ts`：线程的时间戳ID

## 开发

1. 克隆仓库
2. 安装依赖：`uv pip install -e .`
3. 运行测试：`uv run pytest -vv -s cursor_mcp_slack/test_slack.py`