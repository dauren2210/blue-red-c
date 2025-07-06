#!/usr/bin/env python3
"""
Example script demonstrating how to use the CallProcessor for AI phone conversations.

This script shows how to:
1. Create a call processor with a specific request prompt
2. Start a conversation with a phone number
3. Handle the conversation flow

Usage:
    python example_call.py
"""

import asyncio
import os
from app.services.call_processor import CallProcessor

async def example_conversation():
    """Example of how to use the CallProcessor"""
    
    # Set up environment variables (you would normally do this in your .env file)
    os.environ["GROQ_API_KEY"] = "your_groq_api_key_here"
    os.environ["TWILIO_ACCOUNT_SID"] = "your_twilio_account_sid"
    os.environ["TWILIO_AUTH_TOKEN"] = "your_twilio_auth_token"
    os.environ["TWILIO_PHONE_NUMBER"] = "+1234567890"  # Your Twilio phone number
    
    # Example request prompt for supplier inquiry
    request_prompt = "Need 50 office chairs for delivery on March 15th to 123 Business Ave, Downtown. Looking for ergonomic chairs with adjustable height and armrests."
    
    # Phone number to call (replace with actual number)
    phone_number = "+1234567890"
    
    try:
        # Create call processor
        call_processor = CallProcessor(
            call_sid="",  # Will be set after call creation
            phone_number=phone_number,
            request_prompt=request_prompt
        )
        
        print(f"Starting supplier inquiry call with {phone_number}")
        print(f"Request details: {request_prompt}")
        
        # Start the conversation
        call_sid = await call_processor.start_conversation()
        print(f"Call initiated with SID: {call_sid}")
        
        # In a real application, the conversation would continue via webhooks
        # This is just a demonstration of the setup
        
        print("Supplier inquiry started! The AI will now:")
        print("1. Ask if the supplier can provide the requested product/service")
        print("2. Get the exact price if available")
        print("3. Collect any additional relevant information")
        print("4. End the call politely once all information is gathered")
        
        # Wait a bit to simulate the call duration
        await asyncio.sleep(5)
        
        # Extract supplier data (this would normally happen when the call ends)
        print("Extracting supplier data from conversation...")
        supplier_data = await call_processor.extract_supplier_data()
        print(f"Extracted supplier data: {supplier_data}")
        
        # End the conversation
        await call_processor.end_conversation()
        print("Supplier inquiry completed.")
        
    except Exception as e:
        print(f"Error during conversation: {e}")

if __name__ == "__main__":
    # Run the example
    asyncio.run(example_conversation()) 