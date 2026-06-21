"""Fetch BooksNTax Instagram Reels + audience demographics via the Instagram
Graph API, using a stored long-lived Page access token (no interactive login,
so it works on a server exactly like the YouTube refresh-token setup).

Secrets needed (Streamlit Cloud -> Settings -> Secrets), added alongside your
existing [youtube] and [supabase] blocks:

    [instagram]
    ig_user_id   = "YOUR_INSTAGRAM_BUSINESS_ACCOUNT_ID"
    access_token = "YOUR_LONG_LIVED_PAGE_ACCESS_TOKEN"
"""
import requests
import streamlit as st

GRAPH = "https://graph.facebook.com/v22.0"


def _cfg():
    ig = st.secrets["instagram"]
    return ig["ig_user_id"], ig["access_token"]


def _get(path, params):
    r = requests.get(f"{GRAPH}/{path}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def fetch_reels():
    """Return a list of Reels as dicts shaped like the YouTube videos, so they
    flow through supa.save_videos() and the existing dashboard unchanged."""
    ig_user_id, token = _cfg()
    fields = ("id,caption,media_type,media_product_type,permalink,"
              "timestamp,like_count,comments_count")
    videos = []
    data = _get(f"{ig_user_id}/media",
                {"fields": fields, "access_token": token, "limit": 50})
    while True:
        for m in data.get("data", []):
            # Reels only -- the Instagram equivalent of your "Shorts only" filter.
            if m.get("media_product_type") != "REELS":
                continue
            caption = (m.get("caption") or "").strip()
            title = caption.split("\n")[0][:200] if caption else "(no caption)"
            videos.append({
                "platform": "instagram",
                "platform_video_id": m["id"],
                "title": title,
                "url": m.get("permalink"),
                "published_at": m.get("timestamp"),
                "views": _reel_views(m["id"], token),
                "likes": m.get("like_count"),
                "comments": m.get("comments_count"),
            })
        nxt = data.get("paging", {}).get("next")
        if not nxt:
            break
        r = requests.get(nxt, timeout=30)
        r.raise_for_status()
        data = r.json()
    return videos


def _reel_views(media_id, token):
    """Reels report plays under the 'views' metric in current API versions;
    fall back to 'reach' if a particular Reel hasn't populated 'views' yet."""
    for metric in ("views", "reach"):
        try:
            j = _get(f"{media_id}/insights",
                     {"metric": metric, "access_token": token})
            vals = j.get("data", [])
            if vals and vals[0].get("values"):
                return vals[0]["values"][0].get("value")
        except requests.HTTPError:
            continue
    return None


def fetch_demographics():
    """Audience age / gender / country for your own account, shaped exactly like
    the YouTube demographics rows the dashboard renders:
        {"dimension": "age"|"gender"|"country", "bucket": str, "percentage": float}
    Counts are normalised to a % within each dimension. Returns [] quietly if
    Instagram withholds it (it needs ~100+ followers before it will report)."""
    ig_user_id, token = _cfg()
    gmap = {"F": "Female", "M": "Male", "U": "Unknown"}
    rows = []
    for breakdown, dim in (("age", "age"), ("gender", "gender"),
                           ("country", "country")):
        try:
            j = _get(f"{ig_user_id}/insights", {
                "metric": "follower_demographics",
                "period": "lifetime",
                "metric_type": "total",
                "breakdown": breakdown,
                "access_token": token,
            })
            data = j.get("data", [])
            if not data:
                continue
            breakdowns = data[0].get("total_value", {}).get("breakdowns", [])
            if not breakdowns:
                continue
            results = breakdowns[0].get("results", [])
            total = sum(r.get("value", 0) for r in results) or 1
            for item in results:
                dv = item.get("dimension_values", [])
                label = dv[0] if dv else "Unknown"
                if dim == "gender":
                    label = gmap.get(label, label)
                rows.append({
                    "dimension": dim,
                    "bucket": label,
                    "percentage": round(100 * item.get("value", 0) / total, 1),
                })
        except requests.HTTPError:
            continue
    return rows
