"""BooksNTax — Social Dashboard (YouTube stage)."""
import calendar as calmod
import re

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import supa

# ---------------------------------------------------------------- palette ----
PRIMARY = "#6C5CE7"        # violet / indigo
PRIMARY_DARK = "#4A36C9"
ACCENT = "#06B6D4"         # cyan, used sparingly
INK = "#1E1B3A"
MUTED = "#6E6B8A"
GRID = "#ECECF6"
SEQ = ["#6C5CE7", "#06B6D4", "#9B8CFF", "#F472B6", "#22C55E", "#4A36C9"]
PLATFORM_ICON = {"youtube": "▶️", "instagram": "📸"}

st.set_page_config(page_title="BooksNTax · Social Dashboard", page_icon="📊", layout="wide")

# ------------------------------------------------------------------- style ---
st.markdown(
    f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
      html, body, [class*="css"], .stApp {{ font-family: 'Inter', sans-serif; }}
      .block-container {{ padding-top: 1.3rem; max-width: 1320px; }}
      .stApp {{ background: #F6F6FB; }}

      .bnt-header {{
        background: linear-gradient(120deg, #7B6BF0 0%, {PRIMARY_DARK} 100%);
        padding: 26px 30px; border-radius: 20px; color: #fff; margin-bottom: 22px;
        box-shadow: 0 16px 40px -16px rgba(76,54,201,.55);
        border-bottom: 3px solid {ACCENT};
      }}
      .bnt-header h1 {{ margin: 0; font-size: 1.8rem; font-weight: 800; letter-spacing: -.3px; }}
      .bnt-header p  {{ margin: 6px 0 0; opacity: .92; font-size: .96rem; }}

      div[data-testid="stMetric"] {{
        background: #fff; border: 1px solid {GRID}; border-radius: 16px;
        padding: 16px 18px; box-shadow: 0 6px 20px -14px rgba(30,27,58,.4);
      }}
      div[data-testid="stMetricLabel"] p {{
        font-size: .72rem !important; text-transform: uppercase; letter-spacing: .6px;
        color: {MUTED} !important; font-weight: 600;
      }}
      div[data-testid="stMetricValue"] {{ color: {INK}; font-weight: 700; }}

      .bnt-sec {{ font-size: 1.14rem; font-weight: 700; color: {INK};
        margin: 26px 0 10px; padding-left: 12px; border-left: 4px solid {PRIMARY}; }}
      .bnt-cap {{ color: {MUTED}; font-size: .84rem; margin-top: -4px; }}

      .bnt-spot {{ background: linear-gradient(120deg,#fff,#F5F3FF);
        border: 1px solid #E4DEFB; border-left: 5px solid {PRIMARY};
        border-radius: 16px; padding: 18px 22px; box-shadow: 0 8px 26px -16px rgba(76,54,201,.5); }}

      .cal {{ width: 100%; border-collapse: separate; border-spacing: 7px; }}
      .cal th {{ color: {MUTED}; font-size: .72rem; font-weight: 700; text-transform: uppercase; }}
      .cal td {{ height: 66px; width: 14.2%; vertical-align: top; border-radius: 12px;
        background: #fff; border: 1px solid {GRID}; padding: 6px 9px; transition: transform .1s; }}
      .cal td.empty {{ background: transparent; border: none; }}
      .cal td.yt   {{ background: #FFF1F3; border: 1px solid #FB7185; }}
      .cal td.ig   {{ background: #F4F1FE; border: 1px solid #A78BFA; }}
      .cal td.both {{ background: linear-gradient(135deg,#FFF1F3,#F1ECFE); border: 1px solid #C084FC; }}
      .cal td.today {{ box-shadow: 0 0 0 2px {ACCENT}; }}
      .cal .daynum {{ font-size: .78rem; color: {MUTED}; font-weight: 700; }}
      .cal .icons {{ font-size: 1.1rem; margin-top: 6px; }}
      .leg {{ color:{MUTED}; font-size:.82rem; margin-top:8px; }}
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
    fig.update_layout(height=height, font=dict(family="Inter", color=INK, size=13),
                      margin=dict(l=10, r=10, t=20, b=10), plot_bgcolor="white",
                      paper_bgcolor="white", title=None, showlegend=fig.layout.showlegend)
    fig.update_xaxes(gridcolor=GRID, zeroline=False)
    fig.update_yaxes(gridcolor=GRID, zeroline=False)
    return fig


def show(fig, h=380):
    st.plotly_chart(style_fig(fig, h), use_container_width=True, config={"displayModeBar": False})


def clean_title(t):
    if not isinstance(t, str) or not t.strip():
        return "(untitled)"
    t = re.sub(r"\s+", " ", t.replace("#", " ")).strip()
    return t or "(untitled)"


# ------------------------------------------------------------------ sidebar ---
with st.sidebar:
    st.subheader("Controls")
    if st.button("🔄 Fetch latest data", use_container_width=True):
        try:
            with st.spinner("Pulling from YouTube…"):
                from youtube_client import fetch_youtube
                yt = st.secrets["youtube"]
                channel, videos, demo = fetch_youtube(
                    yt["client_id"], yt["client_secret"], yt["refresh_token"])
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
try:
    df["published_at"] = df["published_at"].dt.tz_convert("Australia/Melbourne")
except Exception:
    pass
df["clean_title"] = df["title"].map(clean_title)
df["short_title"] = df["clean_title"].apply(lambda s: (s[:38] + "…") if len(s) > 38 else s)

# apply a pending focus (set by a table click on the previous run) BEFORE widgets
if "_pending_focus" in st.session_state:
    st.session_state["focus_id"] = st.session_state.pop("_pending_focus")

with st.sidebar:
    platforms = sorted(df["platform"].dropna().unique())
    if len(platforms) > 1:
        chosen = st.multiselect("Platform", platforms, default=platforms,
                                format_func=lambda p: f"{PLATFORM_ICON.get(p,'')} {p.title()}")
        df = df[df["platform"].isin(chosen)]
    if st.toggle("Shorts only (≤ 3 min)", value=False):
        df = df[df["duration_seconds"].fillna(9999) <= 180]

    ids = list(df["platform_video_id"])
    titles = dict(zip(df["platform_video_id"], df["short_title"]))
    if st.session_state.get("focus_id") not in ids:
        st.session_state["focus_id"] = None
    st.divider()
    st.selectbox("🔍 Focus on a video", [None] + ids, key="focus_id",
                 format_func=lambda v: "All videos" if v is None else titles.get(v, v))

if df.empty:
    st.warning("No videos match the current filters.")
    st.stop()

focus = st.session_state.get("focus_id")
view = df[df["platform_video_id"] == focus] if focus else df

# ------------------------------------------------------------- focus banner ---
if focus and not view.empty:
    r = view.iloc[0]
    pct = r["avg_view_percentage"]
    section("Viewing one video")
    st.markdown(
        f"""<div class="bnt-spot">
        <div style="font-weight:700;color:{INK};font-size:1.05rem;margin-bottom:6px">
          {PLATFORM_ICON.get(r['platform'],'')} {r['clean_title'][:90]}</div>
        <div style="color:{MUTED};font-size:.88rem">
          Views <b style="color:{INK}">{int(r['views'] or 0):,}</b> &nbsp;·&nbsp;
          Likes <b style="color:{INK}">{int(r['likes'] or 0):,}</b> &nbsp;·&nbsp;
          Comments <b style="color:{INK}">{int(r['comments'] or 0):,}</b> &nbsp;·&nbsp;
          % watched <b style="color:{INK}">{(f'{pct:.0f}%' if pd.notna(pct) else '—')}</b>
          &nbsp;·&nbsp; <a href="{r['url']}" target="_blank">Open ↗</a></div>
        </div>""", unsafe_allow_html=True)
    if st.button("← Back to all videos"):
        st.session_state["focus_id"] = None
        st.rerun()

# --------------------------------------------------------- summary metrics ---
section("Overview" if not focus else "This video")
total = len(view)
views = int(view["views"].fillna(0).sum())
avg_views = int(view["views"].fillna(0).mean()) if total else 0
likes = int(view["likes"].fillna(0).sum())
comments = int(view["comments"].fillna(0).sum())
eng = round(100 * (likes + comments) / views, 2) if views else 0
aw = view["avg_view_percentage"].dropna().mean() if "avg_view_percentage" in view else None
avg_watched = f"{aw:.0f}%" if aw is not None and pd.notna(aw) else "—"

cols = st.columns(6)
cols[0].metric("Videos", f"{total:,}")
cols[1].metric("Total views", f"{views:,}")
cols[2].metric("Avg views", f"{avg_views:,}")
cols[3].metric("Engagement", f"{eng}%")
cols[4].metric("Likes", f"{likes:,}")
cols[5].metric("Avg % watched", avg_watched)

# ------------------------------------------------------------- top + cadence ---
left, right = st.columns(2)
with left:
    section("Top videos by views")
    top = df.sort_values("views", ascending=False, na_position="last").head(8).copy()
    bar_colors = [ACCENT if v == focus else PRIMARY for v in top["platform_video_id"]]
    fig = go.Figure(go.Bar(
        x=top["views"].fillna(0), y=top["short_title"], orientation="h",
        marker_color=bar_colors, text=top["views"].fillna(0),
        texttemplate="%{text:,.0f}", textposition="outside", cliponaxis=False,
        hovertemplate="%{y}<br>%{x:,.0f} views<extra></extra>"))
    fig.update_layout(yaxis={"categoryorder": "total ascending", "title": ""},
                      xaxis_title="views", showlegend=False)
    show(fig, 430)

with right:
    section("Videos posted per month")
    cad = df.dropna(subset=["published_at"]).copy()
    if not cad.empty:
        cad["m"] = cad["published_at"].dt.tz_localize(None).dt.to_period("M").dt.to_timestamp()
        g = cad.groupby("m").size().reset_index(name="videos").sort_values("m")
        g["label"] = g["m"].dt.strftime("%b %Y")
        fig = px.bar(g, x="label", y="videos", color_discrete_sequence=[PRIMARY], text="videos")
        fig.update_xaxes(type="category", title="")
        fig.update_yaxes(dtick=1, rangemode="tozero", title="videos")
        fig.update_layout(showlegend=False)
        show(fig, 430)

# ----------------------------------------------------------- calendar view ---
section("Posting calendar", "Days you posted are highlighted.")
caldf = df.dropna(subset=["published_at"]).copy()
if not caldf.empty:
    caldf["ym"] = caldf["published_at"].dt.tz_localize(None).dt.to_period("M")
    months = sorted(caldf["ym"].unique(), reverse=True)
    pick = st.selectbox("Month", months, format_func=lambda p: p.strftime("%B %Y"))
    sub = caldf[caldf["ym"] == pick]
    posts_by_day = {}
    for _, rr in sub.iterrows():
        posts_by_day.setdefault(rr["published_at"].day, set()).add(rr["platform"])
    try:
        now = pd.Timestamp.now(tz="Australia/Melbourne")
    except Exception:
        now = pd.Timestamp.utcnow()
    cal = calmod.Calendar(firstweekday=6)
    head = "".join(f"<th>{w}</th>" for w in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"])
    body = ""
    for week in cal.monthdayscalendar(pick.year, pick.month):
        body += "<tr>"
        for day in week:
            if day == 0:
                body += '<td class="empty"></td>'
                continue
            plats = posts_by_day.get(day)
            cls = ""
            if plats:
                cls = "both" if len(plats) > 1 else ("yt" if "youtube" in plats else "ig")
            if now.year == pick.year and now.month == pick.month and now.day == day:
                cls += " today"
            icons = "".join(PLATFORM_ICON.get(p, "•") for p in sorted(plats)) if plats else ""
            body += (f'<td class="{cls}"><div class="daynum">{day}</div>'
                     f'<div class="icons">{icons}</div></td>')
        body += "</tr>"
    st.markdown(f'<table class="cal"><tr>{head}</tr>{body}</table>'
                f'<div class="leg">▶️ YouTube &nbsp; 📸 Instagram &nbsp; '
                f'<span style="color:{ACCENT}">▮</span> today</div>', unsafe_allow_html=True)

# --------------------------------------------------------------- retention ---
ret = df.dropna(subset=["avg_view_percentage"]) if "avg_view_percentage" in df else df.iloc[0:0]
if not ret.empty:
    section("How much of each video people watch", "Higher = people stay longer. 100% − this ≈ average skip.")
    r2 = ret.sort_values("avg_view_percentage", ascending=False).head(15)
    fig = px.bar(r2, x="avg_view_percentage", y="short_title", orientation="h",
                 color="avg_view_percentage", color_continuous_scale=["#EDE9FE", PRIMARY],
                 labels={"avg_view_percentage": "% watched", "short_title": ""})
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
    show(fig, 440)

# -------------------------------------------------------------- demographics ---
demo = supa.load_demographics()
if not demo.empty:
    demo = demo[demo["platform"] == "youtube"]
section("Audience", "Shown for the whole channel — YouTube doesn't break audience down per video at low view counts.")
if not demo.empty:
    d1, d2, d3 = st.columns(3)
    age = demo[demo["dimension"] == "age"].sort_values("bucket")
    if not age.empty:
        with d1:
            section("Age") if False else st.caption("Age")
            fig = px.bar(age, x="bucket", y="percentage", color_discrete_sequence=[PRIMARY],
                         labels={"bucket": "", "percentage": "%"})
            fig.update_layout(showlegend=False)
            show(fig, 300)
    gen = demo[demo["dimension"] == "gender"]
    if not gen.empty:
        with d2:
            st.caption("Gender")
            fig = px.pie(gen, names="bucket", values="percentage", hole=.55,
                         color_discrete_sequence=SEQ)
            show(fig, 300)
    ctry = demo[demo["dimension"] == "country"].sort_values("percentage", ascending=False)
    if not ctry.empty:
        with d3:
            st.caption("Top countries")
            fig = px.bar(ctry, x="percentage", y="bucket", orientation="h",
                         color_discrete_sequence=[ACCENT], labels={"bucket": "", "percentage": "% of views"})
            fig.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
            show(fig, 300)
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
        show(fig, 320)

# ------------------------------------------------------------------- table ---
section("All videos", "Tip: click a row to focus the whole dashboard on that video.")
tbl = df.sort_values("views", ascending=False, na_position="last").reset_index(drop=True)
ids_in_order = tbl["platform_video_id"].tolist()
disp = [c for c in ["platform", "clean_title", "published_at", "views", "likes",
                    "comments", "avg_view_percentage", "url"] if c in tbl.columns]
event = st.dataframe(
    tbl[disp], use_container_width=True, hide_index=True,
    on_select="rerun", selection_mode="single-row", key="vtable",
    column_config={
        "clean_title": st.column_config.TextColumn("title"),
        "url": st.column_config.LinkColumn("link", display_text="open"),
        "avg_view_percentage": st.column_config.NumberColumn("% watched", format="%.0f"),
    },
)
try:
    sel_rows = event.selection["rows"]
except Exception:
    sel_rows = getattr(getattr(event, "selection", None), "rows", []) or []
if sel_rows:
    sel_id = ids_in_order[sel_rows[0]]
    if sel_id != st.session_state.get("focus_id"):
        st.session_state["_pending_focus"] = sel_id
        st.rerun()
