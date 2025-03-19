# Cursor MCP Slack Service

一个用于Cursor MCP的Slack服务集成，提供获取Slack频道用户列表和获取指定线程聊天记录的功能。

## 功能

- 获取指定Slack频道下的用户列表
- 获取指定Slack频道中特定线程的聊天记录
- 获取指定Slack频道中的聊天记录

## 使用方法

### 创建和配置Slack App

在使用此服务之前，您需要创建并配置一个Slack App：

1. **创建Slack App**:
   - 访问 [Slack API网站](https://api.slack.com/apps)
   - 点击"Create New App"
   - 选择"From scratch"，输入App名称和选择工作区

2. **配置Bot权限**:
   - 在左侧菜单中选择"OAuth & Permissions"
   - 在"Bot Token Scopes"部分，添加以下权限:
     - `channels:history` (查看频道消息历史)
     - `channels:read` (查看频道信息)
     - `groups:history` (查看私有频道消息历史)
     - `groups:read` (查看私有频道信息)
     - `users:read` (查看用户信息)
     - `users:read.email` (查看用户邮箱)

3. **安装App到工作区**:
   - 在"OAuth & Permissions"页面，点击"Install to Workspace"
   - 授权App访问工作区
   - 安装完成后，您将获得一个Bot User OAuth Token，以"xoxb-"开头
   - 保存此Token，用于后续配置

4. **添加App到频道**:
   - 在需要获取历史消息的频道中，添加您创建的App
   - 在Slack中，打开频道，点击频道名称打开详情
   - 滚动到底部，点击"Integrations" > "Add apps"
   - 搜索并添加您创建的App

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
   - 参数：`channel_id`: Slack频道ID

2. `get_thread_messages`: 获取指定Slack频道中特定线程的聊天记录
   - 参数：
     - `channel_id`: Slack频道ID
     - `thread_ts`: 线程的时间戳ID
3. `get_conversation_history`: 获取指定Slack频道的对话历史记录
   - 参数：
     - `channel_id`: Slack频道ID
     - `limit`: 返回的消息数量上限,默认100条
     - `cursor`: 分页游标,用于获取更多消息

## 开发

1. 克隆仓库
2. 安装依赖: `uv pip install -e .`
3. 启动服务: `uv run slack --transport sse --port 8005`
4. 运行测试: `uv run pytest -vv -s cursor_mcp_slack/test_slack.py`