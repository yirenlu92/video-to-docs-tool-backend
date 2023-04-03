import os
import cv2
from uuid import uuid4
import stable_whisper
from flask import Flask, request, send_file
from flask_cors import CORS, cross_origin
from google.cloud import storage
import openai
import base64
from io import BytesIO
import requests
import tempfile
import json

app = Flask(__name__)
CORS(app)

@app.route('/')
def health():
    return 'Hello Ren'

@app.route('/extract_screenshots_from_video_and_upload_to_google_storage', methods=['POST'])
def extract_screenshots_from_video_and_upload_to_google_storage():
    video_url = request.form.get("video_url")
    timestamps = request.form.get("timestamps")
    timestamps = [float(timestamp) for timestamp in timestamps.split(",")]
    folder_name = request.form.get("folder_name")

    bucket_name = "video-tutorial-screenshots"
    # create bucket if it doesn't already exist
    bucket = create_bucket_class_location(bucket_name)

    # extract screenshots from the video at the timestamps given, using opencv
    video_data = download_video(video_url)
    screenshots = extract_screenshot_images(video_data, timestamps)
    screenshot_urls = upload_screenshots_to_gcs(screenshots, folder_name, bucket)

    # send back screenshot_urls as json
    return {"screenshot_urls": screenshot_urls}


#add flask routes
@app.route("/upload", methods=["POST"])
def upload():
    # get the title from the form
    title = request.form.get("title")
    # get the video from the form
    video = request.files.get("video")
    # get the name of the video
    video_name = video.filename
    # save the file
    video.save(video_name)

    # transcribe the video
    transcribe_video_whisper(video_name)

    relevant_frames, phrase_texts, video_url, folder_name = extract_screenshots(video_name, title)

    # return relevant_frames, phrase_texts, video_url, and folder_name as json
    return {"relevant_frames": relevant_frames, "phrase_texts": phrase_texts, "video_url": video_url, "folder_name": folder_name}

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

def create_bucket_class_location(bucket_name):
    """
    Create a new bucket in the US region with the coldline storage
    class
    """
    
    # Access GCS credentials from the environment variable
    gcs_credentials_json = os.environ.get("GCS_CREDENTIALS")

    # Parse the JSON string into a Python dictionary
    gcs_credentials = json.loads(gcs_credentials_json)

    storage_client = storage.Client.from_service_account_info(gcs_credentials)
    

    # check if bucket already exists
    if storage_client.lookup_bucket(bucket_name):
        print("Bucket {} already exists".format(bucket_name))

        # return bucket
        return storage_client.get_bucket(bucket_name)
    
    # otherwise create bucket and make it publically available
    print("Creating bucket {}".format(bucket_name))
    bucket = storage_client.bucket(bucket_name)
    bucket.storage_class = "COLDLINE"
    new_bucket = storage_client.create_bucket(bucket, location="us")
    # make bucket publically available
    bucket.default_object_acl.all().grant_read()
    bucket.default_object_acl.save()

    bucket.acl.all().grant_read()
    bucket.acl.save()

    print(
        "Created bucket {} in {} with storage class {}".format(
            new_bucket.name, new_bucket.location, new_bucket.storage_class
        )
    )
    return new_bucket



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


# Extract relevant screenshots from the video
def extract_screenshots(input_video, title):

    # turn title into slug
    slug = title.lower().replace(" ", "-")

    # Set up the paths for the input video and output screenshots
    input_path = input_video

    phrase_texts = []
    relevant_frames = []

    # create new bucket name with slug and generated id
    folder_name = slug + "-" + str(uuid4())
    bucket = create_bucket_class_location("video-tutorial-screenshots")

    # upload the video to the bucket
    blob = bucket.blob(f"{folder_name}/video.mp4")
    blob.upload_from_filename(input_path, content_type="video/mp4")

    # get the public URL of the video
    video_url = blob.public_url

    # read the audio.srt file contents
    with open("audio.srt", "r") as f:
        srt = f.read()

        instructions = transcript_to_tutorial_instructions_with_chatgpt(srt)
        print(instructions)
        # split the instructions on blank lines
        instructions = instructions.split("\n")
        # remove empty strings and strip whitespace
        instructions = [instruction.strip() for instruction in instructions if instruction != ""]
        # first line is the instruction, second line is the timestamp
        print(instructions)
        for i, instruction in enumerate(instructions):
            lines = instruction.split(" -- ")
            # get the start times and end times
            start_time = lines[1].split(" --> ")[0]
            end_time = lines[1].split(" --> ")[1]

            # remove the milliseconds
            start_time = start_time.split(",")[0]
            end_time = end_time.split(",")[0]

            # convert to seconds
            start_time = start_time.split(":")
            start_time = int(start_time[0]) * 3600 + int(start_time[1]) * 60 + float(start_time[2])
            end_time = end_time.split(":")
            end_time = int(end_time[0]) * 3600 + int(end_time[1]) * 60 + float(end_time[2])

            # add to the timestamps list
            relevant_frames.append(start_time + 2)
            
            # add the phrase text to the list
            phrase_texts.append(lines[0])

    return relevant_frames, phrase_texts, video_url, folder_name

# Generate Markdown output with screenshots and corresponding transcribed text
def generate_markdown(screenshot_urls, phrase_texts, title):
    markdown = ""
    markdown = f"# {title}\n\n"

    # Iterate through screenshots
    for i in range(len(screenshot_urls)):
        # Add the screenshot and corresponding text to the Markdown output
        markdown += f"{phrase_texts[i]}\n\n"
        markdown += f"![Step {i+1}]({screenshot_urls[i]})\n\n"
    
    # write the markdown to file
    with open("output.md", "w") as f:
        f.write(markdown)

    return markdown


# if __name__ == '__main__':
#     app.run(host="localhost", port=8000, debug=True)
