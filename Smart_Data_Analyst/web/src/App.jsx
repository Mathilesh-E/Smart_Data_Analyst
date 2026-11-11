import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Activity, ArrowDownToLine, ArrowLeft, ArrowRight, BarChart3, Check,
  ChevronDown, ChevronUp, CircleHelp, Clock3, CloudUpload, Database, Download,
  Eraser, FileSpreadsheet, FlaskConical, Gauge, LayoutDashboard, Lightbulb,
  LineChart as LineChartIcon, ListFilter, LoaderCircle, Menu, Moon, RotateCcw, Search, SlidersHorizontal,
  ShieldCheck, Sun, Table2, X,
} from "lucide-react";
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, LabelList, Line,
  LineChart as RechartsLineChart, Pie, PieChart, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis,
  YAxis,
} from "recharts";

const API = "/api";
const PALETTE = ["#635bdb", "#008f82", "#dc7a12", "#d34f72", "#187cb8", "#9b55b5"];
const NAV = [
  { id: "overview", label: "Overview", icon: LayoutDashboard, group: "workspace" },
  { id: "explorer", label: "Data explorer", icon: Table2, group: "workspace" },
  { id: "quality", label: "Data quality", icon: ShieldCheck, group: "workspace" },
  { id: "cleaning", label: "Cleaning studio", icon: Eraser, group: "workspace" },
  { id: "charts", label: "Chart studio", icon: BarChart3, group: "analysis" },
  { id: "workbench", label: "Analysis workbench", icon: SlidersHorizontal, group: "analysis" },
  { id: "insights", label: "Insights", icon: Lightbulb, group: "analysis" },
  { id: "statistics", label: "Statistical lab", icon: FlaskConical, group: "analysis" },
  { id: "ml", label: "ML lab", icon: Gauge, group: "analysis" },
  { id: "segments", label: "Segments & anomalies", icon: Activity, group: "analysis" },
  { id: "timeseries", label: "Time series", icon: LineChartIcon, group: "analysis" },
  { id: "reports", label: "Reports & exports", icon: ArrowDownToLine, group: "manage" },
];

async function request(path, workspace, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (workspace) headers["X-Workspace-Id"] = workspace;
  if (options.body && !(options.body instanceof FormData)) headers["Content-Type"] = "application/json";
  const response = await fetch(`${API}${path}`, { ...options, headers });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try { message = (await response.json()).detail || message; } catch { /* use the status text */ }
    throw new Error(message);
  }
  return response;
}

async function downloadExport(kind, workspace) {
  const response = await request(`/export/${kind}`, workspace);
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement("a");
  link.href = url;
  link.download = ({ pdf: "analysis_report.pdf", csv: "smart_data_analyst.csv", xlsx: "smart_data_analyst.xlsx", json: "dataset_profile.json", segments: "segments.csv", anomalies: "anomaly_review.csv" })[kind];
  link.click();
  URL.revokeObjectURL(url);
}

function downloadRowsCsv(filename, columns, rows) {
  const quote = (value) => `"${String(value ?? "").replaceAll('"', '""')}"`;
  const content = [columns.map(quote).join(","), ...rows.map((row) => columns.map((column) => quote(row[column])).join(","))].join("\r\n");
  const url = URL.createObjectURL(new Blob([content], { type: "text/csv;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function Card({ children, className = "", title, action }) {
  return <section className={`card ${className}`}>
    {(title || action) && <div className="card-heading">{title && <h2>{title}</h2>}{action}</div>}
    {children}
  </section>;
}

function Metric({ label, value, note, icon: Icon, tone = "violet" }) {
  return <motion.div className="metric-card" whileHover={{ y: -3, transition: { duration: .18 } }}>
    <div className={`metric-icon ${tone}`}><Icon size={17} /></div>
    <div className="metric-label">{label}</div><div className="metric-value">{value}</div>
    <div className="metric-note">{note}</div>
  </motion.div>;
}

function Chart({ data = [], kind = "bar", height = 250, color = PALETTE[0], xLabel = "Category", yLabel = "Records", showLegend = false, showSeriesLegend = false, seriesNames = [], stacked = false }) {
  const common = { margin: { top: 17, right: 18, left: 8, bottom: 35 } };
  const axisTick = { fill: "var(--chart-axis)", fontSize: 11 };
  const axisLabel = { fill: "var(--chart-axis)", fontSize: 11 };
  const grid = <CartesianGrid stroke="var(--chart-grid)" vertical={false} strokeDasharray="3 5" />;
  const xAxis = <XAxis dataKey="name" tick={axisTick} axisLine={false} tickLine={false} tickMargin={11}
    interval={data.length > 12 ? Math.ceil(data.length / 10) : 0}
    tickFormatter={(value) => String(value).length > 15 ? `${String(value).slice(0, 13)}…` : value}
    label={{ value: xLabel, position: "insideBottom", offset: -22, ...axisLabel }} />;
  const yAxis = <YAxis tick={axisTick} axisLine={false} tickLine={false} width={66}
    tickFormatter={formatAxisValue}
    label={{ value: yLabel, angle: -90, position: "insideLeft", offset: 8, ...axisLabel }} />;
  const tooltip = <Tooltip contentStyle={{ background: "var(--chart-tooltip-bg)", border: "1px solid var(--chart-tooltip-border)", borderRadius: 10, color: "var(--chart-tooltip-text)", boxShadow: "0 12px 32px rgba(0,0,0,.18)" }}
    formatter={(value, name) => [formatAxisValue(value), name === "value" ? yLabel : name]}
    labelFormatter={(label) => `${xLabel}: ${label}`} />;
  const animated = { isAnimationActive: true, animationDuration: 850, animationEasing: "ease-out" };
  const trendProps = { data, ...common };
  const legendTotal = data.reduce((sum, entry) => sum + (Number(entry.value) || 0), 0);

  return <motion.div className={`chart-wrap chart-${kind}`} style={{ height: showLegend || showSeriesLegend ? "auto" : height }} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .42, ease: [.22, 1, .36, 1] }}>
    <ResponsiveContainer width="100%" height={showLegend || showSeriesLegend ? height : "100%"}>
      {kind === "line" ? <RechartsLineChart {...trendProps}>{grid}{xAxis}{yAxis}{tooltip}{(seriesNames.length ? seriesNames : ["value"]).map((series, index) => <Line key={series} type="monotone" dataKey={series} name={series === "value" ? yLabel : series} stroke={seriesNames.length ? PALETTE[index % PALETTE.length] : color} strokeWidth={3} dot={{ r: 3.5, fill: seriesNames.length ? PALETTE[index % PALETTE.length] : color, stroke: "var(--panel)", strokeWidth: 2 }} activeDot={{ r: 6, strokeWidth: 0 }} {...animated} />)}</RechartsLineChart>
        : kind === "area" ? <AreaChart {...trendProps}>{grid}{xAxis}{yAxis}{tooltip}<defs><linearGradient id="chartFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={color} stopOpacity={.34} /><stop offset="95%" stopColor={color} stopOpacity={.015} /></linearGradient></defs><Area type="monotone" dataKey="value" name={yLabel} stroke={color} strokeWidth={2.8} fill="url(#chartFill)" activeDot={{ r: 5 }} {...animated} /></AreaChart>
          : kind === "pie" || kind === "donut" ? <PieChart><Tooltip contentStyle={{ background: "var(--chart-tooltip-bg)", border: "1px solid var(--chart-tooltip-border)", borderRadius: 10, color: "var(--chart-tooltip-text)" }} formatter={(value) => [formatAxisValue(value), "Records"]} /><Pie data={data} dataKey="value" nameKey="name" innerRadius={kind === "donut" ? "58%" : 0} outerRadius="76%" paddingAngle={3} stroke="var(--panel)" strokeWidth={2} label={data.length <= 8 ? ({ percent }) => `${(percent * 100).toFixed(0)}%` : false} labelLine={false} {...animated}>{data.map((entry, i) => <Cell key={entry.name || i} fill={entry.color || PALETTE[i % PALETTE.length]} />)}</Pie></PieChart>
            : kind === "scatter" ? <ScatterChart margin={{ ...common.margin, bottom: 30, left: 20 }}><CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 5" /><XAxis type="number" dataKey="x" tick={axisTick} axisLine={false} tickLine={false} tickFormatter={formatAxisValue} label={{ value: xLabel, position: "insideBottom", offset: -18, ...axisLabel }} /><YAxis type="number" dataKey="y" tick={axisTick} axisLine={false} tickLine={false} width={72} tickFormatter={formatAxisValue} label={{ value: yLabel, angle: -90, position: "insideLeft", ...axisLabel }} /><Tooltip contentStyle={{ background: "var(--chart-tooltip-bg)", border: "1px solid var(--chart-tooltip-border)", borderRadius: 10, color: "var(--chart-tooltip-text)" }} formatter={(value, name) => [formatAxisValue(value), name === "x" ? xLabel : yLabel]} cursor={{ strokeDasharray: "3 3" }} /><Scatter data={data} fill={color} fillOpacity={.72} isAnimationActive animationDuration={700} /></ScatterChart>
              : <BarChart data={data} {...common}>{grid}{xAxis}{yAxis}{tooltip}{(seriesNames.length ? seriesNames : ["value"]).map((series, seriesIndex) => <Bar key={series} dataKey={series} name={series === "value" ? yLabel : series} stackId={stacked ? "total" : undefined} fill={seriesNames.length ? PALETTE[seriesIndex % PALETTE.length] : color} radius={stacked || (seriesNames.length && seriesIndex < seriesNames.length - 1) ? [0, 0, 0, 0] : [5, 5, 0, 0]} maxBarSize={44} {...animated}>{!seriesNames.length && data.map((entry, i) => <Cell key={entry.name || i} fill={entry.color || (data.length === 1 ? color : PALETTE[i % PALETTE.length])} />)}{!stacked && data.length <= 8 && (!seriesNames.length || seriesNames.length <= 3) && <LabelList dataKey={series} position="top" formatter={(value) => value == null ? "" : formatAxisValue(value)} fill="var(--chart-value)" fontSize={9} />}</Bar>)}</BarChart>}
    </ResponsiveContainer>
    {showLegend && <div className="chart-legend">{data.map((item, index) => {
      const percent = legendTotal ? (Number(item.value || 0) / legendTotal) * 100 : 0;
      return <div key={item.name || index}><i style={{ background: item.color || PALETTE[index % PALETTE.length] }} /><span title={item.name}>{item.name}</span><b>{percent.toFixed(1)}%</b></div>;
    })}</div>}
    {showSeriesLegend && <div className="chart-legend chart-series-legend">{seriesNames.map((name, index) => <div key={name}><i style={{ background: PALETTE[index % PALETTE.length] }} /><span title={name}>{name}</span></div>)}</div>}
  </motion.div>;
}

function formatAxisValue(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return String(value ?? "");
  return new Intl.NumberFormat(undefined, { notation: Math.abs(numeric) >= 10000 ? "compact" : "standard", maximumFractionDigits: 2 }).format(numeric);
}

function EmptyState({ icon: Icon = Database, title, detail }) {
  return <div className="empty-state"><div className="empty-icon"><Icon size={23} /></div><h2>{title}</h2><p>{detail}</p></div>;
}

function formatBytes(bytes = 0) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB"];
  const index = Math.min(units.length - 1, Math.floor(Math.log(bytes) / Math.log(1024)));
  return `${(bytes / (1024 ** index)).toFixed(index ? 1 : 0)} ${units[index]}`;
}

function formatStat(value) {
  if (value == null || value === "") return "—";
  return typeof value === "number" ? value.toPrecision(4) : String(value);
}

function App() {
  const [page, setPage] = useState(() => {
    const params = new URLSearchParams(window.location.search);
    return params.get("page") || "overview";
  });
  const [theme, setTheme] = useState(() => {
    const params = new URLSearchParams(window.location.search);
    return params.get("theme") || localStorage.getItem("sda-theme") || "light";
  });
  const [workspace, setWorkspace] = useState(() => localStorage.getItem("sda-workspace"));
  const [data, setData] = useState(null);
  const [samples, setSamples] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");
  const [mobileNav, setMobileNav] = useState(false);
  const [dragging, setDragging] = useState(false);
  const fileRef = useRef(null);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("sda-theme", theme);
  }, [theme]);

  const loadWorkspace = useCallback(async (id) => {
    setBusy(true); setError("");
    try {
      const response = await request("/overview", id);
      setWorkspace(id); localStorage.setItem("sda-workspace", id); setData(await response.json());
    } catch (e) {
      setWorkspace(null); setData(null); localStorage.removeItem("sda-workspace");
      if (e.message !== "No dataset is loaded in this workspace.") setError(e.message);
    } finally { setBusy(false); }
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const targetSample = params.get("sample");
    const isWelcome = params.get("welcome") === "1";

    fetch(`${API}/samples`)
      .then((r) => r.json())
      .then((sampleList) => {
        setSamples(sampleList);
        if (isWelcome) {
          setData(null);
          return;
        }
        if (targetSample) {
          loadSample(targetSample);
        } else if (!workspace && sampleList.length > 0) {
          loadSample(sampleList[0].file);
        }
      })
      .catch(() => setSamples([]));
    if (!targetSample && !isWelcome && workspace) loadWorkspace(workspace);
  }, []); // Initial restore only.

  const notify = (message) => { setToast(message); window.setTimeout(() => setToast(""), 3200); };
  const acceptDataset = (result) => {
    setWorkspace(result.workspace_id); localStorage.setItem("sda-workspace", result.workspace_id);
    setData(result.overview);
    const initialUrlPage = new URLSearchParams(window.location.search).get("page");
    if (!initialUrlPage) setPage("overview");
    setError(""); setMobileNav(false);
    notify(`Loaded ${result.overview.profile.rows.toLocaleString()} records`);
  };
  const upload = async (file) => {
    if (!file) return;
    setBusy(true); setError("");
    try {
      const form = new FormData(); form.append("file", file);
      const response = await request("/upload", workspace, { method: "POST", body: form });
      acceptDataset(await response.json());
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  };
  const loadSample = async (filename) => {
    setBusy(true); setError("");
    try {
      const response = await request(`/samples/${encodeURIComponent(filename)}`, workspace, { method: "POST" });
      acceptDataset(await response.json());
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  };
  const reset = async () => {
    if (!workspace) return;
    try { const response = await request("/reset", workspace, { method: "POST" }); setData(await response.json()); notify("Restored the original data"); }
    catch (e) { setError(e.message); }
  };
  const clear = async () => {
    try { await request("/workspace", workspace, { method: "DELETE" }); } catch { /* The local workspace can still be cleared. */ }
    localStorage.removeItem("sda-workspace"); setWorkspace(null); setData(null); setPage("overview"); setError("");
  };
  const current = NAV.find((item) => item.id === page);
  const renderPage = () => {
    if (!data) return <Welcome samples={samples} onUpload={() => fileRef.current?.click()} onSample={loadSample} busy={busy} />;
    const shared = { data, workspace, setData, notify, setError };
    switch (page) {
      case "explorer": return <Explorer {...shared} />;
      case "quality": return <Quality {...shared} />;
      case "cleaning": return <Cleaning {...shared} />;
      case "charts": return <ChartStudio {...shared} />;
      case "workbench": return <AnalysisWorkbench {...shared} />;
      case "insights": return <Insights {...shared} />;
      case "statistics": return <Statistics {...shared} />;
      case "ml": return <MachineLearning {...shared} />;
      case "segments": return <Segments {...shared} />;
      case "timeseries": return <TimeSeries {...shared} />;
      case "reports": return <Reports {...shared} />;
      default: return <Overview {...shared} />;
    }
  };

  return <div className="app-shell" data-theme={theme} onDragOver={(e) => { e.preventDefault(); setDragging(true); }} onDragLeave={(e) => { if (!e.currentTarget.contains(e.relatedTarget)) setDragging(false); }} onDrop={(e) => { e.preventDefault(); setDragging(false); upload(e.dataTransfer.files?.[0]); }}>
    <input ref={fileRef} type="file" accept=".csv,.xlsx,.xls" hidden onChange={(e) => { upload(e.target.files?.[0]); e.target.value = ""; }} />
    <AnimatePresence>{dragging && <motion.div className="drop-overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}><CloudUpload size={30} />Drop a CSV or Excel file to analyze</motion.div>}</AnimatePresence>
    <aside className={`sidebar ${mobileNav ? "open" : ""}`}>
      <div className="brand"><div className="brand-mark"><Activity size={19} /></div><div><strong>Smart <span>Data Analyst</span></strong><small>DATA ANALYSIS PLATFORM</small></div><button className="icon-btn mobile-close" onClick={() => setMobileNav(false)} aria-label="Close menu"><X size={18} /></button></div>
      <div className="workspace-label">WORKSPACE</div>
      {["workspace", "analysis", "manage"].map((group) => <div className="nav-group" key={group}>
        <div className="nav-group-label">{group === "workspace" ? "YOUR DATA" : group}</div>
        {NAV.filter((item) => item.group === group).map(({ id, label, icon: Icon }) => <button key={id} className={`nav-item ${page === id ? "active" : ""}`} onClick={() => { setPage(id); setMobileNav(false); }}><Icon size={17} /><span>{label}</span>{id === "overview" && data && <i className="nav-indicator" />}</button>)}
      </div>)}
      <div className="sidebar-bottom">
        <div className="dataset-selector-box">
          <label className="field-label" style={{ fontSize: "10px", color: "var(--muted)", marginBottom: "4px" }}>SAMPLE DATASETS</label>
          <select style={{ width: "100%", padding: "5px 8px", fontSize: "11px", borderRadius: "6px", background: "var(--panel-raised)", color: "var(--text)", border: "1px solid var(--border)" }} onChange={(e) => { if (e.target.value) loadSample(e.target.value); }}>
            <option value="">Switch sample dataset...</option>
            {samples.map((s) => <option key={s.file} value={s.file}>{s.label}</option>)}
          </select>
        </div>
        {data && <div className="dataset-mini" style={{ marginTop: "8px" }}><div className="dataset-mini-icon"><FileSpreadsheet size={16} /></div><div className="dataset-mini-copy"><b>{data.profile.filename || "Active dataset"}</b><span>{data.profile.rows.toLocaleString()} rows · {data.profile.columns} cols</span></div><button className="icon-btn" onClick={reset} title="Reset original"><RotateCcw size={14} /></button></div>}
      </div>
    </aside>
    {mobileNav && <button className="nav-backdrop" onClick={() => setMobileNav(false)} aria-label="Close navigation" />}
    <main className="main-area">
      <header className="topbar">
        <button className="icon-btn menu-btn" onClick={() => setMobileNav(true)} aria-label="Open menu"><Menu size={19} /></button>
        <div className="breadcrumbs"><span>Smart Data Analyst</span><span className="crumb-slash">/</span><b>{current?.label || "Overview"}</b></div>
        <div className="topbar-actions"><div className="local-badge"><span />INTELLIGENT ANALYTICS</div><button className="btn btn-quiet theme-toggle" onClick={() => setTheme(theme === "dark" ? "light" : "dark")} aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`} title={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}>{theme === "dark" ? <Sun size={15} /> : <Moon size={15} />}<span>{theme === "dark" ? "Light" : "Dark"}</span></button>{data ? <><button className="btn btn-quiet" onClick={() => fileRef.current?.click()}><CloudUpload size={15} /> Replace data</button><button className="btn btn-primary" onClick={() => setPage("reports")}><Download size={15} /> Export</button></> : <button className="btn btn-primary" onClick={() => fileRef.current?.click()}><CloudUpload size={15} /> Upload dataset</button>}</div>
      </header>
      <div className="page-content">
        {error && <div className="alert error"><CircleHelp size={17} /><span>{error}</span><button className="icon-btn" onClick={() => setError("")} aria-label="Dismiss"><X size={15} /></button></div>}
        {busy && <div className="busy-line"><span /></div>}
        <AnimatePresence mode="wait"><motion.div key={`${page}-${workspace || "empty"}`} initial={{ opacity: 0, y: 7 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -5 }} transition={{ duration: .2 }}>{renderPage()}</motion.div></AnimatePresence>
      </div>
      <footer className="page-footer"><span>SMART DATA ANALYST</span><span><span className="footer-dot" /> Advanced Automated Data Intelligence</span></footer>
    </main>
    <AnimatePresence>{toast && <motion.div className="toast" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 8 }}><Check size={16} />{toast}</motion.div>}</AnimatePresence>
  </div>;
}

function PageTitle({ eyebrow, title, detail, action }) {
  return <div className="page-title"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{detail}</p></div>{action}</div>;
}

function Welcome({ samples, onUpload, onSample, busy }) {
  return <div className="welcome">
    <motion.div className="welcome-orb orb-one" animate={{ y: [0, -12, 0], x: [0, 7, 0] }} transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }} />
    <motion.div className="welcome-orb orb-two" animate={{ y: [0, 13, 0], x: [0, -8, 0] }} transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }} />
    <div className="welcome-copy">
      <div className="eyebrow"><span className="eyebrow-dot" /> ENTERPRISE DATA INTELLIGENCE</div>
      <h1>Your data has<br />a <span>story to tell.</span></h1>
      <p>Explore patterns, run statistical tests, train machine learning models and create dynamic dashboards with intelligent automated analytics.</p>
      <button className="btn btn-primary btn-large" onClick={onUpload} disabled={busy}><CloudUpload size={17} /> {busy ? "Preparing workspace…" : "Upload a dataset"} <ArrowRight size={16} /></button>
      <div className="welcome-meta"><span><ShieldCheck size={14} /> Full analysis suite</span><span><FileSpreadsheet size={14} /> CSV · XLSX · XLS</span><span><Activity size={14} /> Real-time models</span></div>
    </div>
    <motion.div className="welcome-preview" initial={{ opacity: 0, scale: .97, y: 10 }} animate={{ opacity: 1, scale: 1, y: 0 }} transition={{ duration: .45, delay: .12 }}>
      <div className="preview-top"><div><span className="preview-live" /> WORKSPACE PREVIEW</div><span>NO DATA LOADED</span></div>
      <div className="preview-metrics"><div><small>RECORDS</small><b>—</b><span>Calculated after upload</span></div><div><small>DATA QUALITY</small><b className="quality-preview">—<span> / 100</span></b><span>Heuristic from your dataset</span></div></div>
      <div className="preview-chart"><div className="preview-chart-label"><span>Automatic analysis</span><span>Waiting for a dataset</span></div><div className="preview-empty"><Database size={19} /><span>Charts and insights will appear here</span></div></div>
      <div className="preview-bottom"><div className="preview-badge"><Activity size={14} /><span><b>Built around your data</b><small>Profile · quality · visual exploration</small></span></div><div className="preview-status">READY</div></div>
      <div className="preview-glow" />
    </motion.div>
    <div className="sample-row"><div><b>Just exploring?</b><span> Open a sample dataset</span></div>{samples.map((sample) => <button key={sample.file} className="sample-chip" onClick={() => onSample(sample.file)} disabled={busy}><FileSpreadsheet size={14} />{sample.label}<ArrowRight size={13} /></button>)}</div>
  </div>;
}

function Overview({ data, workspace, setError }) {
  const p = data.profile;
  const composition = Object.entries(p.kinds).reduce((out, [, type]) => { const name = type === "identifier" ? "Identifier" : ["categorical", "boolean"].includes(type) ? "Categorical" : type[0].toUpperCase() + type.slice(1); out[name] = (out[name] || 0) + 1; return out; }, {});
  const compData = Object.entries(composition).map(([name, value]) => ({ name, value }));
  const charts = useMemo(() => dashboardChartSpecs(p), [p]);
  const [controls, setControls] = useState([]);
  const [draftFilters, setDraftFilters] = useState([]);
  const [activeFilters, setActiveFilters] = useState([]);
  const [filteredRows, setFilteredRows] = useState(p.rows);
  const [controlsLoading, setControlsLoading] = useState(true);
  const [showAllCharts, setShowAllCharts] = useState(false);
  const [chartLayout, setChartLayout] = useState('sparse');
  useEffect(() => {
    let active = true;
    setControlsLoading(true);
    request("/controls", workspace)
      .then((response) => response.json())
      .then((result) => { if (active) setControls(result.columns); })
      .catch((error) => { if (active) setError(error.message); })
      .finally(() => { if (active) setControlsLoading(false); });
    return () => { active = false; };
  }, [workspace, setError]);
  const handleFilteredRows = useCallback((count) => setFilteredRows(count), []);
  const addDashboardFilter = () => {
    if (draftFilters.length >= 4) return;
    const field = controls.find((item) => !draftFilters.some((filter) => filter.column === item.column));
    if (!field) return;
    const categorical = ["categorical", "boolean", "identifier"].includes(field.kind);
    setDraftFilters((current) => [...current, {
      column: field.column,
      operator: categorical ? "eq" : "gte",
      value: "",
      value_to: "",
    }]);
  };
  const updateDashboardFilter = (index, patch) => setDraftFilters((current) => current.map((filter, itemIndex) => itemIndex === index ? { ...filter, ...patch } : filter));
  const appliedFilters = draftFilters.filter((filter) => ["is_null", "not_null"].includes(filter.operator)
    || (filter.value !== "" && filter.value != null && (filter.operator !== "between" || (filter.value_to !== "" && filter.value_to != null))));
  const setDashboardFilters = () => {
    setFilteredRows(null);
    setActiveFilters(appliedFilters);
  };
  const visibleCharts = showAllCharts ? charts : charts.slice(0, 4);
  const hiddenChartCount = Math.max(0, charts.length - visibleCharts.length);
  return <div className="stack-lg">
    <PageTitle eyebrow="YOUR DATA, AT A GLANCE" title="Overview" detail="Explore an automatically assembled dashboard. Charts adapt to your columns and respond to shared slicers." action={<div className="data-file-tag"><FileSpreadsheet size={15} /><span>{p.filename || "Dataset loaded"}</span><span className="tag-separator">·</span>{p.rows.toLocaleString()} rows<span className="tag-separator">·</span>{formatBytes(p.file_size)}</div>} />
    <Card className="dashboard-filter-card">
      <div className="dashboard-filter-top">
        <div><div className="dashboard-filter-title"><ListFilter size={16} /><b>Dashboard slicers</b><span>{activeFilters.length ? `${activeFilters.length} active` : "No filters applied"}</span></div><p>Set filters once to update every recommended chart. Your dataset is not changed.</p></div>
        <div className="dashboard-filter-actions">
          <button type="button" className="btn btn-quiet" onClick={addDashboardFilter} disabled={controlsLoading || draftFilters.length >= 4 || draftFilters.length >= controls.length}>Add slicer</button>
          <button type="button" className="btn btn-primary" onClick={setDashboardFilters} disabled={controlsLoading}>Apply to charts</button>
          {(draftFilters.length > 0 || activeFilters.length > 0) && <button type="button" className="btn btn-quiet" onClick={() => { setDraftFilters([]); setActiveFilters([]); setFilteredRows(p.rows); }}>Clear</button>}
        </div>
      </div>
      {draftFilters.length > 0 && <div className="dashboard-slicer-list">{draftFilters.map((filter, index) => {
        const field = controls.find((item) => item.column === filter.column);
        const categorical = field && ["categorical", "boolean", "identifier", "text"].includes(field.kind);
        const textual = field?.kind === "text";
        const operators = textual
          ? [["contains", "contains"], ["eq", "is"], ["ne", "is not"], ["is_null", "is missing"], ["not_null", "is present"]]
          : categorical
          ? [["eq", "is"], ["ne", "is not"], ["contains", "contains"], ["is_null", "is missing"], ["not_null", "is present"]]
          : [["gte", "at least"], ["lte", "at most"], ["between", "between"], ["eq", "is"], ["is_null", "is missing"], ["not_null", "is present"]];
        const availableFields = controls.filter((item) => !draftFilters.some((other, otherIndex) => other.column === item.column && otherIndex !== index));
        return <div className="dashboard-slicer-row" key={`dashboard-filter-${index}`}>
          <select aria-label={`Dashboard slicer ${index + 1} field`} value={filter.column} onChange={(event) => {
            const nextField = controls.find((item) => item.column === event.target.value);
            const nextCategorical = nextField && ["categorical", "boolean", "identifier", "text"].includes(nextField.kind);
            updateDashboardFilter(index, { column: event.target.value, operator: nextCategorical ? "eq" : "gte", value: "", value_to: "" });
          }}>{availableFields.map((item) => <option key={item.column} value={item.column}>{item.column}</option>)}</select>
          <select aria-label={`Dashboard slicer ${index + 1} condition`} value={filter.operator} onChange={(event) => updateDashboardFilter(index, { operator: event.target.value, value: "", value_to: "" })}>{operators.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>
          {!["is_null", "not_null"].includes(filter.operator) && (textual
            ? filter.operator === "contains"
              ? <input aria-label={`Dashboard slicer ${index + 1} value`} type="search" placeholder="Contains…" value={filter.value} onChange={(event) => updateDashboardFilter(index, { value: event.target.value })} />
              : <input aria-label={`Dashboard slicer ${index + 1} value`} type="text" placeholder="Value" value={filter.value} onChange={(event) => updateDashboardFilter(index, { value: event.target.value })} />
            : categorical
            ? filter.operator === "contains"
              ? <input aria-label={`Dashboard slicer ${index + 1} value`} type="search" placeholder="Contains…" value={filter.value} onChange={(event) => updateDashboardFilter(index, { value: event.target.value })} />
              : <select aria-label={`Dashboard slicer ${index + 1} value`} value={filter.value} onChange={(event) => updateDashboardFilter(index, { value: event.target.value })}><option value="">Choose a value</option>{(field?.options || []).map((value) => <option key={value} value={value}>{value}</option>)}</select>
            : <><input aria-label={`Dashboard slicer ${index + 1} value`} type={field?.kind === "datetime" ? "date" : "number"} placeholder={filter.operator === "between" ? "From" : "Value"} value={filter.value} onChange={(event) => updateDashboardFilter(index, { value: event.target.value })} />{filter.operator === "between" && <input aria-label={`Dashboard slicer ${index + 1} upper value`} type={field?.kind === "datetime" ? "date" : "number"} placeholder="To" value={filter.value_to} onChange={(event) => updateDashboardFilter(index, { value_to: event.target.value })} />}</>)}
          <button type="button" className="icon-btn" aria-label={`Remove dashboard slicer ${index + 1}`} onClick={() => setDraftFilters((current) => current.filter((_, itemIndex) => itemIndex !== index))}><X size={14} /></button>
        </div>;
      })}</div>}
      <div className="dashboard-filter-summary">{controlsLoading ? "Preparing dataset filter options…" : filteredRows == null ? "Updating charts…" : `Showing ${filteredRows.toLocaleString()} of ${p.rows.toLocaleString()} records in dashboard charts`}{activeFilters.length > 0 && <span> · KPIs and profile below describe the full dataset</span>}</div>
    </Card>
    <div className="dashboard-section-heading"><div><div className="eyebrow">AUTOMATIC EXPLORATION</div><h2>Recommended views</h2><p>Selected from your inferred numeric, categorical and date columns.</p></div><span>{charts.length} charts · hover for values</span></div>
    <div className="chart-layout-bar">
      <span>Layout</span>
      <button type="button" className={`layout-btn${chartLayout === 'sparse' ? ' active' : ''}`} onClick={() => setChartLayout('sparse')}>▬ Single column</button>
      <button type="button" className={`layout-btn${chartLayout === 'two' ? ' active' : ''}`} onClick={() => setChartLayout('two')}>▪▪ 2 columns</button>
      <button type="button" className={`layout-btn${chartLayout === 'three' ? ' active' : ''}`} onClick={() => setChartLayout('three')}>▪▪▪ 3 columns</button>
      <button type="button" className={`layout-btn${chartLayout === 'auto' ? ' active' : ''}`} onClick={() => setChartLayout('auto')}>⊞ Fit width</button>
    </div>
    {charts.length > 0
      ? <><div className={`dashboard-chart-grid${chartLayout !== 'sparse' ? ` layout-${chartLayout}` : ''}`}>{visibleCharts.map((spec) => <DashboardChartCard key={spec.id} spec={spec} workspace={workspace} filters={activeFilters} onRecords={handleFilteredRows} />)}</div>
        {charts.length > 4 && <button type="button" className="dashboard-more-button" onClick={() => setShowAllCharts((current) => !current)}>{showAllCharts ? <ChevronUp size={15} /> : <ChevronDown size={15} />}{showAllCharts ? "Show fewer views" : `Explore ${hiddenChartCount} more views`}<span>{showAllCharts ? "Keep the dashboard focused" : "Relationships and additional field distributions"}</span></button>}</>
      : <Card><EmptyState icon={BarChart3} title="No compatible charts detected" detail="Review the inferred column types in Data explorer. You can still build a custom view in Chart studio." /></Card>}
    <div className="section-heading"><div><div className="eyebrow">DATASET HEALTH</div><h2>Structure and quality</h2></div><span>{p.columns} columns · {p.rows.toLocaleString()} records</span></div>
    <div className="metric-grid">
      <Metric label="Total records" value={p.rows.toLocaleString()} note="Rows available to explore" icon={Database} tone="violet" />
      <Metric label="Data attributes" value={p.columns} note="Columns detected" icon={Table2} tone="blue" />
      <Metric label="Missing cells" value={p.missing.toLocaleString()} note={`${p.missing_pct}% of all values`} icon={ListFilter} tone="amber" />
      <Metric label="Completeness" value={`${(100 - p.missing_pct).toFixed(1)}%`} note="Non-missing cells" icon={Gauge} tone="teal" />
      <Metric label="Duplicate rows" value={p.duplicates.toLocaleString()} note={`${p.duplicate_pct}% fully repeated`} icon={RotateCcw} tone="rose" />
      <Metric label="Quality index" value={`${p.quality}`} note="Project-defined heuristic / 100" icon={ShieldCheck} tone="green" />
    </div>
    <div className="overview-grid">
      <Card className="composition-card" title="Column composition" action={<span className="subtle-count">{p.columns} columns</span>}>
        {compData.length ? <div className="composition-content"><Chart data={compData} kind="donut" height={214} xLabel="Column type" yLabel="Field count" /><div className="legend-list">{compData.map((item, index) => <div className="legend-row" key={item.name}><span className="legend-dot" style={{ background: PALETTE[index % PALETTE.length] }} /><span>{item.name}</span><b>{item.value}</b></div>)}</div></div> : <EmptyState title="No columns found" detail="Check the uploaded file and try again." />}
      </Card>
      <Card className="missing-card" title="Missing values" action={<span className="subtle-count">By column</span>}>
        {data.missing.length ? <Chart data={data.missing.slice(0, 8).map((item) => ({ name: item.column, value: item.count }))} height={254} color="#dc7a12" xLabel="Column" yLabel="Missing cells" /> : <div className="clean-state"><div><Check size={20} /></div><b>No missing cells found</b><span>Every column is complete.</span></div>}
      </Card>
    </div>
    <div className="section-heading"><div><div className="eyebrow">AUTOMATED READOUT</div><h2>Patterns worth a closer look</h2></div><span>{data.insights.length} observations</span></div>
    {data.insights.length ? <div className="insight-grid">{data.insights.slice(0, 4).map((item, index) => <InsightCard key={item.title} item={item} index={index} />)}</div> : <Card><EmptyState icon={Lightbulb} title="No notable patterns detected" detail="Try the chart studio to investigate the dataset in more detail." /></Card>}
    <div className="overview-grid bottom-grid">
      <Card title="Strongest numeric associations" action={<span className="subtle-count">Pearson correlation</span>}>
        {data.correlations.length ? <div className="association-list">{data.correlations.slice(0, 5).map((item) => <div className="association-row" key={`${item.x}-${item.y}`}><div><b>{item.x}</b><span>with</span><b>{item.y}</b></div><div className="association-track"><i style={{ width: `${Math.min(100, Math.abs(item.value) * 100)}%`, background: item.value >= 0 ? "#52cbae" : "#e484a6" }} /></div><strong className={item.value < 0 ? "negative" : ""}>{item.value > 0 ? "+" : ""}{item.value.toFixed(2)}</strong></div>)}</div> : <div className="inline-empty">Two or more numeric fields are needed to calculate associations.</div>}
      </Card>
      <Card title="Analytical profile" action={<span className="subtle-count">Automatically inferred</span>}>
        <div className="profile-summary">{Object.entries(composition).map(([name, value], i) => <div key={name}><span className="legend-dot" style={{ background: PALETTE[i % PALETTE.length] }} /><span>{name}</span><b>{value}</b></div>)}</div>
        <div className="profile-foot"><span>{p.constants.length} constant fields</span><span>{p.dates.length} date-like</span><span>{p.identifiers.length} identifier-like</span></div>
      </Card>
    </div>
    <p className="disclaimer"><CircleHelp size={14} /> Automated observations are descriptive, based on the loaded data, and do not imply causation.</p>
  </div>;
}

function dashboardChartSpecs(profile) {
  const identifiers = new Set(profile.identifiers || []);
  const schema = new Map((profile.schema || []).map((field) => [field.Column, field]));
  const numeric = (profile.numeric || [])
    .filter((column) => !identifiers.has(column) && !(profile.constants || []).includes(column))
    .sort((first, second) => measurePriority(second) - measurePriority(first)
      || (schema.get(second)?.["Unique %"] || 0) - (schema.get(first)?.["Unique %"] || 0));
  const categorical = (profile.categorical || [])
    .filter((column) => {
      const count = schema.get(column)?.Unique || 0;
      return count >= 2 && count <= Math.min(24, Math.max(8, Math.ceil(profile.rows * .05)));
    })
    .sort((first, second) => categoryPriority(first, schema) - categoryPriority(second, schema));
  const date = profile.dates?.[0];
  const measure = numeric[0];
  const specs = [];
  if (categorical.length && measure) {
    const color = categorical.find((column) => column !== categorical[0] && (schema.get(column)?.Unique || 0) <= 6);
    specs.push({
      id: "category-measure", title: `${measure} by ${categorical[0]}`,
      subtitle: `Average ${measure} by ${categorical[0]}${color ? `, split by ${color}` : ""}`,
      chart: color && (schema.get(categorical[0])?.Unique || 0) <= 8 ? "grouped_bar" : "bar",
      x: categorical[0], y: measure, color: color && (schema.get(categorical[0])?.Unique || 0) <= 8 ? color : null, aggregation: "mean",
    });
  }
  if (date && measure) {
    specs.push({
      id: "time-trend", title: `${measure} over time`,
      subtitle: `Average ${measure}, automatically grouped into readable time periods`,
      chart: "line", x: date, y: measure, aggregation: "mean", dateFrequency: "auto",
    });
  }
  if (measure) {
    specs.push({
      id: "numeric-distribution", title: `${measure} distribution`,
      subtitle: "Frequency across automatically selected value ranges",
      chart: "histogram", x: measure,
    });
  }
  if (categorical[0]) {
    specs.push({
      id: "category-frequency", title: `${categorical[0]} frequency`,
      subtitle: `Most frequent values in ${categorical[0]}`,
      chart: "category", x: categorical[0],
    });
  }
  if (numeric.length > 1) {
    specs.push({
      id: "numeric-relationship", title: `${numeric[0]} and ${numeric[1]}`,
      subtitle: "Observed relationship · each point is one record",
      chart: "scatter", x: numeric[0], y: numeric[1],
    });
  }
  if (categorical[1]) {
    specs.push({
      id: "secondary-category-frequency", title: `${categorical[1]} frequency`,
      subtitle: `Most frequent values in ${categorical[1]}`,
      chart: "category", x: categorical[1],
    });
  }
  if (numeric[1]) {
    specs.push({
      id: "secondary-numeric-distribution", title: `${numeric[1]} distribution`,
      subtitle: "Frequency across automatically selected value ranges",
      chart: "histogram", x: numeric[1],
    });
  }
  if (numeric.length > 2) {
    specs.push({
      id: "correlation-matrix", title: "Numeric correlations",
      subtitle: "Pairwise Pearson correlations for the filtered records",
      chart: "correlation",
    });
  }
  return specs;
}

function measurePriority(column) {
  const name = column.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
  const priorities = [
    [/\b(revenue|sales|profit|earnings|income)\b/, 12],
    [/\b(delay|amount|total|value|spend|expense|cost)\b/, 10],
    [/\b(score|rating|grade|result|outcome)\b/, 8],
    [/\b(quantity|units|volume|count|number)\b/, 7],
    [/\b(delay|duration|distance|rate|percent|percentage|pct)\b/, 6],
  ];
  return priorities.find(([pattern]) => pattern.test(name))?.[1] || 0;
}

function categoryPriority(column, schema) {
  const field = schema.get(column);
  const count = field?.Unique || 0;
  const kindPriority = field?.Type === "categorical" ? 0 : 1;
  return kindPriority * 100 + Math.abs(count - 6);
}

function dateBucketLabel(bucket) {
  return ({ date: "individual dates", day: "daily", week: "weekly", month: "monthly", quarter: "quarterly", year: "yearly" })[bucket] || bucket;
}

function DashboardChartCard({ spec, workspace, filters, onRecords }) {
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    setResult(null);
    request("/chart", workspace, {
      method: "POST",
      body: JSON.stringify({
        chart: spec.chart,
        x: spec.x || null,
        y: spec.y || null,
        color: spec.color || null,
        aggregation: spec.aggregation || "mean",
        date_frequency: spec.dateFrequency || "auto",
        limit: 8,
        filters,
      }),
    }).then((response) => response.json())
      .then((value) => {
        if (!active) return;
        setResult(value);
        onRecords(value.records_after_filters);
      })
      .catch((requestError) => { if (active) setError(requestError.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [filters, onRecords, spec, workspace]);

  const chartKind = spec.chart === "line" ? "line" : spec.chart === "scatter" ? "scatter" : "bar";
  const timeBucket = result?.date_bucket ? ` · ${dateBucketLabel(result.date_bucket)}` : "";
  return <Card className="dashboard-chart-card" title={spec.title} action={<span className="dashboard-chart-type">{spec.chart === "correlation" ? "RELATIONSHIPS" : spec.chart.replaceAll("_", " ").toUpperCase()}</span>}>
    <p className="dashboard-chart-subtitle">{spec.subtitle}{timeBucket}</p>
    {loading ? <div className="dashboard-chart-loading"><LoaderCircle className="spin" size={18} /> Recalculating for current filters…</div>
      : error ? <div className="dashboard-chart-message"><CircleHelp size={17} /><span>{error.includes("No records match") ? "No records match the selected slicers." : error}</span></div>
        : result?.columns ? <CorrelationMatrix result={result} />
          : result?.series?.length ? <Chart data={result.series} kind={chartKind} height={320} xLabel={spec.x || "Column"} yLabel={spec.chart === "histogram" || spec.chart === "category" ? "Record count" : spec.chart === "scatter" ? spec.y : `${spec.aggregation} ${spec.y}`} showSeriesLegend={Boolean(result.series_names?.length)} seriesNames={result.series_names || []} />
            : <div className="dashboard-chart-message">No usable values were found for this chart.</div>}
    {result && <div className="dashboard-chart-foot"><span>{result.records_after_filters?.toLocaleString()} records in filtered view</span><span>{result.sampled ? "Representative sample shown" : "All matching records analyzed"}</span></div>}
  </Card>;
}

function InsightCard({ item, index }) {
  const icon = item.level === "warning" ? CircleHelp : item.level === "success" ? Check : Lightbulb;
  const Icon = icon;
  return <motion.div className={`insight-card ${item.level || ""}`} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * .06 }}><div className="insight-icon"><Icon size={15} /></div><div><b>{item.title}</b><p>{item.detail}</p></div></motion.div>;
}

function Explorer({ data, workspace, setData, notify, setError }) {
  const [search, setSearch] = useState("");
  const [offset, setOffset] = useState(0);
  const [table, setTable] = useState(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let active = true; setLoading(true);
    request(`/table?offset=${offset}&limit=30&search=${encodeURIComponent(search)}`, workspace)
      .then((r) => r.json()).then((value) => { if (active) setTable(value); })
      .catch((e) => setError(e.message)).finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [offset, search, workspace, setError]);
  const updateType = async (column, type) => {
    try { const response = await request("/types", workspace, { method: "PUT", body: JSON.stringify({ [column]: type }) }); setData(await response.json()); notify(`${column} is now treated as ${type}`); }
    catch (e) { setError(e.message); }
  };
  const types = ["numeric", "categorical", "boolean", "datetime", "identifier", "text", "empty"];
  return <div className="stack-lg">
    <PageTitle eyebrow="INSPECT & UNDERSTAND" title="Data explorer" detail="Browse records, search across fields, and fine-tune inferred column types." action={<button className="btn btn-quiet" onClick={() => downloadExport("csv", workspace).catch((e) => setError(e.message))}><Download size={15} /> Download CSV</button>} />
    <Card className="schema-card" title="Data dictionary" action={<span className="subtle-count">{data.profile.schema.length} fields · select a type to override</span>}>
      <div className="table-scroll"><table className="data-table schema-table"><thead><tr><th>Column</th><th>Inferred type</th><th>Missing</th><th>Invalid parsed</th><th>Unique</th><th>Min</th><th>Max</th><th>Mean</th><th>Median</th><th>Std dev</th><th>Most frequent</th><th>Sample values</th></tr></thead><tbody>{data.profile.schema.map((field) => <tr key={field.Column}><td><b>{field.Column}</b></td><td><select value={data.profile.kinds[field.Column]} onChange={(e) => updateType(field.Column, e.target.value)}>{types.map((type) => <option key={type}>{type}</option>)}</select></td><td><span className={field["Missing %"] ? "warning-text" : ""}>{field.Missing.toLocaleString()} <small>({field["Missing %"]}%)</small></span></td><td className={field["Invalid values"] ? "warning-text" : ""}>{field["Invalid values"] || "—"}</td><td>{field.Unique.toLocaleString()}</td><td>{formatStat(field.Minimum)}</td><td>{formatStat(field.Maximum)}</td><td>{formatStat(field.Mean)}</td><td>{formatStat(field.Median)}</td><td>{formatStat(field["Std dev"])}</td><td>{formatStat(field["Most frequent"])}</td><td className="sample-cell">{field.Sample || "—"}</td></tr>)}</tbody></table></div>
    </Card>
    <Card className="table-card" title="Record preview" action={<div className="search-field"><Search size={15} /><input placeholder="Search any field…" value={search} onChange={(e) => { setOffset(0); setSearch(e.target.value); }} /><kbd>Enter</kbd></div>}>
      {loading ? <div className="table-loading"><LoaderCircle className="spin" size={18} /> Loading records…</div> : table?.rows.length ? <>
        <div className="table-scroll"><table className="data-table"><thead><tr>{table.columns.map((column) => <th key={column}>{column}<small>{data.profile.kinds[column]}</small></th>)}</tr></thead><tbody>{table.rows.map((row, i) => <tr key={i}>{table.columns.map((column) => <td key={column}>{row[column] == null ? <span className="null-value">null</span> : String(row[column])}</td>)}</tr>)}</tbody></table></div>
        <div className="pagination"><span>Showing {offset + 1}–{Math.min(offset + table.rows.length, table.total)} of {table.total.toLocaleString()} records</span><div><button className="icon-btn" disabled={!offset} onClick={() => setOffset(Math.max(0, offset - 30))} aria-label="Previous page"><ArrowLeft size={16} /></button><button className="icon-btn" disabled={offset + 30 >= table.total} onClick={() => setOffset(offset + 30)} aria-label="Next page"><ArrowRight size={16} /></button></div></div>
      </> : <EmptyState icon={Search} title="No matching records" detail="Try a different search term." />}
    </Card>
  </div>;
}

function Quality({ data }) {
  const diagnostics = data.diagnostics || [];
  const missingByCol = diagnostics.filter((row) => row.Missing > 0).map((row) => ({ name: row.Column, value: row.Missing }));
  const outlierByCol = diagnostics.filter((row) => (row["IQR outlier candidates"] || 0) > 0).map((row) => ({ name: row.Column, value: row["IQR outlier candidates"] }));

  return <div className="stack-lg">
    <PageTitle eyebrow="TRUST YOUR DATA" title="Data quality" detail="A transparent audit of completeness, duplication, constants and outlier candidates." />
    <div className="quality-overview">
      <Card className="quality-score-card"><div className="score-gauge"><div className="score-ring" style={{ "--score": `${data.profile.quality * 3.6}deg` }}><div><b>{data.profile.quality}</b><small> / 100</small></div></div><div><div className="eyebrow">PROJECT HEURISTIC</div><h2>{data.profile.quality >= 85 ? "Strong starting point" : data.profile.quality >= 65 ? "Room to improve" : "Needs a closer look"}</h2><p>This score summarizes completeness, duplicate rows and constant fields. It is not a universal data-quality standard.</p></div></div></Card>
      <div className="quality-components"><div><span>Completeness</span><b>{(100 - data.profile.missing_pct).toFixed(1)}%</b><div className="progress-track"><i style={{ width: `${100 - data.profile.missing_pct}%` }} /></div></div><div><span>Unique records</span><b>{(100 - data.profile.duplicate_pct).toFixed(1)}%</b><div className="progress-track teal"><i style={{ width: `${100 - data.profile.duplicate_pct}%` }} /></div></div><div><span>Non-constant columns</span><b>{data.profile.columns ? ((1 - data.profile.constants.length / data.profile.columns) * 100).toFixed(1) : "0.0"}%</b><div className="progress-track blue"><i style={{ width: `${data.profile.columns ? (1 - data.profile.constants.length / data.profile.columns) * 100 : 0}%` }} /></div></div></div>
    </div>
    <div className="overview-grid">
      <Card title="Missing values distribution" action={<span className="subtle-count">{missingByCol.length} columns affected</span>}>
        {missingByCol.length ? <Chart data={missingByCol} kind="bar" height={220} color="#dc7a12" xLabel="Column" yLabel="Missing count" /> : <div className="clean-state"><div><Check size={20} /></div><b>All columns complete</b><span>No missing values detected across dataset.</span></div>}
      </Card>
      <Card title="IQR Outlier candidates" action={<span className="subtle-count">{outlierByCol.length} columns flagged</span>}>
        {outlierByCol.length ? <Chart data={outlierByCol} kind="bar" height={220} color="#e484a6" xLabel="Column" yLabel="Candidate rows" /> : <div className="clean-state"><div><Check size={20} /></div><b>No severe IQR outliers</b><span>Values align within expected interquartile bounds.</span></div>}
      </Card>
    </div>
    <Card title="Column-level diagnostics" action={<span className="subtle-count">{diagnostics.length} fields reviewed</span>}>
      <div className="table-scroll"><table className="data-table"><thead><tr><th>Column</th><th>Type</th><th>Missing</th><th>Invalid parsed</th><th>Unique</th><th>Infinite</th><th>IQR outlier candidates</th><th>Constant</th></tr></thead><tbody>{diagnostics.map((row) => <tr key={row.Column}><td><b>{row.Column}</b></td><td><span className="type-pill">{row.Type}</span></td><td>{row.Missing.toLocaleString()} <small>({row["Missing %"]}%)</small></td><td className={row["Invalid values"] ? "warning-text" : ""}>{row["Invalid values"] || "—"}</td><td>{row.Unique.toLocaleString()}</td><td>{row["Infinite values"] ? <span className="warning-text">{row["Infinite values"]}</span> : "—"}</td><td>{row["IQR outlier candidates"] ? <span className="warning-text">{row["IQR outlier candidates"].toLocaleString()}</span> : "—"}</td><td>{row.Constant ? <span className="warning-text">Yes</span> : "No"}</td></tr>)}</tbody></table></div>
    </Card>
    <div className="alert subtle"><CircleHelp size={16} /><span>Outliers and repeated records are review candidates, not automatically invalid data. Quality thresholds depend on your use case.</span></div>
  </div>;
}

function Cleaning({ data, workspace, setData, notify, setError }) {
  const [options, setOptions] = useState(null);
  const [selected, setSelected] = useState({});
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  useEffect(() => { request("/cleaning", workspace).then((r) => r.json()).then(setOptions).catch((e) => setError(e.message)); }, [workspace, setError]);
  const actions = useMemo(() => options?.recommendations.filter((item) => selected[item.key] && selected[item.key] !== "leave").map((item) => ({ key: item.key, strategy: selected[item.key] })) || [], [options, selected]);
  const previewChanges = async () => {
    setLoading(true);
    try { const response = await request("/cleaning/preview", workspace, { method: "POST", body: JSON.stringify({ actions }) }); setPreview(await response.json()); }
    catch (e) { setError(e.message); } finally { setLoading(false); }
  };
  const applyChanges = async () => {
    if (!window.confirm("Apply these changes to the working copy? Your original upload stays preserved.")) return;
    setLoading(true);
    try { const response = await request("/cleaning/apply", workspace, { method: "POST", body: JSON.stringify({ actions }) }); setData(await response.json()); const latest = await request("/cleaning", workspace); setOptions(await latest.json()); setSelected({}); setPreview(null); notify("Cleaning changes applied to the working copy"); }
    catch (e) { setError(e.message); } finally { setLoading(false); }
  };
  return <div className="stack-lg">
    <PageTitle eyebrow="CHANGE WITH CONFIDENCE" title="Cleaning studio" detail="Review recommended actions, inspect a preview, then approve changes to a separate working copy." />
    <div className="alert info"><ShieldCheck size={17} /><span>The original upload is preserved. No edits happen until you choose actions and apply them. Values that failed inferred numeric/date parsing are marked separately and remain unchanged in the original.</span></div>
    <Card title="Recommended actions" action={<span className="subtle-count">{options?.recommendations.length || 0} suggestions</span>}>
      {!options?.recommendations.length ? <EmptyState icon={Check} title="Nothing urgent to clean" detail="No missing values, duplicates or constant columns were found." /> : <div className="recommendation-list">{options.recommendations.map((item) => <label className="recommendation-row" key={item.key}><input type="checkbox" checked={Boolean(selected[item.key])} onChange={(e) => setSelected((value) => ({ ...value, [item.key]: e.target.checked ? (item.strategy || "yes") : false }))} /><span className="custom-check"><Check size={13} /></span><span className="recommendation-copy"><b>{item.label}</b><small>{item.risk} · Review suggested impact before applying</small></span>{item.strategy && <select value={selected[item.key] && selected[item.key] !== true ? selected[item.key] : item.strategy} onClick={(e) => e.stopPropagation()} onChange={(e) => setSelected((value) => ({ ...value, [item.key]: e.target.value }))}><option value="median">Median</option><option value="mode">Mode</option><option value="leave">Leave unchanged</option></select>}</label>)}</div>}
      {options?.recommendations.length > 0 && <div className="clean-actions"><button className="btn btn-quiet" disabled={!actions.length || loading} onClick={previewChanges}><Search size={15} /> Preview selected ({actions.length})</button>{preview && <button className="btn btn-primary" disabled={!actions.length || loading} onClick={applyChanges}><Check size={15} /> Apply to working copy</button>}</div>}
    </Card>
    {preview && <Card title="Before and after preview" className="preview-results"><div className="before-after"><div><span>ROWS BEFORE</span><b>{preview.before.rows.toLocaleString()}</b></div><ArrowRight size={17} /><div><span>ROWS AFTER</span><b>{preview.after.rows.toLocaleString()}</b></div><div><span>COLUMNS AFTER</span><b>{preview.after.columns}</b></div></div>{preview.changes.map((line) => <div className="preview-change" key={line}><Check size={14} />{line}</div>)}<div className="table-scroll"><table className="data-table"><thead><tr>{Object.keys(preview.preview[0] || {}).map((column) => <th key={column}>{column}</th>)}</tr></thead><tbody>{preview.preview.slice(0, 6).map((row, i) => <tr key={i}>{Object.keys(row).map((key) => <td key={key}>{row[key] == null ? <span className="null-value">null</span> : String(row[key])}</td>)}</tr>)}</tbody></table></div></Card>}
    {options?.history?.length > 0 && <Card title="Change history"><div className="history-list">{options.history.map((item, index) => <div key={`${index}-${item}`}><span className="history-dot" /><span>{item}</span></div>)}</div></Card>}
  </div>;
}

function AnalysisWorkbench({ data, workspace, setError }) {
  const profile = data.profile;
  const [operation, setOperation] = useState("describe");
  const [columns, setColumns] = useState(profile.numeric.slice(0, 4));
  const [pivotMeasure, setPivotMeasure] = useState(profile.numeric[0] || "");
  const [firstCategory, setFirstCategory] = useState(profile.categorical[0] || "");
  const [secondCategory, setSecondCategory] = useState(profile.categorical[1] || "");
  const [groupBy, setGroupBy] = useState(profile.categorical[0] || profile.dates[0] || "");
  const [statistic, setStatistic] = useState("mean");
  const [method, setMethod] = useState("pearson");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const numeric = profile.numeric;
  const operations = [
    { id: "describe", label: "Descriptive profile", detail: "Means, spread, missingness and type-aware summaries." },
    { id: "group_summary", label: "Group comparison", detail: "Compare numeric measures across any inferred category." },
    { id: "crosstab", label: "Cross-tabulation", detail: "Inspect counts and associations across two categories." },
    { id: "pivot_table", label: "Pivot table", detail: "Aggregate one numeric measure across two dimensions." },
    { id: "correlation", label: "Correlation matrix", detail: "Compare numeric relationships with Pearson or Spearman." },
    { id: "missingness", label: "Missing-value audit", detail: "Rank all fields and quantify complete versus incomplete rows." },
    { id: "outliers", label: "Outlier screening", detail: "Review IQR or three-standard-deviation candidates." },
    { id: "frequency", label: "Frequency table", detail: "Rank category values with percentages and cumulative share." },
    { id: "duplicates", label: "Duplicate records", detail: "Find repeated rows without changing the dataset." },
  ];
  const toggleColumn = (column) => setColumns((current) => current.includes(column) ? current.filter((value) => value !== column) : [...current, column]);
  const run = async () => {
    setLoading(true);
    try {
      const selected = operation === "crosstab" ? [firstCategory, secondCategory]
        : operation === "pivot_table" ? [pivotMeasure].filter(Boolean)
        : operation === "frequency" ? [firstCategory]
          : ["correlation", "outliers"].includes(operation) ? columns.filter((column) => numeric.includes(column))
            : operation === "group_summary" ? columns.filter((column) => numeric.includes(column) && column !== groupBy)
              : operation === "describe" ? columns
                : [];
      const response = await request("/analysis", workspace, { method: "POST", body: JSON.stringify({ operation, columns: selected, group_by: operation === "pivot_table" ? firstCategory : groupBy, column_by: operation === "pivot_table" ? secondCategory : null, statistic, method }) });
      setResult(await response.json());
    } catch (error) {
      setResult(null);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };
  const hasSelection = operation === "crosstab" || operation === "pivot_table" ? Boolean(firstCategory && secondCategory && firstCategory !== secondCategory && (operation !== "pivot_table" || pivotMeasure))
    : operation === "frequency" ? Boolean(firstCategory)
      : ["correlation", "outliers", "group_summary"].includes(operation) ? columns.some((column) => numeric.includes(column) && (operation !== "group_summary" || column !== groupBy)) && (operation !== "correlation" || columns.filter((column) => numeric.includes(column)).length >= 2) && (operation !== "group_summary" || Boolean(groupBy))
        : true;
  useEffect(() => {
    if (hasSelection) run();
  }, [operation, firstCategory, secondCategory, groupBy, statistic, method]);
  return <div className="stack-lg">
    <PageTitle eyebrow="ANALYZE THE WORKING DATA" title="Analysis workbench" detail="Choose a statistical operation, inspect the exact output, then pivot to another slice of your dataset." />
    <div className="workbench-grid">
      <Card className="workbench-controls" title="Analysis controls">
        <label className="field-label" htmlFor="analysis-operation">Operation</label>
        <select id="analysis-operation" value={operation} onChange={(event) => { setOperation(event.target.value); setResult(null); }}>
          {operations.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}
        </select>
        <p className="operation-help">{operations.find((item) => item.id === operation)?.detail}</p>
        {(operation === "crosstab" || operation === "pivot_table") && <>
          <label className="field-label" htmlFor="crosstab-first">First dimension</label>
          <select id="crosstab-first" value={firstCategory} onChange={(event) => setFirstCategory(event.target.value)}>{profile.categorical.map((column) => <option key={column}>{column}</option>)}</select>
          <label className="field-label" htmlFor="crosstab-second">Second dimension</label>
          <select id="crosstab-second" value={secondCategory} onChange={(event) => setSecondCategory(event.target.value)}>{profile.categorical.filter((column) => column !== firstCategory).map((column) => <option key={column}>{column}</option>)}</select>
        </>}
        {operation === "pivot_table" && <>
          <label className="field-label" htmlFor="pivot-statistic">Aggregation</label>
          <select id="pivot-statistic" value={statistic} onChange={(event) => setStatistic(event.target.value)}>{["mean", "median", "sum", "count", "min", "max", "std"].map((item) => <option key={item} value={item}>{item === "std" ? "Standard deviation" : item[0].toUpperCase() + item.slice(1)}</option>)}</select>
          <label className="field-label">Numeric measure</label>
          <div className="field-check-list workbench-fields">{numeric.map((column) => <label key={column}><input type="radio" name="pivot-measure" checked={pivotMeasure === column} onChange={() => setPivotMeasure(column)} /><span>{column}</span></label>)}</div>
        </>}
        {operation === "frequency" && <>
          <label className="field-label" htmlFor="frequency-field">Field</label>
          <select id="frequency-field" value={firstCategory} onChange={(event) => setFirstCategory(event.target.value)}>{profile.schema.map((field) => <option key={field.Column}>{field.Column}</option>)}</select>
        </>}
        {operation === "group_summary" && <>
          <label className="field-label" htmlFor="group-field">Group rows by</label>
          <select id="group-field" value={groupBy} onChange={(event) => setGroupBy(event.target.value)}>{profile.schema.map((field) => <option key={field.Column}>{field.Column}</option>)}</select>
          <label className="field-label" htmlFor="group-statistic">Summary statistic</label>
          <select id="group-statistic" value={statistic} onChange={(event) => setStatistic(event.target.value)}>{["mean", "median", "sum", "count", "min", "max", "std"].map((item) => <option key={item} value={item}>{item === "std" ? "Standard deviation" : item[0].toUpperCase() + item.slice(1)}</option>)}</select>
        </>}
        {operation === "correlation" && <><label className="field-label" htmlFor="correlation-method">Correlation method</label><select id="correlation-method" value={method} onChange={(event) => setMethod(event.target.value)}><option value="pearson">Pearson · linear association</option><option value="spearman">Spearman · rank association</option></select></>}
        {operation === "outliers" && <><label className="field-label" htmlFor="outlier-method">Screening rule</label><select id="outlier-method" value={method} onChange={(event) => setMethod(event.target.value)}><option value="iqr">IQR · 1.5 × interquartile range</option><option value="zscore">Z-score · 3 standard deviations</option></select></>}
        {["describe", "correlation", "outliers", "group_summary"].includes(operation) && <>
          <label className="field-label">{operation === "describe" ? "Fields to profile" : "Numeric measures"}</label>
          <div className="field-check-list workbench-fields">{(operation === "describe" ? profile.schema.map((field) => field.Column) : numeric.filter((column) => operation !== "group_summary" || column !== groupBy)).map((column) => <label key={column}><input type="checkbox" checked={columns.includes(column)} onChange={() => toggleColumn(column)} /><span>{column}</span><small>{profile.kinds[column]}</small></label>)}</div>
        </>}
        <button className="btn btn-primary full-btn" disabled={loading || !hasSelection} onClick={run}>{loading ? <LoaderCircle className="spin" size={16} /> : <SlidersHorizontal size={16} />} Run analysis</button>
      </Card>
      <Card className="workbench-results" title="Analysis results" action={result && <div className="workbench-result-actions"><span className="subtle-count">{result.records_analyzed?.toLocaleString() || result.rows?.length?.toLocaleString() || 0} rows returned</span><button className="btn btn-quiet" onClick={() => {
        const exportRows = result.matrix
          ? result.matrix.map((row, index) => ({ Field: result.columns[index], ...Object.fromEntries(result.columns.map((column, columnIndex) => [column, row[columnIndex]])) }))
          : result.rows || [];
        const exportColumns = result.matrix ? ["Field", ...result.columns] : result.columns || [];
        downloadRowsCsv(`analysis_${operation}.csv`, exportColumns, exportRows);
      }}><Download size={13} /> CSV</button></div>}>
        {!result ? <EmptyState icon={BarChart3} title="Ready for an analysis" detail="Select an operation and fields. Results update only when you run an analysis." /> : <>
          <div className="workbench-result-heading"><div><span className="eyebrow">COMPUTED FROM CURRENT WORKING DATA</span><h2>{result.title}</h2></div><span className="result-stamp">{result.records_analyzed?.toLocaleString() || profile.rows.toLocaleString()} records</span></div>
          {operation === "correlation" ? <CorrelationMatrix result={{ columns: result.columns, values: result.matrix, pairCounts: result.pair_counts }} />
            : operation === "frequency" ? <Chart data={result.rows.map((row) => ({ name: row.Value, value: row.Count }))} height={Math.max(240, Math.min(380, result.rows.length * 25))} xLabel="Value" yLabel="Records" color={PALETTE[1]} />
            : operation === "group_summary" && result.rows?.length && result.columns?.length > 1 ? <>
                <div style={{ marginBottom: 18 }}><Chart data={result.rows.slice(0, 15).map((row) => ({ name: String(row[result.columns[0]]), value: Number(row[result.columns[1]]) || 0 }))} kind="bar" height={260} xLabel={result.columns[0]} yLabel={result.columns[1]} color={PALETTE[2]} /></div>
                <div className="table-scroll workbench-table"><table className="data-table"><thead><tr>{result.columns.map((column) => <th key={column}>{column}</th>)}</tr></thead><tbody>{result.rows.slice(0, 200).map((row, rowIndex) => <tr key={rowIndex}>{result.columns.map((column) => <td key={column}>{row[column] == null ? "—" : typeof row[column] === "number" ? formatStat(row[column]) : String(row[column])}</td>)}</tr>)}</tbody></table>{result.rows.length > 200 && <div className="table-cap">Showing first 200 results.</div>}</div>
              </>
              : <div className="table-scroll workbench-table"><table className="data-table"><thead><tr>{result.columns.map((column) => <th key={column}>{column}</th>)}</tr></thead><tbody>{result.rows.slice(0, 200).map((row, rowIndex) => <tr key={rowIndex}>{result.columns.map((column) => <td key={column}>{row[column] == null ? "—" : typeof row[column] === "number" ? formatStat(row[column]) : String(row[column])}</td>)}</tr>)}</tbody></table>{result.rows.length > 200 && <div className="table-cap">Showing first 200 results.</div>}</div>}
          {result.operation === "duplicates" && <div className="workbench-summary"><div><b>{result.duplicate_rows}</b><span>Repeated rows</span></div><div><b>{result.duplicate_members}</b><span>Rows in duplicate groups</span></div></div>}
          {result.operation === "missingness" && <div className="workbench-summary"><div><b>{result.complete_rows?.toLocaleString()}</b><span>Complete rows</span></div><div><b>{result.rows_with_missing?.toLocaleString()}</b><span>Rows with missing values</span></div></div>}
          {result.operation === "frequency" && <div className="workbench-summary"><div><b>{result.distinct_values?.toLocaleString()}</b><span>Distinct values</span></div><div><b>{result.truncated ? "Top 100" : "All values"}</b><span>Categories displayed</span></div></div>}
          {result.truncated && <div className="alert subtle compact-alert"><CircleHelp size={14} /><span>Output is capped for readability. Use more selective fields or filters for a focused view.</span></div>}
          {result.warning && <div className="alert subtle compact-alert"><CircleHelp size={14} /><span>{result.warning}</span></div>}
        </>}
      </Card>
    </div>
    <Card title="Analysis guide" className="analysis-guide"><p>Descriptive summaries characterize this data. Correlations measure association, group summaries compare observed records, and outlier screens only flag rows for review. These analyses do not establish causality or prove data errors.</p></Card>
  </div>;
}

function ChartStudio({ data, workspace, setError }) {
  const p = data.profile;
  const [chart, setChart] = useState("histogram");
  const [x, setX] = useState(p.numeric[0] || p.categorical[0] || "");
  const [y, setY] = useState(p.numeric.find((v) => v !== x) || p.numeric[0] || "");
  const [colorBy, setColorBy] = useState("");
  const [aggregation, setAggregation] = useState("mean");
  const [dateFrequency, setDateFrequency] = useState("auto");
  const [result, setResult] = useState(null);
  const [controls, setControls] = useState([]);
  const [filters, setFilters] = useState([]);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    let active = true;
    request("/controls", workspace).then((response) => response.json()).then((value) => {
      if (active) setControls(value.columns);
    }).catch((error) => setError(error.message));
    return () => { active = false; };
  }, [workspace, setError]);
  const xOptions = chart === "histogram" || chart === "scatter" ? p.numeric
    : chart === "category" || chart === "pie" ? [...p.categorical, ...p.numeric]
      : [...p.categorical, ...p.dates, ...p.numeric];
  useEffect(() => {
    if (!xOptions.includes(x)) setX(xOptions[0] || "");
    if (!p.numeric.includes(y)) setY(p.numeric.find((column) => column !== x) || p.numeric[0] || "");
    if (![...p.categorical, ...p.dates].includes(colorBy)) setColorBy("");
  }, [chart, xOptions.join("|"), p.numeric.join("|"), p.categorical.join("|"), p.dates.join("|")]);
  const choices = [
    { id: "histogram", label: "Histogram", needsY: false, defaultKind: "bar" },
    { id: "category", label: "Category count", needsY: false, defaultKind: "bar" },
    { id: "pie", label: "Donut chart", needsY: false, defaultKind: "donut" },
    { id: "bar", label: "Bar comparison", needsY: true, defaultKind: "bar" },
    { id: "grouped_bar", label: "Grouped bars", needsY: true, defaultKind: "bar", grouped: true },
    { id: "stacked_bar", label: "Stacked bars", needsY: true, defaultKind: "bar", grouped: true, stacked: true },
    { id: "line", label: "Trend line", needsY: true, defaultKind: "line" },
    { id: "area", label: "Area trend", needsY: true, defaultKind: "area" },
    { id: "scatter", label: "Scatter plot", needsY: true, defaultKind: "scatter" },
    { id: "correlation", label: "Correlation matrix", needsY: false, defaultKind: "bar" },
  ];
  const addFilter = () => {
    if (filters.length >= 4) return;
    const available = controls.filter((field) => !filters.some((filter) => filter.column === field.column));
    if (!available.length) return;
    const field = available[0];
    const categorical = ["categorical", "boolean", "identifier", "text"].includes(field.kind);
    setFilters((current) => [...current, { column: field.column, operator: categorical ? "eq" : "gte", value: field.options?.[0] ?? field.minimum ?? "", value_to: field.maximum ?? "" }]);
  };
  const updateFilter = (index, patch) => setFilters((current) => current.map((filter, itemIndex) => itemIndex === index ? { ...filter, ...patch } : filter));
  const makeChart = async () => {
    setLoading(true);
    try { const response = await request("/chart", workspace, { method: "POST", body: JSON.stringify({ chart, x: chart === "correlation" ? null : x, y, color: selectedChart?.grouped ? colorBy || null : null, aggregation, date_frequency: dateFrequency, limit: 30, filters: filters.filter((filter) => filter.operator === "is_null" || filter.operator === "not_null" || (filter.value !== "" && filter.value != null && (filter.operator !== "between" || (filter.value_to !== "" && filter.value_to != null)))) }) }); setResult(await response.json()); }
    catch (e) { setError(e.message); } finally { setLoading(false); }
  };
  const selectedChart = choices.find((item) => item.id === chart);
  useEffect(() => {
    if ((chart === "correlation" || x) && (!selectedChart?.needsY || y)) {
      makeChart();
    }
  }, [chart, x, y, colorBy, aggregation, dateFrequency]);
  return <div className="stack-lg">
    <PageTitle eyebrow="ASK YOUR DATA A QUESTION" title="Chart studio" detail="Build interactive distributions, category comparisons, time trends and correlation views." />
    <div className="studio-grid"><Card className="chart-controls" title="Chart configuration">
      <label className="field-label">Visualization type</label><div className="chart-type-grid">{choices.map((item) => {
        const Icon = item.id === "pie" ? Gauge : item.id === "line" || item.id === "area" ? LineChartIcon : item.id === "scatter" ? Activity : BarChart3;
        return <button className={`chart-type ${chart === item.id ? "selected" : ""}`} onClick={() => { setChart(item.id); setResult(null); }} key={item.id}><Icon size={17} /><span>{item.label}</span></button>;
      })}</div>
      {chart !== "correlation" && <><label className="field-label" htmlFor="chart-x">X-axis / field</label><select id="chart-x" value={x} onChange={(e) => { setX(e.target.value); setResult(null); }}>{(chart === "histogram" || chart === "scatter" ? p.numeric : chart === "category" || chart === "pie" ? [...p.categorical, ...p.numeric] : [...p.categorical, ...p.dates, ...p.numeric]).map((column) => <option key={column}>{column}</option>)}</select></>}
      {selectedChart?.needsY && <><label className="field-label" htmlFor="chart-y">Measure</label><select id="chart-y" value={y} onChange={(e) => { setY(e.target.value); setResult(null); }}>{p.numeric.map((column) => <option key={column}>{column}</option>)}</select><label className="field-label" htmlFor="chart-agg">Aggregation</label><select id="chart-agg" value={aggregation} onChange={(e) => { setAggregation(e.target.value); setResult(null); }}>{["mean", "sum", "count", "median"].map((item) => <option key={item} value={item}>{item[0].toUpperCase() + item.slice(1)}</option>)}</select></>}
      {p.dates.includes(x) && ["line", "area", "bar", "grouped_bar", "stacked_bar"].includes(chart) && <><label className="field-label" htmlFor="chart-date-frequency">Date rollup</label><select id="chart-date-frequency" value={dateFrequency} onChange={(event) => { setDateFrequency(event.target.value); setResult(null); }}><option value="auto">Automatic (recommended)</option><option value="D">Daily</option><option value="W">Weekly</option><option value="MS">Monthly</option><option value="QS">Quarterly</option><option value="YS">Yearly</option></select></>}
      {selectedChart?.grouped && <><label className="field-label" htmlFor="chart-color">Series / color breakdown</label><select id="chart-color" value={colorBy} onChange={(e) => { setColorBy(e.target.value); setResult(null); }}><option value="">No breakdown</option>{[...p.categorical, ...p.dates].filter((column) => column !== x).map((column) => <option key={column}>{column}</option>)}</select></>}
      <div className="slicer-heading"><div><strong>Data slicers</strong><small>Filter rows before plotting</small></div><button type="button" className="btn btn-quiet slicer-add" onClick={addFilter} disabled={filters.length >= 4 || controls.length === 0}>Add filter</button></div>
      {filters.length > 0 && <div className="slicer-list">{filters.map((filter, index) => {
        const field = controls.find((item) => item.column === filter.column);
        const categorical = field && ["categorical", "boolean", "identifier"].includes(field.kind);
        const textual = field?.kind === "text";
        const operators = textual ? [["contains", "contains"], ["eq", "is"], ["ne", "is not"], ["is_null", "is missing"], ["not_null", "is present"]]
          : categorical ? [["eq", "is"], ["ne", "is not"], ["contains", "contains"], ["is_null", "is missing"], ["not_null", "is present"]]
          : [["gte", "at least"], ["lte", "at most"], ["gt", "greater than"], ["lt", "less than"], ["between", "between"], ["eq", "is"], ["ne", "is not"], ["is_null", "is missing"], ["not_null", "is present"]];
        return <div className="slicer-row" key={`slicer-${index}`}>
          <select aria-label={`Slicer ${index + 1} field`} value={filter.column} onChange={(event) => {
            const nextField = controls.find((item) => item.column === event.target.value);
            updateFilter(index, { column: event.target.value, operator: nextField && ["categorical", "boolean", "identifier", "text"].includes(nextField.kind) ? "eq" : "gte", value: nextField?.options?.[0] ?? nextField?.minimum ?? "", value_to: nextField?.maximum ?? "" });
            setResult(null);
          }}>{controls.filter((item) => !filters.some((other, otherIndex) => other.column === item.column && otherIndex !== index)).map((item) => <option key={item.column} value={item.column}>{item.column}</option>)}</select>
          <select aria-label={`Slicer ${index + 1} condition`} value={filter.operator} onChange={(event) => { updateFilter(index, { operator: event.target.value, ...(event.target.value === "between" && !filter.value_to ? { value_to: field?.maximum ?? "" } : {}) }); setResult(null); }}>{operators.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>
          {!["is_null", "not_null"].includes(filter.operator) && (textual
            ? <input aria-label={`Slicer ${index + 1} value`} type="text" placeholder={filter.operator === "contains" ? "Contains…" : "Value"} value={filter.value} onChange={(event) => { updateFilter(index, { value: event.target.value }); setResult(null); }} />
            : categorical
              ? filter.operator === "contains"
                ? <input aria-label={`Slicer ${index + 1} value`} type="search" placeholder="Contains…" value={filter.value} onChange={(event) => { updateFilter(index, { value: event.target.value }); setResult(null); }} />
                : <select aria-label={`Slicer ${index + 1} value`} value={filter.value} onChange={(event) => { updateFilter(index, { value: event.target.value }); setResult(null); }}><option value="">Choose value</option>{(field?.options || []).map((value) => <option key={value}>{value}</option>)}</select>
              : <><input aria-label={`Slicer ${index + 1} value`} type={field?.kind === "datetime" ? "date" : "number"} value={filter.value} min={field?.kind === "numeric" ? field.minimum : undefined} max={field?.kind === "numeric" ? field.maximum : undefined} onChange={(event) => { updateFilter(index, { value: event.target.value }); setResult(null); }} />{filter.operator === "between" && <input aria-label={`Slicer ${index + 1} upper value`} type={field?.kind === "datetime" ? "date" : "number"} value={filter.value_to || ""} max={field?.kind === "numeric" ? field.maximum : undefined} onChange={(event) => { updateFilter(index, { value_to: event.target.value }); setResult(null); }} />}</>)}
          <button type="button" className="icon-btn slicer-remove" aria-label={`Remove slicer ${index + 1}`} onClick={() => { setFilters((current) => current.filter((_, itemIndex) => itemIndex !== index)); setResult(null); }}><X size={14} /></button>
        </div>;
      })}</div>}
      <button className="btn btn-primary full-btn" disabled={loading || (chart !== "correlation" && !x) || (selectedChart?.needsY && !y)} onClick={makeChart}>{loading ? <LoaderCircle className="spin" size={16} /> : <BarChart3 size={16} />} Generate visualization</button>
    </Card><Card className="chart-output" title="Visualization preview" action={result?.sampled && <span className="sample-notice">Sampled to 50k rows</span>}>
      {!result ? <EmptyState icon={BarChart3} title="Your chart appears here" detail="Choose a chart and generate a view to explore your data." /> : result.columns ? <CorrelationMatrix result={result} /> : <><div className="chart-context"><span className="chart-context-icon"><BarChart3 size={15} /></span><span><b>{selectedChart?.label}</b><small>{xLabelForChart(chart, x)}{selectedChart?.needsY ? ` · ${aggregation} of ${y}` : ""}</small></span></div><Chart data={result.series} kind={selectedChart?.defaultKind || "bar"} height={chart === "pie" ? 245 : 320} xLabel={chart === "histogram" ? `${x} range` : x} yLabel={selectedChart?.needsY ? `${aggregation} ${y}` : "Record count"} showLegend={chart === "pie"} showSeriesLegend={Boolean(result.series_names?.length)} seriesNames={result.series_names || []} stacked={selectedChart?.stacked} /></>}
      {result && <div className="chart-output-foot"><span>{result.records_after_filters?.toLocaleString() || result.series?.length || result.columns?.length || 0} {result.records_after_filters != null ? "records after filters" : "plotted values"}</span><span>{result.sampled ? "Representative sample · " : ""}Current working data</span></div>}
    </Card></div>
  </div>;
}

function xLabelForChart(chart, column) {
  if (chart === "histogram") return `${column} distribution`;
  if (chart === "correlation") return "Numeric fields";
  return column ? `Grouped by ${column}` : "Select a field";
}

function CorrelationMatrix({ result }) {
  return <div className="corr-table-wrap">{result.truncated && <div className="corr-truncated-note">Showing the first {result.columns.length} of {result.available_columns || result.columns.length} numeric fields. Choose fields in Analysis workbench for a focused matrix.</div>}<table className="corr-table"><thead><tr><th></th>{result.columns.map((column) => <th key={column}>{column}</th>)}</tr></thead><tbody>{result.values.map((row, i) => <tr key={result.columns[i]}><th>{result.columns[i]}</th>{row.map((value, j) => <td key={j} title={value == null ? "Not enough paired values" : `${value}`} style={{ background: value == null ? "var(--panel-raised)" : value >= 0 ? `rgba(67,215,186,${Math.abs(value) * .68})` : `rgba(236,123,163,${Math.abs(value) * .68})` }}>{value == null ? "—" : value.toFixed(2)}</td>)}</tr>)}</tbody></table></div>;
}

function Insights({ data }) {
  return <div className="stack-lg"><PageTitle eyebrow="SIGNAL, NOT NOISE" title="Automated insights" detail="Calculated observations to help direct your next investigation — never causal claims." /><div className="insight-toolbar"><span><Lightbulb size={15} /> {data.insights.length} data-driven observations</span><small>Descriptive analysis · not business interpretation</small></div>{data.insights.length ? <div className="insight-grid">{data.insights.map((item, index) => <InsightCard key={`${item.title}-${index}`} item={item} index={index} />)}</div> : <Card><EmptyState icon={Lightbulb} title="Nothing notable found yet" detail="Explore the visualizations and statistics to look deeper." /></Card>}<Card title="Strongest relationships" action={<span className="subtle-count">Pairwise complete numeric data</span>}>{data.correlations.length ? <div className="association-list">{data.correlations.slice(0, 12).map((item) => <div className="association-row" key={`${item.x}-${item.y}`}><div><b>{item.x}</b><span>with</span><b>{item.y}</b></div><div className="association-track"><i style={{ width: `${Math.abs(item.value) * 100}%`, background: item.value >= 0 ? "#52cbae" : "#e484a6" }} /></div><strong className={item.value < 0 ? "negative" : ""}>{item.value.toFixed(3)}</strong></div>)}</div> : <div className="inline-empty">There are not enough numeric variables for pairwise correlations.</div>}<div className="alert subtle compact-alert"><CircleHelp size={14} /><span>Correlation describes association only. It does not show that one variable causes another.</span></div></Card></div>;
}

function Statistics({ data, workspace, setError }) {
  const p = data.profile;
  const [test, setTest] = useState("pearson");
  const [x, setX] = useState(p.numeric[0] || "");
  const [y, setY] = useState(p.numeric[1] || "");
  const [group, setGroup] = useState(p.categorical[0] || "");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const isChiSquare = test === "chi_square";
  const correlation = ["pearson", "spearman"].includes(test);
  const firstOptions = isChiSquare ? p.categorical : p.numeric;
  const secondOptions = isChiSquare ? p.categorical.filter((column) => column !== x) : p.numeric.filter((column) => column !== x);
  const chooseTest = (next) => {
    setTest(next); setResult(null);
    if (next === "chi_square") { setX(p.categorical[0] || ""); setGroup(p.categorical[1] || ""); }
    else { setX(p.numeric[0] || ""); setY(p.numeric[1] || ""); }
  };
  const run = async () => {
    setLoading(true);
    try { const response = await request("/statistics", workspace, { method: "POST", body: JSON.stringify({ test, x, y: isChiSquare ? null : y, group }) }); setResult(await response.json()); }
    catch (e) { setResult(null); setError(e.message); } finally { setLoading(false); }
  };
  useEffect(() => {
    if (x && (correlation ? y : group)) run();
  }, [test, x, y, group]);

  return <div className="stack-lg"><PageTitle eyebrow="EXPLORE STATISTICAL EVIDENCE" title="Statistical lab" detail="Run an appropriate exploratory test and review the sample size, statistic and caveats." /><div className="studio-grid"><Card className="chart-controls" title="Test setup"><label className="field-label">Statistical test</label><select value={test} onChange={(e) => chooseTest(e.target.value)}><option value="pearson">Pearson correlation</option><option value="spearman">Spearman correlation</option><option value="welch">Welch's t-test</option><option value="mann_whitney">Mann–Whitney U</option><option value="kruskal">Kruskal–Wallis</option><option value="chi_square">Chi-square independence</option></select><label className="field-label">{isChiSquare ? "First categorical variable" : "Numeric variable"}</label><select value={x} onChange={(e) => setX(e.target.value)}>{firstOptions.map((column) => <option key={column}>{column}</option>)}</select>{correlation ? <><label className="field-label">Second numeric variable</label><select value={y} onChange={(e) => setY(e.target.value)}>{secondOptions.map((column) => <option key={column}>{column}</option>)}</select></> : <><label className="field-label">{isChiSquare ? "Second categorical variable" : "Grouping variable"}</label><select value={group} onChange={(e) => setGroup(e.target.value)}>{(isChiSquare ? secondOptions : p.categorical).map((column) => <option key={column}>{column}</option>)}</select></>}<button className="btn btn-primary full-btn" disabled={loading || !x || (correlation ? !y : !group)} onClick={run}>{loading ? <LoaderCircle className="spin" size={16} /> : <FlaskConical size={16} />} Run analysis</button></Card><Card className="result-card" title="Test results">{result ? <><div className="result-title"><div className="result-icon"><FlaskConical size={18} /></div><div><small>EXPLORATORY RESULT</small><h2>{result.test}</h2></div></div><div className="result-metrics"><div><span>Observations</span><b>{result.n.toLocaleString()}</b></div><div><span>Test statistic</span><b>{Number(result.statistic).toPrecision(4)}</b></div><div><span>P-value</span><b>{Number(result.p_value).toPrecision(4)}</b></div>{result.effect != null && <div><span>{isChiSquare ? "Cramér's V" : "Effect / coefficient"}</span><b>{Number(result.effect).toPrecision(4)}</b></div>}{result.degrees_freedom != null && <div><span>Degrees of freedom</span><b>{result.degrees_freedom}</b></div>}</div>
    {correlation && y && <div style={{ marginTop: 16 }}><Chart data={[{ name: `${x} vs ${y}`, value: Number(result.statistic) || 0 }]} kind="bar" height={190} xLabel="Comparison" yLabel="Correlation index" color={result.statistic >= 0 ? "#52cbae" : "#e484a6"} /></div>}
    <div className="alert subtle" style={{ marginTop: 14 }}><CircleHelp size={15} /><span>{result.interpretation}</span></div></> : <EmptyState icon={FlaskConical} title="Results appear here" detail="Choose a supported test and run the analysis." />}</Card></div><div className="alert info"><CircleHelp size={16} /><span>Results are exploratory, not proof of a hypothesis. Check sample design, expected cell counts, test assumptions and multiple-comparison risk before interpreting significance.</span></div></div>;
}

function MachineLearning({ data, workspace, setError }) {
  const p = data.profile;
  const [task, setTask] = useState(p.categorical.length ? "classification" : "regression");
  const [target, setTarget] = useState(p.categorical[0] || p.numeric[0] || "");
  const [features, setFeatures] = useState(p.numeric.filter((column) => column !== target && !p.identifiers.includes(column)).slice(0, 10));
  const [split, setSplit] = useState(20);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const available = p.schema.map((field) => field.Column).filter((column) => column !== target && !p.identifiers.includes(column) && p.kinds[column] !== "empty" && p.kinds[column] !== "datetime");
  const chooseTarget = (value) => { setTarget(value); setFeatures((current) => current.filter((item) => item !== value)); setResult(null); };
  const toggleFeature = (column) => setFeatures((current) => current.includes(column) ? current.filter((item) => item !== column) : [...current, column]);
  const train = async () => {
    setLoading(true); setResult(null);
    try {
      const response = await request("/ml", workspace, { method: "POST", body: JSON.stringify({ task, target, features, test_size: split / 100 }) });
      setResult(await response.json());
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };
  useEffect(() => {
    if (target && features.length) train();
  }, [task, target]);

  return <div className="stack-lg"><PageTitle eyebrow="OPTIONAL PREDICTIVE BASELINES" title="Machine learning lab" detail="Compare simple, reproducible models with a held-out test split. Choose your target and input features." /><div className="alert info"><CircleHelp size={16} /><span>Models train only after you choose a target and run them. Exclude sensitive or post-outcome fields; a single holdout score does not establish generalization.</span></div><div className="studio-grid"><Card className="chart-controls" title="Model setup"><label className="field-label">Prediction task</label><select value={task} onChange={(e) => { setTask(e.target.value); setResult(null); }}><option value="classification">Classification</option><option value="regression">Regression</option></select><label className="field-label">Target variable</label><select value={target} onChange={(e) => chooseTarget(e.target.value)}>{p.schema.map((field) => <option key={field.Column}>{field.Column}</option>)}</select><label className="field-label">Input features <span className="field-hint">({features.length} selected)</span></label><div className="field-check-list">{available.map((column) => <label key={column}><input type="checkbox" checked={features.includes(column)} onChange={() => toggleFeature(column)} /><span>{column}</span></label>)}</div><label className="field-label">Test set <b className="field-value">{split}%</b></label><input className="range-input" type="range" min="15" max="40" step="5" value={split} onChange={(e) => setSplit(Number(e.target.value))} /><button className="btn btn-primary full-btn" disabled={loading || !features.length} onClick={train}>{loading ? <LoaderCircle className="spin" size={16} /> : <Gauge size={16} />} Train baseline models</button></Card><Card className="result-card" title="Holdout comparison">{result ? <><div className="result-metrics"><div><span>Training records</span><b>{result.train_count.toLocaleString()}</b></div><div><span>Test records</span><b>{result.test_count.toLocaleString()}</b></div><div><span>Target</span><b>{result.target}</b></div><div><span>Features used</span><b>{result.features.length}</b></div></div>
    {result.results?.length > 0 && <div style={{ marginBottom: 16 }}><Chart data={result.results.map((m) => ({ name: m.model, value: Number(m.accuracy ?? m.r2 ?? m.f1_macro ?? 0) }))} kind="bar" height={200} xLabel="Model" yLabel={task === "classification" ? "Accuracy score" : "R² score"} color={PALETTE[0]} /></div>}
    <div className="ml-model-grid">{result.results.map((model) => <div className="ml-model" key={model.model}><h3>{model.model}</h3>{Object.entries(model).filter(([key]) => !["model", "confusion", "labels"].includes(key)).map(([key, value]) => <div key={key}><span>{key.replaceAll("_", " ")}</span><b>{typeof value === "number" ? value.toFixed(4) : value}</b></div>)}{model.confusion && <div className="confusion-wrap"><small>CONFUSION MATRIX · rows are actual labels</small><div className="table-scroll"><table className="data-table"><tbody>{model.confusion.map((row, i) => <tr key={i}>{row.map((value, j) => <td key={j} title={`${model.labels[i]} predicted ${model.labels[j]}`}>{value}</td>)}</tr>)}</tbody></table></div></div>}</div>)}</div>{result.excluded_empty_features.length > 0 && <p className="subtle-paragraph">Empty features excluded: {result.excluded_empty_features.join(", ")}</p>}<div className="alert subtle">{result.warning}</div></> : <EmptyState icon={Gauge} title="Train a baseline when you're ready" detail="Choose a meaningful target and review your feature selection before training." />}</Card></div></div>;
}

function Segments({ data, workspace, setError }) {
  const p = data.profile;
  const [columns, setColumns] = useState(p.numeric.filter((column) => !p.identifiers.includes(column)).slice(0, 5));
  const [method, setMethod] = useState("cluster");
  const [clusters, setClusters] = useState(3);
  const [contamination, setContamination] = useState(.03);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const run = async () => {
    setLoading(true);
    try { const response = await request("/segments", workspace, { method: "POST", body: JSON.stringify({ columns, clusters, contamination, method }) }); setResult(await response.json()); }
    catch (e) { setError(e.message); } finally { setLoading(false); }
  };
  useEffect(() => {
    if (columns.length >= 2) run();
  }, [method, clusters, contamination]);
  const toggle = (column) => setColumns((current) => current.includes(column) ? current.filter((value) => value !== column) : [...current, column]);
  return <div className="stack-lg"><PageTitle eyebrow="UNSUPERVISED EXPLORATION" title="Segments & anomalies" detail="Standardized numeric features support optional K-means clustering or Isolation Forest review." /><div className="studio-grid"><Card className="chart-controls" title="Analysis setup"><div className="seg-toggle"><button className={method === "cluster" ? "selected" : ""} onClick={() => setMethod("cluster")}>K-means segments</button><button className={method === "anomaly" ? "selected" : ""} onClick={() => setMethod("anomaly")}>Anomaly review</button></div><label className="field-label">Numeric features <span className="field-hint">({columns.length} selected)</span></label><div className="field-check-list">{p.numeric.map((column) => <label key={column}><input type="checkbox" checked={columns.includes(column)} onChange={() => toggle(column)} /><span>{column}</span></label>)}</div>{method === "cluster" ? <><label className="field-label">Number of segments <b className="field-value">{clusters}</b></label><input className="range-input" type="range" min="2" max="8" value={clusters} onChange={(e) => setClusters(Number(e.target.value))} /></> : <><label className="field-label">Expected anomaly fraction <b className="field-value">{(contamination * 100).toFixed(0)}%</b></label><input className="range-input" type="range" min=".01" max=".15" step=".01" value={contamination} onChange={(e) => setContamination(Number(e.target.value))} /></>}<button className="btn btn-primary full-btn" disabled={loading || columns.length < 2} onClick={run}>{loading ? <LoaderCircle className="spin" size={16} /> : <Activity size={16} />} {method === "cluster" ? "Find segments" : "Flag anomaly candidates"}</button>    </Card><Card className="result-card" title="Analysis result">{result ? method === "cluster" ? <><div className="result-metrics"><div><span>Records analyzed</span><b>{result.count.toLocaleString()}</b></div><div><span>Segments</span><b>{result.profiles.length}</b></div><div><span>Silhouette score</span><b>{result.score == null ? "—" : result.score.toFixed(3)}</b></div></div>{result.profiles.length > 0 && <div style={{ marginBottom: 16 }}><Chart data={result.profiles.map((pr, idx) => ({ name: `Cluster ${pr.cluster ?? idx}`, value: Number(pr.count || pr.records || pr.Size || Math.round(result.count / result.profiles.length)) }))} kind="donut" height={220} xLabel="Cluster" yLabel="Records" /></div>}<div className="table-scroll"><table className="data-table"><thead><tr>{Object.keys(result.profiles[0] || {}).map((column) => <th key={column}>{column}</th>)}</tr></thead><tbody>{result.profiles.map((row, i) => <tr key={i}>{Object.values(row).map((value, j) => <td key={j}>{String(value)}</td>)}</tr>)}</tbody></table></div><button className="btn btn-quiet export-inline" onClick={() => downloadExport("segments", workspace).catch((e) => setError(e.message))}><Download size={14} /> Export segmented rows</button></> : <><div className="result-metrics"><div><span>Flagged records</span><b>{result.count}</b></div><div><span>Features</span><b>{columns.length}</b></div></div><p className="subtle-paragraph">{result.warning}</p><div className="table-scroll"><DataTable rows={result.rows.slice(0, 15)} /></div><button className="btn btn-quiet export-inline" onClick={() => downloadExport("anomalies", workspace).catch((e) => setError(e.message))}><Download size={14} /> Export anomaly results</button></> : <EmptyState icon={Activity} title="Choose fields to begin" detail="At least two numeric features and 20 complete records are needed." />}</Card></div><div className="alert info"><CircleHelp size={16} /><span>Scaling and feature selection affect these results. Flags and clusters are exploratory review candidates, not proof of errors or meaningful business groups.</span></div></div>;
}

function DataTable({ rows }) {
  if (!rows.length) return <div className="inline-empty">No rows to display.</div>;
  const columns = Object.keys(rows[0]);
  return <table className="data-table"><thead><tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr></thead><tbody>{rows.map((row, i) => <tr key={i}>{columns.map((column) => <td key={column}>{row[column] == null ? "—" : String(row[column])}</td>)}</tr>)}</tbody></table>;
}

function TimeSeries({ data, workspace, setError }) {
  const p = data.profile;
  const [date, setDate] = useState(p.dates[0] || "");
  const [value, setValue] = useState(p.numeric[0] || "");
  const [frequency, setFrequency] = useState("MS");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const run = async () => {
    setLoading(true);
    try { const response = await request("/timeseries", workspace, { method: "POST", body: JSON.stringify({ date, value, frequency, aggregation: "mean" }) }); setResult(await response.json()); }
    catch (e) { setError(e.message); } finally { setLoading(false); }
  };
  useEffect(() => {
    if (date && value) run();
  }, [date, value, frequency]);
  return <div className="stack-lg"><PageTitle eyebrow="TIME-INDEXED EXPLORATION" title="Time series" detail="Aggregate a date-like field over time and explore a transparent trend baseline." />{!p.dates.length && <div className="alert info"><CircleHelp size={16} /><span>No date-like fields were detected. You can override a column type in Data explorer if it contains dates.</span></div>}<div className="studio-grid"><Card className="chart-controls" title="Series configuration"><label className="field-label">Date field</label><select value={date} onChange={(e) => setDate(e.target.value)}>{p.dates.map((column) => <option key={column}>{column}</option>)}</select><label className="field-label">Numeric measure</label><select value={value} onChange={(e) => setValue(e.target.value)}>{p.numeric.map((column) => <option key={column}>{column}</option>)}</select><label className="field-label">Aggregation period</label><select value={frequency} onChange={(e) => setFrequency(e.target.value)}><option value="D">Daily</option><option value="W">Weekly</option><option value="MS">Monthly</option><option value="QS">Quarterly</option><option value="YS">Yearly</option></select><button className="btn btn-primary full-btn" onClick={run} disabled={loading || !date || !value}>{loading ? <LoaderCircle className="spin" size={16} /> : <LineChartIcon size={16} />} Build time series</button></Card><Card className="chart-output" title="Aggregated trend">{result ? <><Chart data={result.series} kind="area" height={310} color="#55cbb2" /><div className="chart-output-foot"><span>{result.periods} time periods</span><span>Mean aggregation · no forecast implied</span></div></> : <EmptyState icon={Clock3} title="Your trend appears here" detail="Choose an inferred date field and numeric measure." />}</Card></div></div>;
}

function Reports({ data, workspace, setError }) {
  const [loading, setLoading] = useState("");
  const exports = [
    { kind: "pdf", label: "PDF analysis report", description: "Overview, quality summary, observations and column profile", icon: FileSpreadsheet, format: "PDF" },
    { kind: "csv", label: "Cleaned dataset", description: "Export the current working copy as CSV", icon: Table2, format: "CSV" },
    { kind: "xlsx", label: "Workbook & data dictionary", description: "Excel workbook with working data and schema", icon: FileSpreadsheet, format: "XLSX" },
    { kind: "json", label: "Analysis profile", description: "Structured profile, diagnostics and observations", icon: Database, format: "JSON" },
  ];
  const download = async (kind) => {
    setLoading(kind);
    try { await downloadExport(kind, workspace); }
    catch (e) { setError(e.message); } finally { setLoading(""); }
  };
  return <div className="stack-lg"><PageTitle eyebrow="TAKE YOUR ANALYSIS WITH YOU" title="Reports & exports" detail="Download the current dataset or a concise, evidence-based analysis report." /><div className="report-grid">{exports.map(({ kind, label, description, icon: Icon, format }) => <motion.div className="report-card" key={kind} whileHover={{ y: -3 }}><div className="report-icon"><Icon size={18} /></div><div className="report-format">{format}</div><h2>{label}</h2><p>{description}</p><button className="btn btn-quiet" onClick={() => download(kind)} disabled={loading === kind}>{loading === kind ? <LoaderCircle className="spin" size={15} /> : <Download size={15} />} Download file</button></motion.div>)}</div><Card title="Current dataset summary"><div className="report-summary"><div><span>Active file</span><b>{data.profile.filename || "Local dataset"}</b></div><div><span>Working records</span><b>{data.profile.rows.toLocaleString()}</b></div><div><span>Columns</span><b>{data.profile.columns}</b></div><div><span>Cleaning actions</span><b>{data.cleaning_history?.length || 0}</b></div></div><div className="report-note"><ShieldCheck size={15} /><span>Exports are generated locally from the current workspace. Original data remains available through Reset to original.</span></div></Card></div>;
}

export default App;
