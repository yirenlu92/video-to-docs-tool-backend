import os
import uuid
from flask import Flask, request, jsonify, redirect, flash
from flask_cors import CORS
import json
from celery.result import AsyncResult
from tasks import extract_screenshots, extract_screenshots_from_video_and_upload_celery, transcribe_video_and_extract_screenshots
from tasks import app as celery_app
from video_utilities import transcribe_video_whisper
from gcs_utilities import upload_video_to_gcs
from database_utilities import insert_project


app = Flask(__name__)
CORS(app)

@app.route('/')
def health():
    return 'Hello Ren this is the video to docs backend'

@app.route('/extract_screenshots_from_video_and_upload_to_google_storage', methods=['POST'])
def extract_screenshots_from_video_and_upload_to_google_storage():
    video_url = request.form.get("video_url")
    timestamps = request.form.get("timestamps")
    project_id = request.form.get("project_id")
    # convert timestamps from string to list of floats
    timestamps = json.loads(timestamps)
    timestamps = [float(timestamp) for timestamp in timestamps]

    folder_name = request.form.get("folder_name")
    
    result = extract_screenshots_from_video_and_upload_celery.delay(project_id, folder_name, video_url, timestamps)

    return {"task_id": result.id}


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

    # transcribe video
    # sentences = transcribe_video_whisper(video_url)
    # print(sentences)

    # send the video processing task to the celery queue
    result = transcribe_video_and_extract_screenshots.delay(project_id, video_url, title)

    return {"project_id": project_id}


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
    # app.run(debug=True, host="0.0.0.0")
