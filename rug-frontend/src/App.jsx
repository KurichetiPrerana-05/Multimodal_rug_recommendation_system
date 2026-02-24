import { useState, useRef } from "react";

const css = `
  @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;1,300;1,400&family=DM+Mono:wght@300;400&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --ink: #0e0d0b;
    --paper: #f5f2ec;
    --paper2: #ede9e0;
    --gold: #c8a96e;
    --gold-dim: #c8a96e33;
    --rust: #a0522d;
    --muted: #8a8070;
    --border: #d8d0c0;
    --card-bg: #faf8f4;
    --font-display: 'Cormorant Garamond', Georgia, serif;
    --font-mono: 'DM Mono', monospace;
    --ease: cubic-bezier(0.25, 0.46, 0.45, 0.94);
  }

  body {
    background: var(--paper);
    color: var(--ink);
    font-family: var(--font-display);
    min-height: 100vh;
    -webkit-font-smoothing: antialiased;
  }

  .root { min-height: 100vh; position: relative; overflow-x: hidden; }

  .noise {
    pointer-events: none;
    position: fixed;
    inset: 0;
    z-index: 100;
    opacity: 0.035;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
    background-size: 200px 200px;
  }

  .header {
    border-bottom: 1px solid var(--border);
    padding: 28px 48px;
    display: flex;
    align-items: center;
    backdrop-filter: blur(8px);
    background: rgba(245,242,236,0.85);
    position: sticky;
    top: 0;
    z-index: 50;
  }

  .header-inner {
    display: flex;
    align-items: center;
    gap: 20px;
    max-width: 1200px;
    margin: 0 auto;
    width: 100%;
  }

  .logo-mark {
    font-size: 28px;
    color: var(--gold);
    line-height: 1;
    flex-shrink: 0;
    animation: spin-slow 18s linear infinite;
  }

  @keyframes spin-slow { to { transform: rotate(360deg); } }

  .header-title {
    font-size: 26px;
    font-weight: 400;
    letter-spacing: 0.08em;
    color: var(--ink);
    line-height: 1;
  }

  .header-sub {
    font-size: 11.5px;
    font-family: var(--font-mono);
    color: var(--muted);
    letter-spacing: 0.06em;
    margin-top: 4px;
    font-weight: 300;
  }

  .main {
    max-width: 1200px;
    margin: 0 auto;
    padding: 56px 48px 96px;
  }

  .mode-toggle {
    display: inline-flex;
    border: 1px solid var(--border);
    border-radius: 2px;
    overflow: hidden;
    margin-bottom: 40px;
    background: var(--paper2);
  }

  .mode-btn {
    padding: 11px 26px;
    font-family: var(--font-mono);
    font-size: 11.5px;
    font-weight: 400;
    letter-spacing: 0.08em;
    border: none;
    background: transparent;
    color: var(--muted);
    cursor: pointer;
    transition: all 0.22s var(--ease);
    display: flex;
    align-items: center;
    gap: 8px;
    border-right: 1px solid var(--border);
  }

  .mode-btn:last-child { border-right: none; }
  .mode-btn:hover { color: var(--ink); background: rgba(200,169,110,0.08); }
  .mode-btn.active { background: var(--ink); color: var(--paper); }
  .mode-icon { font-size: 13px; color: var(--gold); }
  .mode-btn.active .mode-icon { color: var(--gold); }

  .search-panel {
    border: 1px solid var(--border);
    border-radius: 3px;
    padding: 36px;
    background: var(--card-bg);
    display: flex;
    flex-direction: column;
    gap: 24px;
    position: relative;
    overflow: hidden;
  }

  .search-panel::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--gold) 0%, transparent 70%);
  }

  .upload-zone {
    border: 1.5px dashed var(--border);
    border-radius: 2px;
    min-height: 220px;
    cursor: pointer;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s var(--ease), background 0.2s var(--ease);
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--paper);
  }

  .upload-zone:hover, .upload-zone.drag-active {
    border-color: var(--gold);
    background: rgba(200,169,110,0.04);
  }

  .upload-zone.has-image { border-style: solid; border-color: var(--border); }

  .upload-preview { width: 100%; height: 220px; object-fit: cover; display: block; }

  .upload-overlay {
    position: absolute;
    inset: 0;
    background: rgba(14,13,11,0.55);
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity 0.2s;
    font-family: var(--font-mono);
    font-size: 11px;
    letter-spacing: 0.12em;
    color: var(--paper);
    text-transform: uppercase;
  }

  .upload-zone:hover .upload-overlay { opacity: 1; }

  .upload-placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 16px;
    color: var(--muted);
    user-select: none;
  }

  .upload-icon { font-size: 36px; color: var(--border); line-height: 1; }

  .upload-placeholder-text { text-align: center; }
  .upload-placeholder-text p { font-size: 17px; font-weight: 300; color: var(--ink); margin-bottom: 4px; }
  .upload-placeholder-text span { font-family: var(--font-mono); font-size: 11px; color: var(--muted); letter-spacing: 0.08em; }

  .filters-row { display: flex; gap: 18px; align-items: flex-end; flex-wrap: wrap; }
  .flex-grow { flex: 1; min-width: 200px; }

  .input-group { display: flex; flex-direction: column; gap: 7px; }

  .input-label {
    font-family: var(--font-mono);
    font-size: 10.5px;
    letter-spacing: 0.1em;
    color: var(--muted);
    text-transform: uppercase;
  }

  .text-input {
    padding: 11px 14px;
    border: 1px solid var(--border);
    border-radius: 2px;
    background: var(--paper);
    font-family: var(--font-display);
    font-size: 16px;
    color: var(--ink);
    font-weight: 300;
    transition: border-color 0.18s var(--ease), box-shadow 0.18s var(--ease);
    outline: none;
    -webkit-appearance: none;
  }

  .text-input:focus { border-color: var(--gold); box-shadow: 0 0 0 3px var(--gold-dim); }
  .text-input::placeholder { color: var(--border); }
  .price-input { width: 140px; }
  .select-input { width: 140px; cursor: pointer; }

  .search-btn {
    align-self: flex-start;
    padding: 13px 40px;
    background: var(--ink);
    color: var(--paper);
    border: 1.5px solid var(--ink);
    border-radius: 2px;
    font-family: var(--font-display);
    font-size: 17px;
    font-weight: 300;
    letter-spacing: 0.05em;
    cursor: pointer;
    transition: background 0.2s var(--ease), color 0.2s var(--ease), transform 0.15s var(--ease);
  }

  .search-btn:not(:disabled):hover { background: var(--gold); border-color: var(--gold); color: var(--ink); }
  .search-btn:not(:disabled):active { transform: translateY(1px); }
  .search-btn:disabled { opacity: 0.5; cursor: default; }

  .btn-loading { display: flex; align-items: center; gap: 10px; }

  .spinner {
    width: 13px; height: 13px;
    border: 1.5px solid rgba(245,242,236,0.3);
    border-top-color: var(--paper);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }

  @keyframes spin { to { transform: rotate(360deg); } }

  /* Parsed query tag strip */
  .parsed-strip {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: -8px;
    margin-bottom: 4px;
  }

  .parsed-tag {
    font-family: var(--font-mono);
    font-size: 10px;
    letter-spacing: 0.1em;
    padding: 4px 10px;
    border-radius: 1px;
    background: var(--gold-dim);
    border: 1px solid var(--gold);
    color: var(--rust);
    text-transform: uppercase;
  }

  .results-section { margin-top: 56px; }

  .results-header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-bottom: 28px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border);
  }

  .results-title { font-size: 30px; font-weight: 300; color: var(--ink); font-style: italic; }

  .model-badge {
    font-family: var(--font-mono);
    font-size: 10px;
    letter-spacing: 0.14em;
    padding: 4px 11px;
    border-radius: 1px;
    text-transform: uppercase;
  }

  .model-badge.clip { background: var(--ink); color: var(--gold); }
  .model-badge.sbert { background: var(--gold-dim); color: var(--rust); border: 1px solid var(--gold); }
  .model-badge.structured { background: var(--rust); color: var(--paper); }

  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 24px; }

  .card {
    border: 1px solid var(--border);
    border-radius: 3px;
    background: var(--card-bg);
    overflow: hidden;
    transition: transform 0.22s var(--ease), box-shadow 0.22s var(--ease), border-color 0.22s;
    animation: fade-up 0.45s var(--ease) both;
  }

  @keyframes fade-up {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  .card:hover { transform: translateY(-4px); box-shadow: 0 16px 40px rgba(14,13,11,0.1); border-color: var(--gold); }

  .card-img-wrap { position: relative; aspect-ratio: 4/3; overflow: hidden; background: var(--paper2); }

  .card-img { width: 100%; height: 100%; object-fit: cover; display: block; transition: transform 0.4s var(--ease); }
  .card:hover .card-img { transform: scale(1.04); }

  .card-img-placeholder { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: var(--paper2); }

  .placeholder-inner { text-align: center; display: flex; flex-direction: column; align-items: center; gap: 8px; }
  .placeholder-initials { font-size: 32px; font-weight: 300; color: var(--border); letter-spacing: 0.1em; }
  .placeholder-label { font-family: var(--font-mono); font-size: 10px; color: var(--border); letter-spacing: 0.08em; }

  .score-pill {
    position: absolute; top: 10px; right: 10px;
    background: rgba(14,13,11,0.78);
    backdrop-filter: blur(6px);
    color: var(--gold);
    font-family: var(--font-mono);
    font-size: 10px;
    padding: 4px 9px;
    border-radius: 1px;
    letter-spacing: 0.06em;
  }

  .card-body { padding: 18px 20px 20px; display: flex; flex-direction: column; gap: 6px; }
  .card-title { font-size: 17px; font-weight: 400; line-height: 1.35; color: var(--ink); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
  .card-price { font-family: var(--font-mono); font-size: 13px; color: var(--rust); font-weight: 400; letter-spacing: 0.04em; }
  .card-why { font-size: 13.5px; font-weight: 300; color: var(--muted); line-height: 1.6; font-style: italic; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

  .skeleton { pointer-events: none; animation: fade-up 0.35s var(--ease) both; }

  .skel-img {
    aspect-ratio: 4/3;
    background: linear-gradient(90deg, var(--paper2) 25%, var(--border) 50%, var(--paper2) 75%);
    background-size: 300% 100%;
    animation: shimmer 1.5s infinite;
  }

  .skel-body { padding: 18px 20px; display: flex; flex-direction: column; gap: 10px; }

  .skel-line {
    height: 13px; border-radius: 2px;
    background: linear-gradient(90deg, var(--paper2) 25%, var(--border) 50%, var(--paper2) 75%);
    background-size: 300% 100%;
    animation: shimmer 1.5s infinite;
  }

  .skel-line.short { width: 55%; }
  .skel-line.xshort { width: 35%; }

  @keyframes shimmer { to { background-position: -300% 0; } }

  .empty-state {
    text-align: center; padding: 80px 0; color: var(--muted);
    display: flex; flex-direction: column; align-items: center; gap: 14px;
  }

  .empty-icon { font-size: 40px; color: var(--border); animation: pulse 2.5s ease-in-out infinite; }
  .empty-state p { font-size: 18px; font-weight: 300; font-style: italic; }

  @keyframes pulse {
    0%, 100% { opacity: 0.4; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.08); }
  }

  @media (max-width: 768px) {
    .header { padding: 20px 24px; }
    .main { padding: 36px 24px 72px; }
    .search-panel { padding: 24px; }
    .filters-row { flex-direction: column; }
    .price-input, .select-input { width: 100%; }
  }
`;

export default function App() {
  const [image, setImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [textQuery, setTextQuery] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [modelType, setModelType] = useState("clip");
  const [sortBy, setSortBy] = useState("score");
  const [results, setResults] = useState([]);
  const [parsedQuery, setParsedQuery] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef();

  const handleImageChange = (file) => {
    if (!file) return;
    setImage(file);
    setImagePreview(URL.createObjectURL(file));
  };

  const handleSearch = async () => {
    if (modelType === "clip" && !image) {
      alert("Please upload a room image for CLIP search");
      return;
    }
    if ((modelType === "sbert" || modelType === "structured") && !textQuery) {
      alert("Please enter a text query");
      return;
    }

    const formData = new FormData();
    if (image) formData.append("image", image);
    formData.append("text_query", textQuery || "");
    formData.append("top_k", 8);
    formData.append("model_type", modelType);

    // ── FIX: only send max_price if it's a valid positive number ──
    const parsedMax = parseFloat(maxPrice);
    if (maxPrice !== "" && !isNaN(parsedMax)) {
      formData.append("max_price", parsedMax);
    }

    setLoading(true);
    setResults([]);
    setParsedQuery(null);

    try {
      const res = await fetch("http://127.0.0.1:8000/search/multimodal", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      // Show parsed query tags for structured mode
      if (data.parsed_query) setParsedQuery(data.parsed_query);

      let arr = Array.isArray(data.results) ? data.results : [];
      arr = sortBy === "price"
        ? arr.sort((a, b) => a.price - b.price)
        : arr.sort((a, b) => b.score - a.score);
      setResults(arr);
    } catch (err) {
      console.error(err);
      alert("Error calling backend.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <style>{css}</style>
      <div className="root">
        <div className="noise" />

        <header className="header">
          <div className="header-inner">
            <div className="logo-mark">✦</div>
            <div>
              <h1 className="header-title">Rug Recommender</h1>
              <p className="header-sub">Multimodal search — CLIP · SBERT · Structured</p>
            </div>
          </div>
        </header>

        <main className="main">
          {/* Mode Toggle */}
          <div className="mode-toggle">
            <button
              className={`mode-btn ${modelType === "clip" ? "active" : ""}`}
              onClick={() => setModelType("clip")}
            >
              <span className="mode-icon">⬡</span> CLIP — Image + Text
            </button>
            <button
              className={`mode-btn ${modelType === "sbert" ? "active" : ""}`}
              onClick={() => setModelType("sbert")}
            >
              <span className="mode-icon">◈</span> SBERT — Text only
            </button>
            <button
              className={`mode-btn ${modelType === "structured" ? "active" : ""}`}
              onClick={() => setModelType("structured")}
            >
              <span className="mode-icon">◇</span> Structured — Parsed Query
            </button>
          </div>

          <div className="search-panel">
            {/* Image upload — only for CLIP */}
            {modelType === "clip" && (
              <div
                className={`upload-zone ${dragOver ? "drag-active" : ""} ${imagePreview ? "has-image" : ""}`}
                onClick={() => fileInputRef.current.click()}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setDragOver(false);
                  handleImageChange(e.dataTransfer.files[0]);
                }}
              >
                {imagePreview ? (
                  <>
                    <img src={imagePreview} className="upload-preview" alt="preview" />
                    <div className="upload-overlay"><span>Change image</span></div>
                  </>
                ) : (
                  <div className="upload-placeholder">
                    <div className="upload-icon">⬡</div>
                    <div className="upload-placeholder-text">
                      <p>Drop your room image here</p>
                      <span>or click to browse</span>
                    </div>
                  </div>
                )}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  hidden
                  onChange={(e) => handleImageChange(e.target.files[0])}
                />
              </div>
            )}

            <div className="filters-row">
              <div className="input-group flex-grow">
                <label className="input-label">
                  {modelType === "structured"
                    ? "Structured query (e.g. 8x10 beige traditional rug)"
                    : modelType === "sbert"
                    ? "Describe what you want"
                    : "Refine with text (optional)"}
                </label>
                <input
                  type="text"
                  className="text-input"
                  placeholder={
                    modelType === "structured"
                      ? "e.g. round grey modern rug, runner 2x10 navy rug…"
                      : modelType === "sbert"
                      ? "e.g. bohemian vintage persian, minimalist wool…"
                      : "e.g. modern neutral, traditional persian…"
                  }
                  value={textQuery}
                  onChange={(e) => setTextQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                />
              </div>

              <div className="input-group">
                <label className="input-label">Max price (₹)</label>
                <input
                  type="number"
                  className="text-input price-input"
                  placeholder="No limit"
                  value={maxPrice}
                  min="0"
                  onChange={(e) => setMaxPrice(e.target.value)}
                />
              </div>

              <div className="input-group">
                <label className="input-label">Sort by</label>
                <select
                  className="text-input select-input"
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                >
                  <option value="score">Relevance</option>
                  <option value="price">Price ↑</option>
                </select>
              </div>
            </div>

            <button className="search-btn" onClick={handleSearch} disabled={loading}>
              {loading ? (
                <span className="btn-loading">
                  <span className="spinner" /> Searching…
                </span>
              ) : (
                <span>Search Rugs ✦</span>
              )}
            </button>
          </div>

          {/* Parsed query tags — only shown for structured mode */}
          {parsedQuery && modelType === "structured" && (
            <div className="parsed-strip" style={{ marginTop: "16px" }}>
              {parsedQuery.size && (
                <span className="parsed-tag">size: {parsedQuery.size}</span>
              )}
              {parsedQuery.color && (
                <span className="parsed-tag">color: {parsedQuery.color}</span>
              )}
              {parsedQuery.style && (
                <span className="parsed-tag">style: {parsedQuery.style}</span>
              )}
              {parsedQuery.shape && (
                <span className="parsed-tag">shape: {parsedQuery.shape}</span>
              )}
            </div>
          )}

          <section className="results-section">
            {(results.length > 0 || loading) && (
              <div className="results-header">
                <h2 className="results-title">
                  {loading ? "Finding matches…" : `${results.length} results`}
                </h2>
                <div className={`model-badge ${modelType}`}>
                  {modelType === "clip" ? "CLIP" : modelType === "sbert" ? "SBERT" : "STRUCTURED"}
                </div>
              </div>
            )}

            <div className="grid">
              {loading &&
                [...Array(8)].map((_, i) => (
                  <div key={i} className="card skeleton" style={{ animationDelay: `${i * 60}ms` }}>
                    <div className="skel-img" />
                    <div className="skel-body">
                      <div className="skel-line" />
                      <div className="skel-line short" />
                      <div className="skel-line xshort" />
                    </div>
                  </div>
                ))}

              {!loading &&
                results.map((r, idx) => (
                  <div key={idx} className="card" style={{ animationDelay: `${idx * 55}ms` }}>
                    <div className="card-img-wrap">
                      {r.image ? (
                        <img
                          src={`http://127.0.0.1:8000${r.image}`}
                          alt={r.title}
                          className="card-img"
                          onError={(e) => {
                            e.target.style.display = "none";
                            e.target.nextSibling.style.display = "flex";
                          }}
                        />
                      ) : null}
                      <div
                        className="card-img-placeholder"
                        style={{ display: r.image ? "none" : "flex" }}
                      >
                        <div className="placeholder-inner">
                          <div className="placeholder-initials">
                            {r.title?.split(" ").slice(0, 2).map((w) => w[0]).join("").toUpperCase()}
                          </div>
                          <span className="placeholder-label">Image unavailable</span>
                        </div>
                      </div>
                      <div className="score-pill">{Number(r.score).toFixed(3)}</div>
                    </div>

                    <div className="card-body">
                      <h3 className="card-title">{r.title}</h3>
                      <p className="card-price">₹ {r.price?.toLocaleString()}</p>
                      <p className="card-why">{r.why}</p>
                    </div>
                  </div>
                ))}
            </div>

            {!loading && results.length === 0 && (
              <div className="empty-state">
                <div className="empty-icon">◈</div>
                <p>No results yet — run a search above</p>
              </div>
            )}
          </section>
        </main>
      </div>
    </>
  );
}
