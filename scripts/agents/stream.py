import base64, os, subprocess, openai
from dotenv import load_dotenv

load_dotenv()
client = openai.Client(api_key=os.getenv("BOSON_API_KEY"), base_url="https://hackathon.boson.ai/v1")

messages = [
    {"role": "system", "content": "Convert the following text from the user into speech."},
    {"role": "user", "content": "Hello from Boson AI! Live streaming test."},
]

# ffplay reads raw PCM16 @ 24 kHz from stdin
proc = subprocess.Popen(
    ["ffplay", "-f", "s16le", "-ar", "24000", "-i", "-", "-nodisp", "-autoexit", "-loglevel", "error"],
    stdin=subprocess.PIPE,
)

try:
    stream = client.chat.completions.create(
        model="higgs-audio-generation-Hackathon",
        messages=messages,
        modalities=["text", "audio"],
        audio={"format": "pcm16"},  # raw PCM16 chunks
        stream=True,
        max_completion_tokens=300,
    )

    for chunk in stream:
        if proc.poll() is not None:
            break
        delta = getattr(chunk.choices[0], "delta", None)
        audio = getattr(delta, "audio", None)
        if not audio:
            continue
        data = base64.b64decode(audio["data"])
        proc.stdin.write(data)
        proc.stdin.flush()
finally:
    if proc.stdin:
        try: proc.stdin.close()
        except BrokenPipeError: pass
    proc.wait()