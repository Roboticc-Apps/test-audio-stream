from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydub import AudioSegment
import os

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (adjust as needed for production)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Directory for storing audio chunks
CHUNK_DIR = "audio_chunks"
if not os.path.exists(CHUNK_DIR):
    os.makedirs(CHUNK_DIR)

# Load audio file (using a static file for testing)
def load_audio(file_path):
    return AudioSegment.from_file(file_path)

# Generate audio chunks
def generate_chunks(audio, chunk_size=5000):
    return [audio[i:i+chunk_size] for i in range(0, len(audio), chunk_size)]

# Save chunk to local file
def save_chunk_to_local(chunk, filename):
    file_path = os.path.join(CHUNK_DIR, filename)
    chunk.export(file_path, format="mp3")
    return file_path

# Streaming endpoint
@app.get("/stream-audio")
async def stream_audio():
    async def generate():
        # Load and chunk audio
        audio = load_audio("audio.mp3")
        chunks = generate_chunks(audio)

        for i, chunk in enumerate(chunks):
            filename = f"chunk_{i}.mp3"
            save_chunk_to_local(chunk, filename)
            chunk_url = f"http://localhost:5000/get-chunk/{filename}"
            yield f"data: {chunk_url}\n\n"

    return StreamingResponse(generate(), media_type='text/event-stream')

# Endpoint to access chunk audio
@app.get("/get-chunk/{filename}")
async def get_chunk(filename: str):
    file_path = os.path.join(CHUNK_DIR, filename)
    if os.path.exists(file_path):
        return StreamingResponse(open(file_path, "rb"), media_type="audio/mp3")
    else:
        raise HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=5000, log_level="debug")
