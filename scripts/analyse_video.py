import os, openai
from dotenv import load_dotenv

load_dotenv(override=True)

client = openai.Client(api_key=os.getenv("BOSON_API_KEY"),
                       base_url="https://hackathon.boson.ai/v1")

resp = client.chat.completions.create(
    model="Qwen3-Omni-30B-A3B-Thinking-Hackathon",
    messages=[
        {
            "role": "system",
            "content": "You are a AI video commentator"
        },
        {
            "role": "user", 
            "content": [
                {"type": "text", "text": "Comment on this video"},
                {"type": "video_url", "video_url": "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen3-Omni/demo/draw.mp4"}
            ]
        },
        {
            "role": "user", 
            "content": [
                {"type": "text", "text": "Summarize what the video shows."},
                {"type": "video", "video": "/Users/naveent/Desktop/f1-live-commentator/clips/clip_135.mp4"}
            ]
        }
    ],
    max_tokens=256,
    temperature=0.2,
)
print(resp.choices[0].message.content)