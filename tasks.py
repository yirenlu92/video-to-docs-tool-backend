import os
import json
import sys
from uuid import uuid4
from celery import Celery
from celery.utils.log import get_task_logger
from gcs_utilities import create_bucket_class_location
from video_utilities import download_video, extract_screenshot_images, upload_screenshots_to_gcs, transcript_to_tutorial_instructions_with_chatgpt, transcribe_video_whisper_api
from database_utilities import fetch_project_data, update_project_status, insert_timestamps_and_text

app = Celery('tasks', broker=os.getenv("CELERY_BROKER_URL"), backend=os.getenv("CELERY_RESULT_BACKEND"))
logger = get_task_logger(__name__)

@app.task
def transcribe_video_and_extract_screenshots(project_id, video_url, title):

    # fetch the project data from supabase
    project_data = fetch_project_data(project_id)

    print("printing the project data")
    print(project_data)

    # check the status of the project
    if project_data["task_status"] == 1:
        return
    
    print("transcribing video")
    print(video_url)

    # download the video from the video_url
    video_data = download_video(video_url)

    video_path = "video.mp4"

    # Replace 'output_video.mp4' with the desired output file path
    with open(video_path, 'wb') as output_file:
        output_file.write(video_data)

    # openai_transcript = transcribe_video_whisper_api(video_path)
    # print("whisper openai transcript")
    # print(openai_transcript)

    timestamps_and_text = extract_screenshots()

    # insert the timestamps and text into the database
    insert_timestamps_and_text(project_id, timestamps_and_text["phrase_texts"], timestamps_and_text["relevant_frames"])

    # update the status of the project to be "completed"
    update_project_status(project_id, 1)

    return


# Extract relevant screenshots from the video
def extract_screenshots():

    phrase_texts = []
    relevant_frames = []

    # read the transcript from database
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
    return {"relevant_frames": relevant_frames, "phrase_texts": phrase_texts}



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
