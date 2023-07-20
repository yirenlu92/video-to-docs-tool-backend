import os
import json
import sys
from uuid import uuid4
from gcs_utilities import create_bucket_class_location
from video_utilities import download_video, extract_screenshot_images, upload_screenshots_to_gcs, transcript_to_tutorial_instructions_with_chatgpt, transcript_to_blog_post_with_chatgpt, transcribe_video_whisper_api, transcribe_video_whisper
from database_utilities import fetch_project_data, update_error_message, update_project_status, insert_new_screenshot_in_screenshots_table, update_markdown_project_status

def transcribe_video_and_extract_screenshots(project_id, video_url, title):

    # fetch the project data from supabase
    project_data = fetch_project_data(project_id)

    # check the status of the project
    if project_data["task_status"] == 1:
        return
    
    try: 
        sentences = transcribe_video_whisper(video_url)

        timestamps_and_text = extract_screenshots(sentences)

        # create entries in the screenshots table
        for i, timestamp_and_text in enumerate(timestamps_and_text):
            # insert the timestamps and text into the database
            insert_new_screenshot_in_screenshots_table(project_id, timestamp_and_text["phrase_text"], timestamp_and_text["relevant_frame"], i)

        # update the status of the project to be "completed"
        update_project_status(project_id, 1)

        print("just inserted timestamps and text")
    
    except Exception as e:
        print(e)
        # update the status of the project to be "failed"
        update_project_status(project_id, 2)
        update_error_message(project_id, str(e))
        return

    return


def process_video_to_blog_post(transcript):

    # turn the transcript into a blog post using chatgpt
    blog_post = transcript_to_blog_post_with_chatgpt(transcript)

    print(blog_post)

    # split the blog post into paragraphs
    paragraphs = blog_post.split("\n\n")

    # grab timestamps from the video corresponding to the beginning of each paragraph
    relevant_frames = []
    for paragraph in paragraphs:
        relevant_frames.append(1)
    
    return {"relevant_frames": relevant_frames, "phrase_texts": paragraphs}


# Extract relevant screenshots from the video
def extract_screenshots(srt):

    phrase_texts = []
    relevant_frames = []

    instructions = transcript_to_tutorial_instructions_with_chatgpt(srt)
    # split the instructions on blank lines
    instructions = instructions.split("\n")
    # remove empty strings and strip whitespace
    instructions = [instruction.strip() for instruction in instructions if instruction != ""]
    print(instructions)
    for i, instruction in enumerate(instructions):
        lines = instruction.split(" -- ")

        # if the line does not contain a timestamp, continue to the next line
        if len(lines) < 2:
            continue

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
    
    # return as array of objects
    return [{"relevant_frame": relevant_frame, "phrase_text": phrase_text} for relevant_frame, phrase_text in zip(relevant_frames, phrase_texts)]


def extract_screenshots_from_video_and_upload_celery(project_id, folder_name, video_url, timestamps):

    from modal import current_input_id

    bucket_name = "video-tutorial-screenshots"
    # create bucket if it doesn't already exist
    bucket = create_bucket_class_location(bucket_name)

    # extract screenshots from the video at the timestamps given, using opencv
    video_data = download_video(video_url)
    screenshots = extract_screenshot_images(video_data, timestamps)
    screenshot_urls = upload_screenshots_to_gcs(screenshots, folder_name, bucket)

    # update markdown task status, including with the task_id

    # get task id

    # task_id = extract_screenshots_from_video_and_upload_celery.request.id
    update_markdown_project_status(project_id, screenshot_urls)

    # send back task_id
    return {"task_id": current_input_id}


