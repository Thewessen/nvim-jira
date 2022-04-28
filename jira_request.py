#!/usr/bin/env python3.9

import requests
import json
import os
from requests.auth import HTTPBasicAuth
from functools import wraps
from dotenv import load_dotenv

def fires_request(f):
    load_dotenv()
    auth = HTTPBasicAuth(os.getenv('USERNAME'), os.getenv('API_TOKEN'))
    domain = os.getenv('DOMAIN')
    headers = { "Accept": "application/json" }
    base_url = f"https://{domain}.atlassian.net/rest/api/2"
    @wraps(f)
    def req(*args, **kwds):
        url = f(*args, **kwds)
        if type(url) == tuple:
            url, params = url
        else:
            params = {}
        url = base_url + url
        resp = requests.get(url, headers=headers, auth=auth, params=params)
        return resp, url
    return req


@fires_request
def get_specific_issue(key):
    return f"/issue/{key}"


@fires_request
def search_issue(query):
    return "/issue/picker", { "query": query }


@fires_request
def search_dashboards():
    return "/dashboard/search"


@fires_request
def all_dashboards():
    return "/dashboard"


@fires_request
def all_projects():
    return "/project/search"


@fires_request
def get_project(project_id):
    return f"/project/{project_id}"


@fires_request
def all_issues():
    return "/search"


@fires_request
def search_jql(**kwds):
    return f"/search", kwds


@fires_request
def all_fields():
    return "/field"


def parse_paragraph(blob):
    if blob is not None and blob["type"] == "paragraph":
        return ' '.join([b["text"] for b in blob["content"] if b["type"] == "text"]) 
    return ''


def parse_description(payload):
    # TODO: does not include marks or nested lists
    if payload is None:
        yield ''
    else:
        for blob in payload["content"]:
            if blob["type"] == "bulletList":
                for line in blob["content"]:
                    yield '- ' + parse_paragraph(line["content"][0])
            elif blob["type"] == "orderedList":
                for (i, line) in enumerate(blob["content"]):
                    yield (i + 1) + '. ' + parse_paragraph(line["content"][0])
            elif blob["type"] == "paragraph":
                yield parse_paragraph(blob)


def parse_special_summary(issue):
    parts = issue['summary'].split('=')
    for index, part in enumerate(parts):
        if part[-4:] == 'json':
            parsed = json.loads(parts[index + 1][:-1])
            print(json.dumps(parsed, indent=4, sort_keys=True))

def summarize_meaningfull_issues():
    resp, url = search_jql(jql=os.getenv('JQL_EXAMPLE'))
    parsed = json.loads(resp.text)
    return [{
        "key": issue["key"],
        "creator": issue["fields"]["creator"]["displayName"],
        "assignee": issue["fields"]["assignee"]["displayName"] if issue["fields"]["assignee"] else "",
        "status": issue["fields"]["status"]["name"],
        "summary": issue["fields"]["summary"],
        # "summary": issue["fields"]["customfield_11000"],
        "url": issue["self"],
        # "id": issue["id"],
        "storypoints": issue["fields"]["customfield_10004"],
        # "description": '\n'.join(parse_description(issue["fields"]["description"]))
    } for issue in parsed["issues"] if issue["fields"]["status"]["name"] != "Closed"]


if __name__ == '__main__':
    print(json.dumps(list(summarize_meaningfull_issues()), indent=4))
