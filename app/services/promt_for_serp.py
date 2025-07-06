import os
from dotenv import load_dotenv
from groq import Groq
from serpapi import GoogleSearch
import json
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, urljoin

API_KEY_SERP = "fc8f1576be2fc9b836348600df3d06999571c219dce4f1ecfcca8260c610ee8a"

def process_prompt_for_groq(client, prompt, model="llama-3.3-70b-versatile", response_format="text"):
    """
    Process a prompt through Groq API and return the response.
    
    Args:
        client: Groq client instance
        prompt (str): The prompt to send to the LLM
        model (str): The model to use
        response_format (str): "text" for plain text, "json" for structured JSON
        
    Returns:
        str: The LLM response
    """
    messages = [{"role": "user", "content": prompt}]
    
    # Add response format for JSON if specified
    if response_format == "json":
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model,
            response_format={"type": "json_object"}
        )
    else:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model,
        )

    response_content = chat_completion.choices[0].message.content
    if response_content is None:
        raise ValueError("Received None response from Groq API")
    
    return response_content

def extract_product_and_location(voice_text: str, client) -> str:
    """
    Extracts core product name (without color, size, etc.) and city name from voice text.
    
    Args:
        voice_text (str): The transcribed voice input from the client.
        client: Groq client instance

    Returns:
        str: A simple search query with core product name and city only.
    """
    prompt = f"""
    Extract only the core product name and city from the following user request.
    - Product name: Extract only the main product type, ignore colors, sizes, quantities, brands, etc.
    - Location: Extract only the city name, ignore state, country, or other location details.
    
    Return just the core product name and city as a simple search query.

    Examples:
    User request: 'I need a large red t-shirt, 5 pieces, delivered to Berlin by tomorrow.'
    Output: 't-shirt Berlin'

    User request: 'I need 5 red electric bicycles by 11am on July 9th, 2025, delivered to Austin, Texas. The budget is 1000 usd'
    Output: 'electric bicycles Austin'

    User request: 'Looking for a blue Samsung smartphone, latest model, with fast shipping to Munich, Germany'
    Output: 'smartphone Munich'

    User request: '{voice_text}'
    Output:
    """
    search_query = process_prompt_for_groq(client, prompt, model="llama-3.3-70b-versatile", response_format="text")
    return search_query.strip()

def scrape_webpage_content(url: str) -> str:
    """
    Scrapes the content of a webpage and returns relevant text.
    
    Args:
        url (str): The URL to scrape
        
    Returns:
        str: Extracted text content from the webpage
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
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

def extract_phone_numbers(webpage_content: str) -> list:
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

def discover_business_pages(base_url: str) -> list:
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
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(base_url, headers=headers, timeout=10)
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
                                    response = requests.head(full_url, headers=headers, timeout=5)
                                    if response.status_code == 200:
                                        urls_to_search.append(full_url)
                                except:
                                    continue
                            break  # Found a match, no need to check other paths
                
        except Exception as e:
            pass
                
    except Exception as e:
        pass
    
    return urls_to_search

def extract_phone_numbers_from_website(url: str) -> list:
    """
    Extracts phone numbers from a business website by searching multiple pages.
    
    Args:
        url (str): The main URL of the business website
        
    Returns:
        list: List of unique phone numbers found across all pages
    """
    # Discover pages to search
    pages_to_search = discover_business_pages(url)
    
    all_phone_numbers = []
    
    for page_url in pages_to_search:
        try:
            # Scrape page content
            page_content = scrape_webpage_content(page_url)
            if page_content:
                # Extract phone numbers from this page
                page_phones = extract_phone_numbers(page_content)
                if page_phones:
                    all_phone_numbers.extend(page_phones)
        except Exception as e:
            continue
    
    # Remove duplicates and return
    unique_phones = list(set(all_phone_numbers))
    return unique_phones

def check_webpage_requirements(url: str, original_request: str, client) -> dict:
    """
    Visits a webpage and checks if it is a direct seller/deliverer.
    
    Args:
        url (str): The webpage URL to check
        original_request (str): The original user request (not used in analysis)
        client: Groq client instance
        
    Returns:
        dict: Analysis result with 'meets_requirements' boolean and 'reason' string
    """
    print(f"Checking webpage: {url}")
    
    # Scrape webpage content
    webpage_content = scrape_webpage_content(url)
    
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
        analysis_json = process_prompt_for_groq(client, prompt, model="llama-3.3-70b-versatile", response_format="json")
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

def refine_search_results(original_request: str, search_results: dict, client) -> list:
    """
    Refines the search results by visiting each webpage and checking if it meets requirements.
    
    Args:
        original_request (str): The original transcribed voice text.
        search_results (dict): The raw search results from SerpAPI.
        client: Groq client instance

    Returns:
        list: A list of dictionaries, each representing a business that meets requirements
              with 'title', 'url', and analysis details.
    """
    organic_results = search_results.get("organic_results", [])
    
    # Debug: Print the structure of organic_results
    print(f"Debug: organic_results type: {type(organic_results)}")
    if isinstance(organic_results, list) and organic_results:
        print(f"Debug: First result type: {type(organic_results[0])}")
        print(f"Debug: First result: {organic_results[0]}")
    elif isinstance(organic_results, dict):
        print(f"Debug: organic_results is a dict: {organic_results}")
        # Convert dict to list of dicts if possible
        organic_results = [organic_results]
    else:
        print(f"Debug: organic_results is empty or unknown type: {organic_results}")

    # Handle different result formats and extract URLs
    urls_to_check = []
    for r in organic_results:
        if isinstance(r, dict):
            title = r.get("title", r.get("name", "Unknown"))
            url = r.get("link", r.get("url", r.get("href", "")))
            if url:
                urls_to_check.append({"title": title, "url": url})
        elif isinstance(r, str):
            print(f"Debug: Skipping string result: {r}")
            continue
        else:
            print(f"Debug: Unknown result type: {type(r)}, value: {r}")
            continue

    if not urls_to_check:
        print("No valid URLs to check")
        return []

    print(f"\nChecking {len(urls_to_check)} webpages for direct seller qualification...")
    
    # First pass: Check if each webpage is a direct seller
    qualified_businesses = []
    for i, item in enumerate(urls_to_check[:10]):  # Limit to first 10 to avoid too many requests
        print(f"\n--- Checking webpage {i+1}/{min(len(urls_to_check), 10)} ---")
        
        analysis = check_webpage_requirements(item['url'], original_request, client)
        
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
            phone_numbers = extract_phone_numbers_from_website(business['url'])
            business['analysis']['phone_numbers'] = phone_numbers

    return qualified_businesses

def prompt_to_serp(params):
    search = GoogleSearch(params)
    results = search.get_dict()
    # For shopping queries, the key is 'shopping_results', not 'organic_results'
    if 'shopping_results' in results:
        return results['shopping_results']
    elif 'organic_results' in results:
        return results['organic_results']
    else:
        # Return the whole response for debugging if neither key is present
        return results

if __name__ == "__main__":
    # transcript_text_for_groq = "I need 5 packages of coffee beans by 11am on July 9th, 2025, delivered to Austin, Texas. The budget is 200 usd"
    transcript_text_for_groq = "I need 5 packages of cement by 11am on July 9th, 2025, delivered to Austin, Texas. The budget is 200 usd"
    
    load_dotenv()

    client_groq = Groq(
        api_key=os.environ.get("GROQ_API_KEY"),
    )
    
    print(f"\nProcessing request: '{transcript_text_for_groq}'")
    
    # Extract only product name and location for the search query
    search_query = extract_product_and_location(transcript_text_for_groq, client_groq)
    print(f"\n--- Searching with query: '{search_query}' ---")

    # Prepare SerpAPI parameters
    serp_params = {
        "q": search_query,
        "engine": "google",
        "api_key": API_KEY_SERP
    }

    # Get search results
    raw_results = prompt_to_serp(serp_params)
    
    # Refine results by visiting each webpage and checking requirements
    final_businesses = refine_search_results(transcript_text_for_groq, {"organic_results": raw_results}, client_groq)

    print(f"\nFound {len(final_businesses)} businesses that meet requirements.")

    print("\n--- Final Qualified Businesses ---")
    if final_businesses:
        for business in final_businesses:
            print(f"Title: {business.get('title')}")
            print(f"URL: {business.get('url')}")
            analysis = business.get('analysis', {})
            print(f"Reason: {analysis.get('reason', 'N/A')}")
            print(f"Product Listings: {analysis.get('product_listings', 'N/A')}")
            print(f"Pricing Info: {analysis.get('pricing_info', 'N/A')}")
            print(f"Purchase Options: {analysis.get('purchase_options', 'N/A')}")
            print(f"Contact Required: {analysis.get('contact_required', 'N/A')}")
            phone_numbers = analysis.get('phone_numbers', [])
            if phone_numbers:
                print(f"Phone Numbers: {', '.join(phone_numbers)}")
            else:
                print("Phone Numbers: None found")
            print()
    else:
        print("No direct sellers found.")

    # Write to a file
    with open("data.json", "w") as file:
        json.dump(final_businesses, file, indent=4)