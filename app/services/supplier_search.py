import json
import httpx
import logging
import asyncio
import re
from typing import Optional
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from app.core.config import settings
from app.services.language_processor import language_processor

class SupplierSearchService:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.serp_api_url = "https://serpapi.com/search"

    async def _scrape_webpage_content(self, client: httpx.AsyncClient, url: str) -> str:
        """Scrapes content and returns the first 5000 characters of clean text."""
        try:
            response = await client.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            for script_or_style in soup(["script", "style"]):
                script_or_style.decompose()
            text = ' '.join(t.strip() for t in soup.get_text().split())
            return text[:5000]
        except Exception as e:
            logging.error(f"Error scraping {url}: {e}")
            return ""

    async def _check_webpage_requirements(self, client: httpx.AsyncClient, url: str) -> dict:
        """Analyzes a webpage's content to determine if it's a valid supplier."""
        content = await self._scrape_webpage_content(client, url)
        if not content:
            return {'meets_requirements': False, 'reason': 'Could not scrape content.'}

        prompt = f"""
        Analyze the following webpage content and extract the primary phone number and address of the business.

        Webpage Content:
        "{content}"

        Provide your answer as a JSON object with two keys:
        - "phone_number": The contact phone number, or null if not found.
        - "address": The physical address, or null if not found.
        """
        try:
            response_json = await language_processor.process_prompt(
                user_prompt=prompt, model="llama3-70b-8192", response_format="json"
            )
            # The LLM's response IS the analysis
            analysis = json.loads(response_json)
            # We determine "meets_requirements" based on whether a phone was found.
            analysis['meets_requirements'] = bool(analysis.get('phone_number'))
            return analysis
        except Exception as e:
            logging.error(f"Error analyzing webpage {url}: {e}")
            return {'meets_requirements': False, 'reason': f'Error during analysis: {e}'}

    async def _search_suppliers_on_google(self, client: httpx.AsyncClient, search_query: str):
        """Searches Google and returns organic results."""
        params = {"engine": "google", "q": search_query, "api_key": settings.SERP_API_KEY}
        try:
            response = await client.get(self.serp_api_url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"An error occurred during Google search: {e}", exc_info=True)
            return None

    async def find_suppliers(self, search_query: str):
        """Finds suppliers using a two-pass analysis of Google search results."""
        timeout = httpx.Timeout(30.0, connect=60.0)
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=timeout) as client:
            search_results = await self._search_suppliers_on_google(client, search_query)
            if not search_results or "organic_results" not in search_results:
                return []

            # First Pass: Qualify websites by extracting contact info
            qualification_tasks = []
            top_results = search_results.get("organic_results", [])[:10]
            for result in top_results:
                url = result.get("link")
                if url:
                    qualification_tasks.append(self._check_webpage_requirements(client, url))
            
            qualified_analyses = await asyncio.gather(*qualification_tasks)

            # Assemble final list of suppliers
            final_suppliers = []
            for i, analysis in enumerate(qualified_analyses):
                original_result = top_results[i]
                title = original_result.get("title", "Unknown")
                url = original_result.get("link", "N/A")
                
                if analysis.get('meets_requirements'): # True if a phone was found
                    phone = analysis.get("phone_number")
                    address = analysis.get("address")
                    logging.info(f"QUALIFIED: {title} ({url}) - Phone: {phone}, Address: {address}")
                    final_suppliers.append({
                        "title": title,
                        "url": url,
                        "analysis": {
                            "phone_numbers": [phone] if phone else [],
                            "address": address
                        }
                    })
                else:
                    reason = analysis.get('reason', 'No contact info found.')
                    logging.info(f"REJECTED: {title} ({url}) - Reason: {reason}")

            logging.info(f"Found {len(final_suppliers)} qualified suppliers with contact information.")
            return final_suppliers

supplier_search_service = SupplierSearchService() 