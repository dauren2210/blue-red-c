import asyncio
import websockets
import base64
from gtts import gTTS
from pydub import AudioSegment
import io
import os

# Configuration
TEXT_TO_SPEAK = "I need 300 cups of coffee by 11am on July 9th, 2025, delivered to Paris, 3 rue Dupré Saint-Gervais."
WEBSOCKET_URI = "ws://localhost:8000/ws/streaming"
OUTPUT_FILENAME_MP3 = "temp_audio.mp3"
OUTPUT_FILENAME_WAV = "test_audio.wav"
CHUNK_SIZE = 1024 * 4  # 4 KB

async def generate_audio():
    """
    Generates audio from text, converts it to the correct WAV format,
    and returns the path to the final audio file.
    """
    print("1. Generating audio from text using gTTS...")
    tts = gTTS(text=TEXT_TO_SPEAK, lang='en')
    tts.save(OUTPUT_FILENAME_MP3)
    print(f"   - Saved temporary MP3 file as {OUTPUT_FILENAME_MP3}")

    print("2. Converting MP3 to 16-bit, 16kHz mono WAV using pydub...")
    audio = AudioSegment.from_mp3(OUTPUT_FILENAME_MP3)
    audio = audio.set_frame_rate(16000)
    audio = audio.set_sample_width(2)  # 2 bytes = 16 bits
    audio = audio.set_channels(1)     # Mono
    
    audio.export(OUTPUT_FILENAME_WAV, format="wav")
    print(f"   - Saved final WAV file as {OUTPUT_FILENAME_WAV}")
    
    # Clean up the temporary mp3 file
    os.remove(OUTPUT_FILENAME_MP3)
    print(f"   - Removed temporary file {OUTPUT_FILENAME_MP3}")

    return OUTPUT_FILENAME_WAV

async def stream_audio(audio_path):
    """
    Connects to the WebSocket server and streams the audio file.
    """
    print(f"\n3. Connecting to WebSocket server at {WEBSOCKET_URI}...")
    try:
        async with websockets.connect(WEBSOCKET_URI) as websocket:
            print("   - Connection successful.")
            
            # 1. Send start message (optional, but good practice)
            await websocket.send('{"type": "start"}')
            print("   - Sent start message.")

            # 2. Stream audio data
            print("   - Streaming audio data...")
            with open(audio_path, "rb") as audio_file:
                while True:
                    chunk = audio_file.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    await websocket.send(chunk)
                    # Small sleep to simulate real-time streaming
                    await asyncio.sleep(0.1) 
            
            print("   - Finished sending audio data.")
            
            # 3. Send stop message
            await websocket.send('{"type": "stop"}')
            print("   - Sent stop message.")

            # 4. Receive and print responses from the server
            print("\n4. Receiving server responses...")
            try:
                while True:
                    response = await websocket.recv()
                    print(f"   - Received: {response}")
            except websockets.exceptions.ConnectionClosed:
                print("   - Server closed the connection.")

    except Exception as e:
        print(f"   - An error occurred: {e}")
        print("   - Please ensure the backend server is running and accessible.")

async def main():
    audio_file = await generate_audio()
    await stream_audio(audio_file)
    # Clean up the generated WAV file
    if os.path.exists(OUTPUT_FILENAME_WAV):
        os.remove(OUTPUT_FILENAME_WAV)
        print(f"\n5. Cleaned up {OUTPUT_FILENAME_WAV}.")

if __name__ == "__main__":
    asyncio.run(main()) 