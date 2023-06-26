import urllib.request
from typing import List

from tasks import transcribe_video_and_extract_screenshots, extract_screenshots_from_video_and_upload_celery

import modal

FACE_CASCADE_FN = "haarcascade_frontalface_default.xml"

stub = modal.Stub("process-video-job", 
                  
    image=modal.Image.debian_slim().apt_install("libgl1-mesa-glx", "libglib2.0-0", "wget", "git", "ffmpeg").run_commands(
        f"wget https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/{FACE_CASCADE_FN} -P /root"
    ).pip_install(
        "stable-ts==2.6.2", "supabase==1.0.3", "openai==0.27.2", "celery==5.2.6", 
        "opencv-python==4.7.0.72",
        "google-api-core==2.11.0",
"google-auth==2.16.3",
"google-cloud-core==2.3.2",
"google-cloud-storage==2.7.0",
"google-crc32c==1.5.0",
"google-resumable-media==2.4.1"
    ),
                  )



@stub.function(
secret=modal.Secret.from_name("video-to-tutorial-keys"),
    gpu="any",
    retries=3,
)
def process_video(project_id: str, video_url: str, title: str):
   
   transcribe_video_and_extract_screenshots(project_id, video_url, title)

@stub.function(
      secret=modal.Secret.from_name("video-to-tutorial-keys"),
    gpu="any",
    retries=3,
)
def extract_screenshots_from_video_and_upload(project_id: str, folder_name: str, video_url: str, timestamps: List[int]):   
   
   extract_screenshots_from_video_and_upload_celery(project_id, folder_name, video_url, timestamps)
   
