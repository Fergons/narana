from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential_jitter, retry_if_result
import logging
from httpx import AsyncClient, Response
from anyio import open_file
import orjson
from typing import AsyncIterable, Iterable

basic_config = logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




async def retry_fetch(session: AsyncClient, url: str, **kwargs) -> Response:
    async for attempt in AsyncRetrying(stop=stop_after_attempt(3), wait=wait_exponential_jitter(max=30), retry=retry_if_result(lambda res: res.is_server_error)):
        with attempt:
            return await session.get(url, **kwargs)
        

async def async_load_jsonl(path: str) -> AsyncIterable[dict]:
    async with await open_file(path, mode='r') as f:
        async for line in f:
           yield orjson.loads(line)

async def async_dump_jsonl(path: str, data: Iterable[dict]):
    async with await open_file(path, mode='w') as f:
        for item in data:
            await f.write(orjson.dumps(item)+b'\n')