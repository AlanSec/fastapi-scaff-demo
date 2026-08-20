"""database.py 单元测试"""
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.infrastructure.persistence.database import (
    async_session_maker,
    engine,
    session_scope,
)


def test_engine_and_session_maker_created():
    """引擎与会话工厂应已创建"""
    assert engine is not None
    assert async_session_maker is not None


@pytest.mark.asyncio
async def test_session_scope_yields_and_closes():
    """session_scope 应产出会话并在结束时关闭"""
    mock_session = AsyncMock()
    factory = MagicMock(return_value=mock_session)

    async with session_scope(factory) as session:
        assert session is mock_session

    factory.assert_called_once_with()
    mock_session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_session_scope_closes_on_error():
    """session_scope 在异常时也应关闭会话"""
    mock_session = AsyncMock()
    factory = MagicMock(return_value=mock_session)

    with pytest.raises(RuntimeError):
        async with session_scope(factory):
            raise RuntimeError("boom")

    mock_session.close.assert_awaited_once()
