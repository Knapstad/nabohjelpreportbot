import json
import config
from google.oauth2 import service_account
from google.cloud import storage

SCOPES = ["https://www.googleapis.com/auth/devstorage.read_write"]
CREDENTIALS = service_account.Credentials.from_service_account_file(
    config.cloud_credentials, scopes=SCOPES
)

BLOB_NAME = config.blob_name
BUCKET_NAME = config.bucket_name
SLACK_HOOK = config.slack_hook

client = storage.Client(project="obos", credentials=CREDENTIALS)

def load_posts_log_from_cloud(
    client: "google.cloud.storage.client.Client", 
    blob_name: str, 
    bucket_name: str
):
    bucket = client.get_bucket(bucket_name)
    blob = bucket.get_blob(blob_name)
    return blob.download_as_string()