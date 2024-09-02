from pydub import AudioSegment

# Load file MP3 dan konversi ke WAV
audio = AudioSegment.from_mp3("audio.mp3")
audio.export("audio.wav", format="wav")
