#!/usr/bin/env python3
"""Fetch GitHub contribution calendar + profile data via GraphQL and cache as JSON."""
import json, os, sys, urllib.request

TOKEN = os.environ.get("GH_TOKEN")
USER = os.environ.get("GH_USER", "Pushyanth02")
OUT = sys.argv[1] if len(sys.argv) > 1 else "dist/user-data.json"

QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    login name avatarUrl createdAt
    followers { totalCount }
    following { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      nodes { stargazerCount forkCount primaryLanguage { name } }
    }
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount color } }
      }
    }
  }
}
"""

def gql(query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json",
                 "User-Agent": "profile-art-script"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

import datetime as dt
to = dt.datetime.now(dt.timezone.utc)
from_ = to - dt.timedelta(days=371)
res = gql(QUERY, {"login": USER, "from": from_.isoformat(), "to": to.isoformat()})
if "errors" in res:
    print(json.dumps(res["errors"], indent=2)); sys.exit(1)
u = res["data"]["user"]

repos = u["repositories"]["nodes"]
stars = sum(r["stargazerCount"] for r in repos)
data = {
    "login": u["login"],
    "name": u["name"] or u["login"],
    "avatarUrl": u["avatarUrl"],
    "createdAt": u["createdAt"],
    "followers": u["followers"]["totalCount"],
    "following": u["following"]["totalCount"],
    "repos": u["repositories"]["totalCount"],
    "stars": stars,
    "totalContributions": u["contributionsCollection"]["contributionCalendar"]["totalContributions"],
    "weeks": u["contributionsCollection"]["contributionCalendar"]["weeks"],
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w") as f:
    json.dump(data, f)
print(f"OK: {data['login']} total={data['totalContributions']} repos={data['repos']} stars={data['stars']} followers={data['followers']} weeks={len(data['weeks'])}")
