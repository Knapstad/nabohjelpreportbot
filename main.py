import json
import config
import requests

from functools import wraps
from typing import Tuple, Any
from google.oauth2 import service_account
from google.cloud import storage
from myerrors import NotFound, NotAuthenticated


def retry_on_connection_error(max_retry: int = 3):
    def decorate_function(function):
        @wraps(function)
        def retry(*args, **kwargs):
            tries = 0
            while tries < max_retry:
                try:
                    return function(*args, **kwargs)
                except ConnectionError:
                    tries += 1
            return function(*args, **kwargs)

        return retry

    return decorate_function


@retry_on_connection_error()
def load_posts_log_from_cloud(
    client: "google.cloud.storage.client.Client", blob_name: str, bucket_name: str
):
    bucket = client.get_bucket(bucket_name)
    blob = bucket.get_blob(blob_name)
    return blob.download_as_string()


@retry_on_connection_error()
def save_posts_to_cloud(
    client: "google.cloud.storage.client.Client",
    data: list,
    blob_name: str,
    bucket_name: str,
):
    bucket = client.get_bucket(bucket_name)
    blob = bucket.get_blob(blob_name)
    if not blob:
        blob = bucket.blob(blob_name)
    blob.upload_from_string(str(data))


@retry_on_connection_error()
def get_reported_posts():
    response = requests.get(config.nabohjelp_api, headers=config.headers)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        raise NotFound("Page Not Found")
    elif response.status_code == 401:
        raise NotAuthenticated("Needs to Log in")
    else:
        raise Exception(response.status_code, response.text)


def make_slack_message(data: dict) -> str:
    if len(data["description"]) > 20:
        data["description"] = f"{data['description'][:20]}..."
    message = f"Post er rapportert:\n\nId:  *{data['postId']}*\nTittel:  *{data['title']}*\nMelding:  *{data['description']}*\nStatus:  *{data['status']}*\nType:  *{data['postType']}*"
    return message


def send_slack_message(hook: str, message: str):
    slackdata = {
        "blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": message}}]
    }
    print(json.dumps(slackdata))
    a = requests.post(hook, data=json.dumps(slackdata))
    return a


def main(*args, **kwargs):
    SCOPES = ["https://www.googleapis.com/auth/devstorage.read_write"]
    CREDENTIALS = service_account.Credentials.from_service_account_file(
        config.cloud_credentials, scopes=SCOPES
    )

    BLOB_NAME = config.blob_name
    BUCKET_NAME = config.bucket_name
    SLACK_HOOK = config.slack_hook

    client = storage.Client(project="obos", credentials=CREDENTIALS)

    posts = json.loads(
        str(load_posts_log_from_cloud(client, BLOB_NAME, BUCKET_NAME), "utf8")
    )
    print(posts)
    data = get_reported_posts()
    try:
        for i in data:
            if i["postId"] not in posts:
                posts.append(i["postId"])
                send_slack_message(SLACK_HOOK, make_slack_message(i))
    finally:
        save_posts_to_cloud(client, posts, BLOB_NAME, BUCKET_NAME)


if __name__ == "__main__":
    pass
