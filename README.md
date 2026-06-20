# BooksNTax — Social Dashboard (Stage 1: YouTube)

A free, online dashboard for your BooksNTax YouTube Shorts — views per video,
engagement, how much of each video people watch, audience demographics, and view
growth over time. Nothing installs on your computer; everything runs in the cloud.

This is **Stage 1 (YouTube)**. Instagram Reels gets added in Stage 2.

> You'll create accounts on four free services, each doing one job:
> **Google Cloud** (permission to read your channel) · **Supabase** (stores your
> data forever) · **GitHub** (holds the code) · **Streamlit Cloud** (runs the
> dashboard and gives you a web link). Tip: sign into Supabase, GitHub, and
> Streamlit all *with your GitHub account* to keep it simple.

Work top to bottom. Budget a focused afternoon — the Google steps are the fiddly
part; everything else is quick.

---

## Step 1 — Google Cloud: turn on the APIs

1. Go to <https://console.cloud.google.com>, sign in, and create a new project
   (top bar → project menu → **New Project**). Name it `booksntax`.
2. Top search bar → find **"YouTube Data API v3"** → **Enable**. Repeat for
   **"YouTube Analytics API"**.
3. Left menu → **APIs & Services → OAuth consent screen**:
   - User type **External** → Create.
   - Fill the app name and your email where required; save and continue.
   - On the **Scopes** step you can skip adding scopes; continue.
   - On **Test users**, click **Add users** and add your own Google email
     (the one that owns the YouTube channel). Save.
   - Leave publishing status as **Testing** (no Google review needed).

## Step 2 — Google Cloud: create login credentials

1. Left menu → **Credentials → Create credentials → OAuth client ID**.
2. Application type: **Web application**.
3. Under **Authorized redirect URIs**, click **Add URI** and paste exactly:
   ```
   https://developers.google.com/oauthplayground
   ```
4. Create. A popup shows your **Client ID** and **Client secret** — copy both
   somewhere safe for a minute.

## Step 3 — Get your "refresh token" (all in the browser)

This is the key that lets the dashboard read your channel without you logging in
each time.

1. Open <https://developers.google.com/oauthplayground>.
2. Click the **gear icon** (top-right) → tick **Use your own OAuth credentials**
   → paste your Client ID and Client secret from Step 2.
3. On the left, find the box **"Input your own scopes"** and paste these two
   (with a space between them):
   ```
   https://www.googleapis.com/auth/youtube.readonly https://www.googleapis.com/auth/yt-analytics.readonly
   ```
4. Click **Authorize APIs** → sign in with your channel's Google account → allow.
5. Click **Exchange authorization code for tokens**.
6. Copy the **Refresh token** value it shows (a long string starting `1//`).

You now have three values: **client_id**, **client_secret**, **refresh_token**.

## Step 4 — Supabase: your permanent storage

1. Go to <https://supabase.com> → **Start your project** → sign in with GitHub.
2. **New project** — give it a name and a database password (any strong one;
   you won't need it again). Wait ~1 minute for it to finish setting up.
3. Left menu → **SQL Editor → New query**. Open `schema.sql` from this folder,
   copy everything, paste it in, and click **Run**. (This makes the tables.)
4. Left menu → **Project Settings → API**. Copy two things:
   - **Project URL** (looks like `https://abcd.supabase.co`)
   - the **service_role** key (under Project API keys — it's the secret one).

## Step 5 — Put the code on GitHub (no install — drag & drop)

1. Go to <https://github.com> → sign up / sign in → **New repository**.
   Name it `booksntax-dashboard`, set it **Private**, and create it.
2. On the new repo page, click **uploading an existing file**.
3. Drag in everything from this folder **except** `secrets.toml.example` is fine
   to include, but never upload a real secrets file. Include the `.streamlit`
   folder (with `config.toml`), `app.py`, `supa.py`, `youtube_client.py`,
   `requirements.txt`, `schema.sql`, and `.gitignore`.
4. Click **Commit changes**.

## Step 6 — Deploy on Streamlit Cloud

1. Go to <https://share.streamlit.io> → sign in with GitHub → **Create app** →
   **Deploy a public app from GitHub** (your repo can still be private).
2. Pick your `booksntax-dashboard` repo, branch **main**, main file **app.py**.
3. Before deploying, open **Advanced settings → Secrets** and paste this,
   filling in your six values:
   ```toml
   [youtube]
   client_id = "PASTE"
   client_secret = "PASTE"
   refresh_token = "PASTE"

   [supabase]
   url = "PASTE"
   key = "PASTE service_role key"
   ```
4. Click **Deploy**. After a minute you'll get a public link to your dashboard.

## Step 7 — See your data

1. Open your dashboard link.
2. Click **🔄 Fetch latest data** in the sidebar. It pulls your videos and fills
   the charts. Click it again any time to refresh.

---

## Using it

- **Shorts only** is toggled on by default (your focus). Turn it off to see all
  videos.
- The cards up top: total/avg views, engagement rate, and **Avg % watched** —
  your stand-in for "skip rate" (100% minus that ≈ average skip).
- **Audience** charts (age, gender, country) fill in once videos clear YouTube's
  minimum-views threshold for showing demographics — expect them sparse at first.
- **View growth over time** appears after you've fetched on two or more days, so
  fetch every few days to build the trend.

## Notes

- The Google and Supabase/Streamlit consoles rename buttons occasionally — the
  order of steps stays the same even if a label moves.
- Your real secrets live only in Streamlit Cloud's Secrets box, never in GitHub.
- Stage 2 (Instagram Reels) reuses this exact app, Supabase, and Streamlit setup —
  we'll just add an Instagram fetch and the data lands in the same dashboard.
