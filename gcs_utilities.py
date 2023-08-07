import json
from google.cloud import storage
import os
from io import BytesIO

def upload_video_to_gcs(project_id, title, video):

     # turn title into slug
    slug = title.lower().replace(" ", "-")
    # create new bucket name with slug and generated id
    folder_name = slug + "-" + str(project_id)
    bucket = create_bucket_class_location("video-tutorial-screenshots")
    print("got to creating the bucket")

     # upload the video to the bucket
    blob = bucket.blob(f"{folder_name}/video.mp4")

    # Save video to memory using BytesIO and upload to GCS
    video_stream = BytesIO(video.read())
    video_stream.seek(0)
    blob.upload_from_file(video_stream, content_type="video/mp4")
    video_stream.close()

    # get the public URL of the video
    video_url = blob.public_url

    print("public url of video")
    return (video_url, folder_name)

def create_bucket_class_location(bucket_name):
    """
    Create a new bucket in the US region with the coldline storage
    class
    """
    
    # Access GCS credentials from the environment variable
    gcs_credentials_json = os.environ.get("GCS_CREDENTIALS")

    # get credentials from file
    # with open("gcs_credentials.json", "r") as f:
    #     gcs_credentials_json = f.read()


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
    bucket.storage_class = "STANDARD"
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