import os
import json
from uuid import uuid4
from celery import Celery
from celery.utils.log import get_task_logger
from gcs_utilities import create_bucket_class_location
from video_utilities import download_video, extract_screenshot_images, upload_screenshots_to_gcs

app = Celery('tasks', broker=os.getenv("CELERY_BROKER_URL"))
logger = get_task_logger(__name__)


# Extract relevant screenshots from the video
@app.task
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
            relevant_frames.append(start_time + 1)
            
            # add the phrase text to the list
            phrase_texts.append(lines[0])
    
    # return as json
    return json.dumps({"relevant_frames": relevant_frames, "phrase_texts": phrase_texts, "video_url": video_url, "folder_name": folder_name})



@app.task
def extract_screenshots_from_video_and_upload_celery(folder_name, video_url, timestamps):


    bucket_name = "video-tutorial-screenshots"
    # create bucket if it doesn't already exist
    bucket = create_bucket_class_location(bucket_name)

    # extract screenshots from the video at the timestamps given, using opencv
    video_data = download_video(video_url)
    screenshots = extract_screenshot_images(video_data, timestamps)
    screenshot_urls = upload_screenshots_to_gcs(screenshots, folder_name, bucket)

    # send back screenshot_urls as json
    return json.dumps({"screenshot_urls": screenshot_urls})



@app.task
def add(x, y):
    logger.info(f'Adding {x} + {y}')
    return x + y
