import fasut
import aiohttp


async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()


async def post(session, url, data):
    async with session.post(url, data) as response:
        return await response.text()


async def create_task_queue_stream(stream):
    pass


async def investing_dot_com(stream):
    pass
