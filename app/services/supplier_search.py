import json
import re
from urllib.parse import urlparse, urljoin
import httpx
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
        """
        Scrapes the content of a webpage and returns relevant text.
        
        Args:
            url (str): The URL to scrape
            
        Returns:
            str: Extracted text content from the webpage
        """
        try:
            response = await client.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text content
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit text length to avoid token limits
            return text[:5000]  # First 5000 characters
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return ""

    def _extract_phone_numbers(self, webpage_content: str) -> list:
        """
        Extracts phone numbers from webpage content using regex patterns.
        
        Args:
            webpage_content (str): The webpage content to search
            
        Returns:
            list: List of found phone numbers
        """
        phone_numbers = []
        
        # Basic phone number patterns - we'll strip whitespace later
        patterns = [
            # US format with parentheses and dashes
            r'\(\d{3}\)\s*\d{3}[\s\-\.]*\d{4}',  # (123) 456-7890, (123) 456 - 7890
            r'\d{3}[\s\-\.]*\d{3}[\s\-\.]*\d{4}',  # 123-456-7890, 123 456 7890
            r'\(\d{3}\)\s*\d{3}\s*\d{4}',  # (123) 456 7890
            
            # International format
            r'\+\d{1,3}[\s\-\.]*\d{1,4}[\s\-\.]*\d{1,4}[\s\-\.]*\d{1,4}',  # +1 234 567 8901
            
            # UK format
            r'\+44[\s\-\.]*\d{1,4}[\s\-\.]*\d{1,4}[\s\-\.]*\d{1,4}',  # +44 123 456 7890
            r'0\d{1,4}[\s\-\.]*\d{1,4}[\s\-\.]*\d{1,4}',  # 0123 456 7890
            
            # European format
            r'\+3\d[\s\-\.]*\d{1,4}[\s\-\.]*\d{1,4}[\s\-\.]*\d{1,4}',  # +31 123 456 7890
            
            # Toll-free numbers
            r'1[\s\-\.]*800[\s\-\.]*\d{3}[\s\-\.]*\d{4}',  # 1-800-123-4567
            r'800[\s\-\.]*\d{3}[\s\-\.]*\d{4}',  # 800-123-4567
            r'1[\s\-\.]*888[\s\-\.]*\d{3}[\s\-\.]*\d{4}',  # 1-888-123-4567
            r'888[\s\-\.]*\d{3}[\s\-\.]*\d{4}',  # 888-123-4567
            r'1[\s\-\.]*877[\s\-\.]*\d{3}[\s\-\.]*\d{4}',  # 1-877-123-4567
            r'877[\s\-\.]*\d{3}[\s\-\.]*\d{4}',  # 877-123-4567
            r'1[\s\-\.]*866[\s\-\.]*\d{3}[\s\-\.]*\d{4}',  # 1-866-123-4567
            r'866[\s\-\.]*\d{3}[\s\-\.]*\d{4}',  # 866-123-4567
            
            # Plain 10-digit numbers
            r'\d{10}',  # 1234567890
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, webpage_content)
            for match in matches:
                # Strip all whitespace and clean up
                cleaned = re.sub(r'\s', '', str(match))
                # Remove any remaining non-digit characters except +
                cleaned = re.sub(r'[^\d\+]', '', cleaned)
                # Ensure it has at least 10 digits
                digit_count = len(re.findall(r'\d', cleaned))
                if digit_count >= 10 and cleaned not in phone_numbers:
                    phone_numbers.append(cleaned)
        
        return list(set(phone_numbers))  # Remove duplicates

    async def _discover_business_pages(self, client: httpx.AsyncClient, base_url: str) -> list:
        """
        Discovers relevant pages on a business website for phone number extraction.
        
        Args:
            base_url (str): The base URL of the business website
            
        Returns:
            list: List of URLs to search for phone numbers
        """
        urls_to_search = [base_url]  # Always include the main page
        
        try:
            # Common page paths to check
            common_paths = [
                'contact',
                'contact-us',
                'about',
                'about-us',
                'faq',
                'help',
                'support',
                'customer-service',
                'store-locator',
                'locations',
                'find-us',
                'get-in-touch',
                'reach-us',
                'phone',
                'call-us'
            ]
            
            # Extract domain from base URL
            parsed_url = urlparse(base_url)
            domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Get the main page content
            try:
                response = await client.get(base_url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find all links in header and footer
                    header_footer_links = []
                    
                    # Look for header elements
                    header_selectors = ['header', '.header', '#header', 'nav', '.nav', '#nav', '.navigation', '#navigation']
                    for selector in header_selectors:
                        header_elements = soup.select(selector)
                        for element in header_elements:
                            links = element.find_all('a', href=True)
                            header_footer_links.extend(links)
                    
                    # Look for footer elements
                    footer_selectors = ['footer', '.footer', '#footer', '.site-footer', '#site-footer']
                    for selector in footer_selectors:
                        footer_elements = soup.select(selector)
                        for element in footer_elements:
                            links = element.find_all('a', href=True)
                            header_footer_links.extend(links)
                    
                    # Also check for common navigation classes
                    nav_classes = ['.menu', '.main-menu', '.primary-menu', '.secondary-menu', '.footer-menu']
                    for nav_class in nav_classes:
                        nav_elements = soup.select(nav_class)
                        for element in nav_elements:
                            links = element.find_all('a', href=True)
                            header_footer_links.extend(links)
                    
                    # Process found links
                    for link in header_footer_links:
                        href = str(link.get('href', '')).lower()
                        link_text = str(link.get_text()).lower()
                        
                        # Check if link contains any common path
                        for path in common_paths:
                            if path in href or path in link_text:
                                # Convert relative URLs to absolute
                                if href.startswith('/'):
                                    full_url = domain + href
                                elif href.startswith('http'):
                                    full_url = href
                                else:
                                    full_url = urljoin(base_url, href)
                                
                                # Only add if it's from the same domain and not already in the list
                                if full_url.startswith(domain) and full_url not in urls_to_search:
                                    try:
                                        # Verify the page exists
                                        head_response = await client.head(full_url, timeout=5)
                                        if head_response.status_code == 200:
                                            urls_to_search.append(full_url)
                                    except Exception:
                                        continue
                                break  # Found a match, no need to check other paths
                
            except Exception as e:
                pass
                
        except Exception as e:
            pass
        
        return urls_to_search

    async def _extract_phone_numbers_from_website(self, client: httpx.AsyncClient, url: str) -> list:
        """
        Extracts phone numbers from a business website by searching multiple pages.
        
        Args:
            url (str): The main URL of the business website
            
        Returns:
            list: List of unique phone numbers found across all pages
        """
        # Discover pages to search
        pages_to_search = await self._discover_business_pages(client, url)
        
        all_phone_numbers = []
        
        for page_url in pages_to_search:
            try:
                # Scrape page content
                page_content = await self._scrape_webpage_content(client, page_url)
                if page_content:
                    # Extract phone numbers from this page
                    page_phones = self._extract_phone_numbers(page_content)
                    if page_phones:
                        all_phone_numbers.extend(page_phones)
            except Exception as e:
                continue
        
        # Remove duplicates and return
        unique_phones = list(set(all_phone_numbers))
        return unique_phones

    async def _check_webpage_requirements(self, client: httpx.AsyncClient, url: str) -> dict:
        """
        Visits a webpage and checks if it is a direct seller/deliverer.
        
        Args:
            url (str): The webpage URL to check
            
        Returns:
            dict: Analysis result with 'meets_requirements' boolean and 'reason' string
        """
        print(f"Checking webpage: {url}")
        
        # Scrape webpage content
        webpage_content = await self._scrape_webpage_content(client, url)
        
        if not webpage_content:
            return {
                'meets_requirements': False,
                'reason': 'Could not access webpage content',
                'phone_numbers': []
            }
        
        prompt = f"""
        Analyze this webpage content and determine if it is a direct seller/deliverer.
        
        Webpage content (first 5000 characters):
        {webpage_content[:5000]}
        
        Check if this webpage is a direct seller/deliverer by looking for:
        1. Product listings with prices (e-commerce stores)
        2. Shopping cart or "buy now" functionality
        3. Order forms or purchase options
        4. E-commerce store features
        5. Direct sales capabilities
        6. OR businesses that sell products but require direct contact:
           - Phone numbers for direct contact
           - Email addresses for inquiries
           - Contact forms or application forms
           - "Contact us for pricing" or "Request quote" options
           - "Call for availability" or similar messaging
           - B2B or wholesale businesses that don't sell online
        
        Include businesses that:
        - Have product listings with prices and online shopping
        - OR sell products but require direct contact (phone, email, forms)
        - Are manufacturers, wholesalers, or distributors
        - Have "Contact us for pricing" or "Request quote" options
        - Require phone/email contact for orders
        
        Exclude websites that are:
        - Blogs, news articles, or informational content
        - Review sites or comparison pages
        - General directories or listings
        - Social media posts
        - Forums or discussion boards
        - Wikipedia or educational content
        - Pure lead generation sites with no actual products
        
        Provide your analysis as a JSON object with:
        - "meets_requirements": true/false (true if it's a direct seller)
        - "reason": brief explanation of why it is or isn't a direct seller
        - "product_listings": true/false if product listings are found
        - "pricing_info": true/false if pricing is shown
        - "purchase_options": true/false if purchase/order options are available
        - "contact_required": true/false if direct contact is required for sales
        
        Analysis:
        """
        
        try:
            analysis_json = await language_processor.process_prompt(
                user_prompt=prompt,
                model="llama-3.3-70b-versatile",
                response_format="json"
            )
            analysis = json.loads(analysis_json)
            analysis['phone_numbers'] = []  # Initialize empty, will be filled later if qualified
            return analysis
        except Exception as e:
            print(f"Error analyzing webpage {url}: {e}")
            return {
                'meets_requirements': False,
                'reason': f'Error analyzing webpage: {str(e)}',
                'phone_numbers': []
            }

    async def _refine_search_results(self, client: httpx.AsyncClient, search_results: dict) -> list:
        """
        Refines the search results by visiting each webpage and checking if it meets requirements.
        
        Args:
            search_results (dict): The raw search results from SerpAPI.

        Returns:
            list: A list of dictionaries, each representing a business that meets requirements
                  with 'title', 'url', and analysis details.
        """
        organic_results = search_results.get("organic_results", [])
        
        # Handle different result formats and extract URLs
        urls_to_check = []
        for r in organic_results:
            if isinstance(r, dict):
                title = r.get("title", r.get("name", "Unknown"))
                url = r.get("link", r.get("url", r.get("href", "")))
                if url:
                    urls_to_check.append({"title": title, "url": url})
            elif isinstance(r, str):
                continue
            else:
                continue

        if not urls_to_check:
            return []

        print(f"\nChecking {len(urls_to_check)} webpages for direct seller qualification...")
        
        # First pass: Check if each webpage is a direct seller
        qualified_businesses = []
        for i, item in enumerate(urls_to_check[:10]):  # Limit to first 10 to avoid too many requests
            print(f"\n--- Checking webpage {i+1}/{min(len(urls_to_check), 10)} ---")
            
            analysis = await self._check_webpage_requirements(client, item['url'])
            
            if analysis.get('meets_requirements', False):
                qualified_business = {
                    'title': item['title'],
                    'url': item['url'],
                    'analysis': analysis
                }
                qualified_businesses.append(qualified_business)
                print(f"✓ QUALIFIED: {item['title']}")
                print(f"  Reason: {analysis.get('reason', 'N/A')}")
            else:
                print(f"✗ REJECTED: {item['title']}")
                print(f"  Reason: {analysis.get('reason', 'N/A')}")

        # Second pass: Extract phone numbers only for qualified businesses
        if qualified_businesses:
            for business in qualified_businesses:
                phone_numbers = await self._extract_phone_numbers_from_website(client, business['url'])
                business['analysis']['phone_numbers'] = phone_numbers

        return qualified_businesses

    async def _search_suppliers_on_google(self, client: httpx.AsyncClient, search_query: str):
        params = {
            "q": search_query,
            "engine": "google",
            "api_key": settings.SERP_API_KEY
        }
        try:
            response = await client.get(self.serp_api_url, params=params)
            response.raise_for_status()
            results = response.json()
            # For shopping queries, the key is 'shopping_results', not 'organic_results'
            if 'shopping_results' in results:
                return results['shopping_results']
            elif 'organic_results' in results:
                return results['organic_results']
            else:
                # Return the whole response for debugging if neither key is present
                return results
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            print(f"An error occurred during Google search: {e}")
            return None

    async def find_suppliers(self, search_query: str):
        """
        The main function to find and process suppliers.
        """
        print(f"\n--- Searching with query: '{search_query}' ---")

        async with httpx.AsyncClient(headers=self.headers) as client:
            # Get search results
            raw_results = await self._search_suppliers_on_google(client, search_query)
            
            if not raw_results:
                print("No raw results from Google search.")
                return []

            # Refine results by visiting each webpage and checking requirements
            final_businesses = await self._refine_search_results(client, {"organic_results": raw_results})

        print(f"\nFound {len(final_businesses)} businesses that meet requirements.")
        
        return final_businesses

supplier_search_service = SupplierSearchService() 