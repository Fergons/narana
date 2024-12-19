import asyncio
from vespa.application import Vespa, VespaAsync, VespaQueryResponse
from vespa.exceptions import VespaError
from utils.string import camel_to_string
from app.models.tvtropes import EmbedTropeExample
from typing import Sequence
from dataclasses import dataclass

@dataclass
class VespaCRUD:
    @classmethod
    async def async_feed(cls, app: Vespa, *, data: Sequence, feeder_func: callable, num_concurrent_requests: int = 10):
        
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
    async def feed_tvtropes_example_batch(cls, async_app: VespaAsync, batch: list[EmbedTropeExample], semaphore: asyncio.Semaphore):
        doc = {}
        for trope_example in batch:
            doc["id"] = f'{trope_example.title_id}_{trope_example.trope_id}'
            doc["fields"] = {
                "title": camel_to_string(trope_example.title),
                "trope": camel_to_string(trope_example.trope),
                "example": trope_example.example,
                "title_id": trope_example.title_id,
                "trope_id": trope_example.trope_id,
                "dense_rep": trope_example.dense_rep
            }
            await async_app.feed_data_point(
                data_id=doc["id"],
                fields=doc["fields"],
                schema="tvtropes",
                namespace="narana",
                semaphore=semaphore,
                timeout=10)
            
    @classmethod
    def get_tvtropes_ids(cls, app: Vespa):
        all_ids = []
        for slice in app.visit(
            content_cluster_name="narana_content",
            schema="tvtropes",
            namespace="narana",
            selection="true",  # Document selection - see https://docs.vespa.ai/en/reference/document-select-language.html
            slices=4,
            wanted_document_count=500,
        ):
            for response in slice:
                if response.is_successful():
                    all_ids.extend([(doc["fields"]["title_id"], doc["fields"]["trope_id"]) for doc in response.documents])
        return all_ids
          
    




if __name__ == "__main__":
    crud = VespaCRUD()
    app = Vespa(url = "http://localhost", port = 8080)
    ids = crud.get_tvtropes_ids(app)
    print(ids)

