import json
from urllib.parse import urlparse
import httpx
import logging
from app.core.config import settings
from app.services.language_processor import language_processor

class SupplierSearchService:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.serp_api_url = "https://serpapi.com/search"

    async def _refine_search_results(self, search_results: dict, search_query: str) -> list:
        """
        Uses an LLM to parse the SerpApi JSON response and extract supplier details.
        """
        # Prune the search results to only include the most relevant parts
        relevant_data = {
            "local_results": search_results.get("local_results", []),
            "organic_results": search_results.get("organic_results", [])
        }

        # Create a prompt for the language model
        prompt = f"""
        You are an expert data extraction assistant. Your task is to analyze the following JSON data from a SerpApi Google Search result and extract a list of relevant suppliers.

        The original search query was: "{search_query}"

        The goal is to identify businesses that are likely to be suppliers of the product mentioned in the query. Look for entries under "local_results" and "organic_results" that appear to be businesses, not directories, blogs, or news articles.

        For each potential supplier, extract the following information:
        - title: The name of the business.
        - address: The physical address, if available.
        - phone: The phone number, if available.
        - website: The business website URL, if available.

        Return the data as a single JSON object with a key "suppliers" which contains a list of these extracted businesses. If no relevant suppliers are found, return an empty list.

        Here is the pruned SerpApi JSON data:
        {json.dumps(relevant_data, indent=2)}
        """

        try:
            # Use the language processor to get the structured data
            response_json = await language_processor.process_prompt(
                user_prompt=prompt,
                model="llama3-70b-8192",
                response_format="json"  # We want a JSON response
            )
            
            # The LLM should return a JSON string, so we parse it
            data = json.loads(response_json)
            
            # The prompt asks for a {"suppliers": []} structure
            suppliers = data.get("suppliers", [])
            
            if not isinstance(suppliers, list):
                logging.error(f"LLM returned unexpected data type for suppliers: {type(suppliers)}")
                return []
                
            logging.info(f"LLM extracted {len(suppliers)} suppliers from SerpApi response.")
            return suppliers

        except json.JSONDecodeError:
            logging.error("Failed to decode JSON response from language model.")
            return []
        except Exception as e:
            logging.error(f"An error occurred during LLM processing of search results: {e}", exc_info=True)
            return []

    async def _search_suppliers_on_google(self, client: httpx.AsyncClient, search_query: str):
        """
        Searches for suppliers on Google and returns a list of potential businesses.
        """
        params = {
            "engine": "google",
            "q": search_query,
            "api_key": settings.SERP_API_KEY,
            "tbs": "lps:1",  # This parameter filters for local results / business listings
        }
        
        try:
            response = await client.get(self.serp_api_url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error occurred during SerpApi call: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logging.error(f"An unexpected error occurred during Google search: {e}", exc_info=True)
        return None

    async def find_suppliers(self, search_query: str):
        """
        Finds suppliers by searching Google and refining the results.
        """
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True) as client:
            search_results = await self._search_suppliers_on_google(client, search_query)
            
            if not search_results:
                return []
            
            # Pass the search_query to the new refine function
            qualified_suppliers = await self._refine_search_results(search_results, search_query)
            return qualified_suppliers

supplier_search_service = SupplierSearchService() 