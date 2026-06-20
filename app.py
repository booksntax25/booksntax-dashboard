"""BooksNTax — Social Dashboard (YouTube stage).

Run locally:   streamlit run app.py
Deployed:      Streamlit Community Cloud reads this file automatically.
"""
import calendar as calmod

import pandas as pd
import plotly.express as px
import streamlit as st

import supa

# ---------------------------------------------------------------- palette ----
INK = "#0B2A22"
PRIMARY = "#0E7C66"
PRIMARY_DARK = "#0A574A"
GOLD = "#D4A53A"
MUTED = "#6B7E78"
GRID = "#E7EEEB"
SEQ = [PRIMARY, GOLD, "#3AA188", "#86C6B6", "#B6891E", "#0A574A"]

PLATFORM_ICON = {"youtube": "▶️", "instagram": "📸"}

st.set_page_config(page_title="BooksNTax · Social Dashboard", page_icon="📊", layout="wide")

# ------------------------------------------------------------------- style ---
st.markdown(
    f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
      html, body, [class*="css"], .stApp {{ font-family: 'Inter', sans-serif; }}
      .block-container {{ padding-top: 1.4rem; max-width: 1300px; }}

      .bnt-header {{
        background: linear-gradient(120deg, {PRIMARY} 0%, {PRIMARY_DARK} 100%);
        padding: 26px 30px; border-radius: 18px; color: #fff; margin-bottom: 22px;
        box-shadow: 0 10px 30px -12px rgba(11,42,34,.45);
        border-bottom: 3px solid {GOLD};
      }}
      .bnt-header h1 {{ margin: 0; font-size: 1.75rem; font-weight: 800; letter-spacing: -.2px; }}
      .bnt-header p  {{ margin: 6px 0 0; opacity: .9; font-size: .96rem; font-weight: 400; }}

      /* KPI cards */
      div[data-testid="stMetric"] {{
        background: #fff; border: 1px solid {GRID}; border-radius: 16px;
        padding: 16px 18px; box-shadow: 0 4px 16px -10px rgba(11,42,34,.25);
      }}
      div[data-testid="stMetricLabel"] p {{
        font-size: .72rem !important; text-transform: uppercase;
        letter-spacing: .6px; color: {MUTED} !important; font-weight: 600;
      }}
      div[data-testid="stMetricValue"] {{ color: {INK}; font-weight: 700; }}

      /* section headings */
      .bnt-sec {{
        font-size: 1.12rem; font-weight: 700; color: {INK};
        margin: 26px 0 10px; padding-left: 12px; border-left: 4px solid {GOLD};
      }}
      .bnt-cap {{ color: {MUTED}; font-size: .84rem; margin-top: -4px; }}

      /* spotlight */
      .bnt-spot {{
        background: #fff; border: 1px solid {GRID}; border-left: 5px solid {PRIMARY};
        border-radius: 14px; padding: 16px 20px; box-shadow: 0 4px 16px -10px rgba(11,42,34,.25);
      }}

      /* calendar */
      .cal {{ width: 100%; border-collapse: separate; border-spacing: 6px; }}
      .cal th {{ color: {MUTED}; font-size: .72rem; font-weight: 600; text-transform: uppercase; padding-bottom: 4px; }}
      .cal td {{
        height: 64px; width: 14.2%; vertical-align: top; border-radius: 10px;
        background: #fff; border: 1px solid {GRID}; padding: 6px 8px;
      }}
      .cal td.empty {{ background: transparent; border: none; }}
      .cal td.has {{ background: #F0F8F5; border: 1px solid {PRIMARY}; }}
      .cal .daynum {{ font-size: .78rem; color: {MUTED}; font-weight: 600; }}
      .cal .icons {{ font-size: 1.05rem; margin-top: 6px; }}
    </style>
    <div class="bnt-header">
      <h1>📊 BooksNTax — Social Dashboard</h1>
      <p>Short-form video performance · views, engagement, retention & audience</p>
    </div>
    """,
    unsafe_allow_html=True,
)


def section(title, caption=None):
    st.markdown(f'<div class="bnt-sec">{title}</div>', unsafe_allow_html=True)
    if caption:
        st.markdown(f'<div class="bnt-cap">{caption}</div>', unsafe_allow_html=True)


def style_fig(fig, height=380):
    fig.update_layout(
        height=height, font=dict(family="Inter", color=INK, size=13),
        margin=dict(l=10, r=10, t=42, b=10), plot_bgcolor="white", paper_bgcolor="white",
        title_font=dict(size=15, color=INK),
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False)
    fig.update_yaxes(gridcolor=GRID, zeroline=False)
    return fig


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
    st.divider()

# --------------------------------------------------------------------- data ---
try:
    df = supa.load_videos()
except Exception as e:
    st.error(f"Couldn't reach the database. Check your Supabase secrets.\n\n{e}")
    st.stop()

if df.empty:
    st.info("No data yet — click **🔄 Fetch latest data** in the sidebar.")
    st.stop()

df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce", utc=True)
for c in ["views", "likes", "comments", "watch_time_minutes",
          "avg_view_duration_seconds", "avg_view_percentage", "duration_seconds"]:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")
try:  # show post dates in the creator's local time, not UTC
    df["published_at"] = df["published_at"].dt.tz_convert("Australia/Melbourne")
except Exception:
    pass
df["short_title"] = df["title"].fillna("(untitled)").str.slice(0, 46)

# ----- sidebar filters (built after data so options reflect what's loaded) ---
with st.sidebar:
    platforms = sorted(df["platform"].dropna().unique())
    if len(platforms) > 1:
        chosen = st.multiselect("Platform", platforms, default=platforms,
                                format_func=lambda p: f"{PLATFORM_ICON.get(p,'')} {p.title()}")
        df = df[df["platform"].isin(chosen)]
    only_shorts = st.toggle("Shorts only (≤ 3 min)", value=False)
    if only_shorts and "is_short" in df.columns:
        df = df[df["duration_seconds"].fillna(9999) <= 180]

    st.divider()
    title_by_id = {r.platform_video_id: r.short_title for r in df.itertuples()}
    spotlight = st.selectbox(
        "🔍 Spotlight a video",
        options=["__all__"] + list(title_by_id.keys()),
        format_func=lambda k: "All videos" if k == "__all__" else title_by_id.get(k, k),
    )

if df.empty:
    st.warning("No videos match the current filters.")
    st.stop()

# ------------------------------------------------------------- spotlight ---
if spotlight != "__all__":
    row = df[df["platform_video_id"] == spotlight]
    if not row.empty:
        r = row.iloc[0]
        pct = r["avg_view_percentage"]
        pct_txt = f"{pct:.0f}%" if pd.notna(pct) else "—"
        section("🔍 Video spotlight")
        st.markdown(
            f"""<div class="bnt-spot">
            <div style="font-weight:700;color:{INK};font-size:1.02rem;margin-bottom:8px">
              {PLATFORM_ICON.get(r['platform'],'')} {(r['title'] or '')[:90]}</div>
            <div style="color:{MUTED};font-size:.86rem">
              Views <b style="color:{INK}">{int(r['views'] or 0):,}</b> &nbsp;·&nbsp;
              Likes <b style="color:{INK}">{int(r['likes'] or 0):,}</b> &nbsp;·&nbsp;
              Comments <b style="color:{INK}">{int(r['comments'] or 0):,}</b> &nbsp;·&nbsp;
              % watched <b style="color:{INK}">{pct_txt}</b></div>
            <div style="margin-top:8px"><a href="{r['url']}" target="_blank">Open video ↗</a></div>
            </div>""",
            unsafe_allow_html=True,
        )
        st.caption("Per-video audience (age/gender/location) isn't shown — YouTube only "
                   "releases demographics for a single video once it has enough viewers.")

# --------------------------------------------------------- summary metrics ---
section("Overview")
total = len(df)
views = int(df["views"].fillna(0).sum())
avg_views = int(df["views"].fillna(0).mean()) if total else 0
likes = int(df["likes"].fillna(0).sum())
comments = int(df["comments"].fillna(0).sum())
eng_rate = round(100 * (likes + comments) / views, 2) if views else 0
aw = df["avg_view_percentage"].dropna().mean() if "avg_view_percentage" in df else None
avg_watched = f"{aw:.0f}%" if aw is not None and pd.notna(aw) else "—"

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Videos", f"{total:,}")
c2.metric("Total views", f"{views:,}")
c3.metric("Avg views", f"{avg_views:,}")
c4.metric("Engagement", f"{eng_rate}%")
c5.metric("Likes", f"{likes:,}")
c6.metric("Avg % watched", avg_watched)

# ------------------------------------------------------------- top + cadence ---
left, right = st.columns(2)
with left:
    section("Top videos by views")
    top = df.sort_values("views", ascending=False, na_position="last").head(10)
    fig = px.bar(top, x="views", y="short_title", orientation="h",
                 color_discrete_sequence=[PRIMARY])
    fig.update_layout(yaxis={"categoryorder": "total ascending", "title": ""})
    left.plotly_chart(style_fig(fig, 420), use_container_width=True)

with right:
    section("Videos posted per month")
    cad = df.dropna(subset=["published_at"]).copy()
    if not cad.empty:
        cad["m"] = cad["published_at"].dt.tz_localize(None).dt.to_period("M").dt.to_timestamp()
        g = cad.groupby("m").size().reset_index(name="videos").sort_values("m")
        g["label"] = g["m"].dt.strftime("%b %Y")
        fig = px.bar(g, x="label", y="videos", color_discrete_sequence=[GOLD], text="videos")
        fig.update_xaxes(type="category", title="")
        right.plotly_chart(style_fig(fig, 420), use_container_width=True)

# ----------------------------------------------------------- calendar view ---
section("Posting calendar", "Days you posted are highlighted. ▶️ YouTube · 📸 Instagram")
caldf = df.dropna(subset=["published_at"]).copy()
if not caldf.empty:
    caldf["ym"] = caldf["published_at"].dt.tz_localize(None).dt.to_period("M")
    months = sorted(caldf["ym"].unique(), reverse=True)
    pick = st.selectbox("Month", months, format_func=lambda p: p.strftime("%B %Y"))
    year, month = pick.year, pick.month
    sub = caldf[caldf["ym"] == pick]
    posts_by_day = {}
    for _, rr in sub.iterrows():
        d = rr["published_at"].day
        posts_by_day.setdefault(d, set()).add(rr["platform"])

    cal = calmod.Calendar(firstweekday=6)  # Sunday first
    head = "".join(f"<th>{w}</th>" for w in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"])
    body = ""
    for week in cal.monthdayscalendar(year, month):
        body += "<tr>"
        for day in week:
            if day == 0:
                body += '<td class="empty"></td>'
                continue
            plats = posts_by_day.get(day)
            cls = "has" if plats else ""
            icons = "".join(PLATFORM_ICON.get(p, "•") for p in sorted(plats)) if plats else ""
            body += (f'<td class="{cls}"><div class="daynum">{day}</div>'
                     f'<div class="icons">{icons}</div></td>')
        body += "</tr>"
    st.markdown(f'<table class="cal"><tr>{head}</tr>{body}</table>', unsafe_allow_html=True)

# --------------------------------------------------------------- retention ---
ret = df.dropna(subset=["avg_view_percentage"]) if "avg_view_percentage" in df else df.iloc[0:0]
if not ret.empty:
    section("How much of each video people watch", "Higher = people stay longer. 100% − this ≈ average skip.")
    r2 = ret.sort_values("avg_view_percentage", ascending=False).head(15)
    fig = px.bar(r2, x="avg_view_percentage", y="short_title", orientation="h",
                 color="avg_view_percentage", color_continuous_scale="Greens",
                 labels={"avg_view_percentage": "% watched", "short_title": ""})
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
    st.plotly_chart(style_fig(fig, 440), use_container_width=True)

# -------------------------------------------------------------- demographics ---
demo = supa.load_demographics()
if not demo.empty:
    demo = demo[demo["platform"] == "youtube"]
section("Audience", "Shown for the whole channel — YouTube doesn't break audience down per video at low view counts.")
if not demo.empty:
    d1, d2, d3 = st.columns(3)
    age = demo[demo["dimension"] == "age"].sort_values("bucket")
    if not age.empty:
        fig = px.bar(age, x="bucket", y="percentage", color_discrete_sequence=[PRIMARY],
                     title="Age", labels={"bucket": "", "percentage": "%"})
        d1.plotly_chart(style_fig(fig, 320), use_container_width=True)
    gen = demo[demo["dimension"] == "gender"]
    if not gen.empty:
        fig = px.pie(gen, names="bucket", values="percentage", hole=.55,
                     color_discrete_sequence=SEQ, title="Gender")
        d2.plotly_chart(style_fig(fig, 320), use_container_width=True)
    ctry = demo[demo["dimension"] == "country"].sort_values("percentage", ascending=False)
    if not ctry.empty:
        fig = px.bar(ctry, x="percentage", y="bucket", orientation="h",
                     color_discrete_sequence=[GOLD], title="Top countries",
                     labels={"bucket": "", "percentage": "% of views"})
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        d3.plotly_chart(style_fig(fig, 320), use_container_width=True)
else:
    st.caption("👥 Audience charts appear once videos pass YouTube's minimum-views threshold.")

# ------------------------------------------------------------ view growth ---
hist = supa.load_history()
if not hist.empty:
    hist["captured_at"] = pd.to_datetime(hist["captured_at"], errors="coerce", utc=True)
    daily = hist.assign(day=hist["captured_at"].dt.date).groupby("day")["views"].sum().reset_index()
    if daily["day"].nunique() > 1:
        section("Total view growth over time")
        fig = px.line(daily, x="day", y="views", markers=True, color_discrete_sequence=[PRIMARY])
        st.plotly_chart(style_fig(fig, 320), use_container_width=True)

# ------------------------------------------------------------------- table ---
section("All videos")
cols = [c for c in ["platform", "title", "published_at", "views", "likes", "comments",
                    "avg_view_percentage", "url"] if c in df.columns]
st.dataframe(
    df[cols].sort_values("views", ascending=False, na_position="last"),
    use_container_width=True, hide_index=True,
    column_config={
        "platform": st.column_config.TextColumn("platform"),
        "url": st.column_config.LinkColumn("link", display_text="open"),
        "avg_view_percentage": st.column_config.NumberColumn("% watched", format="%.0f"),
    },
)
