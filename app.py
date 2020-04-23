from collections import namedtuple

import boto3
from flask import Flask, render_template

from pretty_date import pretty_date

Screenshot = namedtuple("Screenshot", "name url last_updated timestamp")

BUCKET_NAME = "pokerstars-90274"

app = Flask(__name__)


def pull_screenshots(key_prefix):
    s3 = boto3.client("s3")
    response = s3.list_objects(Bucket=BUCKET_NAME)
    keys = [
        item["Key"]
        for item in response["Contents"]
        if item["Key"].startswith("cropped")
    ]

    results = []
    for key in keys:
        url = s3.generate_presigned_url(
            "get_object", Params={"Bucket": BUCKET_NAME, "Key": key}, ExpiresIn=100,
        )
        name = key.replace("cropped\\", "").replace(".png", "")
        last_modified = s3.get_object(Bucket=BUCKET_NAME, Key=key)["LastModified"]
        last_updated = pretty_date(last_modified)
        results.append(Cropped(name=name, url=url, last_updated=last_updated, timestamp=last_modified))

    return sorted(results, key=lambda x: x.timestamp)


@app.route("/")
def index():
    cropped = _get_cropped()
    return render_template("index.html", data=cropped)
