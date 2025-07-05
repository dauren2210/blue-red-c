import yaml
from groq import AsyncGroq
from app.core.config import settings

class LanguageProcessor:
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = "llama3-8b-8192"
        self.system_prompt = """You are an expert order processing assistant. Your task is to extract key details from a user's request and format them as a YAML object.

The fields to extract are:
- 'product_name': The name of the product requested.
- 'amount': The quantity of the product.
- 'date_and_time': The delivery date and time.
- 'location': The delivery address.
- 'comment': Any other relevant details or special instructions.
- 'search_query': A concise and effective search engine query to find suppliers for the requested product in the specified location, including a request for their phone number and address.

If a value for a field is not mentioned, omit the field. Respond ONLY with the YAML object and nothing else.
"""

    async def extract_structured_data(self, transcript: str) -> dict:
        try:
            chat_completion = await self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompt,
                    },
                    {
                        "role": "user",
                        "content": transcript,
                    },
                ],
                model=self.model,
                temperature=0,
                max_tokens=1024,
                top_p=1,
                stop=None,
                stream=False,
            )
            
            response_content = chat_completion.choices[0].message.content
            # The model might sometimes include the yaml ``` markers, so we strip them
            clean_yaml_str = response_content.strip().replace("```yaml", "").replace("```", "").strip()
            
            structured_data = yaml.safe_load(clean_yaml_str)
            return structured_data if isinstance(structured_data, dict) else {}

        except Exception as e:
            print(f"An error occurred while extracting structured data: {e}")
            return {}

# Singleton instance
language_processor = LanguageProcessor() 