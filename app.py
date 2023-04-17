import os

from flask import Flask, request, jsonify, redirect, flash
from flask_cors import CORS
import json
from celery.result import AsyncResult
from tasks import extract_screenshots, extract_screenshots_from_video_and_upload_celery
from tasks import app as celery_app
from video_utilities import transcribe_video_whisper


app = Flask(__name__)
CORS(app)

# celery = Celery(
#         app.name,
#         broker='pubsub://projects/frindle-video-to-tutorial/topics/process-videos', backend='rpc://'
#         # broker='redis://default:e3e0236e350746edb4a4cad5a601a9f0@us1-polite-flamingo-37407.upstash.io:37407/0',
#         # backend='redis://default:e3e0236e350746edb4a4cad5a601a9f0@us1-polite-flamingo-37407.upstash.io:37407/0'
#     )
# celery.conf.update(
#     task_serializer='json',
#     result_serializer='json',
#     accept_content=['json'],
#     broker_transport_options={
#         'transport': GCloudPubSubTransport,
#         'project_id': 'frindle-video-to-tutorial',
#         'keyfile': './gcs_credentials.json'
#     }
# )

app.secret_key = os.getenv('FLASK_SECRET_KEY', "super-secret")


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

    # extract screenshots from video
    result = extract_screenshots.delay(video_name, title)

    return {"task_id": result.id}


@app.route("/task_status/<id>")
def task_status(id: str):
    result = AsyncResult(id)
    return {
        "ready": result.ready(),
        "successful": result.successful(),
        "value": result.result if result.ready() else None,
    }

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
    # app.run(debug=True, host="0.0.0.0")
