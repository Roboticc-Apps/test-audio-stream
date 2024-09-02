import asyncio
import os
import json
from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, SpeechSynthesisResult, ResultReason
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

app = FastAPI()

# Azure Speech SDK configuration
SPEECH_KEY = os.getenv("SPEECH_KEY")
SPEECH_REGION = os.getenv("SPEECH_REGION")

# Texts to be synthesized
texts = [
    "Hello, how are you?",
    "I am fine, thank you.",
    "What are you doing?",
    "I am working on a project.",
    "That's great! Keep up the good work."
]

@app.get("/stream-visemes")
async def stream_visemes():
    try:
        # Configure speech
        speech_config = SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)

        # Set up the speech synthesizer
        synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=None)
        visemes = []

        def viseme_callback(evt):
            visemes.append([evt.audio_offset / 10000, evt.viseme_id])

        synthesizer.viseme_received.connect(viseme_callback)

        # Generate visemes from text
        async def viseme_generator():
            for text in texts:
                result: SpeechSynthesisResult = synthesizer.speak_text_async(text).get()

                if result.reason == ResultReason.SynthesizingAudioCompleted:
                    # Send the visemes received
                    response_data = {
                        "text": text,
                        "visemes": visemes
                    }
                    yield json.dumps(response_data) + '\n\n'
                    visemes.clear()  # Clear visemes for the next text
                else:
                    raise HTTPException(status_code=500, detail=f"Speech synthesis failed with reason: {result.reason}")
                
                # Delay between texts (if needed)
                await asyncio.sleep(5)  # Adjust delay as needed

        # Create streaming response
        response = StreamingResponse(viseme_generator(), media_type="text/event-stream")

        return response

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000, log_level="debug")
