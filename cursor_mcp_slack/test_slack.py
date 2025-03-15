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
# 添加线程时间戳测试常量
TEST_THREAD_TS = "1710432000.000000"  # 需要替换为实际存在的线程时间戳

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

@pytest.mark.asyncio
async def test_get_thread_messages(slack_client):
    """测试获取线程消息"""
    # 首先获取频道历史消息，找到一个有线程的消息
    result = await slack_client.get_conversation_history(
        channel_id=TEST_CHANNEL_ID,
        limit=20
    )
    
    # 查找包含线程的消息
    thread_ts = None
    for message in result["messages"]:
        if message.get("reply_count", 0) > 0:
            thread_ts = message["ts"]
            break
    
    # 如果找不到线程消息，使用预设的测试线程时间戳
    if not thread_ts:
        thread_ts = TEST_THREAD_TS
        pytest.skip(f"未找到包含回复的线程，将使用预设的测试线程时间戳: {thread_ts}")
    
    # 测试获取线程消息
    messages = await slack_client.get_thread_messages(
        channel_id=TEST_CHANNEL_ID,
        thread_ts=thread_ts
    )
    
    assert isinstance(messages, list), "返回的线程消息应该是一个列表"
    assert len(messages) > 0, "线程应该至少包含一条消息"
    
    if messages:
        message = messages[0]
        assert "ts" in message, "消息应包含时间戳"
        assert "text" in message, "消息应包含文本内容"
        assert "user_id" in message, "消息应包含用户ID"
        assert "user_name" in message, "消息应包含用户名"
        assert "thread_ts" in message, "消息应包含线程时间戳"