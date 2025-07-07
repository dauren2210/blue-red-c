import yaml
from groq import AsyncGroq
from app.core.config import settings
from app.models.call_log import CallLog
from typing import Dict, List, Optional
from app.crud.crud_session import get_last_session

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
        # Store conversation history and structured_request per call SID
        self.sid_conversations: Dict[str, Dict] = {}

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

    def create_sid(self, sid: str, structured_request: dict):
        """Initialize a conversation for a new call SID with the structured request."""
        self.sid_conversations[sid] = {
            "history": [],
            "structured_request": structured_request
        }

    async def supplier_key_data_prompt(self, sid: str, last_supplier_message: str) -> Optional[dict]:
        """
        Use the conversation history and structured_request for the call SID to prompt the LLM to extract:
        - available: true/false/none
        - price: decimal
        And generate a short, polite response (max 2 sentences, short for speech).
        If unavailable, response should politely end the call.
        Returns a dict: { 'available': ..., 'price': ..., 'response': ... }
        """
        if sid not in self.sid_conversations:
            last_session = await get_last_session()
            if last_session is None:
                raise ValueError("No last session found")
            self.create_sid(sid, last_session.structured_request)
        history: List[dict] = self.sid_conversations[sid]["history"]
        structured_request = self.sid_conversations[sid]["structured_request"]

        # Add the last message to the history
        history.append({"role": "supplier", "content": last_supplier_message})

        # Compose the prompt
        prompt = f"""
You are a helpful assistant in a phone call with a supplier. The original request is:
{structured_request}

Conversation so far:
"""
        for turn in history:
            prompt += f"{turn['role']}: {turn['content']}\n"
        prompt += """
        Analyze the conversation so far and determine if the supplier is available to fulfill the request.
        If available, extract the price and generate a short, polite response (max 2 sentences, short for speech).
        If unavailable, respond politely and end the call.

        You should understand if the requested goods or services are available to be purchased.
        After that find out the price that the supplier is willing to sell the goods or services for.
        
        Your task now is to generate a response to last message from the supplier, while following your main goals.
        """
        try:
            chat_completion = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant for phone calls with suppliers."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0,
                max_tokens=256,
                top_p=1,
                stop=None,
                stream=False,
            )

            response_content = chat_completion.choices[0].message.content
                
            history.append({"role": "assistant", "content": response_content})
            self.sid_conversations[sid]["history"] = history
            return response_content
        except Exception as e:
            print(f"An error occurred in supplier_key_data_prompt: {e}")
            return None

# Singleton instance
language_processor = LanguageProcessor() 