# FIND-engine - Private Infrastructure Metasearch Engine

FIND-engine is a high-performance, private metasearch engine designed to aggregate search queries across multiple platforms (Wikipedia, Hacker News, arXiv, DuckDuckGo, Google, Bing, Yahoo), normalize their schemas, deduplicate links, and serve them securely over an **encrypted TLS channel** within your **private network (Tailscale / WireGuard)**.

```
Internet (Blocked / Firewalled)
   │
   X  <-- Blocked Public Access
   │
Tailscale / WireGuard Overlay Network
   │
   ▼
[Nginx / SSL Reverse Proxy]  (https://search.yourdomain)
   │
   ├── [React Frontend]       (Protected UI & /login Portal)
   ├── [FastAPI Search API]   (JWT Auth & Protected Endpoints)
   ├── [PostgreSQL]           (User Accounts, Search History & Bookmarks)
   └── [Redis Cache]          (Fast Search Result Caching & Session Storage)
```

---

## 🔒 Private Security & Architecture

1. **Private Network Access (Tailscale / WireGuard)**: Public access (`0.0.0.0`) from the internet is firewalled. Only authenticated members on your private mesh VPN or local home server network can route traffic to `search.yourdomain`.
2. **Encrypted HTTPS / TLS**: Nginx acts as an SSL terminating reverse proxy (HTTP/2 enabled, hardened security headers `HSTS`, `X-Frame-Options`, `X-Content-Type-Options`).
3. **JWT Authentication & `/login` Gateway**: Unauthenticated users are stopped at the private `/login` gateway. All API endpoints enforce JWT Bearer Token validation.
4. **PostgreSQL Persistence**: Stores encrypted user credentials, search query history logs, and saved result bookmarks.
5. **Redis Result Caching**: Accelerated query performance with Redis (<5ms response latency for repeated queries) with a 10-minute cache window.

---

## 🛠️ Tech Stack

- **Reverse Proxy / TLS**: Nginx 1.25+ with SSL certificate termination.
- **Backend API**: FastAPI (Python 3.13), SQLAlchemy 2.0 (Async), `asyncpg`, `redis-py`, PyJWT, Passlib (bcrypt), `httpx`, BeautifulSoup4.
- **Frontend App**: React (Vite), Vanilla CSS (glassmorphism/dark mode), Lucide Icons, Custom Auth Context.
- **Database Layer**: PostgreSQL 16 Alpine.
- **Caching Layer**: Redis 7 Alpine.
- **Containerization**: Docker & Docker Compose.

---

## 🚀 Quick Startup & Private Deployment

### 1. Generate SSL Certificates for `search.yourdomain`

Generate self-signed TLS certificates for `search.yourdomain`:

**On Linux / macOS / Git Bash / WSL:**
```bash
chmod +x scripts/generate-certs.sh
./scripts/generate-certs.sh
```

**On Windows PowerShell:**
```powershell
.\scripts\generate-certs.ps1
```

*(This creates `search.yourdomain.crt` and `search.yourdomain.key` in `./nginx/certs/`)*

### 2. Configure Local DNS / Hosts File

Add `search.yourdomain` to your local machine's `hosts` file:

**Linux / macOS**: `/etc/hosts`  
**Windows**: `C:\Windows\System32\drivers\etc\hosts`

```hosts
127.0.0.1 search.yourdomain
```

### 3. Launch Private Infrastructure via Docker Compose

Run all 5 orchestrated services (`postgres`, `redis`, `backend`, `frontend`, `nginx-proxy`):

```bash
docker-compose up --build
```

---

## 🔑 Accessing Private Search

1. Open your browser and navigate to:
   ```
   https://search.yourdomain
   ```
2. You will be greeted by the **Private Search Portal `/login`**.
3. **Default Admin Credentials**:
   - **Username**: `admin`
   - **Password**: `admin123`
4. Click **Unlock Private Search** to access your encrypted metasearch engine!

---

## 📡 API Endpoints & Security

- **`POST /api/auth/login`**: Authenticate and obtain JWT access token.
- **`GET /api/auth/me`**: Verify JWT token and retrieve profile.
- **`GET /api/search?q={query}&category={cat}`** *(Protected)*: Execute metasearch across all providers with Redis caching and PostgreSQL query logging.
- **`GET /api/history`** *(Protected)*: Retrieve user's search history.
- **`GET /api/bookmarks`** & **`POST /api/bookmarks`** *(Protected)*: Manage saved bookmarks.
- **`GET /health`**: Health status check for Backend, Database, Redis, and Private Infrastructure.

---


## 🛡️ Tailscale / WireGuard Production Setup

To restrict access exclusively to your Tailscale tailnet or WireGuard VPN:

1. Install Tailscale on your host/VPS:
   ```bash
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up
   ```
2. Update `docker-compose.yml` `nginx-proxy` ports to bind directly to your Tailscale IP:
   ```yaml
   ports:
     - "100.x.y.z:80:80"
     - "100.x.y.z:443:443"
   ```
3. Enable Tailscale HTTPS / MagicDNS for `search.yourdomain.ts.net` for automatic Let's Encrypt certificates!
