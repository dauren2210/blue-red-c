import asyncio
import logging
from app.crud.crud_session import create_session
from app.models.session import SessionCreate
from app.core.config import settings
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.services.knowledge_graph_processor import graphiti
from graphiti_core.nodes import EpisodeType
from datetime import datetime

logging.basicConfig(level=logging.INFO)

EXAMPLE_REQUESTS = [
    "Hi, I need to order 50 ergonomic office chairs in black for our new office. Can you have them delivered to Paris, Le Carrousel du Louvre, by July 9th at 11am?",
    "Hello, we're looking for 20 standing desks with adjustable height for our Berlin office at Alexanderplatz. Delivery should be on August 15th at 9:30 in the morning.",
    "Good afternoon, could you help us find 5 large conference tables that seat at least 10 people each? We need them delivered to Canary Wharf in London on September 1st at 2pm.",
    "Hi, I want to purchase 100 27-inch 4K LED monitors for our Amsterdam branch, to be delivered to RAI on July 20th at 10am. Please make sure they are all the same model.",
    "Hello, we need 10 high-lumen wireless projectors for an event at IFEMA in Madrid. The delivery date should be October 5th at 4pm. Can you arrange this?",
]

def print_facts(edges):
    print("\n".join([edge.fact for edge in edges]))

async def main():
    await connect_to_mongo()
    try:
        for idx, transcript in enumerate(EXAMPLE_REQUESTS, 1):
            await graphiti.add_episode(
                name="User request on purchasing",
                episode_body=transcript,
                source=EpisodeType.text,
                source_description="Blue Red C application usage",
                # The timestamp for when this episode occurred or was created
                reference_time=datetime.utcnow(),
            )
            logging.info(f"Created session {idx}: {updated_session}")

        search_query = "What is the area of purchasing of the user?"
        results = await graphiti.search(search_query)
        logging.info(f"Search results for query: {search_query}")
        print_facts(results)
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(main())
