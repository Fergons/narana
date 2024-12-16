from utils.string import camel_to_string
from app.models.tvtropes import TropeExample
from app.models.documents import Book
from app.crud.tvtropes import TropeExamplesCRUD, BaseTropesCRUD
from litellm import aembedding
import asyncio
from vespa.application import Vespa, VespaAsync
from typing import Sequence
import time



async def feed_tvtropes_example_batch(async_app: VespaAsync, batch: Sequence[TropeExample], model: str = "ollama/bge-m3"):
    batch_examples = [trope_example.example for trope_example in batch]
    batch_embeddings = await aembedding(model=model, input=batch_examples)
    for response in batch_embeddings.data:
        trope_example = batch[response.get("index")]
        doc = {}
        doc["id"] = f'{trope_example.title_id}_{trope_example.trope_id}'
        doc["fields"] = {
            "title": camel_to_string(trope_example.title),
            "trope": camel_to_string(trope_example.trope),
            "example": trope_example.example,
            "title_id": trope_example.title_id,
            "trope_id": trope_example.trope_id,
            "dense_rep": response.get("embedding")
        }
        await async_app.feed_data_point(
                    data_id=doc["id"],
                    fields=doc["fields"],
                    schema="tvtropes",
                    namespace="narana",
                    timeout=10)
        

async def feed_book_batch(async_app: VespaAsync, batch: Sequence[Book], model: str = "ollama/bge-m3"):
    batch_examples = [book.text for book in batch]
    batch_embeddings = await aembedding(model=model, input=batch_examples)
    for response in batch_embeddings.data:
        trope_example = batch[response.get("index")]
        doc = {}
        doc["id"] = f'{trope_example.title_id}_{trope_example.trope_id}'
        doc["fields"] = {
            "title": camel_to_string(trope_example.title),
            "trope": camel_to_string(trope_example.trope),
            "example": trope_example.example,
            "title_id": trope_example.title_id,
            "trope_id": trope_example.trope_id,
            "dense_rep": response.get("embedding")
        }
        await async_app.feed_data_point(
                    data_id=doc["id"],
                    fields=doc["fields"],
                    schema="tvtropes",
                    namespace="narana",
                    timeout=10)




async def async_feed_vespa(*,app: Vespa, data: Sequence, feeder_func,  num_concurrent_requests: int = 10):
    sem = asyncio.Semaphore(num_concurrent_requests)
    tasks = []
    async with app.asyncio() as async_app:
        for batch in data:
            async with sem:
                task = asyncio.create_task(
                    feeder_func(async_app, batch)
                )
                tasks.append(task)
        await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)

                


if __name__ == "__main__":
    app = Vespa(url = "http://localhost", port = 8080)
    crud = TropeExamplesCRUD.load_from_csv('lit_goodreads_match')
    start_at = time.time()
    data_gen = crud.batch_generator(batch_size=16, limit=10000, offset=10000, exclude_ids=[])
    asyncio.run(async_feed_vespa(app=app, data=data_gen, feeder_func=feed_tvtropes_example_batch))
    print(f'Time to load data: {time.time() - start_at}')





        

       






