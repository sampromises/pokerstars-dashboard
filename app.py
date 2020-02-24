import boto3

from collections import namedtuple
from flask import Flask
from flask import render_template

Cropped = namedtuple("Cropped", "name url last_modified")

BUCKET_NAME = "pokerstars-90274"

app = Flask(__name__)


def _get_cropped():
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
        print(last_modified)
        results.append(Cropped(name=name, url=url, last_modified=last_modified,))

    return results


@app.route("/")
def index():
    cropped = _get_cropped()
    return render_template("index.html", data=cropped)
