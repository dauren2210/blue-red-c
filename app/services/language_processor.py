import yaml
from groq import AsyncGroq
from app.core.config import settings
from typing import Optional, Dict, Any, List

class LanguageProcessor:
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.default_model = "llama3-8b-8192"
        self.default_system_prompt = """You are an expert order processing assistant. Your task is to extract key details from a user's request and format them as a YAML object.

The fields to extract are:
- 'product_name': The name of the product requested.
- 'amount': The quantity of the product.
- 'date_and_time': The delivery date and time.
- 'location': The delivery address.
- 'comment': Any other relevant details or special instructions.
- 'search_query': A concise and effective search engine query to find suppliers for the requested product in the specified location, including a request for their phone number and address.

If a value for a field is not mentioned, omit the field. Respond ONLY with the YAML object and nothing else.
---
**Search Query Guidelines:**
- The `search_query` should be optimized to find local businesses.
- It should be phrased naturally, as a human would type into Google Maps.
- Use the product name and the location.
- Examples:
  - If the user asks for "coffee in Paris," a good query would be "coffee suppliers in Paris."
  - If the user provides a full address like "3 Rue Dupré-Saint-Gervais, Paris," a good query would be "coffee suppliers near 3 Rue Dupré-Saint-Gervais, Paris."
- Do NOT add extra terms like "phone number" or "address" to the query itself; the search service handles this.
"""

    async def process_prompt(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        response_format: str = "text",
        model: Optional[str] = None,
    ) -> str:
        if model is None:
            model = self.default_model

        messages: List[Dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        try:
            request_params = {
                "messages": messages,
                "model": model,
                "temperature": 0,
                "max_tokens": 2048,  # Increased for webpage analysis
                "top_p": 1,
                "stop": None,
                "stream": False,
            }
            if response_format == "json":
                request_params["response_format"] = {"type": "json_object"}

            chat_completion = await self.client.chat.completions.create(**request_params)

            response_content = chat_completion.choices[0].message.content
            if response_content is None:
                raise ValueError("Received None response from Groq API")
            
            return response_content

        except Exception as e:
            print(f"An error occurred while processing prompt: {e}")
            return ""

    async def extract_structured_data(self, transcript: str) -> dict:
        try:
            response_content = await self.process_prompt(
                system_prompt=self.default_system_prompt,
                user_prompt=transcript,
            )
            
            if not response_content:
                return {}

            # The model might sometimes include the yaml ``` markers, so we strip them
            clean_yaml_str = response_content.strip().replace("```yaml", "").replace("```", "").strip()
            
            structured_data = yaml.safe_load(clean_yaml_str)
            return structured_data if isinstance(structured_data, dict) else {}

        except Exception as e:
            print(f"An error occurred while extracting structured data: {e}")
            return {}

# Singleton instance
language_processor = LanguageProcessor() 