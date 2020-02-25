from collections import namedtuple

from pytz import timezone

import boto3
import pytz
from flask import Flask, render_template

Cropped = namedtuple("Cropped", "name url last_updated timestamp")

BUCKET_NAME = "pokerstars-90274"

app = Flask(__name__)


def pretty_date(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc

    Adapted from: https://stackoverflow.com/a/1551394
    """
    from datetime import datetime
    now = datetime.now(pytz.utc)
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time,datetime):
        diff = now - time
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + " seconds ago"
        if second_diff < 120:
            return "a minute ago"
        if second_diff < 3600:
            return str(second_diff // 60) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str(second_diff // 3600) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if day_diff < 14:
        return str(day_diff // 7) + " week ago"
    if day_diff < 31:
        return str(day_diff // 7) + " weeks ago"
    if day_diff < 365:
        return str(day_diff // 30) + " months ago"
    if day_diff < 365*2:
        return str(day_diff // 365) + " year ago"
    return str(day_diff // 365) + " years ago"


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
        last_updated = pretty_date(last_modified)
        results.append(Cropped(name=name, url=url, last_updated=last_updated, timestamp=last_modified))

    return sorted(results, key=lambda x: x.timestamp)


@app.route("/")
def index():
    cropped = _get_cropped()
    return render_template("index.html", data=cropped)
