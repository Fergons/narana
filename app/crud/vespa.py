import asyncio
from vespa.application import Vespa, VespaAsync, VespaQueryResponse
from vespa.exceptions import VespaError
from utils.string import camel_to_string
from app.models.tvtropes import TropeExample
from litellm import aembedding
from typing import Sequence
from dataclasses import dataclass

@dataclass
class VespaCRUD:
    @classmethod
    async def async_feed(self, app: Vespa, *, data: Sequence, feeder_func: callable, num_concurrent_requests: int = 10):
        semaphore = asyncio.Semaphore(num_concurrent_requests)
        async with app.asyncio() as async_app:
            tasks = []
            for batch in data:
                async with semaphore:
                    task = asyncio.create_task(
                       feeder_func(async_app, batch)
                    )
                    tasks.append(task)
            await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
    
    @classmethod
    async def feed_tvtropes_example_batch(async_app: VespaAsync, batch: list[TropeExample], model: str = "ollama/bge-m3"):
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
            
    @classmethod
    def get_tvtropes_ids(app: Vespa):
        all_ids = []
        for slice in app.visit(
            content_cluster_name="narana_content",
            schema="tvtropes",
            namespace="narana",
            selection="true",  # Document selection - see https://docs.vespa.ai/en/reference/document-select-language.html
            slices=4,
            wanted_document_count=300,
        ):
            for response in slice:
                print(response.number_documents_retrieved)
                all_ids.extend(response.documents)
        
          
    




    


