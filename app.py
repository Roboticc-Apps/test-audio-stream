from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydub import AudioSegment
import os
import logging

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Directory for storing audio chunks
CHUNK_DIR = "audio_chunks"
if not os.path.exists(CHUNK_DIR):
    os.makedirs(CHUNK_DIR)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

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
async def stream_audio(request: Request):
    def generate():
        # Load and chunk audio
        audio = load_audio("audio.mp3")
        chunks = generate_chunks(audio)

        # Use host URL to generate chunk URLs
        host_url = f"https://{request.url.hostname}"

        for i, chunk in enumerate(chunks):
            filename = f"chunk_{i}.mp3"
            save_chunk_to_local(chunk, filename)
            chunk_url = f"{host_url}/get-chunk/{filename}"
            logging.debug(f"Generated chunk URL: {chunk_url}")
            yield f"data: {chunk_url}\n\n"

    return StreamingResponse(generate(), media_type='text/event-stream')

# Endpoint to access chunk audio allowing all HTTP methods
@app.api_route("/get-chunk/{filename}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def get_chunk(request: Request, filename: str):
    file_path = os.path.join(CHUNK_DIR, filename)
    if os.path.exists(file_path):
        if request.method == "HEAD":
            return Response(status_code=200)  # Respond with 200 OK for HEAD request
        logging.debug(f"Serving file: {file_path}")
        return StreamingResponse(open(file_path, "rb"), media_type="audio/mp3")
    else:
        logging.error(f"File not found: {file_path}")
        raise HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000, log_level="debug")
