"""Fetch your YouTube channel's videos + Studio insights using a stored refresh
token, so it works on a server with no interactive login.

Returns:
  channel_title, videos (list of dicts), demographics (list of dicts)

Insights included:
  - per video: views, likes, comments, watch time, avg view duration,
    avg view percentage (the "% watched" / skip proxy)
  - channel: viewer age, gender, and top countries (where YouTube has enough data)
"""
import re
from datetime import datetime, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]
TOKEN_URI = "https://oauth2.googleapis.com/token"


def _build_services(client_id, client_secret, refresh_token):
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=TOKEN_URI,
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )
    creds.refresh(Request())  # exchange refresh token for a fresh access token
    yt = build("youtube", "v3", credentials=creds)
    yta = build("youtubeAnalytics", "v2", credentials=creds)
    return yt, yta


def _iso8601_to_seconds(duration):
    if not duration:
        return None
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
    if not m:
        return None
    h, mn, s = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mn * 60 + s


def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def fetch_youtube(client_id, client_secret, refresh_token):
    yt, yta = _build_services(client_id, client_secret, refresh_token)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # 1. Channel + uploads playlist
    ch = yt.channels().list(part="contentDetails,snippet", mine=True).execute()
    if not ch.get("items"):
        raise RuntimeError("No channel found for this Google account.")
    info = ch["items"][0]
    channel_title = info["snippet"]["title"]
    uploads = info["contentDetails"]["relatedPlaylists"]["uploads"]

    # 2. Collect every uploaded video id
    video_ids, page = [], None
    while True:
        pl = yt.playlistItems().list(
            part="contentDetails", playlistId=uploads, maxResults=50, pageToken=page
        ).execute()
        video_ids += [it["contentDetails"]["videoId"] for it in pl.get("items", [])]
        page = pl.get("nextPageToken")
        if not page:
            break

    # 3. Details + lifetime stats (batches of 50)
    videos = []
    for i in range(0, len(video_ids), 50):
        vr = yt.videos().list(
            part="snippet,statistics,contentDetails",
            id=",".join(video_ids[i:i + 50]),
        ).execute()
        for v in vr.get("items", []):
            sn, stt, cd = v.get("snippet", {}), v.get("statistics", {}), v.get("contentDetails", {})
            secs = _iso8601_to_seconds(cd.get("duration"))
            videos.append({
                "platform": "youtube",
                "platform_video_id": v["id"],
                "title": sn.get("title"),
                "url": f"https://www.youtube.com/watch?v={v['id']}",
                "published_at": sn.get("publishedAt"),
                "views": _to_int(stt.get("viewCount")),
                "likes": _to_int(stt.get("likeCount")),
                "comments": _to_int(stt.get("commentCount")),
                "duration_seconds": secs,
                "is_short": (secs is not None and secs <= 60),
                "thumbnail_url": sn.get("thumbnails", {}).get("medium", {}).get("url"),
                "watch_time_minutes": None,
                "avg_view_duration_seconds": None,
                "avg_view_percentage": None,
            })

    # 4. Per-video watch metrics (best effort)
    try:
        rep = yta.reports().query(
            ids="channel==MINE", startDate="2005-01-01", endDate=today,
            metrics="estimatedMinutesWatched,averageViewDuration,averageViewPercentage",
            dimensions="video", maxResults=500, sort="-estimatedMinutesWatched",
        ).execute()
        cols = [c["name"] for c in rep.get("columnHeaders", [])]
        by_video = {dict(zip(cols, r))["video"]: dict(zip(cols, r)) for r in rep.get("rows", [])}
        for v in videos:
            a = by_video.get(v["platform_video_id"])
            if a:
                v["watch_time_minutes"] = a.get("estimatedMinutesWatched")
                v["avg_view_duration_seconds"] = a.get("averageViewDuration")
                v["avg_view_percentage"] = a.get("averageViewPercentage")
    except Exception as e:
        print(f"[youtube] watch metrics skipped: {e}")

    # 5. Channel demographics (best effort; YouTube hides low-volume data)
    demographics = []
    demographics += _safe_demo(yta, today, "age", "viewerPercentage", "ageGroup")
    demographics += _safe_demo(yta, today, "gender", "viewerPercentage", "gender")
    demographics += _safe_country(yta, today)

    return channel_title, videos, demographics


def _safe_demo(yta, today, label, metric, dimension):
    try:
        rep = yta.reports().query(
            ids="channel==MINE", startDate="2005-01-01", endDate=today,
            metrics=metric, dimensions=dimension,
        ).execute()
        cols = [c["name"] for c in rep.get("columnHeaders", [])]
        out = []
        for r in rep.get("rows", []):
            rd = dict(zip(cols, r))
            out.append({"dimension": label, "bucket": str(rd.get(dimension)),
                        "percentage": rd.get(metric)})
        return out
    except Exception as e:
        print(f"[youtube] {label} demographics skipped: {e}")
        return []


def _safe_country(yta, today):
    try:
        rep = yta.reports().query(
            ids="channel==MINE", startDate="2005-01-01", endDate=today,
            metrics="views", dimensions="country", sort="-views", maxResults=10,
        ).execute()
        cols = [c["name"] for c in rep.get("columnHeaders", [])]
        rows = [dict(zip(cols, r)) for r in rep.get("rows", [])]
        total = sum((rd.get("views") or 0) for rd in rows) or 1
        return [{"dimension": "country", "bucket": rd.get("country"),
                 "percentage": round(100 * (rd.get("views") or 0) / total, 1)} for rd in rows]
    except Exception as e:
        print(f"[youtube] country demographics skipped: {e}")
        return []
