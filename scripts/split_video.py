import os
import subprocess

def split_video_ffmpeg(video_path, output_dir="clips", clip_duration=5):
    """
    Split video into fixed-length clips using ffmpeg.

    Args:
        video_path (str): Path to the video file
        output_dir (str): Folder to save clips
        clip_duration (int): Clip length in seconds
    """
    os.makedirs(output_dir, exist_ok=True)

    # Construct ffmpeg command
    # -i: input file
    # -c copy: copy codecs (fast)
    # -map 0: include all streams
    # -f segment: use segment muxer
    # -segment_time: length of each clip
    # -reset_timestamps 1: start timestamps from 0 for each clip
    command = [
        "ffmpeg",
        "-i", video_path,
        "-c", "copy",
        "-map", "0",
        "-f", "segment",
        "-segment_time", str(clip_duration),
        "-reset_timestamps", "1",
        os.path.join(output_dir, "clip_%03d.mp4")
    ]

    print("Running ffmpeg to split video...")
    subprocess.run(command, check=True)
    print(f"✅ Done! Clips saved in '{output_dir}'.")


if __name__ == "__main__":
    video_path = "/Users/naveent/Desktop/singapore_race_without_audio.mp4"
    split_video_ffmpeg(video_path)
