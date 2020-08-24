import json
import os
from collections import namedtuple

import boto3
from flask import Flask, flash, redirect, render_template, request, url_for
from pretty_date import pretty_date

Screenshot = namedtuple("Screenshot", "name url last_updated timestamp")

BUCKET_NAME = "pokerstars-90274"

app = Flask(__name__)
app.config.update(SECRET_KEY=os.environ.get("FLASK_SECRET_KEY"))


def pull_screenshots(key_prefix):
    s3 = boto3.client("s3")
    response = s3.list_objects(Bucket=BUCKET_NAME)
    keys = [item["Key"] for item in response["Contents"] if item["Key"].startswith(key_prefix)]

    results = []
    for key in keys:
        url = s3.generate_presigned_url(
            "get_object", Params={"Bucket": BUCKET_NAME, "Key": key}, ExpiresIn=100,
        )
        last_modified = s3.get_object(Bucket=BUCKET_NAME, Key=key)["LastModified"]
        last_updated = pretty_date(last_modified)
        results.append(
            Screenshot(name=key, url=url, last_updated=last_updated, timestamp=last_modified)
        )

    return sorted(results, key=lambda x: x.timestamp)


def _get_cropped():
    screenshots = pull_screenshots("cropped")

    def rename_screenshot(ss):
        new_name = ss.name.replace("cropped\\", "").replace(".png", "")
        return Screenshot(
            name=new_name, url=ss.url, last_updated=ss.last_updated, timestamp=ss.timestamp,
        )

    return map(rename_screenshot, screenshots)


def _get_full():
    return pull_screenshots("full")


def _get_login_json():
    s3 = boto3.client("s3")
    obj = s3.get_object(Bucket=BUCKET_NAME, Key="input.json")
    return json.loads(obj["Body"].read())


def _upload_login_json(data):
    s3 = boto3.client("s3")
    s3.put_object(
        Body=data.encode("utf8"), Bucket=BUCKET_NAME, Key="input.json",
    )


@app.route("/admin", methods=["GET", "POST"])
def admin():
    data = _get_login_json()
    if "user_input" in request.form:
        user_data = request.form["user_input"]
        try:
            if json.loads(user_data) != data:
                _upload_login_json(user_data)
                flash("Successfully uploaded data.")
        except json.JSONDecodeError:
            flash("Input data is not valid JSON.")

    return render_template("admin.html", data=json.dumps(data, indent=4))


@app.route("/debug")
def debug():
    full = _get_full()
    return render_template("index.html", data=full)


@app.route("/")
def index():
    cropped = _get_cropped()
    return render_template("index.html", data=cropped)
