from anyio import open_file
import orjson
from typing import AsyncIterable, Iterable

async def async_load_jsonl(path: str) -> AsyncIterable[dict]:
    """Load JSONL file asynchronously.
    
    Args:
        path: Path to JSONL file
        
    Yields:
        Dictionary for each line in the file
    """
    async with await open_file(path, mode='r') as f:
        async for line in f:
           yield orjson.loads(line)

def load_jsonl(path: str) -> list:
    """Load JSONL file synchronously.
    
    Args:
        path: Path to JSONL file
        
    Returns:
        List of dictionaries from the file
    """
    with open(path, mode='r') as f:
        return [orjson.loads(line) for line in f]

async def async_dump_jsonl(path: str, data: Iterable[dict]):
    """Write data to JSONL file asynchronously.
    
    Args:
        path: Path to output file
        data: Iterable of dictionaries to write
    """
    async with await open_file(path, mode='w') as f:
        for item in data:
            await f.write(orjson.dumps(item)+b'\n') 