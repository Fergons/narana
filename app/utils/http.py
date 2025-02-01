from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential_jitter, retry_if_result
from httpx import AsyncClient, Response
import logging

logger = logging.getLogger(__name__)

async def retry_fetch(session: AsyncClient, url: str, **kwargs) -> Response:
    """Fetch URL with retry logic for server errors.
    
    Args:
        session: AsyncClient session to use
        url: URL to fetch
        **kwargs: Additional arguments to pass to get request
        
    Returns:
        Response from the server
    """
    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(3), 
        wait=wait_exponential_jitter(max=30), 
        retry=retry_if_result(lambda res: res.is_server_error)
    ):
        with attempt:
            return await session.get(url, **kwargs) 