import { useState, useEffect } from "react";
import { 
  Search, 
  BookOpen, 
  Newspaper, 
  FileText, 
  ExternalLink, 
  AlertCircle, 
  Compass, 
  ArrowRight,
  Globe,
  Sliders,
  Sparkles,
  Shield,
  History,
  Bookmark,
  LogOut,
  Zap,
  Trash2,
  X,
  UserCheck
} from "lucide-react";
import { useAuth } from "./AuthContext";
import { LoginModal } from "./LoginModal";
import "./App.css";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "";

function App() {
  const { isAuthenticated, loading: authLoading, user, logout, authFetch } = useAuth();

  const [query, setQuery] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [category, setCategory] = useState("all");
  const [results, setResults] = useState([]);
  const [isCached, setIsCached] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeFilter, setActiveFilter] = useState("all");
  const [hasSearched, setHasSearched] = useState(false);

  // Drawer states
  const [showHistory, setShowHistory] = useState(false);
  const [showBookmarks, setShowBookmarks] = useState(false);
  const [historyItems, setHistoryItems] = useState([]);
  const [bookmarkItems, setBookmarkItems] = useState([]);
  const [bookmarkedUrls, setBookmarkedUrls] = useState(new Set());

  const suggestions = [
    "Quantum Computing",
    "Machine Learning",
    "Vite JS",
    "Space Exploration",
    "WebAssembly"
  ];

  // Fetch bookmarks when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      loadBookmarks();
    }
  }, [isAuthenticated]);

  const loadBookmarks = async () => {
    try {
      const res = await authFetch(`${BACKEND_URL}/api/bookmarks`);
      if (res.ok) {
        const data = await res.json();
        setBookmarkItems(data);
        setBookmarkedUrls(new Set(data.map(b => b.url)));
      }
    } catch (err) {
      console.error("Failed to load bookmarks:", err);
    }
  };

  const loadHistory = async () => {
    try {
      const res = await authFetch(`${BACKEND_URL}/api/history`);
      if (res.ok) {
        const data = await res.json();
        setHistoryItems(data);
      }
    } catch (err) {
      console.error("Failed to load history:", err);
    }
  };

  const toggleHistoryDrawer = () => {
    if (!showHistory) {
      loadHistory();
    }
    setShowHistory(!showHistory);
    setShowBookmarks(false);
  };

  const toggleBookmarksDrawer = () => {
    if (!showBookmarks) {
      loadBookmarks();
    }
    setShowBookmarks(!showBookmarks);
    setShowHistory(false);
  };

  const handleSearch = async (e, queryText, categoryOverride) => {
    if (e) e.preventDefault();
    
    const targetQuery = queryText || query;
    if (!targetQuery || !targetQuery.trim()) return;

    const selectedCategory = categoryOverride !== undefined ? categoryOverride : category;

    setLoading(true);
    setError(null);
    setSearchQuery(targetQuery);
    setQuery(targetQuery);
    
    try {
      let url = `${BACKEND_URL}/api/search?q=${encodeURIComponent(targetQuery)}`;
      if (selectedCategory && selectedCategory !== "all") {
        url += `&category=${encodeURIComponent(selectedCategory)}`;
      }
      
      const response = await authFetch(url);
      if (!response.ok) {
        if (response.status === 401) {
          logout();
          throw new Error("Session expired. Please log in again.");
        }
        throw new Error(`Failed to fetch results: ${response.statusText}`);
      }
      const data = await response.json();
      setResults(data.results || []);
      setIsCached(!!data.is_cached);
      setHasSearched(true);
      setActiveFilter("all");
    } catch (err) {
      console.error(err);
      setError(err.message || "Unable to retrieve search results. Make sure the backend server is running.");
    } finally {
      setLoading(false);
    }
  };

  const handleCategoryChange = (newCategory) => {
    setCategory(newCategory);
    if (hasSearched && searchQuery) {
      handleSearch(null, searchQuery, newCategory);
    }
  };

  const handleSaveBookmark = async (result) => {
    try {
      const res = await authFetch(`${BACKEND_URL}/api/bookmarks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: result.title,
          url: result.url,
          domain: result.domain,
          snippet: result.snippet,
          source: result.source,
          raw_score: result.raw_score || 0.0
        })
      });
      if (res.ok) {
        setBookmarkedUrls(prev => new Set([...prev, result.url]));
        loadBookmarks();
      }
    } catch (err) {
      console.error("Failed to add bookmark:", err);
    }
  };

  const handleDeleteBookmark = async (id, url) => {
    try {
      const res = await authFetch(`${BACKEND_URL}/api/bookmarks/${id}`, {
        method: "DELETE"
      });
      if (res.ok) {
        setBookmarkItems(prev => prev.filter(b => b.id !== id));
        setBookmarkedUrls(prev => {
          const next = new Set(prev);
          next.delete(url);
          return next;
        });
      }
    } catch (err) {
      console.error("Failed to delete bookmark:", err);
    }
  };

  const getSourceIcon = (source) => {
    switch (source) {
      case "exa":
        return <Sparkles size={14} />;
      case "wikipedia":
        return <BookOpen size={14} />;
      case "hackernews":
        return <Newspaper size={14} />;
      case "arxiv":
        return <FileText size={14} />;
      case "duckduckgo":
      case "yahoo":
        return <Globe size={14} />;
      case "google":
      case "bing":
        return <Search size={14} />;
      default:
        return <Compass size={14} />;
    }
  };

  const getSourceLabel = (source) => {
    switch (source) {
      case "exa":
        return "Exa AI";
      case "wikipedia":
        return "Wikipedia";
      case "hackernews":
        return "Hacker News";
      case "arxiv":
        return "arXiv";
      case "duckduckgo":
        return "DuckDuckGo";
      case "google":
        return "Google";
      case "bing":
        return "Bing";
      case "yahoo":
        return "Yahoo";
      default:
        return source.charAt(0).toUpperCase() + source.slice(1);
    }
  };


  const formatDate = (dateStr) => {
    if (!dateStr) return null;
    try {
      const date = new Date(dateStr);
      if (isNaN(date.getTime())) return dateStr;
      return date.toLocaleDateString(undefined, { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
      });
    } catch (e) {
      return dateStr;
    }
  };

  const getSourcesList = (sourceStr) => {
    return (sourceStr || "").split(",").map(s => s.trim());
  };

  const filteredResults = activeFilter === "all" 
    ? results 
    : results.filter(r => getSourcesList(r.source).includes(activeFilter));

  const getSourceCount = (sourceName) => {
    if (sourceName === "all") return results.length;
    return results.filter(r => getSourcesList(r.source).includes(sourceName)).length;
  };

  if (authLoading) {
    return (
      <div className="loading-fullscreen">
        <div className="spinner"></div>
        <p>Connecting to Private Infrastructure...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginModal />;
  }

  return (
    <>
      <nav className="top-nav">
        <div className="nav-left">
          <div className="net-status-badge">
            <Shield size={14} className="shield-online-icon" />
            <span>Private Network (TLS & Tailscale)</span>
          </div>
        </div>
        <div className="nav-right">
          <div className="user-pill">
            <UserCheck size={14} />
            <span>{user?.username || "Authenticated"}</span>
          </div>
          <button 
            onClick={toggleHistoryDrawer} 
            className={`nav-action-btn ${showHistory ? "active" : ""}`}
            title="Private Search History"
          >
            <History size={16} />
            <span>History</span>
          </button>
          <button 
            onClick={toggleBookmarksDrawer} 
            className={`nav-action-btn ${showBookmarks ? "active" : ""}`}
            title="Saved Bookmarks"
          >
            <Bookmark size={16} />
            <span>Bookmarks</span>
            {bookmarkItems.length > 0 && (
              <span className="nav-badge-count">{bookmarkItems.length}</span>
            )}
          </button>
          <button onClick={logout} className="logout-btn" title="Sign Out">
            <LogOut size={16} />
          </button>
        </div>
      </nav>

      {/* History Drawer */}
      {showHistory && (
        <div className="drawer-panel">
          <div className="drawer-header">
            <h3><History size={18} style={{ marginRight: "8px" }} /> Private Search History</h3>
            <button onClick={() => setShowHistory(false)} className="close-btn"><X size={18} /></button>
          </div>
          <div className="drawer-content">
            {historyItems.length > 0 ? (
              historyItems.map((item) => (
                <div 
                  key={item.id} 
                  className="history-item"
                  onClick={() => {
                    handleSearch(null, item.query, item.category);
                    setShowHistory(false);
                  }}
                >
                  <div className="history-main">
                    <span className="history-query">{item.query}</span>
                    <span className="history-cat">{item.category}</span>
                  </div>
                  <div className="history-sub">
                    <span>{item.result_count} hits</span>
                    <span className="meta-dot">•</span>
                    <span>{formatDate(item.created_at)}</span>
                  </div>
                </div>
              ))
            ) : (
              <p className="empty-drawer">No search history recorded yet.</p>
            )}
          </div>
        </div>
      )}

      {/* Bookmarks Drawer */}
      {showBookmarks && (
        <div className="drawer-panel">
          <div className="drawer-header">
            <h3><Bookmark size={18} style={{ marginRight: "8px" }} /> Saved Bookmarks</h3>
            <button onClick={() => setShowBookmarks(false)} className="close-btn"><X size={18} /></button>
          </div>
          <div className="drawer-content">
            {bookmarkItems.length > 0 ? (
              bookmarkItems.map((bm) => (
                <div key={bm.id} className="bookmark-item">
                  <div className="bookmark-content">
                    <a href={bm.url} target="_blank" rel="noopener noreferrer" className="bookmark-title">
                      {bm.title}
                    </a>
                    <span className="bookmark-domain">{bm.domain}</span>
                  </div>
                  <button 
                    onClick={() => handleDeleteBookmark(bm.id, bm.url)} 
                    className="delete-bm-btn"
                    title="Remove Bookmark"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              ))
            ) : (
              <p className="empty-drawer">No saved bookmarks in your private database.</p>
            )}
          </div>
        </div>
      )}

      <header className="header">
        <div className="logo-container">
          <Search size={38} className="logo-icon" />
          <h1 className="logo-text">FIND-engine</h1>
        </div>
        <p className="logo-sub">
          Private Infrastructure Metasearch Engine. Integrated with PostgreSQL, Redis Caching, and TLS Security.
        </p>
      </header>

      <div className="search-container">
        <form onSubmit={(e) => handleSearch(e)}>
          <div className="search-box">
            <Search className="search-icon" size={20} />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search privately across all engines..."
              className="search-input"
              disabled={loading}
              autoFocus
            />
            <button type="submit" className="search-button" disabled={loading}>
              Search
              <ArrowRight size={16} />
            </button>
          </div>

          <div className="category-selector">
            <span className="category-label">
              <Sliders size={13} style={{ marginRight: "4px", verticalAlign: "middle" }} />
              Ranking Bias:
            </span>
            <button
              type="button"
              onClick={() => handleCategoryChange("all")}
              className={`category-chip ${category === "all" ? "active" : ""}`}
            >
              Balanced
            </button>
            <button
              type="button"
              onClick={() => handleCategoryChange("tech")}
              className={`category-chip ${category === "tech" ? "active" : ""}`}
            >
              Tech & Dev
            </button>
            <button
              type="button"
              onClick={() => handleCategoryChange("academic")}
              className={`category-chip ${category === "academic" ? "active" : ""}`}
            >
              Academic
            </button>
            <button
              type="button"
              onClick={() => handleCategoryChange("news")}
              className={`category-chip ${category === "news" ? "active" : ""}`}
            >
              News & General
            </button>
          </div>
        </form>
      </div>

      {!hasSearched && !loading && (
        <div className="suggestions-container">
          <span className="suggestion-label">Try searching:</span>
          {suggestions.map((s) => (
            <button
              key={s}
              onClick={(e) => handleSearch(e, s)}
              className="suggestion-chip"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {error && (
        <div className="no-results-state" style={{ borderColor: "rgba(239, 68, 68, 0.2)" }}>
          <AlertCircle size={40} style={{ color: "#ef4444", marginBottom: "16px" }} />
          <h3>Connection Error</h3>
          <p>{error}</p>
          <button 
            onClick={(e) => handleSearch(e, searchQuery)} 
            className="suggestion-chip" 
            style={{ marginTop: "12px", background: "rgba(239, 68, 68, 0.1)", borderColor: "rgba(239, 68, 68, 0.3)" }}
          >
            Retry Search
          </button>
        </div>
      )}

      {loading && (
        <div className="results-section">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="skeleton-card">
              <div className="skeleton-header">
                <div className="skeleton-title"></div>
                <div className="skeleton-badge"></div>
              </div>
              <div className="skeleton-url"></div>
              <div className="skeleton-text"></div>
              <div className="skeleton-text short"></div>
            </div>
          ))}
        </div>
      )}

      {hasSearched && !loading && !error && (
        <>
          <div className="filter-bar">
            <button
              onClick={() => setActiveFilter("all")}
              className={`filter-btn ${activeFilter === "all" ? "active" : ""}`}
            >
              All Results
              <span className="filter-badge">{getSourceCount("all")}</span>
            </button>
            <button
              onClick={() => setActiveFilter("exa")}
              className={`filter-btn source-exa ${activeFilter === "exa" ? "active" : ""}`}
            >
              {getSourceIcon("exa")}
              Exa AI
              <span className="filter-badge">{getSourceCount("exa")}</span>
            </button>
            <button
              onClick={() => setActiveFilter("wikipedia")}
              className={`filter-btn source-wikipedia ${activeFilter === "wikipedia" ? "active" : ""}`}
            >
              {getSourceIcon("wikipedia")}
              Wikipedia
              <span className="filter-badge">{getSourceCount("wikipedia")}</span>
            </button>

            <button
              onClick={() => setActiveFilter("hackernews")}
              className={`filter-btn source-hackernews ${activeFilter === "hackernews" ? "active" : ""}`}
            >
              {getSourceIcon("hackernews")}
              Hacker News
              <span className="filter-badge">{getSourceCount("hackernews")}</span>
            </button>
            <button
              onClick={() => setActiveFilter("arxiv")}
              className={`filter-btn source-arxiv ${activeFilter === "arxiv" ? "active" : ""}`}
            >
              {getSourceIcon("arxiv")}
              arXiv
              <span className="filter-badge">{getSourceCount("arxiv")}</span>
            </button>
            <button
              onClick={() => setActiveFilter("duckduckgo")}
              className={`filter-btn source-duckduckgo ${activeFilter === "duckduckgo" ? "active" : ""}`}
            >
              {getSourceIcon("duckduckgo")}
              DuckDuckGo
              <span className="filter-badge">{getSourceCount("duckduckgo")}</span>
            </button>
            <button
              onClick={() => setActiveFilter("google")}
              className={`filter-btn source-google ${activeFilter === "google" ? "active" : ""}`}
            >
              {getSourceIcon("google")}
              Google
              <span className="filter-badge">{getSourceCount("google")}</span>
            </button>
            <button
              onClick={() => setActiveFilter("bing")}
              className={`filter-btn source-bing ${activeFilter === "bing" ? "active" : ""}`}
            >
              {getSourceIcon("bing")}
              Bing
              <span className="filter-badge">{getSourceCount("bing")}</span>
            </button>
            <button
              onClick={() => setActiveFilter("yahoo")}
              className={`filter-btn source-yahoo ${activeFilter === "yahoo" ? "active" : ""}`}
            >
              {getSourceIcon("yahoo")}
              Yahoo
              <span className="filter-badge">{getSourceCount("yahoo")}</span>
            </button>
          </div>

          <div className="results-section">
            <div className="results-info">
              <span>
                Found {results.length} results for <strong>"{searchQuery}"</strong>
              </span>
              {isCached && (
                <span className="redis-cache-badge">
                  <Zap size={12} style={{ marginRight: "4px" }} />
                  Redis Cache Hit (&lt;5ms)
                </span>
              )}
            </div>

            {filteredResults.length > 0 ? (
              filteredResults.map((result, idx) => {
                const isBookmarked = bookmarkedUrls.has(result.url);
                return (
                  <article key={`${result.domain}-${idx}`} className="result-card">
                    <div className="result-card-header">
                      <a
                        href={result.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="result-title-link"
                      >
                        {result.title}
                      </a>
                      <div className="source-badges-container">
                        {getSourcesList(result.source).map(src => (
                          <span key={src} className={`source-badge ${src}`}>
                            {getSourceLabel(src)}
                          </span>
                        ))}
                      </div>
                    </div>
                    
                    <div className="result-meta-row">
                      <span className="result-domain">{result.domain}</span>
                      {result.raw_score && (
                        <>
                          <span className="meta-dot">•</span>
                          <span className="score-pill">
                            <Sparkles size={11} style={{ marginRight: "3px", verticalAlign: "middle" }} />
                            Score: {result.raw_score}
                          </span>
                        </>
                      )}
                      {result.published_date && (
                        <>
                          <span className="meta-dot">•</span>
                          <span className="result-date">{formatDate(result.published_date)}</span>
                        </>
                      )}
                    </div>
                    
                    <p className="result-description">{result.snippet}</p>
                    
                    <div className="result-actions-row">
                      <a
                        href={result.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="result-url-action"
                      >
                        Visit Source <ExternalLink size={12} style={{ marginLeft: "4px" }} />
                      </a>

                      <button
                        type="button"
                        onClick={() => handleSaveBookmark(result)}
                        className={`bookmark-action-btn ${isBookmarked ? "saved" : ""}`}
                        disabled={isBookmarked}
                      >
                        <Bookmark size={13} style={{ marginRight: "4px" }} />
                        {isBookmarked ? "Saved in Postgres" : "Bookmark"}
                      </button>
                    </div>
                  </article>
                );
              })
            ) : (
              <div className="no-results-state">
                <Compass size={40} style={{ color: "var(--text-muted)", marginBottom: "16px" }} />
                <h3>No results found</h3>
                <p>We couldn't find any results from {getSourceLabel(activeFilter)} for your query.</p>
              </div>
            )}
          </div>
        </>
      )}

      {!hasSearched && !loading && !error && (
        <div className="initial-state">
          <div className="initial-graphic">
            <Compass size={48} />
          </div>
          <h3>Private Metasearch Architecture</h3>
          <p>
            FIND-engine operates inside your isolated network. Encrypted via HTTPS, backed by PostgreSQL query history, and powered by Redis acceleration.
          </p>
        </div>
      )}
    </>
  );
}

export default App;
