import os
import base64
import requests
from dotenv import load_dotenv
import json
# import openai
# from dotenv import load_dotenv
import wave

# from langchain_openai import ChatOpenAI, OpenAI
# from langchain_core.messages import HumanMessage
load_dotenv()
BOSON_API_KEY = os.getenv("BOSON_API_KEY")
BASE_URL = os.getenv("BASE_URL")
TTS_MODEL = os.getenv("TTS_MODEL")

reference_path = "scripts/agents/input/david-c-cut-unedited.wav"
reference_transcript = (
    "The turkish Grand Prix, its lights out and away we go. And they are crawling off the line,"
    "especially Max Verstappen. Hamilton though takes a very good start, passes two cars already."
    "Stroll is on the lead taking a turn one ahead of his teammate."
)

def b64_encode(path: str) -> str:
    """Encode an audio file to base64."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def clone_voice_node(state):
    """
    LangGraph node for Boson AI voice cloning.
    Expects the state to contain:
      - 'reference_path': path to the reference WAV file
      - 'reference_transcript': transcript of that audio
      - 'commentator_response': the new text to generate in the cloned voice
    Returns:
      - dict with 'output_audio_path'
    """
    commentator_response = state["commentator_response"][-1]
    print(commentator_response)
    output_dir = state["output_dir"]
    stream = True if "stream" not in state else state["stream"]
    messages = [
        {"role": "system", "content": "You are an AI assistant designed to convert chinese text into speech."},
        {"role": "user", "content": reference_transcript},
        {
            "role": "assistant",
            "content": [
                {
                    "type": "input_audio",
                    "input_audio": {
                        "data": b64_encode(reference_path),
                        "format": "wav"
                    }
                }
            ],
        },
        {"role": "user", "content": commentator_response},
    ]
    print("🎙️  Starting generating voice cloning...")
    payload = {
        "model": "higgs-audio-generation-Hackathon",
        "messages": messages,
        "modalities": ["text", "audio"],
        "max_completion_tokens": 4096,
        "temperature": 0.2,
        "top_p": 0.95,
        "stream": stream,
        "stop": ["<|eot_id|>", "<|end_of_text|>", "<|audio_eos|>"],
        "extra_body": {"top_k": 50},
    }
    if stream:
    # Open WAV file for streaming write
        wf = wave.open(output_dir, "wb")
        wf.setnchannels(1)        # mono
        wf.setsampwidth(2)        # 16-bit PCM
        wf.setframerate(24000)    # 24 kHz

        headers = {
            "Authorization": f"Bearer {BOSON_API_KEY}",
            "Content-Type": "application/json",
        }

        try:
            with requests.post(
                f"{BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                stream=True,
            ) as resp:
                resp.raise_for_status()

                for line in resp.iter_lines(decode_unicode=True):
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[len("data: "):].strip()
                    # print(f"data_str:{data_str}")

                    if data_str == "[DONE]":
                        break
                    print("...")
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk["choices"][0].get("delta", {})
                        audio = delta.get("audio")
                        if audio and "data" in audio:
                            # print(audio)
                            wf.writeframes(base64.b64decode(audio["data"]))
                    except Exception as e:
                        # print("⚠️ Skipped chunk:", e)
                        continue
        finally:
            wf.close()
    else:
        # Non-stream, don't forget to turn off stream=True.
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

        # Extract audio data
        audio_b64 = data["choices"][0]["message"]["audio"]["data"]

        # Save as WAV file
        with open(output_dir, "wb") as f:
            f.write(base64.b64decode(audio_b64))

    print(f"✅ Voice cloned and saved to {output_dir}")
    # return {"output_audio_path": output_dir}
    return state

state = {
    'output_dir': 'scripts/agents/output/chinese_test_py.wav',
    'commentator_response': ["Lǎotiān bǎoyòu jīnshān yínshān quán dōu yǒu. Lǎotiān jiàosuǒ bié guǎn jiānghú lónghǔ dòu. Lǎotiān dīngzhǔ zhè bèizi wǒ shàn bù diū"]
} 
print(clone_voice_node(state))