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
    # convert timestamps from string to list of floats
    timestamps = json.loads(timestamps)
    timestamps = [float(timestamp) for timestamp in timestamps]

    folder_name = request.form.get("folder_name")
    
    result = extract_screenshots_from_video_and_upload_celery.delay(folder_name, video_url, timestamps)

    return {"task_id": result.id}


@app.route("/upload", methods=["POST"])
def upload():

    # get the title from the form
    title = request.form.get("title")
    # get the video from the form
    video = request.files.get("video")

    # generate random project id
    project_id = uuid.uuid4()

    # upload the video to google cloud storage
    video_url, folder_name = upload_video_to_gcs(project_id, title, video)

    # create a project entry in the database
    insert_project(project_id, 0, video_url, title, folder_name)

    # send the video processing task to the celery queue
    result = transcribe_video_and_extract_screenshots.delay(project_id, video_url, title)

    # retrieve task_id
    # task_id = result.id

    return {"project_id": project_id}


# @app.route("/task_status/<id>")
# def task_status(id: str):
#     result = AsyncResult(id)

#     try:
#         # check if the task has completed successfully
#         if result.ready() and not result.failed():
#             task_output = result.get()
#             return {
#                 "ready": result.ready(),
#                 "successful": result.successful(),
#                 "value": result.result if result.ready() else None,
#             }
#         else:
#             # handle the case where the task has not yet completed
#             return {"ready": result.ready(), "successful": result.successful()}

#     except Exception as e:
#         # handle any exceptions that occur during the task execution
#         print(f"Error occurred while processing task: {e}")
#         return {"error": e}

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
    # app.run(debug=True, host="0.0.0.0")
