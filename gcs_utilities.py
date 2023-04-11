import json
from google.cloud import storage

def create_bucket_class_location(bucket_name):
    """
    Create a new bucket in the US region with the coldline storage
    class
    """
    
    # Access GCS credentials from the environment variable
    # gcs_credentials_json = os.environ.get("GCS_CREDENTIALS")

    # get credentials from file
    with open("gcs_credentials.json", "r") as f:
        gcs_credentials_json = f.read()


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