"""BooksNTax — Social Dashboard (YouTube stage)."""
import base64
import calendar as calmod
import os
import re

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import supa

# --------------------------------------------------- palette (from logo) ----
NAVY = "#0C2340"
BAR = "#1F4E79"
GREEN = "#1E8043"
BLUE = "#3D7AB5"
INK = "#0C2340"
MUTED = "#5B6B7B"
GRID = "#E6EBF1"
SEQ = ["#1F4E79", "#1E8043", "#3D7AB5", "#52A66B", "#0C2340", "#9CB3C9"]
PLATFORM_ICON = {"youtube": "▶️", "instagram": "📸"}

st.set_page_config(page_title="BooksNTax · Social Dashboard", page_icon="📊", layout="wide")


def _logo_b64():
    for p in ("logo.png", "BooksNTax_Logo_Exact.png"):
        if os.path.exists(p):
            with open(p, "rb") as f:
                return base64.b64encode(f.read()).decode()
    return None


LOGO = _logo_b64()
try:
    if os.path.exists("logo.png"):
        st.logo("logo.png")
except Exception:
    pass

# ------------------------------------------------------------------- style ---
st.markdown(
    f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
      html, body, [class*="css"], .stApp {{ font-family: 'Inter', sans-serif; }}
      .stApp {{ background: #F4F6F9; }}
      .block-container {{ padding-top: 1.2rem; max-width: 1320px; }}

      .bnt-header {{
        background: #fff; padding: 18px 28px; border-radius: 18px; margin-bottom: 18px;
        border: 1px solid {GRID}; border-bottom: 3px solid {GREEN};
        box-shadow: 0 8px 26px -18px rgba(12,35,64,.45);
        display: flex; align-items: center;
      }}
      .bnt-header img {{ height: 74px; margin-right: 24px; }}
      .bnt-header h1 {{ margin: 0; font-size: 1.95rem; font-weight: 800; color: {NAVY}; letter-spacing:-.3px;}}
      .bnt-header p  {{ margin: 5px 0 0; color: {MUTED}; font-size: .96rem; }}

      /* every section is a white card with a green accent + shadow (header concept) */
      div[data-testid="stVerticalBlockBorderWrapper"] {{
        background: #fff; border: 1px solid {GRID} !important; border-bottom: 3px solid {GREEN} !important;
        border-radius: 16px; box-shadow: 0 8px 26px -18px rgba(12,35,64,.45);
      }}

      div[data-testid="stMetric"] {{
        background: #fff; border: 1px solid {GRID}; border-bottom: 3px solid {GREEN}; border-radius: 14px;
        padding: 14px 16px; box-shadow: 0 4px 14px -12px rgba(12,35,64,.35);
      }}
      div[data-testid="stMetricLabel"] p {{
        font-size: .72rem !important; text-transform: uppercase; letter-spacing: .5px;
        color: {MUTED} !important; font-weight: 600;
      }}
      div[data-testid="stMetricValue"] {{ color: {NAVY}; font-weight: 700; }}

      .bnt-sec {{ font-size: 1.06rem; font-weight: 700; color: {NAVY};
        margin: 2px 0 12px; padding-left: 11px; border-left: 4px solid {GREEN}; }}
      .bnt-cap {{ color: {MUTED}; font-size: .82rem; margin: -8px 0 8px; }}

      .bnt-spot {{ background: #F4FAF6; border: 1px solid #CDE8D6; border-left: 5px solid {GREEN};
        border-radius: 12px; padding: 16px 20px; }}

      /* calendar */
      .calwrap {{ max-width: 760px; margin: 4px auto 0; }}
      .cal {{ width: 100%; border-collapse: separate; border-spacing: 6px; }}
      .cal th {{ color: {MUTED}; font-size: .68rem; font-weight: 700; text-transform: uppercase; padding-bottom:2px;}}
      .cal td {{ height: 52px; border-radius: 10px; text-align: center; vertical-align: middle;
        background: #FFFFFF; border: 1px solid {GRID}; padding: 4px; }}
      .cal td.alt {{ background: #EEF2F7; }}
      .cal td.empty {{ background: transparent; border: none; }}
      .cal td.yt   {{ background: #FDEDEF; border: 1px solid #E2557A; }}
      .cal td.ig   {{ background: #EEE8FD; border: 1px solid #9B7BE6; }}
      .cal td.both {{ background: linear-gradient(135deg,#FDEDEF,#EEE8FD); border: 1px solid #B57BD6; }}
      .cal td.today {{ box-shadow: 0 0 0 2px {GREEN}; }}
      .cal .daynum {{ font-size: .95rem; color: {NAVY}; font-weight: 700; }}
      .cal .icons {{ font-size: 1rem; margin-top: 2px; }}
      .leg {{ color:{MUTED}; font-size:.8rem; margin-top:10px; text-align:center; }}
    </style>
    """,
    unsafe_allow_html=True,
)

logo_tag = f'<img src="data:image/png;base64,{LOGO}">' if LOGO else "📊 "
st.markdown(
    f"""<div class="bnt-header">{logo_tag}
      <div><h1>BooksNTax — Social Dashboard</h1>
      <p>Short-form video performance · Views, Engagement, Retention & Audience</p></div>
    </div>""",
    unsafe_allow_html=True,
)


def section(title, caption=None):
    st.markdown(f'<div class="bnt-sec">{title}</div>', unsafe_allow_html=True)
    if caption:
        st.markdown(f'<div class="bnt-cap">{caption}</div>', unsafe_allow_html=True)


def style_fig(fig, height=320):
    fig.update_layout(height=height, font=dict(family="Inter", color=INK, size=12.5),
                      margin=dict(l=10, r=10, t=8, b=10), plot_bgcolor="white",
                      paper_bgcolor="white", title="")
    fig.update_xaxes(gridcolor=GRID, zeroline=False)
    fig.update_yaxes(gridcolor=GRID, zeroline=False)
    return fig


def show(fig, h=320):
    st.plotly_chart(style_fig(fig, h), use_container_width=True, config={"displayModeBar": False})


def clean_title(t):
    if not isinstance(t, str) or not t.strip():
        return "(untitled)"
    return re.sub(r"\s+", " ", t.replace("#", " ")).strip() or "(untitled)"


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
    titles = {r.platform_video_id: (r.clean_title[:34] + ("…" if len(r.clean_title) > 34 else ""))
              for r in df.itertuples()}
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
    with st.container(border=True):
        section("Viewing one video")
        st.markdown(
            f"""<div class="bnt-spot">
            <div style="font-weight:700;color:{INK};font-size:1.02rem;margin-bottom:6px">
              {PLATFORM_ICON.get(r['platform'],'')} {r['clean_title'][:90]}</div>
            <div style="color:{MUTED};font-size:.88rem">
              Views <b style="color:{INK}">{int(r['views'] or 0):,}</b> &nbsp;·&nbsp;
              Likes <b style="color:{INK}">{int(r['likes'] or 0):,}</b> &nbsp;·&nbsp;
              Comments <b style="color:{INK}">{int(r['comments'] or 0):,}</b> &nbsp;·&nbsp;
              % watched <b style="color:{INK}">{(f'{pct:.0f}%' if pd.notna(pct) else '—')}</b>
              &nbsp;·&nbsp; <a href="{r['url']}" target="_blank">Open ↗</a></div></div>""",
            unsafe_allow_html=True)
        if st.button("← Back to all videos"):
            st.session_state["focus_id"] = None
            st.rerun()

# --------------------------------------------------------- summary metrics ---
with st.container(border=True):
    section("Overview" if not focus else "This video")
    total = len(view)
    views = int(view["views"].fillna(0).sum())
    avg_views = int(view["views"].fillna(0).mean()) if total else 0
    likes = int(view["likes"].fillna(0).sum())
    comments = int(view["comments"].fillna(0).sum())
    eng = round(100 * (likes + comments) / views, 2) if views else 0
    aw = view["avg_view_percentage"].dropna().mean() if "avg_view_percentage" in view else None
    avg_watched = f"{aw:.0f}%" if aw is not None and pd.notna(aw) else "—"
    m = st.columns(6)
    m[0].metric("Videos", f"{total:,}")
    m[1].metric("Total views", f"{views:,}")
    m[2].metric("Avg views", f"{avg_views:,}")
    m[3].metric("Engagement", f"{eng}%")
    m[4].metric("Likes", f"{likes:,}")
    m[5].metric("Avg % watched", avg_watched)

# ------------------------------------------------------------- top + cadence ---
left, right = st.columns(2)
with left:
    with st.container(border=True):
        section("Top videos by views")
        top = df.sort_values("views", ascending=False, na_position="last").head(8).copy()
        names = top["clean_title"].apply(lambda s: s[:26] + ("…" if len(s) > 26 else ""))
        colors = [GREEN if v == focus else BAR for v in top["platform_video_id"]]
        fig = go.Figure(go.Bar(
            x=top["views"].fillna(0), y=top["clean_title"], orientation="h",
            marker_color=colors, width=0.55, text=names, textposition="inside",
            insidetextanchor="start", textfont=dict(color="white", size=12),
            hovertemplate="%{customdata}<br>%{x:,.0f} views<extra></extra>",
            customdata=top["clean_title"]))
        for _, rr in top.iterrows():
            fig.add_annotation(x=rr["views"] or 0, y=rr["clean_title"], xanchor="left", xshift=6,
                               text=f"{int(rr['views'] or 0):,}", showarrow=False,
                               font=dict(color=INK, size=12))
        fig.update_yaxes(showticklabels=False, categoryorder="total ascending")
        fig.update_layout(xaxis_title="views", showlegend=False, bargap=0.35)
        show(fig, 320)

with right:
    with st.container(border=True):
        section("Videos posted per month")
        cad = df.dropna(subset=["published_at"]).copy()
        if not cad.empty:
            cad["mo"] = cad["published_at"].dt.tz_localize(None).dt.to_period("M").dt.to_timestamp()
            g = cad.groupby("mo").size().reset_index(name="videos").sort_values("mo")
            g["label"] = g["mo"].dt.strftime("%b %Y")
            fig = px.bar(g, x="label", y="videos", color_discrete_sequence=[BAR], text="videos")
            fig.update_xaxes(type="category", title="")
            fig.update_yaxes(dtick=1, rangemode="tozero", title="videos")
            fig.update_traces(width=0.5, textposition="outside")
            fig.update_layout(showlegend=False)
            show(fig, 320)

# ----------------------------------------------------------- calendar view ---
with st.container(border=True):
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
            for col, day in enumerate(week):
                if day == 0:
                    body += '<td class="empty"></td>'
                    continue
                cls = []
                if col in (0, 6):
                    cls.append("alt")
                plats = posts_by_day.get(day)
                if plats:
                    cls.append("both" if len(plats) > 1 else ("yt" if "youtube" in plats else "ig"))
                if now.year == pick.year and now.month == pick.month and now.day == day:
                    cls.append("today")
                icons = "".join(PLATFORM_ICON.get(p, "•") for p in sorted(plats)) if plats else ""
                body += (f'<td class="{" ".join(cls)}"><div class="daynum">{day}</div>'
                         f'<div class="icons">{icons}</div></td>')
            body += "</tr>"
        st.markdown(
            f'<div class="calwrap"><table class="cal"><tr>{head}</tr>{body}</table>'
            f'<div class="leg">▶️ YouTube &nbsp; 📸 Instagram &nbsp; '
            f'<span style="color:{GREEN}">▮</span> today</div></div>', unsafe_allow_html=True)

# --------------------------------------------------------------- retention ---
ret = df.dropna(subset=["avg_view_percentage"]) if "avg_view_percentage" in df else df.iloc[0:0]
if not ret.empty:
    with st.container(border=True):
        section("How much of each video people watch", "Higher = people stay longer. 100% − this ≈ average skip.")
        r2 = ret.sort_values("avg_view_percentage", ascending=False).head(15)
        fig = px.bar(r2, x="avg_view_percentage", y="clean_title", orientation="h",
                     color="avg_view_percentage", color_continuous_scale=["#D5E6F0", BAR],
                     labels={"avg_view_percentage": "% watched", "clean_title": ""})
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
        show(fig, 420)

# -------------------------------------------------------------- demographics ---
demo = supa.load_demographics()
if not demo.empty:
    demo = demo[demo["platform"] == "youtube"]
with st.container(border=True):
    section("Audience", "Shown for the whole channel — YouTube doesn't break audience down per video at low view counts.")
    if not demo.empty:
        d1, d2, d3 = st.columns(3)
        age = demo[demo["dimension"] == "age"].sort_values("bucket")
        if not age.empty:
            with d1:
                st.markdown("**Age**")
                fig = px.bar(age, x="bucket", y="percentage", color_discrete_sequence=[BAR],
                             labels={"bucket": "", "percentage": "%"})
                fig.update_layout(showlegend=False)
                show(fig, 290)
        gen = demo[demo["dimension"] == "gender"]
        if not gen.empty:
            with d2:
                st.markdown("**Gender**")
                fig = px.pie(gen, names="bucket", values="percentage", hole=.55, color_discrete_sequence=SEQ)
                show(fig, 290)
        ctry = demo[demo["dimension"] == "country"].sort_values("percentage", ascending=False)
        if not ctry.empty:
            with d3:
                st.markdown("**Top countries**")
                fig = px.bar(ctry, x="percentage", y="bucket", orientation="h",
                             color_discrete_sequence=[BLUE], labels={"bucket": "", "percentage": "% of views"})
                fig.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
                show(fig, 290)
    else:
        st.caption("👥 Audience charts appear once videos pass YouTube's minimum-views threshold.")

# ------------------------------------------------------------ view growth ---
hist = supa.load_history()
if not hist.empty:
    hist["captured_at"] = pd.to_datetime(hist["captured_at"], errors="coerce", utc=True)
    daily = hist.assign(day=hist["captured_at"].dt.date).groupby("day")["views"].sum().reset_index()
    if daily["day"].nunique() > 1:
        with st.container(border=True):
            section("Total view growth over time")
            fig = px.line(daily, x="day", y="views", markers=True, color_discrete_sequence=[GREEN])
            show(fig, 300)

# ------------------------------------------------------------------- table ---
with st.container(border=True):
    section("All videos", "Tip: click a row to focus the whole dashboard on that video.")
    tbl = df.sort_values("views", ascending=False, na_position="last").reset_index(drop=True)
    ids_in_order = tbl["platform_video_id"].tolist()
    disp = [c for c in ["platform", "clean_title", "published_at", "views", "likes",
                        "comments", "avg_view_percentage", "url"] if c in tbl.columns]
    event = st.dataframe(
        tbl[disp], use_container_width=True, hide_index=True,
        on_select="rerun", selection_mode="single-row", key="vtable",
        column_config={
            "clean_title": st.column_config.TextColumn("video"),
            "url": st.column_config.LinkColumn("link", display_text="open"),
            "avg_view_percentage": st.column_config.NumberColumn("% watched", format="%.0f"),
        })
    try:
        sel_rows = event.selection["rows"]
    except Exception:
        sel_rows = getattr(getattr(event, "selection", None), "rows", []) or []
    if sel_rows:
        sel_id = ids_in_order[sel_rows[0]]
        if sel_id != st.session_state.get("focus_id"):
            st.session_state["_pending_focus"] = sel_id
            st.rerun()
