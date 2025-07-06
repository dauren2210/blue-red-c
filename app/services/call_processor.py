import asyncio
import io
import wave
import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Optional, AsyncGenerator, List
from decimal import Decimal
from groq import AsyncGroq
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
import os

from app.core.config import settings
from app.services.language_processor import language_processor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CallProcessor:
    def __init__(self, call_sid: str, phone_number: str, request_prompt: str):
        self.call_sid = call_sid
        self.phone_number = phone_number
        self.request_prompt = request_prompt
        self.session_id = str(uuid.uuid4())
        
        # Initialize clients
        self.groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.stt_model = "whisper-large-v3"
        self.tts_model = "llama3-8b-8192"
        
        # Twilio client
        self.twilio_client = self._get_twilio_client()
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER")
        
        # Audio processing
        self.audio_buffer = bytearray()
        self.is_conversation_active = False
        self.conversation_history = []
        self.full_conversation_history = []  # Keep full history in memory
        
        # Call tracking
        self.call_start_time = datetime.now()
        self.max_call_duration = 300  # 5 minutes max call duration
        self.key_information_collected = {
            "availability": None,
            "price": None,
            "comments": []
        }
        
        # Conversation system prompt for supplier calls
        self.conversation_prompt = f"""You are an AI assistant calling a supplier to gather specific information about a product or service request.

REQUEST DETAILS: {request_prompt}

YOUR GOALS:
1. FIRST PRIORITY: Determine if the supplier can provide the requested product/service in the specified amount, date, and location
   - If they CANNOT provide it, politely end the conversation and mark availability as False
   - If they CAN provide it, mark availability as True and proceed to price inquiry

2. SECOND PRIORITY: Get the exact price for the requested product/service
   - Ask for the total price including any additional costs
   - Be specific about the quantity and specifications mentioned in the request

3. ADDITIONAL INFORMATION: Collect any other relevant details in the comments section

CONVERSATION GUIDELINES:
- Be professional, polite, and concise
- Use clear, direct questions
- If supplier cannot provide the service, politely say: "Thank you for your time. I understand you cannot provide this service. Have a great day!"
- If you get the key information (availability and price), politely end the conversation
- Keep responses under 30 seconds when spoken
- Always use "Alice" voice for TTS

RESPONSE FORMAT:
- Focus on getting availability first, then price
- Be direct and business-like
- End conversation once you have both availability and price information"""

    def _get_twilio_client(self) -> Client:
        """Initialize and return Twilio client"""
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        
        if not all([account_sid, auth_token]):
            raise Exception("Twilio configuration missing: TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN")
        
        return Client(account_sid, auth_token)

    def add_audio_chunk(self, chunk: bytes):
        """Add audio chunk to buffer for processing"""
        self.audio_buffer.extend(chunk)
        logger.info(f"Call {self.call_sid}: Audio chunk added. Buffer size: {len(self.audio_buffer)} bytes")

    def _package_audio_as_wav(self) -> bytes:
        """Package raw audio buffer into WAV format"""
        with io.BytesIO() as wav_buffer:
            with wave.open(wav_buffer, 'wb') as wf:
                wf.setnchannels(1)  # Mono
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(16000)  # 16kHz
                wf.writeframes(self.audio_buffer)
            return wav_buffer.getvalue()

    async def transcribe_audio(self) -> Optional[str]:
        """Transcribe audio buffer to text using Groq Whisper"""
        if not self.audio_buffer:
            return None
            
        try:
            wav_data = self._package_audio_as_wav()
            logger.info(f"Call {self.call_sid}: Transcribing {len(wav_data)} bytes of audio")
            
            transcription_response = await self.groq_client.audio.transcriptions.create(
                file=("audio.wav", wav_data),
                model=self.stt_model
            )
            
            transcript = transcription_response.text.strip()
            logger.info(f"Call {self.call_sid}: Transcribed: '{transcript}'")
            
            # Clear buffer after successful transcription
            self.audio_buffer.clear()
            
            return transcript if transcript else None
            
        except Exception as e:
            logger.error(f"Call {self.call_sid}: Transcription error: {e}")
            return None

    async def generate_response(self, user_input: str) -> str:
        """Generate AI response using Groq LLM"""
        try:
            # Add user input to both conversation histories
            self.conversation_history.append({"role": "user", "content": user_input})
            self.full_conversation_history.append({"role": "user", "content": user_input})
            
            # Check if call duration exceeded
            if (datetime.now() - self.call_start_time).seconds > self.max_call_duration:
                return "Thank you for your time. I need to end this call now. Have a great day!"
            
            # Prepare messages for the LLM (use recent history for context management)
            messages = [
                {"role": "system", "content": self.conversation_prompt}
            ]
            
            # Add conversation history (keep last 10 exchanges to manage context)
            recent_history = self.conversation_history[-10:]
            messages.extend(recent_history)
            
            logger.info(f"Call {self.call_sid}: Generating response for: '{user_input}'")
            
            chat_completion = await self.groq_client.chat.completions.create(
                messages=messages,
                model=self.tts_model,
                temperature=0.7,
                max_tokens=150,  # Keep responses concise for phone calls
                top_p=1,
                stop=None,
                stream=False,
            )
            
            response = chat_completion.choices[0].message.content.strip()
            
            # Add AI response to both conversation histories
            self.conversation_history.append({"role": "assistant", "content": response})
            self.full_conversation_history.append({"role": "assistant", "content": response})
            
            logger.info(f"Call {self.call_sid}: Generated response: '{response}'")
            return response
            
        except Exception as e:
            logger.error(f"Call {self.call_sid}: Response generation error: {e}")
            return "I'm sorry, I'm having trouble processing that. Could you please repeat?"

    async def text_to_speech(self, text: str) -> str:
        """Convert text to speech using Twilio TTS (returns TwiML)"""
        try:
            logger.info(f"Call {self.call_sid}: Converting to speech: '{text}'")
            
            # Return TwiML with Alice voice for TTS
            twiml = f"""
            <Response>
                <Say voice="alice">{text}</Say>
            </Response>
            """
            
            return twiml
            
        except Exception as e:
            logger.error(f"Call {self.call_sid}: TTS error: {e}")
            return f"""
            <Response>
                <Say voice="alice">I'm sorry, I'm having trouble speaking right now.</Say>
            </Response>
            """

    async def update_twilio_call(self, twiml: str):
        """Update the Twilio call with new TwiML"""
        try:
            # Update the call with new TwiML
            call = self.twilio_client.calls(self.call_sid).update(twiml=twiml)
            logger.info(f"Call {self.call_sid}: Updated with new TwiML")
            return call
        except TwilioException as e:
            logger.error(f"Call {self.call_sid}: Twilio update error: {e}")
            raise

    async def start_conversation(self):
        """Start the conversation by making the initial call"""
        try:
            # Create initial TwiML with greeting
            initial_message = f"Hello! I'm calling regarding a product or service inquiry. I have a request for: {self.request_prompt}. Can you help me with this?"
            
            twiml = f"""
            <Response>
                <Say voice="alice">{initial_message}</Say>
                <Record 
                    action="/twilio/webhook/{self.call_sid}" 
                    method="POST"
                    maxLength="30"
                    playBeep="false"
                    trim="trim-silence"
                    recordingStatusCallback="/twilio/recording-status/{self.call_sid}"
                    recordingStatusCallbackMethod="POST"
                />
            </Response>
            """
            
            # Make the call
            call = self.twilio_client.calls.create(
                twiml=twiml,
                to=self.phone_number,
                from_=self.from_number,
                status_callback=f"/twilio/call-status/{self.call_sid}",
                status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
                status_callback_method='POST'
            )
            
            self.call_sid = call.sid
            self.is_conversation_active = True
            
            logger.info(f"Call {self.call_sid}: Conversation started with {self.phone_number}")
            return call.sid
            
        except Exception as e:
            logger.error(f"Call {self.call_sid}: Failed to start conversation: {e}")
            raise

    async def process_user_input(self, audio_data: bytes) -> str:
        """Process user audio input and return AI response"""
        try:
            # Add audio to buffer
            self.add_audio_chunk(audio_data)
            
            # Transcribe audio
            transcript = await self.transcribe_audio()
            if not transcript:
                return "I didn't catch that. Could you please repeat?"
            
            # Generate AI response
            response = await self.generate_response(transcript)
            
            return response
            
        except Exception as e:
            logger.error(f"Call {self.call_sid}: Error processing user input: {e}")
            return "I'm sorry, I'm having trouble understanding. Could you please try again?"

    async def end_conversation(self):
        """End the conversation gracefully"""
        try:
            goodbye_message = "Thank you for your time. Have a great day!"
            
            twiml = f"""
            <Response>
                <Say voice="alice">{goodbye_message}</Say>
                <Hangup/>
            </Response>
            """
            
            await self.update_twilio_call(twiml)
            self.is_conversation_active = False
            
            logger.info(f"Call {self.call_sid}: Conversation ended")
            
        except Exception as e:
            logger.error(f"Call {self.call_sid}: Error ending conversation: {e}")

    async def extract_supplier_data(self) -> dict:
        """Extract structured supplier data from the conversation"""
        try:
            # Combine all user inputs from full conversation history
            user_inputs = [
                msg["content"] for msg in self.full_conversation_history 
                if msg["role"] == "user"
            ]
            
            if not user_inputs:
                return {
                    "available": None,
                    "price": None,
                    "comments": []
                }
            
            full_transcript = " ".join(user_inputs)
            
            # Use a specialized prompt to extract supplier information
            supplier_extraction_prompt = f"""
            You are analyzing a conversation with a supplier about this request: {self.request_prompt}
            
            CONVERSATION TRANSCRIPT: {full_transcript}
            
            Extract the following information and respond ONLY with a JSON object:
            {{
                "available": true/false/null (whether supplier can provide the service/product),
                "price": decimal/null (exact price in decimal format, e.g., 150.50),
                "comments": [
                    {{"type": "string", "content": "string"}}
                ] (any additional relevant information)
            }}
            
            RULES:
            - If supplier clearly says they CANNOT provide the service, set available to false
            - If supplier says they CAN provide it, set available to true
            - Extract exact price including currency if mentioned
            - Put any other relevant details in comments
            - If information is unclear, use null values
            """
            
            chat_completion = await self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": supplier_extraction_prompt}
                ],
                model=self.tts_model,
                temperature=0,
                max_tokens=500,
                top_p=1,
                stop=None,
                stream=False,
            )
            
            response_content = chat_completion.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                supplier_data = json.loads(response_content)
                
                # Ensure proper structure
                result = {
                    "available": supplier_data.get("available"),
                    "price": supplier_data.get("price"),
                    "comments": supplier_data.get("comments", [])
                }
                
                logger.info(f"Call {self.call_sid}: Extracted supplier data: {result}")
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Call {self.call_sid}: Failed to parse supplier data JSON: {e}")
                return {
                    "available": None,
                    "price": None,
                    "comments": [{"type": "error", "content": "Failed to parse supplier response"}]
                }
            
        except Exception as e:
            logger.error(f"Call {self.call_sid}: Error extracting supplier data: {e}")
            return {
                "available": None,
                "price": None,
                "comments": [{"type": "error", "content": f"Error extracting data: {str(e)}"}]
            }

    async def extract_final_needs(self) -> dict:
        """Extract structured supplier data from the conversation"""
        return await self.extract_supplier_data()

# Dictionary to store active call processors
active_calls: Dict[str, CallProcessor] = {}

def get_call_processor(call_sid: str) -> Optional[CallProcessor]:
    """Get call processor by call SID"""
    return active_calls.get(call_sid)

def add_call_processor(call_sid: str, processor: CallProcessor):
    """Add call processor to active calls"""
    active_calls[call_sid] = processor

def remove_call_processor(call_sid: str):
    """Remove call processor from active calls"""
    if call_sid in active_calls:
        del active_calls[call_sid] 