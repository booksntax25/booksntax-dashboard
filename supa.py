"""Supabase read/write helpers for the BooksNTax Social Dashboard.

Credentials come from Streamlit secrets (set in the Streamlit Cloud dashboard,
or in .streamlit/secrets.toml when running locally).
"""
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from supabase import create_client


@st.cache_resource
def get_client():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)


def _now():
    return datetime.now(timezone.utc).isoformat()


# ---- writes ----
def save_videos(videos):
    """Upsert each video and append a fresh stats snapshot for history."""
    if not videos:
        return
    client = get_client()
    now = _now()
    rows = []
    history = []
    for v in videos:
        v = {**v, "last_fetched_at": now}
        rows.append(v)
        history.append({
            "platform": v.get("platform"),
            "platform_video_id": v.get("platform_video_id"),
            "captured_at": now,
            "views": v.get("views"),
            "likes": v.get("likes"),
            "comments": v.get("comments"),
        })
    client.table("videos").upsert(
        rows, on_conflict="platform,platform_video_id"
    ).execute()
    client.table("stats_history").insert(history).execute()


def save_demographics(platform, demo_rows):
    """Append a demographics snapshot (one batch per fetch)."""
    if not demo_rows:
        return
    client = get_client()
    now = _now()
    rows = [{**r, "platform": platform, "captured_at": now} for r in demo_rows]
    client.table("channel_demographics").insert(rows).execute()


# ---- reads ----
def _df(table):
    client = get_client()
    res = client.table(table).select("*").execute()
    return pd.DataFrame(res.data or [])


def load_videos():
    return _df("videos")


def load_history():
    return _df("stats_history")


def load_demographics():
    """Return only the most recent demographics snapshot per platform/dimension.

    Uses transform('max') so the 'latest' value stays row-aligned with the
    full frame — a plain groupby().max() returns a shorter Series and pandas
    raises 'Can only compare identically-labeled Series objects'.
    """
    df = _df("channel_demographics")
    if df.empty:
        return df

    df["captured_at"] = pd.to_datetime(df["captured_at"], errors="coerce", utc=True)
    df = df.dropna(subset=["captured_at"])
    if df.empty:
        return df

    keys = [c for c in ["platform", "dimension"] if c in df.columns]
    if keys:
        latest = df.groupby(keys)["captured_at"].transform("max")
    else:
        latest = df["captured_at"].max()

    return df[df["captured_at"].eq(latest)].reset_index(drop=True)
