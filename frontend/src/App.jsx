import { useState } from "react";
import { 
  Search, 
  BookOpen, 
  Newspaper, 
  FileText, 
  ExternalLink, 
  AlertCircle, 
  Compass, 
  ArrowRight,
  Globe
} from "lucide-react";
import "./App.css";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

function App() {
  const [query, setQuery] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeFilter, setActiveFilter] = useState("all");
  const [hasSearched, setHasSearched] = useState(false);

  const suggestions = [
    "Quantum Computing",
    "Machine Learning",
    "Vite JS",
    "Space Exploration",
    "WebAssembly"
  ];

  const handleSearch = async (e, queryText) => {
    if (e) e.preventDefault();
    
    const targetQuery = queryText || query;
    if (!targetQuery || !targetQuery.trim()) return;

    setLoading(true);
    setError(null);
    setSearchQuery(targetQuery);
    setQuery(targetQuery);
    
    try {
      const response = await fetch(`${BACKEND_URL}/search?q=${encodeURIComponent(targetQuery)}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch results: ${response.statusText}`);
      }
      const data = await response.json();
      setResults(data.results || []);
      setHasSearched(true);
      setActiveFilter("all"); // reset filter on new search
    } catch (err) {
      console.error(err);
      setError("Unable to retrieve search results. Make sure the backend server is running.");
    } finally {
      setLoading(false);
    }
  };

  const getSourceIcon = (source) => {
    switch (source) {
      case "wikipedia":
        return <BookOpen size={14} />;
      case "hackernews":
        return <Newspaper size={14} />;
      case "arxiv":
        return <FileText size={14} />;
      case "duckduckgo":
        return <Globe size={14} />;
      case "google":
        return <Search size={14} />;
      case "bing":
        return <Search size={14} />;
      default:
        return <Compass size={14} />;
    }
  };

  const getSourceLabel = (source) => {
    switch (source) {
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

  // Helper to parse sources list from result (handles merged sources)
  const getSourcesList = (sourceStr) => {
    return sourceStr.split(",").map(s => s.trim());
  };

  // Filtered results calculation
  const filteredResults = activeFilter === "all" 
    ? results 
    : results.filter(r => getSourcesList(r.source).includes(activeFilter));

  // Count results per source
  const getSourceCount = (sourceName) => {
    if (sourceName === "all") return results.length;
    return results.filter(r => getSourcesList(r.source).includes(sourceName)).length;
  };

  return (
    <>
      <header className="header">
        <div className="logo-container">
          <Search size={38} className="logo-icon" />
          <h1 className="logo-text">FIND-engine</h1>
        </div>
        <p className="logo-sub">
          A high-performance search aggregator. Explore Wikipedia, Hacker News, arXiv, DuckDuckGo, Google, and Bing.
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
              placeholder="What are you looking for?"
              className="search-input"
              disabled={loading}
              autoFocus
            />
            <button type="submit" className="search-button" disabled={loading}>
              Search
              <ArrowRight size={16} />
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
          </div>

          <div className="results-section">
            <div className="results-info">
              <span>
                Found {results.length} unique results for <strong>"{searchQuery}"</strong>
              </span>
              {activeFilter !== "all" && (
                <span>
                  Showing {filteredResults.length} from {getSourceLabel(activeFilter)}
                </span>
              )}
            </div>

            {filteredResults.length > 0 ? (
              filteredResults.map((result, idx) => (
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
                    {result.published_date && (
                      <>
                        <span className="meta-dot">•</span>
                        <span className="result-date">{formatDate(result.published_date)}</span>
                      </>
                    )}
                  </div>
                  
                  <p className="result-description">{result.snippet}</p>
                  
                  <a
                    href={result.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="result-url-action"
                  >
                    Visit Source <ExternalLink size={12} style={{ marginLeft: "4px" }} />
                  </a>
                </article>
              ))
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
          <h3>Aggregated Knowledge</h3>
          <p>
            FIND-engine performs real-time queries across different engines. Enter a search term to find articles, papers, and community posts.
          </p>
        </div>
      )}
    </>
  );
}

export default App;
