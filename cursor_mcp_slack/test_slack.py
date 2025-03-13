import os
import pytest
import pytest_asyncio
from dotenv import load_dotenv
from cursor_mcp_slack.slack import SlackClient

# 加载环境变量
load_dotenv()

# 测试常量
TEST_CHANNEL_ID = "C08G3P0DCTD"
TEST_LIMIT = 10

# 配置 pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

@pytest.fixture
def token():
    """提供 Slack API Token 的 fixture"""
    token = os.getenv("TOKEN")
    if not token:
        pytest.skip("缺少 TOKEN 环境变量，跳过测试")
    return token

@pytest_asyncio.fixture
async def slack_client(token):
    """提供 SlackClient 实例的 fixture"""
    return SlackClient(token=token)

@pytest.mark.asyncio
async def test_get_conversation_history(slack_client):
    """测试获取频道历史消息"""
    result = await slack_client.get_conversation_history(
        channel_id=TEST_CHANNEL_ID,
        limit=TEST_LIMIT
    )
    
    assert "messages" in result, "返回结果中应包含 messages 字段"
    assert isinstance(result["messages"], list), "messages 应该是一个列表"
    assert len(result["messages"]) <= TEST_LIMIT, f"消息数量应不超过请求的限制 {TEST_LIMIT}"
    
    if result["messages"]:
        message = result["messages"][0]
        assert "ts" in message, "消息应包含时间戳"
        assert "text" in message, "消息应包含文本内容"
        assert "user_name" in message, "消息应包含用户名"

@pytest.mark.asyncio
async def test_get_channel_users(slack_client):
    """测试获取频道用户"""
    users = await slack_client.get_channel_users(TEST_CHANNEL_ID)
    
    assert isinstance(users, list), "返回的用户应该是一个列表"
    assert len(users) > 0, "频道应该至少有一个用户"