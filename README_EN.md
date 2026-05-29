# AI Backend News Sources Spider

[中文](README.md) | English

---

Automatically crawls GitHub Trending, Hacker News, TLDR AI, OpenAI, Anthropic, and InfoQ AI Development daily. Generates Chinese summaries via AI, outputs unified JSON, archives by source permanently, and caches hot data in Redis for 3 days. Also provides a FastAPI read-only API and a Vue frontend news feed page.

## Features

- Crawl GitHub Trending **daily** and **weekly** hotspots (Top 10 each by default)
- Crawl **Hacker News Top 10** stories and comments (via official Firebase API)
- Crawl **TLDR AI latest issue** curated content (via official archive page)
- Crawl **OpenAI News** official latest content
- Crawl **Anthropic Newsroom** official latest content
- Crawl **InfoQ AI Development** latest engineering practices (RSS preferred)
- Generate Chinese summaries via GitHub Models API (GPT-4o)
- GitHub summaries: recommend like a senior colleague — explain pain points, compare advantages, how backend can use it
- HN summaries: [Topic] + [Community Highlights] + [Controversies/Insights], citing specific commenters
- TLDR AI summaries: Chinese quick report for backend engineers, focus on engineering implementation
- OpenAI / Anthropic / InfoQ summaries: Chinese summary + backend action items (down to API/SDK level)
- Generate HTML table emails, support multiple recipients
- Generate unified JSON: default `output/latest.json`
- Archive by source permanently: `output/<source>/<YYYY-MM-DD>/<batch>.json`
- Write Redis latest snapshot, default TTL 3 days
- Provide FastAPI read-only API, with fallback to disk when Redis is unavailable
- Provide Vue frontend engineering news feed page
- Six sources independently fault-tolerant — any one succeeding will output JSON, archive, and refresh Redis
- Email disabled by default, can be enabled via configuration
- Built-in scheduler runs collection after API startup
- API access logs: record IP, path, duration, status code for each request
- Hourly access statistics: total requests, unique IPs, top endpoints, avg duration

## Deployment

### 1. Clone & Install

```bash
git clone https://github.com/wenbochang888/github-trending-spider.git
cd github-trending-spider
pip3 install -r requirements.txt
```

Frontend dependencies:

```bash
cd frontend
npm install
```

### 2. Configure Environment Variables

Edit `~/.bash_profile`, append:

```bash
# AI Backend Sources Spider
export GITHUB_TOKEN="ghp_your_token"
export SMTP_USER="your_email@example.com"
export SMTP_PASSWORD="your_smtp_password"
export MAIL_TO="recipient@example.com"
export SEND_EMAIL_ENABLED=false
export REDIS_URL="redis://localhost:6379/0"
export SPIDER_SCHEDULER_ENABLED=true
export SPIDER_SCHEDULE_TIMES="07:50,15:50,23:50"
export SPIDER_RUN_ON_STARTUP=false
```

Apply:

```bash
source ~/.bash_profile
```

> Get GitHub Token: [https://github.com/settings/tokens](https://github.com/settings/tokens) -> Generate new token -> check `models:read`

### 3. Test Collection

```bash
python3 main.py
```

If `output/latest.json`, `output/<source>/<YYYY-MM-DD>/<batch>.json` are generated and Redis is refreshed, the collection is successful. Logs at `/root/logs/github-python/trending.log`.

### 4. Start Backend API (Local Debug)

```bash
python3 -m uvicorn api:app --host 0.0.0.0 --port 8000
```

After starting, both FastAPI and the in-process scheduler will run. Default schedule: `07:50`, `15:50`, `23:50` daily. In production, keep uvicorn single-worker to avoid multiple schedulers.

### 5. Start Frontend (Local Debug)

```bash
cd frontend
npm run serve
```

## File Structure

```
github-trending-spider/
├── main.py              # Main entry, orchestrates full workflow
├── github_trending.py   # GitHub Trending crawler + AI summary
├── hacker_news.py       # Hacker News API fetch + comments + AI summary
├── tldr_ai.py           # TLDR AI latest issue scraping + Chinese formatting
├── official_ai_sources.py # OpenAI / Anthropic / InfoQ scraping
├── content_items.py     # Unified content items, AI summary, JSON output
├── content_store.py     # Archive by source, Redis snapshot, disk fallback
├── redis_client.py      # Redis process-level connection pool
├── scheduler.py         # FastAPI in-process collection scheduler
├── source_registry.py   # Source ID and display info registry
├── api.py               # FastAPI public read-only API
├── access_log.py        # API access log middleware + hourly stats
├── email_builder.py     # HTML email template generation
├── email_sender.py      # SMTP email sending
├── config.py            # Configuration center (reads from env vars)
├── test_email.py        # SMTP email sending test
├── frontend/            # Vue 3 + Vue CLI frontend news feed
├── scripts/             # Backend, frontend, local dev startup scripts
├── requirements.txt     # Python dependencies
└── README.md            # Chinese README
```

## Configuration Options

All options have defaults, override via environment variables:

| Variable | Default | Description |
| --- | --- | --- |
| `GITHUB_TRENDING_TOP_COUNT` | 10 | GitHub Daily/Weekly top N repos each |
| `HN_TOP_COUNT` | 10 | HN top N stories |
| `HN_COMMENTS_PER_STORY` | 10 | Top N comments per story |
| `HN_MAX_RETRIES` | 5 | HN max request retries |
| `HN_CONCURRENT_WORKERS` | 10 | Concurrent request threads |
| `TLDR_AI_HOME_URL` | https://ai.tldr.tech/ | TLDR AI official archive page |
| `TLDR_AI_TOP_COUNT` | 10 | TLDR AI top N items |
| `TLDR_AI_MAX_RETRIES` | 5 | TLDR AI max request retries |
| `OPENAI_NEWS_URL` | https://openai.com/news/ | OpenAI official news page |
| `OPENAI_NEWS_RSS_URL` | https://openai.com/news/rss.xml | OpenAI official news RSS |
| `OPENAI_NEWS_COUNT` | 10 | OpenAI top N items |
| `ANTHROPIC_NEWS_URL` | https://www.anthropic.com/news | Anthropic official news page |
| `ANTHROPIC_NEWS_COUNT` | 10 | Anthropic top N items |
| `INFOQ_AI_RSS_URL` | https://feed.infoq.com/ai-development/news | InfoQ AI Development single RSS |
| `INFOQ_AI_PAGE_URL` | https://www.infoq.com/ai-development/ | InfoQ AI Development page |
| `INFOQ_AI_RSS_URLS` | Multiple InfoQ AI feeds | InfoQ aggregated RSS list |
| `INFOQ_AI_NEWS_COUNT` | 10 | InfoQ top N items |
| `OFFICIAL_AI_MAX_RETRIES` | 5 | Official AI sources max retries |
| `OUTPUT_JSON_PATH` | output/latest.json | Unified JSON output path |
| `OUTPUT_ARCHIVE_DIR` | output | Archive root directory by source |
| `REDIS_URL` | redis://localhost:6379/0 | Redis connection URL |
| `REDIS_SNAPSHOT_TTL_SECONDS` | 259200 | Redis source snapshot TTL (3 days) |
| `REDIS_KEY_PREFIX` | github-trending-spider | Redis key prefix |
| `API_MAX_ITEMS_PER_SOURCE` | 100 | Max items per source in API response |
| `API_CORS_ORIGINS` | empty | API CORS whitelist, comma-separated |
| `SEND_EMAIL_ENABLED` | false | Send email after each collection |
| `SPIDER_SCHEDULER_ENABLED` | true | Enable in-process scheduled collection |
| `SPIDER_SCHEDULE_TIMES` | 07:50,15:50,23:50 | Daily collection times (24h, comma-separated) |
| `SPIDER_RUN_ON_STARTUP` | false | Run collection immediately on API startup |
| `AI_MODEL` | gpt-4o | AI model |

Count configs follow "at most N items": e.g., if `INFOQ_AI_NEWS_COUNT=100` but only 14 items are parsed, only 14 are shown.

## Unified JSON Output

After running, `output/latest.json` is generated:

```json
{
  "generated_at": "2026-05-29T08:00:00",
  "item_count": 1,
  "items": [
    {
      "source": "OpenAI",
      "category": "AI Official Updates",
      "title": "Example Title",
      "url": "https://openai.com/news/...",
      "published_at": "May 29, 2026",
      "original_summary": "Original summary",
      "chinese_summary": "Chinese summary",
      "backend_focus": "Backend engineer focus points"
    }
  ]
}
```

## Archive by Source & Redis

Each collection also writes batch snapshots by source:

```text
output/github-daily/2026-05-29/01.json
output/github-weekly/2026-05-29/01.json
output/hacker-news/2026-05-29/01.json
output/tldr-ai/2026-05-29/01.json
output/openai/2026-05-29/01.json
output/anthropic/2026-05-29/01.json
output/infoq/2026-05-29/01.json
```

Multiple runs on the same day increment batch numbers to `02.json`, `03.json`. Disk archives are permanent; Redis only keeps the latest snapshot per source with a default 3-day TTL. API reads Redis first; falls back to latest disk batch if Redis is unavailable.

Redis URL examples:

```bash
# No password
export REDIS_URL="redis://localhost:6379/0"

# With password, no username
export REDIS_URL="redis://:password@localhost:6379/0"

# Redis ACL username + password
export REDIS_URL="redis://username:password@localhost:6379/0"
```

If the password contains special characters like `@`, `:`, `/`, `#`, URL-encode them first. E.g., `p@ss:word` becomes `p%40ss%3Aword`.

Redis client uses a process-level connection pool; API requests do not recreate the pool.

## API

```bash
# Health check
curl http://localhost:8000/api/health

# Source list
curl http://localhost:8000/api/sources

# Latest data for a single source
curl http://localhost:8000/api/sources/github-daily/latest
```

The v1 API only exposes public read-only GET queries. No public collection, write, or email endpoints. Rate limiting and caching at the Nginx layer is recommended for production.

## Built-in Scheduled Collection

After starting `./scripts/start_backend.sh`, the FastAPI process automatically starts the background scheduler. Default config:

```bash
export SPIDER_SCHEDULER_ENABLED=true
export SPIDER_SCHEDULE_TIMES="07:50,15:50,23:50"
export SPIDER_RUN_ON_STARTUP=false
```

To run collection immediately on startup:

```bash
export SPIDER_RUN_ON_STARTUP=true
```

No Linux cron needed. If deploying with multiple workers in the future, extract the scheduler into a separate process or add a distributed lock to avoid duplicate collection.

## Frontend

Frontend is in `frontend/`, using Vue 3 + Vue CLI. In dev mode, `/api` is proxied to `http://localhost:8000`.

Page title is **Daily AI Frontier** (Chinese: 每日AI前沿信息). Sidebar source labels are overridden by the frontend `SOURCE_DISPLAY_MAP` (backend registry unchanged):

| Source ID | Sidebar Display (EN) |
| --- | --- |
| github-daily | GitHub Daily Trending |
| github-weekly | GitHub Weekly Picks |
| hacker-news | Hacker News Hot |
| tldr-ai | TLDR AI Digest |
| openai | OpenAI Updates |
| anthropic | Anthropic Updates |
| infoq | AI Engineering |

Each content card shows title + summary + "Read More →" link. Topbar shows a countdown to next update.

**Language Switch**: The frontend supports Chinese/English via URL parameter `?lang=en` or `?lang=zh`. Default is Chinese. A toggle in the top bar allows manual switching.

```bash
cd frontend
npm install
npm run serve
```

Build:

```bash
cd frontend
npm run build
```

## Troubleshooting

```bash
# View logs
cat /root/logs/github-python/trending.log

# View API access records
grep "\[访问\]" /root/logs/github-python/trending.log

# Check if data comes from Redis or disk
grep "\[数据\]" /root/logs/github-python/trending.log

# View hourly statistics
grep "\[统计\]" /root/logs/github-python/trending.log

# Check Redis fallback
grep "磁盘归档" /root/logs/github-python/trending.log

# Check all accesses from a specific IP
grep "来源IP=123.45.67.89" /root/logs/github-python/trending.log

# Verify environment variables
echo $GITHUB_TOKEN
echo $SMTP_PASSWORD
```

Basic compile check:

```bash
python3 -m py_compile main.py config.py github_trending.py hacker_news.py tldr_ai.py official_ai_sources.py content_items.py content_store.py redis_client.py scheduler.py source_registry.py api.py access_log.py email_builder.py email_sender.py
```

## Production Startup & Updates

### Start Backend in Background

`scripts/start_backend.sh` automatically handles loading env vars, installing deps, stopping old processes, starting new backend in background, and log writing. Just run:

```bash
cd /root/work/workspace/gitee/github-trending-spider
bash scripts/start_backend.sh
```

Check if backend is listening on port `8000`:

```bash
ss -lntp | grep 8000
```

View backend logs:

```bash
tail -f /root/logs/github-python/backend.out
```

### Restart After Backend Code Changes

```bash
cd /root/work/workspace/gitee/github-trending-spider
git pull
bash scripts/start_backend.sh
ss -lntp | grep 8000
tail -f /root/logs/github-python/backend.out
```

The script writes application logs to `/root/logs/github-python/trending.log` and backend startup output to `/root/logs/github-python/backend.out`.

### Update After Frontend Code Changes

Frontend is served by Nginx from `frontend/dist/`. After modifying frontend code, rebuild:

```bash
cd /root/work/workspace/gitee/github-trending-spider
git pull
cd frontend
npm install
npm run build
```

Verify the built assets include the `/ai/` path:

```bash
cat dist/index.html
```

If only frontend code changed and `frontend/dist/` was regenerated, usually no Nginx restart is needed; just refresh the browser at `https://www.gdufe888.top/ai/`.

### Reload After Nginx Config Changes

Only when `/usr/local/nginx/conf/nginx.conf` is modified, test and reload Nginx:

```bash
/usr/local/nginx/sbin/nginx -t
/usr/local/nginx/sbin/nginx -s reload
```

Current production access flow:

```text
https://www.gdufe888.top/ai/     -> Nginx serves frontend/dist/ (static)
https://www.gdufe888.top/api/... -> Nginx reverse proxy to 127.0.0.1:8000 FastAPI
```
