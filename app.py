"""BooksNTax — Social Dashboard (YouTube stage)."""
import base64
import calendar as calmod
import os
import re
import urllib.parse
from contextlib import contextmanager

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
YT_COLOR = "#FF0000"
IG_COLOR = "#C13584"

# Stylized, brand-coloured platform marks (clean functional icons, not the
# trademarked logo files — keeps the dashboard shareable without IP issues).
YT_SVG = ('<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">'
          '<rect x="1" y="4" width="22" height="16" rx="5" fill="#FF0000"/>'
          '<path d="M10 8.5 L16.5 12 L10 15.5 Z" fill="#fff"/></svg>')
IG_SVG = ('<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><defs>'
          '<linearGradient id="igg" x1="0" y1="1" x2="1" y2="0">'
          '<stop offset="0" stop-color="#FEDA75"/><stop offset=".5" stop-color="#D62976"/>'
          '<stop offset="1" stop-color="#962FBF"/></linearGradient></defs>'
          '<rect x="1" y="1" width="22" height="22" rx="7" fill="url(#igg)"/>'
          '<circle cx="12" cy="12" r="5" fill="none" stroke="#fff" stroke-width="2"/>'
          '<circle cx="17.6" cy="6.4" r="1.4" fill="#fff"/></svg>')


def _uri(svg):
    return "data:image/svg+xml," + urllib.parse.quote(svg)


YT_URI, IG_URI = _uri(YT_SVG), _uri(IG_SVG)


def plogo(platform, size=16):
    svg = YT_SVG if platform == "youtube" else IG_SVG
    return svg.replace(
        "<svg ", f'<svg width="{size}" height="{size}" style="vertical-align:middle;margin-right:3px" ', 1)

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
      html, body {{ overflow-x: hidden; }}
      .stApp {{ background: #F4F6F9; }}
      .block-container {{ padding-top: 1.2rem; max-width: 1320px; overflow-x: hidden; }}
      /* let the page scroll vertically over charts instead of the chart zooming */
      [data-testid="stPlotlyChart"], .js-plotly-plot, .plot-container,
      .js-plotly-plot .draglayer {{ touch-action: pan-y !important; }}

      .bnt-header {{
        background: #fff; padding: 18px 28px; border-radius: 18px; margin-bottom: 18px;
        border: 1px solid {GRID}; border-bottom: 3px solid {GREEN};
        box-shadow: 0 8px 26px -18px rgba(12,35,64,.45);
        display: flex; align-items: center;
      }}
      .bnt-header img {{ height: 74px; margin-right: 24px; }}
      .bnt-header h1 {{ margin: 0; font-size: 1.95rem; font-weight: 800; color: {NAVY}; letter-spacing:-.3px;}}
      .bnt-header p  {{ margin: 5px 0 0; color: {MUTED}; font-size: .96rem; }}

      /* every section card carries the SAME green bottom border as the main header.
         Streamlit attaches the st-key-bntcard* class to the actual bordered element,
         so we recolour its real bottom border — no overlaid bar, hugs the corners. */
      [class*="st-key-bntcard"] {{
        border-bottom: 3px solid {GREEN} !important;
        box-shadow: 0 8px 26px -18px rgba(12,35,64,.45);
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

      /* section header band — green marker + underline, like the main header */
      .bnt-sec {{ font-size: 1.08rem; font-weight: 800; color: {NAVY};
        margin: -2px 0 14px; padding: 0 0 9px; display:flex; align-items:center; gap:9px;
        border-bottom: 2px solid {GRID}; letter-spacing:-.2px; }}
      .bnt-sec::before {{ content:""; width:7px; height:20px; border-radius:3px;
        background:{GREEN}; display:inline-block; flex:0 0 auto; }}
      .bnt-cap {{ color: {MUTED}; font-size: .82rem; margin: -8px 0 10px; }}

      .bnt-spot {{ background: #F4FAF6; border: 1px solid #CDE8D6; border-left: 5px solid {GREEN};
        border-radius: 12px; padding: 16px 20px; }}

      /* platform toggle (top of page) */
      .bnt-toggle-label {{ font-size:.72rem; text-transform:uppercase; letter-spacing:.5px;
        color:{MUTED}; font-weight:700; margin: 0 0 6px 2px; }}
      div[role="radiogroup"] {{ gap:10px; }}
      div[role="radiogroup"] > label {{
        position:relative; border:1.5px solid {GRID}; border-radius:12px; background:#fff; cursor:pointer;
        padding:9px 16px; font-weight:700; color:{NAVY}; transition:all .15s;
        box-shadow:0 3px 12px -10px rgba(12,35,64,.4);
      }}
      div[role="radiogroup"] > label:hover {{ border-color:{GREEN}; }}
      div[role="radiogroup"] > label > div:first-child {{ display:none; }}
      div[role="radiogroup"] > label:nth-of-type(2),
      div[role="radiogroup"] > label:nth-of-type(3) {{ padding-left:42px; }}
      div[role="radiogroup"] > label:nth-of-type(2)::before,
      div[role="radiogroup"] > label:nth-of-type(3)::before {{
        content:""; position:absolute; left:14px; top:50%; transform:translateY(-50%);
        width:21px; height:21px; background-size:contain; background-repeat:no-repeat; background-position:center;
      }}
      div[role="radiogroup"] > label:nth-of-type(2)::before {{ background-image:url("{YT_URI}"); }}
      div[role="radiogroup"] > label:nth-of-type(3)::before {{ background-image:url("{IG_URI}"); }}
      div[role="radiogroup"] > label:has(input:checked) {{
        border-color:{GREEN}; background:#F4FAF6; box-shadow:0 5px 16px -10px rgba(12,35,64,.5); }}

      /* calendar */
      .calwrap {{ max-width: 780px; margin: 4px auto 0; }}
      .cal {{ width: 100%; border-collapse: separate; border-spacing: 7px; }}
      .cal th {{ color: {MUTED}; font-size: .7rem; font-weight: 800; text-transform: uppercase; padding-bottom:3px;}}
      .cal td {{ height: 60px; border-radius: 11px; text-align: center; vertical-align: middle;
        background: #FFFFFF; border: 2px solid #C7D2DE; padding: 4px; }}
      .cal td.cba {{ background: #EAF1F8; }}   /* light blue */
      .cal td.cbb {{ background: #EDF6F0; }}   /* light green */
      .cal td.empty {{ background: transparent; border: none; }}
      .cal td.yt   {{ background: #FFF1F3; border-color: #E2557A; }}
      .cal td.ig   {{ background: #F3EDFD; border-color: #9B7BE6; }}
      .cal td.both {{ background: linear-gradient(135deg,#FFF1F3,#F3EDFD); border-color: #B57BD6; }}
      .cal td.today {{ box-shadow: 0 0 0 3px {GREEN}; border-color: {GREEN}; }}
      .cal .daynum {{ font-size: 1.1rem; color: {NAVY}; font-weight: 600; line-height:1;
        font-variant-numeric: tabular-nums; letter-spacing: .3px; }}
      .cal .icons {{ margin-top: 4px; display:flex; gap:3px; justify-content:center; align-items:center; }}
      .cal .icons svg {{ display:block; }}
      .leg {{ color:{MUTED}; font-size:.82rem; margin-top:12px; text-align:center; }}
      .leg svg {{ vertical-align:middle; }}
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


_card_seq = 0


@contextmanager
def card():
    """A bordered section card whose real bottom border matches the brand header line.

    Each card gets a unique 'bntcard{n}' key so Streamlit tags the bordered element
    with class 'st-key-bntcard{n}', which the stylesheet recolours. Falls back
    gracefully if the running Streamlit version doesn't accept a container key.
    """
    global _card_seq
    _card_seq += 1
    try:
        ctx = st.container(border=True, key=f"bntcard{_card_seq}")
    except TypeError:
        ctx = st.container(border=True)
    with ctx:
        yield


def style_fig(fig, height=320):
    fig.update_layout(height=height, font=dict(family="Inter", color=INK, size=12.5),
                      margin=dict(l=10, r=10, t=8, b=10), plot_bgcolor="white",
                      paper_bgcolor="white", title="")
    fig.update_xaxes(gridcolor=GRID, zeroline=False)
    fig.update_yaxes(gridcolor=GRID, zeroline=False)
    return fig


def show(fig, h=320):
    # dragmode=False + the config below stop Plotly from hijacking touch gestures
    # on mobile (the "zooms in and in" problem) while keeping hover on desktop.
    fig.update_layout(dragmode=False)
    st.plotly_chart(
        style_fig(fig, h), use_container_width=True,
        config={"displayModeBar": False, "scrollZoom": False, "doubleClick": False,
                "showAxisDragHandles": False, "showTips": False, "staticPlot": False})


def clean_title(t):
    if not isinstance(t, str) or not t.strip():
        return "(untitled)"
    return re.sub(r"\s+", " ", t.replace("#", " ")).strip() or "(untitled)"


# ------------------------------------------------------------------ sidebar ---
with st.sidebar:
    st.subheader("Controls")
    if st.button("🔄 Fetch latest data", use_container_width=True):
        msgs, errs = [], []
        # ---- YouTube ----
        try:
            with st.spinner("Pulling from YouTube…"):
                from youtube_client import fetch_youtube
                yt = st.secrets["youtube"]
                channel, videos, demo = fetch_youtube(
                    yt["client_id"], yt["client_secret"], yt["refresh_token"])
                supa.save_videos(videos)
                supa.save_demographics("youtube", demo)
            msgs.append(f"▶️ {channel}: {len(videos)} videos")
        except Exception as e:
            errs.append(f"YouTube fetch failed: {e}")
        # ---- Instagram (only if secrets are set; independent of YouTube) ----
        if "instagram" in st.secrets:
            try:
                with st.spinner("Pulling from Instagram…"):
                    import instagram_client
                    reels = instagram_client.fetch_reels()
                    supa.save_videos(reels)
                    supa.save_demographics("instagram", instagram_client.fetch_demographics())
                msgs.append(f"📸 Instagram: {len(reels)} reels")
            except Exception as e:
                errs.append(f"Instagram fetch failed: {e}")
        if msgs:
            st.success(" · ".join(msgs))
        for er in errs:
            st.error(er)
        if msgs:
            st.rerun()
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

# ---- platform toggle (top of the page, above Overview) ----
all_plats = sorted(df["platform"].dropna().unique())
plat_view = "both"
if len(all_plats) > 1:
    st.markdown('<div class="bnt-toggle-label">Platform</div>', unsafe_allow_html=True)
    order = [p for p in ["youtube", "instagram"] if p in all_plats]
    pick = st.radio("platform", ["Both"] + [p.title() for p in order], horizontal=True,
                    label_visibility="collapsed", key="plat_choice")
    plat_view = pick.lower()
    if plat_view != "both":
        df = df[df["platform"] == plat_view]

with st.sidebar:
    if st.toggle("Shorts only (≤ 3 min)", value=False):
        df = df[df["duration_seconds"].fillna(9999) <= 180]
    ids = list(df["platform_video_id"])
    titles = {r.platform_video_id: (r.clean_title[:34] + ("…" if len(r.clean_title) > 34 else ""))
              for r in df.itertuples()}
    if st.session_state.get("focus_id") not in ids:
        st.session_state["focus_id"] = None
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
    with card():
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
with card():
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
    with card():
        section("Top videos by views", "Labelled by post date · hover a bar for the caption.")
        top = df.sort_values("views", na_position="first").tail(8).copy()
        top["datelbl"] = top["published_at"].dt.strftime("%d %b")
        yv = list(range(len(top)))
        colors = [GREEN if r.platform_video_id == focus
                  else (IG_COLOR if r.platform == "instagram" else BAR)
                  for r in top.itertuples()]
        fig = go.Figure(go.Bar(
            x=top["views"].fillna(0), y=yv, orientation="h", marker_color=colors, width=0.6,
            hovertemplate="%{customdata[0]}<br>%{customdata[1]} · %{x:,.0f} views<extra></extra>",
            customdata=top[["clean_title", "datelbl"]].values))
        for i, rr in enumerate(top.itertuples()):
            v = int(rr.views) if pd.notna(rr.views) else 0
            fig.add_annotation(x=v, y=i, xanchor="left", xshift=6, text=f"{v:,}",
                               showarrow=False, font=dict(color=INK, size=12, family="Inter"))
        fig.update_yaxes(tickmode="array", tickvals=yv, ticktext=list(top["datelbl"]),
                         tickfont=dict(size=12.5, color=MUTED))
        fig.update_layout(xaxis_title="views", showlegend=False, bargap=0.3,
                          margin=dict(l=10, r=64, t=8, b=10))
        show(fig, 340)
        st.markdown(
            f'<div class="bnt-cap"><span style="color:{BAR}">▮</span> YouTube &nbsp; '
            f'<span style="color:{IG_COLOR}">▮</span> Instagram &nbsp; '
            f'<span style="color:{GREEN}">▮</span> focused</div>', unsafe_allow_html=True)

with right:
    with card():
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
with card():
    section("Posting Calendar", "Days you posted are highlighted.")
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
        for wk_i, week in enumerate(cal.monthdayscalendar(pick.year, pick.month)):
            body += "<tr>"
            for col, day in enumerate(week):
                if day == 0:
                    body += '<td class="empty"></td>'
                    continue
                cls = ["cba" if (wk_i + col) % 2 == 0 else "cbb"]
                plats = posts_by_day.get(day)
                if plats:
                    cls.append("both" if len(plats) > 1 else ("yt" if "youtube" in plats else "ig"))
                if now.year == pick.year and now.month == pick.month and now.day == day:
                    cls.append("today")
                icons = "".join(plogo(p, 15) for p in sorted(plats)) if plats else ""
                body += (f'<td class="{" ".join(cls)}"><div class="daynum">{day}</div>'
                         f'<div class="icons">{icons}</div></td>')
            body += "</tr>"
        st.markdown(
            f'<div class="calwrap"><table class="cal"><tr>{head}</tr>{body}</table>'
            f'<div class="leg">{plogo("youtube",15)} YouTube &nbsp; '
            f'{plogo("instagram",15)} Instagram &nbsp; '
            f'<span style="color:{GREEN}">▮</span> today</div></div>', unsafe_allow_html=True)

# --------------------------------------------------------------- retention ---
ret = df.dropna(subset=["avg_view_percentage"]) if "avg_view_percentage" in df else df.iloc[0:0]
if not ret.empty:
    with card():
        section("How much of each video people watch", "Higher = people stay longer. 100% − this ≈ average skip.")
        r2 = ret.sort_values("avg_view_percentage", ascending=False).head(15)
        fig = px.bar(r2, x="avg_view_percentage", y="clean_title", orientation="h",
                     color="avg_view_percentage", color_continuous_scale=["#D5E6F0", BAR],
                     labels={"avg_view_percentage": "% watched", "clean_title": ""})
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
        show(fig, 420)

# -------------------------------------------------------------- demographics ---
demo_all = supa.load_demographics()


def render_audience(pdemo):
    d1, d2, d3 = st.columns(3)
    age = pdemo[pdemo["dimension"] == "age"].sort_values("bucket")
    if not age.empty:
        with d1:
            st.markdown("**Age**")
            fig = px.bar(age, x="bucket", y="percentage", color_discrete_sequence=[BAR],
                         labels={"bucket": "", "percentage": "%"})
            fig.update_layout(showlegend=False)
            show(fig, 290)
    gen = pdemo[pdemo["dimension"] == "gender"]
    if not gen.empty:
        with d2:
            st.markdown("**Gender**")
            fig = px.pie(gen, names="bucket", values="percentage", hole=.55, color_discrete_sequence=SEQ)
            show(fig, 290)
    ctry = pdemo[pdemo["dimension"] == "country"].sort_values("percentage", ascending=False).head(8)
    if not ctry.empty:
        with d3:
            st.markdown("**Top countries**")
            fig = px.bar(ctry, x="percentage", y="bucket", orientation="h",
                         color_discrete_sequence=[BLUE], labels={"bucket": "", "percentage": "%"})
            fig.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
            show(fig, 290)


_aud_plats = ["youtube", "instagram"] if plat_view == "both" else [plat_view]
_aud_shown = False
for _p in _aud_plats:
    pdemo = demo_all[demo_all["platform"] == _p] if not demo_all.empty else demo_all
    if pdemo is None or pdemo.empty:
        continue
    _aud_shown = True
    with card():
        section(f'{plogo(_p, 18)} {_p.title()} audience', "Channel-level breakdown of who's watching.")
        render_audience(pdemo)
if not _aud_shown:
    with card():
        section("Audience")
        st.caption("👥 Audience charts appear once your accounts pass each platform's threshold "
                   "(YouTube needs enough views; Instagram needs ~100+ followers).")

# ------------------------------------------------------------------- table ---
with card():
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
