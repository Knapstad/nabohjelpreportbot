import json
import config
import requests
from google.oauth2 import service_account
from google.cloud import storage
from myerrors import NotFound, NotAuthenticated


SCOPES = ["https://www.googleapis.com/auth/devstorage.read_write"]
CREDENTIALS = service_account.Credentials.from_service_account_file(
    config.cloud_credentials, scopes=SCOPES
)

BLOB_NAME = config.blob_name
BUCKET_NAME = config.bucket_name
SLACK_HOOK = config.slack_hook

client = storage.Client(project="obos", credentials=CREDENTIALS)


def load_posts_log_from_cloud(
    client: "google.cloud.storage.client.Client", blob_name: str, bucket_name: str
):
    bucket = client.get_bucket(bucket_name)
    blob = bucket.get_blob(blob_name)
    return blob.download_as_string()


def get_reported_posts():
    response = requests.get(config.nabohjelp_api, headers=config.headers)
    if response.status_code == 200:
        return response.json(), response.text
    elif response.status_code == 404:
        raise NotFound("Page Not Found")
    elif response.status_code == 401:
        raise NotAuthenticated("Needs to Log in")
    else:
        raise Exception(response.status_code, response.text)
