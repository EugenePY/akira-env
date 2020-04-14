import pytest
from unittest.mock import Mock, patch

from akira.akira_models.app import app, train, process_predict

@pytest.fixture()
def test_app(event_loop):
    """passing in event_loop helps avoid 'attached to a different loop' error"""
    app.finalize()
    app.conf.store = 'memory://'
    app.flow_control.resume()
    return app

@pytest.mark.asyncio()
async def test_foo(test_app):
    with patch(__name__ + '.bar') as mocked_bar:
        mocked_bar.send = mock_coro()
        async with foo.test_context() as agent:
            await agent.put('hey')
            mocked_bar.send.assert_called_with('hey')

def mock_coro(return_value=None, **kwargs):
    """Create mock coroutine function."""
    async def wrapped(*args, **kwargs):
        return return_value
    return Mock(wraps=wrapped, **kwargs)

@pytest.mark.asyncio()
async def test_bar(test_app):
    async with bar.test_context() as agent:
        event = await agent.put('hey')
        assert agent.results[event.message.offset] == 'heyYOLO'