-- Run this ONCE in your Supabase project: SQL Editor -> New query -> paste -> Run.
-- It creates the tables the dashboard reads and writes.

create table if not exists videos (
  platform text not null,
  platform_video_id text not null,
  title text,
  url text,
  published_at timestamptz,
  views bigint,
  likes bigint,
  comments bigint,
  watch_time_minutes double precision,
  avg_view_duration_seconds double precision,
  avg_view_percentage double precision,   -- "% of the video watched on average" (skip proxy)
  duration_seconds integer,
  is_short boolean,
  thumbnail_url text,
  last_fetched_at timestamptz,
  primary key (platform, platform_video_id)
);

create table if not exists stats_history (
  id bigint generated always as identity primary key,
  platform text not null,
  platform_video_id text not null,
  captured_at timestamptz not null,
  views bigint,
  likes bigint,
  comments bigint
);

create table if not exists channel_demographics (
  id bigint generated always as identity primary key,
  platform text not null,
  captured_at timestamptz not null,
  dimension text not null,   -- 'age' | 'gender' | 'country'
  bucket text not null,
  percentage double precision
);
