import tempfile
import requests
import cv2
import stable_whisper
import openai
import os

def download_video(url):
    response = requests.get(url)
    video_data = response.content
    return video_data

def extract_screenshot_images(video_data, timestamps):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
        temp_file.write(video_data)
        temp_file.flush()

        video = cv2.VideoCapture(temp_file.name)

        screenshots = []
        for timestamp in timestamps:
            video.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
            ret, frame = video.read()

            if ret:
                img_encoded = cv2.imencode(".png", frame)[1].tobytes()
                screenshots.append(img_encoded)

        video.release()

        os.unlink(temp_file.name)

    return screenshots

def upload_screenshots_to_gcs(screenshots, folder_name, bucket):
    public_urls = []
    for idx, screenshot in enumerate(screenshots):
        file_name = f"{folder_name}/screenshot_{idx}.png"
        blob = bucket.blob(file_name)
        blob.upload_from_string(screenshot, content_type="image/png")
        blob.make_public()
        public_urls.append(blob.public_url)

    return public_urls

def transcribe_video_whisper(video_path):
    model = stable_whisper.load_model('base')
    # modified model should run just like the regular model but accepts additional parameters
    results = model.transcribe(video_path)

    # sentence/phrase-level
    stable_whisper.results_to_sentence_srt(results, 'audio.srt')


def transcript_to_tutorial_instructions_with_chatgpt(transcript):

    prompt = f"""
    Please lightly rewrite the transcript into a step by step tutorial for the software, mapping each of the steps to a timestamp in the video that it would correspond to. You may want to combine a few of the steps for brevity. The tutorial should have the format:\n\n    Step 1: Navigate to the main readme landing page -- 00:00:00,640 --> 00:00:03,320\n\n    ...\n\n\"\"\"\n1\n{transcript}\"\"\"
    """

    messages=[
        {"role": "system", "content": "You are transcribing the audio of a software demo video. The timestamps correspond to the times that the phrases were spoken."},
        {"role": "user", "content": prompt},
    ]

    completion = openai.ChatCompletion.create(
    model="gpt-4",
    temperature=0.1,
    messages=messages
    )

    return completion.choices[0].message["content"]