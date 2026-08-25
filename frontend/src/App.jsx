import { useState, useEffect } from "react";
import { 
  Search, 
  BookOpen, 
  Newspaper, 
  FileText, 
  ExternalLink, 
  AlertCircle, 
  Compass, 
  ArrowRight
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

  // Suggestions for the landing view
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
    if (!targetQuery.strip ? !targetQuery.trim() : !targetQuery.trim()) return;

    setLoading(true);
    setError(null);
    setSearchQuery(targetQuery);
    setQuery(targetQuery); // keep input in sync
    
    try {
      const response = await fetch(`${BACKEND_URL}/search?q=${encodeURIComponent(targetQuery)}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch results: ${response.statusText}`);
      }
      const data = await response.json();
      setResults(data.results || []);
      setHasSearched(true);
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
        return <BookOpen size={16} />;
      case "hackernews":
        return <Newspaper size={16} />;
      case "arxiv":
        return <FileText size={16} />;
      default:
        return <Compass size={16} />;
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
      default:
        return source;
    }
  };

  // Filtered results calculation
  const filteredResults = activeFilter === "all" 
    ? results 
    : results.filter(r => r.source === activeFilter);

  // Count results per source
  const getSourceCount = (sourceName) => {
    if (sourceName === "all") return results.length;
    return results.filter(r => r.source === sourceName).length;
  };

  return (
    <>
      {/* Header Area */}
      <header className="header">
        <div className="logo-container">
          <Search size={38} className="logo-icon" />
          <h1 className="logo-text">FIND-engine</h1>
        </div>
        <p className="logo-sub">
          A high-performance search aggregator. Explore Wikipedia, Hacker News, and arXiv concurrently.
        </p>
      </header>

      {/* Search Input Box */}
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

      {/* Suggestion Chips (Before Searching) */}
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

      {/* Search Error Indicator */}
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

      {/* Skeleton Loading State */}
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

      {/* Results Rendering */}
      {hasSearched && !loading && !error && (
        <>
          {/* Provider Filter Chips */}
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
          </div>

          <div className="results-section">
            <div className="results-info">
              <span>
                Found {results.length} results for <strong>"{searchQuery}"</strong>
              </span>
              {activeFilter !== "all" && (
                <span>
                  Showing {filteredResults.length} from {getSourceLabel(activeFilter)}
                </span>
              )}
            </div>

            {filteredResults.length > 0 ? (
              filteredResults.map((result, idx) => (
                <article key={`${result.source}-${idx}`} className="result-card">
                  <div className="result-card-header">
                    <a
                      href={result.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="result-title-link"
                    >
                      {result.title}
                    </a>
                    <span className={`source-badge ${result.source}`}>
                      {getSourceLabel(result.source)}
                    </span>
                  </div>
                  <a
                    href={result.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="result-url"
                  >
                    {result.url} <ExternalLink size={12} style={{ marginLeft: "4px", verticalAlign: "middle" }} />
                  </a>
                  <p className="result-description">{result.description}</p>
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

      {/* Welcome Landing (Initial State) */}
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
