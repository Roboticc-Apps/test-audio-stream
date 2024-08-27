from flask import Flask, Response, send_file
from pydub import AudioSegment
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins

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
@app.route('/stream-audio', methods=['GET'])
def stream_audio():
    def generate():
        # Load and chunk audio
        audio = load_audio("audio.mp3")
        chunks = generate_chunks(audio)

        for i, chunk in enumerate(chunks):
            filename = f"chunk_{i}.mp3"
            save_chunk_to_local(chunk, filename)
            chunk_url = f"http://localhost:5000/get-chunk/{filename}"
            yield f"data: {chunk_url}\n\n"

    return Response(generate(), mimetype='text/event-stream')

# Endpoint to access chunk audio
@app.route('/get-chunk/<filename>', methods=['GET'])
def get_chunk(filename):
    file_path = os.path.join(CHUNK_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path, mimetype="audio/mp3")
    else:
        return "File not found", 404

if __name__ == "__main__":
    app.run(port=5000, debug=True)
