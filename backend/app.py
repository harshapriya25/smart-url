import json
import os
import re
import secrets
from urllib.parse import urlparse

import boto3
from boto3.dynamodb.conditions import Key

TABLE_NAME = os.environ.get("URLS_TABLE", "SmartUrls")
table = boto3.resource("dynamodb").Table(TABLE_NAME)


def response(status_code, body, headers=None):
    base_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    }
    if headers:
        base_headers.update(headers)
    return {
        "statusCode": status_code,
        "headers": base_headers,
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    method = event.get("httpMethod", "")
    path = event.get("path", "/")

    if method == "OPTIONS":
        return response(200, {"message": "OK"})

    if method == "POST" and path == "/shorten":
        return create_short_url(event)

    if method == "GET" and path.startswith("/stats/"):
        code = path.rsplit("/", 1)[-1]
        return get_stats(code)

    if method == "GET":
        code = path.strip("/")
        if code:
            return redirect_to_original(code)

    return response(404, {"error": "Route not found"})


def create_short_url(event):
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return response(400, {"error": "Request body must be valid JSON"})

    original_url = (body.get("url") or "").strip()
    parsed = urlparse(original_url)

    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return response(400, {"error": "Enter a valid URL starting with http:// or https://"})

    code = secrets.token_urlsafe(5).replace("-", "").replace("_", "")[:7]
    item = {
        "code": code,
        "original_url": original_url,
        "clicks": 0,
    }

    try:
        table.put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(code)",
        )
    except Exception as exc:
        # A collision is exceptionally unlikely; return a safe error rather than
        # accidentally overwriting an existing short link.
        print(f"Could not save URL: {exc}")
        return response(500, {"error": "Could not create short URL. Please try again."})

    domain = event.get("headers", {}).get("Host", "")
    stage = event.get("requestContext", {}).get("stage", "")
    prefix = f"/{stage}" if stage and stage not in ("$default", "default") else ""
    short_url = f"https://{domain}{prefix}/{code}" if domain else f"/{code}"

    return response(201, {
        "message": "Short URL created",
        "code": code,
        "original_url": original_url,
        "short_url": short_url,
        "clicks": 0,
    })


def redirect_to_original(code):
    if not re.fullmatch(r"[A-Za-z0-9]{4,12}", code):
        return response(404, {"error": "Short URL not found"})

    try:
        result = table.get_item(Key={"code": code})
        item = result.get("Item")
        if not item:
            return response(404, {"error": "Short URL not found"})

        table.update_item(
            Key={"code": code},
            UpdateExpression="ADD clicks :increment",
            ExpressionAttributeValues={":increment": 1},
        )
        return {
            "statusCode": 302,
            "headers": {
                "Location": item["original_url"],
                "Cache-Control": "no-store",
            },
            "body": "",
        }
    except Exception as exc:
        print(f"Could not redirect URL: {exc}")
        return response(500, {"error": "Could not redirect this URL"})


def get_stats(code):
    if not re.fullmatch(r"[A-Za-z0-9]{4,12}", code):
        return response(404, {"error": "Short URL not found"})

    try:
        result = table.get_item(Key={"code": code})
        item = result.get("Item")
        if not item:
            return response(404, {"error": "Short URL not found"})

        return response(200, {
            "code": item["code"],
            "original_url": item["original_url"],
            "clicks": int(item.get("clicks", 0)),
        })
    except Exception as exc:
        print(f"Could not fetch stats: {exc}")
        return response(500, {"error": "Could not fetch URL analytics"})
