import yaml
from groq import AsyncGroq
from app.core.config import settings
from app.models.call_log import CallLog
from typing import Dict, List, Optional
from app.crud.crud_session import get_last_session
import logging

logging.basicConfig(level=logging.INFO)

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

    def create_sid(self, sid: str, structured_request: dict, supplier_phone: str):
        """Initialize a conversation for a new call SID with the structured request."""
        self.sid_conversations[sid] = {
            "history": [],
            "structured_request": structured_request,
            "supplier_phone": supplier_phone
        }

    async def supplier_key_data_prompt(self, sid: str, last_supplier_message: str) -> Optional[dict]:
        """
        Use the conversation history and structured_request for the call SID to prompt the LLM to extract:
        - available: true/false/none
        - price: decimal
        And generate a short, polite response (max 2 sentences, short for speech).
        If unavailable, response should politely end the call.
        Returns a dict: text to be spoken to the supplier.
        """
        
        history: List[dict] = self.sid_conversations[sid]["history"]
        structured_request = self.sid_conversations[sid]["structured_request"]

        # Add the last message to the history
        history.append({"role": "supplier", "content": last_supplier_message})

        # Compose the prompt
        prompt = f"""
You are a helpful assistant in a phone call with a supplier. 
The original request of a person you are speaking on behalf of is to find a supplier for specific product in the specified amount.
You should speak to a supplier to find out if they can provide requested goods described in the following description:
<START of original_request>
{structured_request}
<END of original_request>

<START of conversation history>
"""
        for turn in history:
            prompt += f"{turn['role']}: {turn['content']}\n"
        prompt += """
<END of conversation history>

Based on the conversation history and original request generate a response to the last message.
Keep your reply short.
If in the conversation history the product is not stated, state the requested product and inquire if it is available.
If in the conversation history the amount is not stated, state the amount of the requested product and inquire if it is available.
If the place and time is not stated in the conversation history, state it and inquire if it a shipment is available.

If product name, amount, place and time are all stated, end the conversation stating that we will contact the person shortly.

You should understand if the requested goods or services are available to be purchased.
After that find out the price that the supplier is willing to sell the goods or services for.

If the person occurs to be in a confusion state the goods from the original request once more.
The person on the other end is a human being, they do not see the full history of your conversation with them.

Your task now is to generate a JSON object with the following fields:
- original_request: use text from <original request> part of this text as a summary of the original request
- reply_to_user: a polite message to the user, maximum 15 words
Respond ONLY with the JSON object and nothing else.
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
            logging.info(f"LLM generated response: {response_content}")
            import json
            try:
                result = json.loads(response_content)
            except Exception:
                import re
                match = re.search(r'\{.*\}', response_content, re.DOTALL)
                if match:
                    result = json.loads(match.group(0))
                else:
                    result = {"original_request": str(structured_request), "reply_to_user": response_content}
            # Only append the reply_to_user to the history
            reply_to_user = result.get("reply_to_user", "Sorry, I'm having technical issues understanding what to reply to you. I will call you later. Thank you!")
            history.append({"role": "assistant", "content": reply_to_user})
            self.sid_conversations[sid]["history"] = history
            return reply_to_user
        except Exception as e:
            print(f"An error occurred in supplier_key_data_prompt: {e}")
            return None

# Singleton instance
language_processor = LanguageProcessor() 