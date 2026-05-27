import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  Archive,
  Boxes,
  BrainCircuit,
  Database,
  Download,
  FileUp,
  FolderOpen,
  GitBranch,
  LayoutDashboard,
  ListFilter,
  Network,
  RefreshCw,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  TerminalSquare,
} from "lucide-react";
import "./styles.css";

const navItems = [
  ["Console", LayoutDashboard],
  ["Ingest", FileUp],
  ["Recall", Search],
  ["Entities", Boxes],
  ["Graph", Network],
  ["Vault", Archive],
];

function App() {
  const [status, setStatus] = useState(null);
  const [entities, setEntities] = useState([]);
  const [graph, setGraph] = useState({ nodes: [], edges: [] });
  const [query, setQuery] = useState("recursive memory architecture");
  const [source, setSource] = useState("");
  const [results, setResults] = useState([]);
  const [log, setLog] = useState([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    refreshAll();
  }, []);

  async function refreshAll() {
    const [statusRes, entityRes, graphRes] = await Promise.all([
      fetch("/api/status"),
      fetch("/api/entities?limit=12"),
      fetch("/api/graph"),
    ]);
    setStatus(await statusRes.json());
    setEntities((await entityRes.json()).entities);
    setGraph(await graphRes.json());
  }

  async function runSearch(event) {
    event?.preventDefault();
    if (!query.trim()) return;
    setBusy(true);
    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=8`);
      const data = await res.json();
      setResults(data.results || []);
      addLog("Recall", `${data.results?.length || 0} results for "${query}"`, "Success");
    } finally {
      setBusy(false);
    }
  }

  async function runIngest(event) {
    event.preventDefault();
    if (!source.trim()) return;
    setBusy(true);
    try {
      const res = await fetch("/api/ingest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Ingest failed");
      addLog("Ingest", `${data.stats.conversations} conversations, ${data.stats.chunks} chunks`, "Success");
      await refreshAll();
    } catch (error) {
      addLog("Ingest", error.message, "Warning");
    } finally {
      setBusy(false);
    }
  }

  async function exportGraph() {
    const res = await fetch("/api/graph/export", { method: "POST" });
    const data = await res.json();
    addLog("Graph", `Exported ${data.path}`, "Success");
    await refreshAll();
  }

  function addLog(operation, details, state) {
    setLog((items) => [
      { time: new Date().toLocaleTimeString(), operation, details, state },
      ...items,
    ].slice(0, 8));
  }

  const counts = status?.counts || {};
  const graphStats = useMemo(() => [
    ["Nodes", graph.nodes?.length || 0],
    ["Edges", graph.edges?.length || 0],
    ["Types", new Set((graph.nodes || []).map((node) => node.type)).size],
  ], [graph]);

  return (
    <div className="app-shell">
      <aside className="side-rail">
        <div className="brand">
          <BrainCircuit size={32} />
          <div>
            <strong>ERMI</strong>
            <span>Command Center</span>
          </div>
        </div>
        <nav>
          {navItems.map(([label, Icon], index) => (
            <button className={index === 0 ? "active" : ""} key={label}>
              <Icon size={20} />
              <span>{label}</span>
            </button>
          ))}
        </nav>
        <div className="rail-footer">
          <button><Settings size={18} />Settings</button>
          <button><TerminalSquare size={18} />System</button>
          <div className="secure">
            <ShieldCheck size={20} />
            <div>
              <strong>ERMI Local</strong>
              <span>Offline capable</span>
            </div>
          </div>
        </div>
      </aside>

      <main>
        <header className="topbar">
          <StatusBlock icon={FolderOpen} label="Archive Root" value={status?.archiveRoot || "archive"} />
          <StatusBlock icon={Database} label="Database Status" value={status?.healthy ? "Healthy" : "Unknown"} accent="green" />
          <StatusBlock icon={BrainCircuit} label="Embedding Engine" value="sentence-transformers / fallback hash" />
          <StatusBlock icon={Activity} label="Last Ingest" value={status?.lastIngest?.imported_at || "No imports yet"} />
          <button className="icon-button" onClick={refreshAll} title="Refresh"><RefreshCw size={18} /></button>
        </header>

        <section className="workspace">
          <div className="primary">
            <Panel title="Semantic Search">
              <form className="search-row" onSubmit={runSearch}>
                <Search size={22} />
                <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Ask ERMI anything..." />
                <button disabled={busy}>Search</button>
              </form>
              <div className="filter-row">
                <button><ListFilter size={17} /> Filters</button>
                <select><option>All Time</option><option>Recent</option></select>
                <select><option>All Sources</option><option>ChatGPT</option><option>Vault</option></select>
                <label><input type="checkbox" defaultChecked /> Hybrid Search</label>
              </div>
            </Panel>

            <Panel title="Top Results" action={`${results.length || 0} loaded`}>
              <div className="results-list">
                {(results.length ? results : seedResults).map((item, index) => (
                  <ResultRow key={item.chunk_id || index} item={item} />
                ))}
              </div>
            </Panel>

            <div className="lower-grid">
              <Panel title="Ingest">
                <form className="ingest-box" onSubmit={runIngest}>
                  <div className="drop-zone">
                    <FileUp size={34} />
                    <strong>Paste a conversations.json path</strong>
                    <span>Raw source is preserved. Derived archive artifacts are rebuilt.</span>
                  </div>
                  <input value={source} onChange={(event) => setSource(event.target.value)} placeholder="C:\\Users\\TacIm\\Downloads\\conversations.json" />
                  <button disabled={busy || !source.trim()}><FileUp size={18} /> Run Ingest</button>
                </form>
              </Panel>

              <Panel title="Recent Operations">
                <table>
                  <tbody>
                    {(log.length ? log : seedLog).map((item, index) => (
                      <tr key={index}>
                        <td>{item.time}</td>
                        <td>{item.operation}</td>
                        <td>{item.details}</td>
                        <td className={item.state.toLowerCase()}>{item.state}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Panel>
            </div>
          </div>

          <aside className="intel">
            <Panel title="Archive Counts">
              <div className="stat-grid">
                <MiniStat label="Conversations" value={counts.conversations || 0} />
                <MiniStat label="Messages" value={counts.messages || 0} />
                <MiniStat label="Chunks" value={counts.chunks || 0} />
                <MiniStat label="Entities" value={counts.entities || 0} />
              </div>
            </Panel>

            <Panel title="Key Entities">
              <div className="entity-list">
                {(entities.length ? entities : seedEntities).map((entity) => (
                  <div className="entity-row" key={`${entity.kind}:${entity.name}`}>
                    <Sparkles size={16} />
                    <span>{entity.name}</span>
                    <small>{entity.kind}</small>
                    <strong>{Math.round(entity.score)}</strong>
                  </div>
                ))}
              </div>
            </Panel>

            <Panel title="Graph Overview">
              <div className="stat-grid three">
                {graphStats.map(([label, value]) => <MiniStat key={label} label={label} value={value} />)}
              </div>
              <div className="graph-line" />
              <button className="wide-action" onClick={exportGraph}><GitBranch size={18} /> Export Graph</button>
            </Panel>

            <Panel title="Quick Actions">
              <div className="quick-actions">
                <button onClick={refreshAll}><RefreshCw size={18} /> Rebuild View</button>
                <button onClick={exportGraph}><Download size={18} /> Export Data</button>
                <button onClick={() => addLog("Diagnostics", "Local API and SQLite responded", "Success")}><Activity size={18} /> Run Diagnostics</button>
              </div>
            </Panel>
          </aside>
        </section>
      </main>
    </div>
  );
}

function StatusBlock({ icon: Icon, label, value, accent }) {
  return (
    <div className="status-block">
      <Icon size={22} />
      <div>
        <span>{label}</span>
        <strong className={accent || ""}>{value}</strong>
      </div>
    </div>
  );
}

function Panel({ title, action, children }) {
  return (
    <section className="panel">
      <div className="panel-title">
        <h2>{title}</h2>
        {action && <span>{action}</span>}
      </div>
      {children}
    </section>
  );
}

function ResultRow({ item }) {
  const score = Number(item.score || 0.72);
  return (
    <div className="result-row">
      <div className="score">
        <span>{score.toFixed(2)}</span>
        <i style={{ width: `${Math.max(10, score * 100)}%` }} />
      </div>
      <div>
        <strong>{item.title}</strong>
        <p>{item.preview}</p>
      </div>
      <small>{item.markdown_path || "No vault file yet"}</small>
    </div>
  );
}

function MiniStat({ label, value }) {
  return (
    <div className="mini-stat">
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}

const seedResults = [
  {
    score: 0.87,
    title: "No indexed memories yet",
    preview: "Run ingest with a ChatGPT conversations.json export, then search recalls will appear here.",
    markdown_path: "archive/vault/conversations",
  },
];

const seedEntities = [
  { name: "ERMI", kind: "system", score: 0 },
  { name: "Memory Architecture", kind: "concept", score: 0 },
  { name: "SQLite", kind: "tool", score: 0 },
];

const seedLog = [
  { time: "--:--", operation: "Ready", details: "Command center initialized", state: "Success" },
];

createRoot(document.getElementById("root")).render(<App />);

