import asyncio
from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.responses import StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydub import AudioSegment
import os
import logging
import httpx

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# D-ID API Basic Auth key
DID_KEY = "bmlja211aXJAeTdtYWlsLmNvbQ:PcR5zmW86VDsTLfdPwvJz"

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
@app.post("/stream-audio")
async def stream_audio(request: Request, body: dict = Body(...)):
    stream_id = body.get("stream_id")
    session_id = body.get("session_id")

    if not stream_id or not session_id:
        raise HTTPException(status_code=400, detail="stream_id and session_id are required in the request body.")

    async def generate():
        # Load and chunk audio
        audio = load_audio("audio.mp3")
        chunks = generate_chunks(audio)

        # Use host URL to generate chunk URLs
        host_url = f"https://{request.url.hostname}"

        async with httpx.AsyncClient() as client:
            for i, chunk in enumerate(chunks):
                filename = f"chunk_{i}.mp3"
                save_chunk_to_local(chunk, filename)
                chunk_url = f"{host_url}/get-chunk/{filename}"
                logging.debug(f"Generated chunk URL: {chunk_url}")

                # Add delay 3 seconds between chunks
                await asyncio.sleep(10)

                # Request body with session_id
                request_body = {
                    "script": {
                        "type": "audio",
                        "audio_url": chunk_url
                    },
                    "config": {
                        "stitch": True
                    },
                    "session_id": session_id,
                }

                # Send the chunk URL to D-ID API with Basic Auth
                response = await client.post(
                    f"https://api.d-id.com/talks/streams/{stream_id}",  # Use stream_id from the body
                    headers={
                        "Authorization": f"Basic {DID_KEY}",
                        "accept": "application/json",
                        "content-type": "application/json"
                    },
                    json=request_body
                )

                if response.status_code == 200:
                    logging.info(f"Chunk sent successfully to D-ID API: {chunk_url}")
                    yield f"data: success\n{chunk_url}\n\n"
                else:
                    logging.error(f"Failed to send chunk to D-ID API: {response.text}")
                    yield f"data: failure\n{chunk_url}\n\n"

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
