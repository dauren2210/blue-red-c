# Call Processor Documentation

## Overview

The Call Processor is a comprehensive system that enables AI-powered supplier inquiry calls using Twilio, Groq's speech-to-text, and LLM capabilities. It allows you to create intelligent phone calls where an AI agent can gather specific information from suppliers about product availability, pricing, and other relevant details.

## Features

- **Real-time Speech-to-Text**: Uses Groq's Whisper model for accurate transcription
- **AI Supplier Inquiries**: Uses Groq's Llama3-8b-8192 model for natural supplier conversations
- **Twilio TTS Integration**: Uses Twilio's Alice voice for all speech output
- **Structured Supplier Data**: Extracts availability, pricing, and additional information
- **Background Processing**: Handles calls asynchronously
- **Call Duration Management**: Automatically ends calls after 5 minutes
- **Full Conversation History**: Maintains complete conversation history while using recent context for LLM

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Twilio Call   │───▶│  Call Processor  │───▶│   Groq LLM      │
│                 │    │                  │    │                 │
│ - Voice Input   │    │ - Audio Buffer   │    │ - Response Gen  │
│ - Recording     │    │ - Transcription  │    │ - Conversation  │
│ - Webhooks      │    │ - Call Management│    │ - Data Extract  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │  Language Proc   │
                       │                  │
                       │ - YAML Output    │
                       │ - Structured Data│
                       └──────────────────┘
```

## Setup

### 1. Environment Variables

Set the following environment variables:

```bash
# Groq API
GROQ_API_KEY=your_groq_api_key_here

# Twilio Configuration
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890  # Your Twilio phone number
```

### 2. Dependencies

The required dependencies are already included in `requirements.txt`:

```
groq
twilio
requests
aiofiles
```

## Usage

### 1. Making a Call via API

```python
import requests

# Start a supplier inquiry call
response = requests.post("http://localhost:8000/twilio/voice-call", json={
    "phone_number": "+1234567890",
    "request_prompt": "Need 50 office chairs for delivery on March 15th to 123 Business Ave, Downtown. Looking for ergonomic chairs with adjustable height and armrests.",
    "callback_url": "https://your-domain.com/webhooks/twilio"
})

print(response.json())
# Output: {"task_id": "uuid", "status": "queued", "message": "Voice call task created successfully..."}
```

### 2. Direct Usage with CallProcessor

```python
from app.services.call_processor import CallProcessor

# Create a call processor
call_processor = CallProcessor(
    call_sid="",
    phone_number="+1234567890",
    request_prompt="Need 50 office chairs for delivery on March 15th to 123 Business Ave, Downtown"
)

# Start the conversation
call_sid = await call_processor.start_conversation()

# The conversation will continue via Twilio webhooks
# When the call ends, extract the supplier data
supplier_data = await call_processor.extract_supplier_data()
```

## API Endpoints

### POST /twilio/voice-call

Creates a new AI conversation call.

**Request Body:**
```json
{
    "phone_number": "+1234567890",
    "request_prompt": "Detailed description of the product/service needed, including quantity, delivery date, location, and specifications",
    "callback_url": "https://your-domain.com/webhooks/twilio"
}
```

**Response:**
```json
{
    "task_id": "uuid",
    "status": "queued",
    "message": "Voice call task created successfully"
}
```

### POST /twilio/webhook/{call_sid}

Handles Twilio webhooks for call interactions (recording processing, AI responses).

### POST /twilio/recording-status/{call_sid}

Handles recording status updates from Twilio.

### POST /twilio/call-status/{call_sid}

Handles call status updates (answered, completed, failed, etc.).

### GET /twilio/health

Health check endpoint for the Twilio API module.

## Conversation Flow

1. **Call Initiation**: User requests a supplier inquiry call via API
2. **Call Setup**: Twilio initiates the call to the supplier's number
3. **Greeting**: AI introduces itself and explains the inquiry purpose
4. **Availability Check**: AI asks if supplier can provide the requested product/service
5. **Price Inquiry**: If available, AI asks for the exact price
6. **Additional Info**: AI collects any other relevant details
7. **Loop**: Steps 4-6 repeat until all information is gathered
8. **Data Extraction**: Final supplier data (availability, price, comments) is extracted
9. **Call End**: AI politely ends the conversation

## Webhook Configuration

To receive Twilio webhooks, your server needs to be publicly accessible. You can use ngrok for development:

```bash
ngrok http 8000
```

Then update your callback URLs to use the ngrok URL.

## Error Handling

The system includes comprehensive error handling:

- **Twilio Errors**: Network issues, invalid phone numbers, etc.
- **Groq API Errors**: Rate limits, authentication issues, etc.
- **Audio Processing Errors**: Invalid audio formats, transcription failures
- **LLM Errors**: Model unavailability, response generation failures

## Monitoring and Logging

All operations are logged with appropriate levels:

- **INFO**: Normal operations (call start, transcription, responses)
- **WARNING**: Non-critical issues (empty audio, missing data)
- **ERROR**: Critical failures (API errors, call failures)

## Security Considerations

1. **API Keys**: Store Twilio and Groq API keys securely
2. **Webhook Validation**: Validate Twilio webhook signatures
3. **Rate Limiting**: Implement rate limiting for API endpoints
4. **Phone Number Validation**: Validate phone numbers before making calls
5. **Data Privacy**: Handle conversation data according to privacy regulations

## Limitations

1. **TTS Integration**: Currently uses Twilio's built-in TTS. For more natural speech, consider integrating with services like ElevenLabs or Azure Cognitive Services.
2. **Audio Download**: The current implementation includes placeholders for audio download from Twilio recordings.
3. **Real-time Processing**: The system processes audio in chunks rather than real-time streaming.

## Future Enhancements

1. **Real-time Streaming**: Implement real-time audio processing
2. **Advanced TTS**: Integrate with high-quality TTS services
3. **Multi-language Support**: Add support for multiple languages
4. **Call Analytics**: Add detailed call analytics and reporting
5. **Custom Voice Models**: Support for custom voice models
6. **Conversation Memory**: Persistent conversation history across sessions

## Troubleshooting

### Common Issues

1. **Call Not Connecting**: Check Twilio credentials and phone number format
2. **No Audio Transcription**: Verify Groq API key and audio format
3. **Webhook Not Receiving**: Ensure server is publicly accessible
4. **LLM Not Responding**: Check Groq API limits and model availability

### Debug Mode

Enable debug logging by setting the log level:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Example Use Cases

1. **Supplier Inquiries**: Checking product availability and pricing
2. **Vendor Management**: Automated vendor communication
3. **Procurement**: Gathering quotes from multiple suppliers
4. **Inventory Checks**: Verifying stock levels with suppliers
5. **Delivery Coordination**: Confirming delivery schedules
6. **Service Quotes**: Getting quotes for professional services 