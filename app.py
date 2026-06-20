"""BooksNTax — Social Dashboard (YouTube stage).

Run locally:   streamlit run app.py
Deployed:      Streamlit Community Cloud reads this file automatically.
"""
import pandas as pd
import plotly.express as px
import streamlit as st

import supa

# ---------------------------------------------------------------- branding ---
BRAND = "BooksNTax"
GREEN = "#15795F"
GOLD = "#C9A227"
PALETTE = ["#15795F", "#C9A227", "#2E9E80", "#5BB89F", "#8A6D1A", "#0E5946"]

st.set_page_config(page_title=f"{BRAND} · Social Dashboard", page_icon="📊", layout="wide")

st.markdown(
    f"""
    <style>
      .block-container {{ padding-top: 1.5rem; }}
      .bnt-header {{
        background: linear-gradient(110deg, {GREEN} 0%, #0E5946 100%);
        padding: 22px 28px; border-radius: 16px; color: #fff; margin-bottom: 18px;
      }}
      .bnt-header h1 {{ margin: 0; font-size: 1.7rem; letter-spacing: .3px; }}
      .bnt-header p  {{ margin: 4px 0 0; opacity: .85; font-size: .95rem; }}
      div[data-testid="stMetric"] {{
        background: #F2F6F4; border: 1px solid #E3ECE8;
        border-radius: 14px; padding: 14px 16px;
      }}
    </style>
    <div class="bnt-header">
      <h1>📊 {BRAND} — Social Dashboard</h1>
      <p>YouTube Shorts performance · views, engagement, retention & audience</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------ sidebar ---
with st.sidebar:
    st.subheader("Controls")
    if st.button("🔄 Fetch latest data", use_container_width=True):
        try:
            with st.spinner("Pulling from YouTube…"):
                from youtube_client import fetch_youtube
                yt = st.secrets["youtube"]
                channel, videos, demo = fetch_youtube(
                    yt["client_id"], yt["client_secret"], yt["refresh_token"]
                )
                supa.save_videos(videos)
                supa.save_demographics("youtube", demo)
            st.success(f"{channel}: {len(videos)} videos updated.")
            st.rerun()
        except Exception as e:
            st.error(f"Fetch failed: {e}")

# --------------------------------------------------------------------- data ---
try:
    df = supa.load_videos()
except Exception as e:
    st.error(f"Couldn't reach the database. Check your Supabase secrets.\n\n{e}")
    st.stop()

if df.empty:
    st.info("No data yet — click **🔄 Fetch latest data** in the sidebar. "
            "(First make sure your secrets and Supabase tables are set up — see README.)")
    st.stop()

# tidy types
df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce", utc=True)
for c in ["views", "likes", "comments", "watch_time_minutes",
          "avg_view_duration_seconds", "avg_view_percentage", "duration_seconds"]:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

# Shorts filter (default on, since the brand focus is Shorts)
only_shorts = st.sidebar.toggle("Shorts only (≤ 60s)", value=True)
if only_shorts and "is_short" in df.columns:
    df = df[df["is_short"] == True]  # noqa: E712

if df.empty:
    st.warning("No videos match the current filter.")
    st.stop()

# --------------------------------------------------------- summary metrics ---
total = len(df)
views = int(df["views"].fillna(0).sum())
avg_views = int(df["views"].fillna(0).mean()) if total else 0
likes = int(df["likes"].fillna(0).sum())
comments = int(df["comments"].fillna(0).sum())
eng_rate = round(100 * (likes + comments) / views, 2) if views else 0
avg_watched = round(df["avg_view_percentage"].dropna().mean(), 1) if "avg_view_percentage" in df else None

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Videos", f"{total:,}")
c2.metric("Total views", f"{views:,}")
c3.metric("Avg views", f"{avg_views:,}")
c4.metric("Engagement", f"{eng_rate}%")
c5.metric("Likes", f"{likes:,}")
c6.metric("Avg % watched", f"{avg_watched}%" if avg_watched is not None else "—")

st.markdown(" ")

# ------------------------------------------------------------- top + cadence ---
left, right = st.columns(2)

top = df.sort_values("views", ascending=False, na_position="last").head(10)
fig_top = px.bar(top, x="views", y="title", orientation="h",
                 color_discrete_sequence=[GREEN], title="Top videos by views")
fig_top.update_layout(yaxis={"categoryorder": "total ascending", "title": ""},
                      height=420, margin=dict(l=10, r=10, t=50, b=10))
left.plotly_chart(fig_top, use_container_width=True)

cad = df.dropna(subset=["published_at"]).copy()
if not cad.empty:
    cad["month"] = cad["published_at"].dt.to_period("M").dt.to_timestamp()
    cad_g = cad.groupby("month").size().reset_index(name="videos")
    fig_cad = px.bar(cad_g, x="month", y="videos",
                     color_discrete_sequence=[GOLD], title="Videos posted per month")
    fig_cad.update_layout(height=420, margin=dict(l=10, r=10, t=50, b=10))
    right.plotly_chart(fig_cad, use_container_width=True)

# --------------------------------------------------------------- retention ---
ret = df.dropna(subset=["avg_view_percentage"])
if not ret.empty:
    st.subheader("How much of each video people watch")
    ret_top = ret.sort_values("avg_view_percentage", ascending=False).head(15)
    fig_ret = px.bar(ret_top, x="avg_view_percentage", y="title", orientation="h",
                     color="avg_view_percentage", color_continuous_scale="Greens",
                     labels={"avg_view_percentage": "% watched"})
    fig_ret.update_layout(yaxis={"categoryorder": "total ascending", "title": ""},
                          height=440, margin=dict(l=10, r=10, t=10, b=10),
                          coloraxis_showscale=False)
    st.plotly_chart(fig_ret, use_container_width=True)
    st.caption("Higher = people stay longer. (100% − this ≈ average skip.)")

# -------------------------------------------------------------- demographics ---
demo = supa.load_demographics()
if not demo.empty:
    demo = demo[demo["platform"] == "youtube"]
if not demo.empty:
    st.subheader("Audience")
    dcols = st.columns(3)

    age = demo[demo["dimension"] == "age"].sort_values("bucket")
    if not age.empty:
        fig_age = px.bar(age, x="bucket", y="percentage",
                         color_discrete_sequence=[GREEN], title="Age", labels={"bucket": ""})
        fig_age.update_layout(height=320, margin=dict(l=10, r=10, t=50, b=10))
        dcols[0].plotly_chart(fig_age, use_container_width=True)

    gen = demo[demo["dimension"] == "gender"]
    if not gen.empty:
        fig_gen = px.pie(gen, names="bucket", values="percentage", hole=.5,
                         color_discrete_sequence=PALETTE, title="Gender")
        fig_gen.update_layout(height=320, margin=dict(l=10, r=10, t=50, b=10))
        dcols[1].plotly_chart(fig_gen, use_container_width=True)

    ctry = demo[demo["dimension"] == "country"].sort_values("percentage", ascending=False)
    if not ctry.empty:
        fig_ctry = px.bar(ctry, x="percentage", y="bucket", orientation="h",
                          color_discrete_sequence=[GOLD], title="Top countries",
                          labels={"bucket": "", "percentage": "% of views"})
        fig_ctry.update_layout(yaxis={"categoryorder": "total ascending"},
                               height=320, margin=dict(l=10, r=10, t=50, b=10))
        dcols[2].plotly_chart(fig_ctry, use_container_width=True)
else:
    st.caption("👥 Audience demographics will appear here once your videos pass "
               "YouTube's minimum view threshold for showing them.")

# ------------------------------------------------------------ view growth ---
hist = supa.load_history()
if not hist.empty:
    hist["captured_at"] = pd.to_datetime(hist["captured_at"], errors="coerce", utc=True)
    daily = (hist.assign(day=hist["captured_at"].dt.date)
             .groupby("day")["views"].sum().reset_index())
    if daily["day"].nunique() > 1:
        st.subheader("Total view growth over time")
        fig_g = px.line(daily, x="day", y="views", markers=True,
                        color_discrete_sequence=[GREEN])
        fig_g.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_g, use_container_width=True)

# ------------------------------------------------------------------- table ---
st.subheader("All videos")
cols = [c for c in ["title", "published_at", "views", "likes", "comments",
                    "avg_view_percentage", "watch_time_minutes", "url"] if c in df.columns]
st.dataframe(
    df[cols].sort_values("views", ascending=False, na_position="last"),
    use_container_width=True, hide_index=True,
    column_config={"url": st.column_config.LinkColumn("link", display_text="open"),
                   "avg_view_percentage": st.column_config.NumberColumn("% watched", format="%.1f")},
)
