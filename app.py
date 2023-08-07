import os
import uuid
from flask import Flask, request, jsonify, redirect, flash
from flask_cors import CORS
import json
# from celery.result import AsyncResult
# from tasks import app as celery_app
from video_utilities import transcribe_video_whisper
from gcs_utilities import upload_video_to_gcs, create_bucket_class_location
from database_utilities import insert_project, update_or_add_screenshot_in_database
import modal


app = Flask(__name__)
CORS(app)

@app.route('/')
def health():
    return 'Hello Ren this is the video to docs backend'


@app.route('/extract_screenshots_from_video_and_upload_to_google_storage', methods=['POST'])
def extract_screenshots_from_video_and_upload_to_google_storage():
    
    # video_url = request.form.get("video_url")
    # timestamps = request.form.get("timestamps")
    # project_id = request.form.get("project_id")
    # # convert timestamps from string to list of floats
    # timestamps = json.loads(timestamps)
    # timestamps = [float(timestamp) for timestamp in timestamps]

    # folder_name = request.form.get("folder_name")

    # fn = modal.Function.lookup("process-video-job", "extract_screenshots_from_video_and_upload")
    # fn.spawn(project_id, folder_name, video_url, timestamps)

    
    return {"task_id": "random id"}


@app.route("/upload", methods=["POST"])
def upload():

    # get the title from the form
    title = request.form.get("title")
    # get the video from the form
    video = request.files.get("video")
    # get the user_id from the form
    user_id = request.form.get("user_id")

    # generate random project id
    project_id = uuid.uuid4()

    # upload the video to google cloud storage
    video_url, folder_name = upload_video_to_gcs(project_id, title, video)

    # create a project entry in the database
    insert_project(project_id, user_id, 0, video_url, title, folder_name)

    fn = modal.Function.lookup("process-video-job", "process_video")
    fn.spawn(project_id, video_url, title)

    return {"project_id": project_id}

@app.route('/upload_image', methods=['POST'])
def upload_image():
    # Get the file from POST request
    file = request.files['file']
    folder_name = request.form.get("folder_name")
    idx = request.form.get("idx")
    screenshot_id = request.form.get("screenshot_id")
    project_id = request.form.get("project_id")
    file_name = f"{folder_name}/screenshot_{idx}.png"
    text = request.form.get("text")
    
    # Create a blob in the bucket
    bucket_name = "video-tutorial-renderer"
    # create bucket if it doesn't already exist
    bucket = create_bucket_class_location(bucket_name)

    blob = bucket.blob(file_name)

    # Set Cache-Control to private
    blob.cache_control = "private"

    # Upload the file to GCS
    blob.upload_from_string(
        file.read(),
        content_type=file.content_type
    )
    public_url = blob.public_url

    # update just that screenshot in the database
    update_or_add_screenshot_in_database(project_id, idx, public_url, text, screenshot_id)

    # Get the blob's public URL and return it
    return jsonify({'url': public_url}), 200

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
