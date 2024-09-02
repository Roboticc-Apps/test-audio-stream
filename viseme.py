import os
from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, SpeechSynthesisResult, ResultReason
from fastapi import FastAPI, HTTPException, Response

app = FastAPI()

# Konfigurasi Azure Speech SDK
SPEECH_KEY = os.getenv("SPEECH_KEY")
SPEECH_REGION = os.getenv("SPEECH_REGION")

@app.get("/get")
async def get_speech(text: str = "I'm excited to try text to speech"):
    try:
        # Mengatur konfigurasi speech
        speech_config = SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
        # speech_config.speech_synthesis_voice_name = f"ja-JP-{teacher}Neural"

        # Mengatur speech synthesizer
        synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=None)
        visemes = []

        def viseme_callback(evt):
            print(f"Viseme received: {evt.viseme_id} at offset {evt.audio_offset / 10000}")
            visemes.append([evt.audio_offset / 10000, evt.viseme_id])

        synthesizer.viseme_received.connect(viseme_callback)

        # Melakukan speech synthesis
        result: SpeechSynthesisResult = synthesizer.speak_text_async(text).get()

        # Memeriksa alasan hasil sintesis
        if result.reason == ResultReason.SynthesizingAudioCompleted:
            # Mengambil data audio dari hasil
            audio_data = result.audio_data

            # Mengatur header respons untuk data audio
            response = Response(content=audio_data, media_type="audio/mpeg")
            response.headers["Content-Disposition"] = "inline; filename=tts.mp3"
            response.headers["Visemes"] = str(visemes)

            return response
        else:
            raise HTTPException(status_code=500, detail=f"Speech synthesis failed with reason: {result.reason}")

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000, log_level="debug")
