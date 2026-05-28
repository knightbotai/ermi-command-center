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
  CheckCircle2,
  XCircle,
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

const apiBase = (import.meta.env.VITE_ERMI_API_BASE || "").replace(/\/$/, "");
const apiUrl = (path) => `${apiBase}${path}`;

function App() {
  const [status, setStatus] = useState(null);
  const [entities, setEntities] = useState([]);
  const [graph, setGraph] = useState({ nodes: [], edges: [] });
  const [query, setQuery] = useState("recursive memory architecture");
  const [source, setSource] = useState("");
  const [sourceType, setSourceType] = useState("chatgpt");
  const [watchSource, setWatchSource] = useState("");
  const [watchers, setWatchers] = useState([]);
  const [schema, setSchema] = useState(null);
  const [flags, setFlags] = useState([]);
  const [timeline, setTimeline] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [setupConfig, setSetupConfig] = useState({ chatgpt_source: "", chatlasso_source: "" });
  const [diagnostics, setDiagnostics] = useState(null);
  const [filters, setFilters] = useState({ mode: "", status: "", archetype: "", project: "", identity: "", regression: false });
  const [results, setResults] = useState([]);
  const [log, setLog] = useState([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    refreshAll();
  }, []);

  async function refreshAll() {
    const [statusRes, entityRes, graphRes, watcherRes, schemaRes, flagsRes, timelineRes, reviewRes, setupRes, diagnosticsRes] = await Promise.all([
      fetch(apiUrl("/api/status")),
      fetch(apiUrl("/api/entities?limit=12")),
      fetch(apiUrl("/api/graph")),
      fetch(apiUrl("/api/watchers")),
      fetch(apiUrl("/api/schema")),
      fetch(apiUrl("/api/flags?limit=20")),
      fetch(apiUrl("/api/timeline?limit=40")),
      fetch(apiUrl("/api/review/imports")),
      fetch(apiUrl("/api/setup")),
      fetch(apiUrl("/api/diagnostics")),
    ]);
    const nextStatus = await statusRes.json();
    setStatus(nextStatus);
    setEntities((await entityRes.json()).entities);
    setGraph(await graphRes.json());
    setWatchers((await watcherRes.json()).chatlasso || nextStatus.watchers || []);
    setSchema(await schemaRes.json());
    setFlags((await flagsRes.json()).flags || []);
    setTimeline((await timelineRes.json()).events || []);
    setReviews((await reviewRes.json()).imports || []);
    setSetupConfig((await setupRes.json()).config || { chatgpt_source: "", chatlasso_source: "" });
    setDiagnostics(await diagnosticsRes.json());
  }

  async function runSearch(event) {
    event?.preventDefault();
    if (!query.trim()) return;
    setBusy(true);
    try {
      const params = new URLSearchParams({ q: query, limit: "8" });
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.set(key, String(value));
      });
      const res = await fetch(apiUrl(`/api/search?${params.toString()}`));
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
      const endpoint = sourceType === "chatlasso" ? "/api/import/chatlasso" : "/api/ingest";
      const res = await fetch(apiUrl(endpoint), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Ingest failed");
      const label = sourceType === "chatlasso" ? "ChatLasso" : "ChatGPT";
      addLog(label, `${data.stats.conversations} memories, ${data.stats.chunks} chunks`, "Success");
      await refreshAll();
    } catch (error) {
      addLog("Ingest", error.message, "Warning");
    } finally {
      setBusy(false);
    }
  }

  async function exportGraph() {
    const res = await fetch(apiUrl("/api/graph/export"), { method: "POST" });
    const data = await res.json();
    addLog("Graph", `Exported ${data.path}`, "Success");
    await refreshAll();
  }

  async function createBackup() {
    const res = await fetch(apiUrl("/api/backup"), { method: "POST" });
    const data = await res.json();
    addLog("Backup", data.path || "Backup created", res.ok ? "Success" : "Warning");
  }

  async function saveSetup(event) {
    event?.preventDefault();
    setBusy(true);
    try {
      const res = await fetch(apiUrl("/api/setup"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(setupConfig),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Setup save failed");
      setSetupConfig(data.config);
      addLog("Setup", "Paths saved", "Success");
    } catch (error) {
      addLog("Setup", error.message, "Warning");
    } finally {
      setBusy(false);
    }
  }

  async function runFirstSetup() {
    setBusy(true);
    try {
      const res = await fetch(apiUrl("/api/setup/run"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(setupConfig),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "First setup failed");
      setSetupConfig(data.config);
      addLog("First Setup", "Initial ingest and watcher setup completed", "Success");
      await refreshAll();
    } catch (error) {
      addLog("First Setup", error.message, "Warning");
    } finally {
      setBusy(false);
    }
  }

  async function runDiagnostics() {
    const res = await fetch(apiUrl("/api/diagnostics"));
    const data = await res.json();
    setDiagnostics(data);
    addLog("Diagnostics", data.healthy ? "All checks passed" : "One or more checks need attention", data.healthy ? "Success" : "Warning");
  }

  async function openFolder(name) {
    const res = await fetch(apiUrl("/api/open-folder"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    const data = await res.json();
    addLog("Open Folder", data.path || name, res.ok ? "Success" : "Warning");
  }

  async function reviewImport(id, action) {
    const res = await fetch(apiUrl(`/api/review/imports/${encodeURIComponent(id)}/${action}`), { method: "POST" });
    const data = await res.json();
    addLog("Review", `${action}: ${data.conversation_id || id}`, res.ok ? "Success" : "Warning");
    await refreshAll();
  }

  async function addWatchFolder(event) {
    event.preventDefault();
    if (!watchSource.trim()) return;
    setBusy(true);
    try {
      const res = await fetch(apiUrl("/api/watchers/chatlasso"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: watchSource }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to add watcher");
      setWatchers(data.chatlasso || []);
      addLog("Watch", `Watching ${watchSource}`, "Success");
      setWatchSource("");
    } catch (error) {
      addLog("Watch", error.message, "Warning");
    } finally {
      setBusy(false);
    }
  }

  async function scanWatchFolders() {
    setBusy(true);
    try {
      const res = await fetch(apiUrl("/api/watchers/chatlasso/scan"), { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Watch scan failed");
      setWatchers(data.chatlasso || []);
      addLog("Watch Scan", `${data.stats.changed} changed, ${data.stats.chunks} chunks`, "Success");
      await refreshAll();
    } catch (error) {
      addLog("Watch Scan", error.message, "Warning");
    } finally {
      setBusy(false);
    }
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
          <StatusBlock icon={BrainCircuit} label="Schema" value={schema ? `${schema.current}/${schema.latest}` : "Checking"} />
          <StatusBlock icon={Activity} label="Last Ingest" value={status?.lastIngest?.imported_at || "No imports yet"} />
          <button className="icon-button" onClick={refreshAll} title="Refresh"><RefreshCw size={18} /></button>
        </header>

        <section className="workspace">
          <div className="primary">
            <Panel title="First-Run Setup" action={setupConfig.completed_at ? "Ready" : "Not completed"}>
              <form className="setup-box" onSubmit={saveSetup}>
                <div className="setup-fields">
                  <label>
                    <span>ChatGPT Export</span>
                    <input value={setupConfig.chatgpt_source || ""} onChange={(event) => setSetupConfig({ ...setupConfig, chatgpt_source: event.target.value })} placeholder="C:\\Users\\TacIm\\Downloads\\conversations.json" />
                  </label>
                  <label>
                    <span>ChatLasso SSI Folder</span>
                    <input value={setupConfig.chatlasso_source || ""} onChange={(event) => setSetupConfig({ ...setupConfig, chatlasso_source: event.target.value })} placeholder="C:\\Path\\To\\10_Data_Harvest\\11_SSI_Raw" />
                  </label>
                </div>
                <div className="setup-actions">
                  <button disabled={busy}><Settings size={17} /> Save Paths</button>
                  <button type="button" disabled={busy || (!setupConfig.chatgpt_source && !setupConfig.chatlasso_source)} onClick={runFirstSetup}><CheckCircle2 size={17} /> Run First Setup</button>
                  <button type="button" disabled={busy} onClick={runDiagnostics}><Activity size={17} /> Diagnostics</button>
                </div>
              </form>
            </Panel>

            <Panel title="Semantic Search">
              <form className="search-row" onSubmit={runSearch}>
                <Search size={22} />
                <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Ask ERMI anything..." />
                <button disabled={busy}>Search</button>
              </form>
              <div className="filter-row">
                <ListFilter size={17} />
                <input value={filters.mode} onChange={(event) => setFilters({ ...filters, mode: event.target.value })} placeholder="Mode" />
                <input value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })} placeholder="Status" />
                <select value={filters.project} onChange={(event) => setFilters({ ...filters, project: event.target.value })}>
                  <option value="">All Projects</option><option>ERMI</option><option>ChatLasso</option>
                </select>
                <select value={filters.identity} onChange={(event) => setFilters({ ...filters, identity: event.target.value })}>
                  <option value="">All Identities</option><option>KnightBot</option><option>Jusstin/DeeTorch</option>
                </select>
                <label><input type="checkbox" checked={filters.regression} onChange={(event) => setFilters({ ...filters, regression: event.target.checked })} /> Flags</label>
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
                  <div className="ingest-mode">
                    <button type="button" className={sourceType === "chatgpt" ? "selected" : ""} onClick={() => setSourceType("chatgpt")}>ChatGPT Export</button>
                    <button type="button" className={sourceType === "chatlasso" ? "selected" : ""} onClick={() => setSourceType("chatlasso")}>ChatLasso SSI</button>
                  </div>
                  <div className="drop-zone">
                    <FileUp size={34} />
                    <strong>{sourceType === "chatlasso" ? "Paste a ChatLasso SSI file or folder" : "Paste a conversations.json path"}</strong>
                    <span>{sourceType === "chatlasso" ? "SSI payloads become searchable ERMI memory chunks." : "Raw source is preserved. Derived archive artifacts are rebuilt."}</span>
                  </div>
                  <input value={source} onChange={(event) => setSource(event.target.value)} placeholder={sourceType === "chatlasso" ? "C:\\Path\\To\\Obsidian\\10_Data_Harvest\\11_SSI_Raw" : "C:\\Users\\TacIm\\Downloads\\conversations.json"} />
                  <button disabled={busy || !source.trim()}><FileUp size={18} /> {sourceType === "chatlasso" ? "Import SSI" : "Run Ingest"}</button>
                </form>
              </Panel>

              <Panel title="Watched Folders">
                <form className="watch-box" onSubmit={addWatchFolder}>
                  <input value={watchSource} onChange={(event) => setWatchSource(event.target.value)} placeholder="C:\\Path\\To\\10_Data_Harvest\\11_SSI_Raw" />
                  <div className="watch-actions">
                    <button disabled={busy || !watchSource.trim()}><FolderOpen size={17} /> Watch Folder</button>
                    <button type="button" disabled={busy} onClick={scanWatchFolders}><RefreshCw size={17} /> Scan Now</button>
                  </div>
                  <div className="watch-list">
                    {watchers.length ? watchers.map((item) => <span key={item}>{item}</span>) : <span>No ChatLasso folders watched yet.</span>}
                  </div>
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

            <div className="ops-grid">
              <Panel title="Regression Flags" action={`${flags.length} active`}>
                <div className="flag-list">
                  {(flags.length ? flags : [{ title: "No active flags", mode: "Clean", loss_report: "Regression surface is quiet." }]).map((item) => (
                    <div className="flag-row" key={item.id || item.title}>
                      <ShieldCheck size={17} />
                      <strong>{item.title}</strong>
                      <span>{item.mode || "Unknown mode"}</span>
                      <small>{item.loss_report || item.reason || "Needs review"}</small>
                    </div>
                  ))}
                </div>
              </Panel>

              <Panel title="Import Review Queue" action={`${reviews.filter((item) => item.status === "pending_review").length} pending`}>
                <div className="review-list">
                  {(reviews.length ? reviews : [{ conversation_id: "none", title: "No imports awaiting review", status: "accepted", reason: "Clean imports auto-accept." }]).slice(0, 8).map((item) => (
                    <div className="review-row" key={item.conversation_id}>
                      <div>
                        <strong>{item.title}</strong>
                        <span>{item.status} · {item.reason || "No review note"}</span>
                      </div>
                      {item.conversation_id !== "none" && (
                        <div className="review-actions">
                          <button title="Accept import" onClick={() => reviewImport(item.conversation_id, "accept")}><CheckCircle2 size={16} /></button>
                          <button title="Reject import" onClick={() => reviewImport(item.conversation_id, "reject")}><XCircle size={16} /></button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </Panel>
            </div>

            <Panel title="Concept Evolution Timeline" action={`${timeline.length} events`}>
              <div className="timeline-list">
                {(timeline.length ? timeline : [{ event_at: "No events yet", concept: "Import ChatLasso SSI or ChatGPT exports", title: "Waiting for memory" }]).slice(0, 12).map((item, index) => (
                  <div className="timeline-row" key={`${item.conversation_id || "seed"}:${item.concept || item.title || "event"}:${item.kind || "kind"}:${item.event_at || "undated"}:${index}`}>
                    <span>{item.event_at || "undated"}</span>
                    <strong>{item.concept || item.title}</strong>
                    <small>{item.mode || item.project || "ERMI"}</small>
                  </div>
                ))}
              </div>
            </Panel>
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
              <GraphPreview graph={graph} />
              <button className="wide-action" onClick={exportGraph}><GitBranch size={18} /> Export Graph</button>
            </Panel>

            <Panel title="Quick Actions">
              <div className="quick-actions">
                <button onClick={refreshAll}><RefreshCw size={18} /> Rebuild View</button>
                <button onClick={exportGraph}><Download size={18} /> Export Data</button>
                <button onClick={createBackup}><Archive size={18} /> Backup</button>
                <button onClick={runDiagnostics}><Activity size={18} /> Run Diagnostics</button>
              </div>
            </Panel>

            <Panel title="Open Folders">
              <div className="folder-actions">
                <button onClick={() => openFolder("archive")}><FolderOpen size={17} /> Archive</button>
                <button onClick={() => openFolder("vault")}><FolderOpen size={17} /> Vault</button>
                <button onClick={() => openFolder("backups")}><FolderOpen size={17} /> Backups</button>
                <button onClick={() => openFolder("exports")}><FolderOpen size={17} /> Exports</button>
                <button onClick={() => openFolder("samples")}><FolderOpen size={17} /> Samples</button>
              </div>
            </Panel>

            <Panel title="Health Diagnostics" action={diagnostics?.healthy ? "Healthy" : "Check"}>
              <div className="diagnostic-list">
                {(diagnostics?.checks || seedDiagnostics).map((item) => (
                  <div className={`diagnostic-row ${item.ok ? "ok" : "bad"}`} key={item.name}>
                    {item.ok ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
                    <strong>{item.name}</strong>
                    <div>
                      <span>{item.detail}</span>
                      <small>{item.fix}</small>
                    </div>
                  </div>
                ))}
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
        <div className="result-meta">
          <span>{item.mode || item.project || "ERMI"}</span>
          <span>{item.status || item.import_status || "accepted"}</span>
          {item.regression_contradictions_found && <span className="warning">Regression</span>}
        </div>
      </div>
      <small>{item.markdown_path || "No vault file yet"}</small>
    </div>
  );
}

function GraphPreview({ graph }) {
  const nodes = (graph.nodes || []).slice(0, 16);
  const edges = (graph.edges || []).slice(0, 24);
  const positions = nodes.map((node, index) => {
    const angle = (Math.PI * 2 * index) / Math.max(nodes.length, 1);
    const radius = node.type === "conversation" ? 72 : 50;
    return { ...node, x: 105 + Math.cos(angle) * radius, y: 82 + Math.sin(angle) * radius };
  });
  const byId = new Map(positions.map((node) => [node.id, node]));
  return (
    <svg className="graph-preview" viewBox="0 0 210 165" role="img" aria-label="ERMI graph preview">
      {edges.map((edge, index) => {
        const source = byId.get(edge.source);
        const target = byId.get(edge.target);
        if (!source || !target) return null;
        return <line key={index} x1={source.x} y1={source.y} x2={target.x} y2={target.y} />;
      })}
      {positions.map((node) => (
        <circle key={node.id} cx={node.x} cy={node.y} r={node.type === "conversation" ? 6 : 4} className={node.flagged ? "flagged-node" : ""} />
      ))}
    </svg>
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

const seedDiagnostics = [
  { name: "Diagnostics", ok: false, detail: "Run diagnostics to check local services." },
];

createRoot(document.getElementById("root")).render(<App />);
