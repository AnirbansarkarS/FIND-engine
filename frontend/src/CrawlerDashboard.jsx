import { useState, useEffect } from "react";
import { 
  Bot, 
  Play, 
  Square, 
  RefreshCw, 
  Database, 
  Layers, 
  Globe, 
  CheckCircle2, 
  AlertCircle, 
  Search, 
  BookOpen, 
  Code, 
  Newspaper, 
  GraduationCap, 
  Terminal, 
  X, 
  Plus, 
  ArrowUpRight 
} from "lucide-react";
import { useAuth } from "./AuthContext";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "";

export const CrawlerDashboard = ({ isOpen, onClose }) => {
  const { authFetch } = useAuth();

  const [activeTab, setActiveTab] = useState("controls"); // controls, documents, custom_seeds
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState("");
  
  // Controls state
  const [selectedPack, setSelectedPack] = useState("documentation");
  const [targetPages, setTargetPages] = useState(100);
  const [customSeedsText, setCustomSeedsText] = useState("");
  
  // Documents browser state
  const [crawledDocs, setCrawledDocs] = useState([]);
  const [docSearchQuery, setDocSearchQuery] = useState("");
  const [docsLoading, setDocsLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchStatus();
      const interval = setInterval(fetchStatus, 3000); // Polling every 3s when dashboard is open
      return () => clearInterval(interval);
    }
  }, [isOpen]);

  useEffect(() => {
    if (isOpen && activeTab === "documents") {
      fetchDocuments();
    }
  }, [isOpen, activeTab, docSearchQuery]);

  const fetchStatus = async () => {
    try {
      const res = await authFetch(`${BACKEND_URL}/api/crawler/status`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.error("Failed to fetch crawler status:", err);
    }
  };

  const fetchDocuments = async () => {
    setDocsLoading(true);
    try {
      const url = docSearchQuery.trim()
        ? `${BACKEND_URL}/api/crawler/documents?q=${encodeURIComponent(docSearchQuery.trim())}&limit=50`
        : `${BACKEND_URL}/api/crawler/documents?limit=50`;
      const res = await authFetch(url);
      if (res.ok) {
        const data = await res.json();
        setCrawledDocs(data);
      }
    } catch (err) {
      console.error("Failed to fetch crawled documents:", err);
    } finally {
      setDocsLoading(false);
    }
  };

  const handleStartCrawl = async () => {
    setLoading(true);
    setActionMsg("");
    try {
      const res = await authFetch(`${BACKEND_URL}/api/crawler/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          preset_pack: selectedPack,
          target_pages: targetPages,
          depth_limit: 2
        })
      });
      if (res.ok) {
        setActionMsg("🚀 Web Crawler launched successfully!");
        fetchStatus();
      } else {
        setActionMsg("Failed to start crawler.");
      }
    } catch (err) {
      setActionMsg(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleStopCrawl = async () => {
    setLoading(true);
    try {
      const res = await authFetch(`${BACKEND_URL}/api/crawler/stop`, {
        method: "POST"
      });
      if (res.ok) {
        setActionMsg("🛑 Web Crawler stopped.");
        fetchStatus();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddCustomSeeds = async (e) => {
    e.preventDefault();
    if (!customSeedsText.trim()) return;

    const urls = customSeedsText
      .split("\n")
      .map(s => s.trim())
      .filter(s => s.startsWith("http://") || s.startsWith("https://"));

    if (urls.length === 0) {
      setActionMsg("Please enter valid HTTP/HTTPS URLs.");
      return;
    }

    setLoading(true);
    try {
      const res = await authFetch(`${BACKEND_URL}/api/crawler/seeds`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(urls)
      });
      if (res.ok) {
        const data = await res.json();
        setActionMsg(`✅ Added ${data.added} custom seed URLs!`);
        setCustomSeedsText("");
        fetchStatus();
      }
    } catch (err) {
      setActionMsg(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const isRunning = stats?.status === "running";

  const presetPacksInfo = [
    { id: "documentation", label: "Developer Docs", desc: "Python, React, MDN, FastAPI, SQLite", icon: Code },
    { id: "wikipedia", label: "Wikipedia & Reference", desc: "Computer Science, AI, Web Search articles", icon: BookOpen },
    { id: "tech_news", label: "Tech & Science News", desc: "HackerNews, ArXiv, Slashdot, Lobsters", icon: Newspaper },
    { id: "universities", label: "Universities", desc: "MIT, Stanford, Harvard research sites", icon: GraduationCap },
    { id: "open_source", label: "Open Source", desc: "GitHub Explore, PyPI Python, Rust Crates", icon: Terminal }
  ];

  return (
    <div className="crawler-drawer-overlay">
      <div className="crawler-drawer-card">
        <div className="crawler-header">
          <div className="crawler-title-group">
            <div className={`bot-icon-badge ${isRunning ? "active-pulse" : ""}`}>
              <Bot size={24} />
            </div>
            <div>
              <div className="crawler-title-row">
                <h2>Autonomous Web Crawler</h2>
                <span className={`status-pill ${isRunning ? "status-running" : "status-idle"}`}>
                  {isRunning ? "CRAWLING LIVE" : "IDLE"}
                </span>
              </div>
              <p className="crawler-subtitle">
                Discover, extract, and index pages independently into local database without third-party search APIs.
              </p>
            </div>
          </div>
          <button onClick={onClose} className="close-btn">
            <X size={20} />
          </button>
        </div>

        {/* Realtime Crawler Metrics Bar */}
        <div className="crawler-metrics-grid">
          <div className="metric-card">
            <div className="metric-header">
              <Database size={16} />
              <span>Pages Indexed</span>
            </div>
            <div className="metric-val">{stats?.pages_crawled ?? 0}</div>
            <div className="metric-sub">Stored in Local FTS Database</div>
          </div>

          <div className="metric-card">
            <div className="metric-header">
              <Layers size={16} />
              <span>URL Queue Depth</span>
            </div>
            <div className="metric-val">{stats?.pages_queued ?? 0}</div>
            <div className="metric-sub">Pending Frontier Links</div>
          </div>

          <div className="metric-card">
            <div className="metric-header">
              <Globe size={16} />
              <span>Target Scope</span>
            </div>
            <div className="metric-val">{stats?.pages_target ?? targetPages}</div>
            <div className="metric-sub">Max Pages limit</div>
          </div>
        </div>

        {/* Progress Bar when running */}
        {isRunning && (
          <div className="live-crawl-progress-box">
            <div className="progress-label-row">
              <span>Crawling Progress</span>
              <span>
                {stats?.pages_crawled ?? 0} / {stats?.pages_target ?? targetPages} pages ({Math.min(100, Math.round(((stats?.pages_crawled || 0) / (stats?.pages_target || 1)) * 100))}%)
              </span>
            </div>
            <div className="progress-bar-track">
              <div 
                className="progress-bar-fill" 
                style={{ width: `${Math.min(100, ((stats?.pages_crawled || 0) / (stats?.pages_target || 1)) * 100)}%` }}
              />
            </div>
            {stats?.current_url && (
              <div className="current-url-ticker">
                <RefreshCw size={12} className="spinning-icon" />
                <span>Crawling: {stats.current_url}</span>
              </div>
            )}
          </div>
        )}

        {/* Navigation Tabs */}
        <div className="crawler-tabs-row">
          <button 
            className={`crawler-tab-btn ${activeTab === "controls" ? "active" : ""}`}
            onClick={() => setActiveTab("controls")}
          >
            <Play size={14} />
            <span>Launch & Controls</span>
          </button>

          <button 
            className={`crawler-tab-btn ${activeTab === "documents" ? "active" : ""}`}
            onClick={() => setActiveTab("documents")}
          >
            <Database size={14} />
            <span>Browse Local Index ({stats?.pages_crawled ?? 0})</span>
          </button>

          <button 
            className={`crawler-tab-btn ${activeTab === "custom_seeds" ? "active" : ""}`}
            onClick={() => setActiveTab("custom_seeds")}
          >
            <Plus size={14} />
            <span>Add Custom Seed URLs</span>
          </button>
        </div>

        {actionMsg && (
          <div className="crawler-action-banner">
            <CheckCircle2 size={16} />
            <span>{actionMsg}</span>
          </div>
        )}

        {/* Tab 1: Controls */}
        {activeTab === "controls" && (
          <div className="crawler-tab-body">
            <div className="section-title">1. Select Target Scale</div>
            <div className="scale-selector-row">
              <button 
                className={`scale-btn ${targetPages === 100 ? "active" : ""}`}
                onClick={() => setTargetPages(100)}
              >
                <div className="scale-num">100 Pages</div>
                <div className="scale-desc">Tiny Crawl (~30 seconds)</div>
              </button>

              <button 
                className={`scale-btn ${targetPages === 1000 ? "active" : ""}`}
                onClick={() => setTargetPages(1000)}
              >
                <div className="scale-num">1,000 Pages</div>
                <div className="scale-desc">Medium Index (~5 minutes)</div>
              </button>

              <button 
                className={`scale-btn ${targetPages === 10000 ? "active" : ""}`}
                onClick={() => setTargetPages(10000)}
              >
                <div className="scale-num">10,000 Pages</div>
                <div className="scale-desc">Deep Domain Index</div>
              </button>
            </div>

            <div className="section-title" style={{ marginTop: "20px" }}>2. Select Seed Pack</div>
            <div className="seed-packs-grid">
              {presetPacksInfo.map((pack) => {
                const IconComp = pack.icon;
                const isSelected = selectedPack === pack.id;
                return (
                  <div 
                    key={pack.id} 
                    className={`seed-pack-card ${isSelected ? "selected" : ""}`}
                    onClick={() => setSelectedPack(pack.id)}
                  >
                    <div className="seed-pack-icon">
                      <IconComp size={20} />
                    </div>
                    <div>
                      <div className="seed-pack-name">{pack.label}</div>
                      <div className="seed-pack-desc">{pack.desc}</div>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="crawler-actions-footer">
              {!isRunning ? (
                <button 
                  onClick={handleStartCrawl} 
                  className="start-crawl-btn"
                  disabled={loading}
                >
                  <Play size={18} />
                  <span>Start Autonomous Crawl ({targetPages} Pages)</span>
                </button>
              ) : (
                <button 
                  onClick={handleStopCrawl} 
                  className="stop-crawl-btn"
                  disabled={loading}
                >
                  <Square size={18} />
                  <span>Stop Active Crawler</span>
                </button>
              )}
            </div>
          </div>
        )}

        {/* Tab 2: Browse Documents */}
        {activeTab === "documents" && (
          <div className="crawler-tab-body">
            <div className="doc-search-box">
              <Search size={16} />
              <input 
                type="text" 
                placeholder="Search locally indexed documents..."
                value={docSearchQuery}
                onChange={(e) => setDocSearchQuery(e.target.value)}
              />
            </div>

            <div className="docs-list-container">
              {docsLoading ? (
                <div className="docs-loading-state">Loading indexed pages...</div>
              ) : crawledDocs.length > 0 ? (
                crawledDocs.map((doc) => (
                  <div key={doc.id} className="crawled-doc-item">
                    <div className="doc-item-title-row">
                      <a href={doc.url} target="_blank" rel="noreferrer" className="doc-item-title">
                        {doc.title}
                        <ArrowUpRight size={14} style={{ marginLeft: "4px", inlineSize: "display" }} />
                      </a>
                      <span className="doc-item-domain">{doc.domain}</span>
                    </div>
                    <p className="doc-item-snippet">{doc.snippet}</p>
                    <div className="doc-item-meta">
                      <span>Word count: {doc.word_count}</span>
                      <span>•</span>
                      <span>Depth: {doc.depth}</span>
                      <span>•</span>
                      <span>Crawled: {doc.crawled_at ? new Date(doc.crawled_at).toLocaleTimeString() : ""}</span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="no-docs-state">
                  <Database size={32} style={{ color: "var(--text-muted)", marginBottom: "8px" }} />
                  <p>No crawled documents found in local index.</p>
                  <span>Launch the crawler above to build your independent index!</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab 3: Custom Seed URLs */}
        {activeTab === "custom_seeds" && (
          <div className="crawler-tab-body">
            <form onSubmit={handleAddCustomSeeds} className="custom-seeds-form">
              <label>Enter Custom Seed URLs (One per line):</label>
              <textarea 
                rows={6}
                placeholder="https://example.com&#10;https://python.org/blogs&#10;https://en.wikipedia.org/wiki/Computer_science"
                value={customSeedsText}
                onChange={(e) => setCustomSeedsText(e.target.value)}
              />
              <button type="submit" className="add-seeds-btn" disabled={loading}>
                <Plus size={16} />
                <span>Add Seeds to Crawl Queue</span>
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
};
