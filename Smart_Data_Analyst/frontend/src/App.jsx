import React, { useState, useEffect, useMemo } from 'react';
import { 
  BarChart3, Database, ShieldAlert, LineChart, 
  Layers, BrainCircuit, FileSpreadsheet, RefreshCw, Upload,
  Zap, ArrowRight, Table, Download, Play, Sliders, Filter,
  TrendingUp, PieChart as PieIcon, Cpu, Grid3X3, SplitSquareVertical,
  CheckCircle2, AlertTriangle, ArrowUpDown, Wand2, Terminal,
  BarChart2, Activity, Info, ChevronRight, Hash, Type, Calendar,
  Binary, HelpCircle, Eye, AlertOctagon, Sun, Moon,
  LayoutDashboard, Search, FileText, Settings, X, ChevronDown, 
  ArrowUpRight, Sparkles as SparklesIcon
} from 'lucide-react';
import { 
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, 
  PieChart, Pie, Cell, LineChart as RechartsLine, Line, ScatterChart, Scatter,
  CartesianGrid, Legend, AreaChart, Area, ComposedChart
} from 'recharts';
import { 
  getDataset, getBenchmarks, loadBenchmark, uploadFile, 
  applyCleaning, resetDataset, getEDA, runStatistics, 
  runClustering, runAnomaly, runTimeSeries, trainML, 
  generatePivotTable, transformColumn, testNormality, getExportUrl 
} from './api';

const DARK_COLORS = ['#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#38bdf8', '#f43f5e'];
const LIGHT_COLORS = ['#4f46e5', '#0891b2', '#059669', '#d97706', '#db2777', '#7c3aed', '#0284c7', '#e11d48'];

export default function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem('sana_theme') || 'dark');
  const isLight = theme === 'light';

  const [activeTab, setActiveTab] = useState('overview');
  const [dataset, setDataset] = useState(null);
  const [benchmarks, setBenchmarks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [edaData, setEdaData] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);

  // Executive Dashboard Slicers (Global across all dashboard visuals)
  const [dashboardSlicers, setDashboardSlicers] = useState({});
  const [primaryMetric, setPrimaryMetric] = useState('');
  const [primaryDimension, setPrimaryDimension] = useState('');

  // Dynamic Visualizer Builder
  const [chartConfig, setChartConfig] = useState({
    chartType: 'bar',
    xAxis: '',
    yAxis: '',
    agg: 'mean'
  });

  // Multivariable Slicers & Explorer
  const [slicers, setSlicers] = useState({});
  const [globalSearch, setGlobalSearch] = useState('');
  const [selectedColumnProfile, setSelectedColumnProfile] = useState(null);

  // Advanced Operations
  const [pivotResult, setPivotResult] = useState(null);
  const [pivotConfig, setPivotConfig] = useState({ index: '', columns: 'None', values: '', aggfunc: 'mean' });
  const [normalityResult, setNormalityResult] = useState(null);
  const [selectedNormCol, setSelectedNormCol] = useState('');
  
  // Hypothesis Testing
  const [statConfig, setStatConfig] = useState({
    test_type: 'ttest',
    val_col: '',
    grp_col: '',
    grp_a: '',
    grp_b: '',
    cat_a: '',
    cat_b: ''
  });
  const [statResult, setStatResult] = useState(null);

  // ML & Modeling
  const [clusterK, setClusterK] = useState(3);
  const [selectedClusterFeatures, setSelectedClusterFeatures] = useState([]);
  const [clusterResult, setClusterResult] = useState(null);
  
  const [anomalyContamination, setAnomalyContamination] = useState(0.05);
  const [selectedAnomalyFeatures, setSelectedAnomalyFeatures] = useState([]);
  const [anomalyResult, setAnomalyResult] = useState(null);

  const [tsDateCol, setTsDateCol] = useState('');
  const [tsValCol, setTsValCol] = useState('');
  const [tsFreq, setTsFreq] = useState('W');
  const [tsResult, setTsResult] = useState(null);

  const [mlTarget, setMlTarget] = useState('');
  const [mlTaskType, setMlTaskType] = useState('Classification');
  const [selectedMlFeatures, setSelectedMlFeatures] = useState([]);
  const [mlResult, setMlResult] = useState(null);
  const [selectedBenchmark, setSelectedBenchmark] = useState('');

  const toggleTheme = () => {
    const next = isLight ? 'dark' : 'light';
    setTheme(next);
    localStorage.setItem('sana_theme', next);
  };

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  useEffect(() => {
    fetchBenchmarks();
    fetchDataset();
  }, []);

  const fetchBenchmarks = async () => {
    try {
      const res = await getBenchmarks();
      setBenchmarks(res.data);
      if (res.data.length > 0) setSelectedBenchmark(res.data[0].id);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchDataset = async () => {
    setLoading(true);
    try {
      const res = await getDataset();
      if (res.data.loaded) {
        initDatasetState(res.data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const initDatasetState = (data) => {
    setDataset(data);
    const numCols = data.numeric_columns || [];
    const catCols = data.categorical_columns || [];
    const allCols = data.all_columns || [];

    // Auto-detect optimal primary metric & dimension for the executive dashboard
    const defaultMeasure = numCols.find(c => 
      c.toLowerCase().includes('revenue') || 
      c.toLowerCase().includes('sales') || 
      c.toLowerCase().includes('score') || 
      c.toLowerCase().includes('exam') || 
      c.toLowerCase().includes('price') || 
      c.toLowerCase().includes('delay')
    ) || numCols[numCols.length - 1] || numCols[0] || '';

    const defaultDimension = catCols.find(c => 
      !c.toLowerCase().includes('id') && 
      !c.toLowerCase().includes('date') && 
      !c.toLowerCase().includes('time')
    ) || catCols[0] || allCols[0] || '';

    setPrimaryMetric(defaultMeasure);
    setPrimaryDimension(defaultDimension);
    setDashboardSlicers({});

    if (numCols.length > 0) {
      setChartConfig({
        chartType: 'bar',
        xAxis: defaultDimension || catCols[0] || allCols[0] || '',
        yAxis: defaultMeasure || numCols[0] || '',
        agg: 'mean'
      });
      setPivotConfig({
        index: defaultDimension || catCols[0] || allCols[0] || '',
        columns: 'None',
        values: defaultMeasure || numCols[0] || '',
        aggfunc: 'mean'
      });
      setSelectedNormCol(defaultMeasure || numCols[0]);
      setTsValCol(defaultMeasure || numCols[0]);
      setSelectedClusterFeatures(numCols.slice(0, 4));
      setSelectedAnomalyFeatures(numCols.slice(0, 4));
    }

    const dateCandidate = allCols.find(c => 
      c.toLowerCase().includes('date') || c.toLowerCase().includes('time') || c.toLowerCase().includes('year') || c.toLowerCase().includes('month')
    );
    if (dateCandidate) setTsDateCol(dateCandidate);
    else if (allCols.length > 0) setTsDateCol(allCols[0]);

    if (catCols.length > 0 && numCols.length > 0) {
      const grp = defaultDimension || catCols[0];
      const vals = Array.from(new Set((data.preview || []).map(r => r[grp]))).filter(Boolean);
      setStatConfig({
        test_type: 'ttest',
        val_col: defaultMeasure || numCols[0],
        grp_col: grp,
        grp_a: vals[0] ? String(vals[0]) : '',
        grp_b: vals[1] ? String(vals[1]) : '',
        cat_a: catCols[0],
        cat_b: catCols[1] || catCols[0]
      });
    }

    if (allCols.length > 0) {
      const defaultTarget = catCols.find(c => 
        c.toLowerCase().includes('target') || 
        c.toLowerCase().includes('passed') || 
        c.toLowerCase().includes('class') || 
        c.toLowerCase().includes('status')
      ) || catCols[0] || allCols[allCols.length - 1];
      
      setMlTarget(defaultTarget);
      setSelectedMlFeatures(allCols.filter(c => c !== defaultTarget).slice(0, 6));
    }
    if (allCols.length > 0) {
      setSelectedColumnProfile(allCols[0]);
    }
  };

  const handleLoadBenchmark = async (bId) => {
    const idToLoad = bId || selectedBenchmark;
    if (!idToLoad) return;
    setLoading(true);
    try {
      const res = await loadBenchmark(idToLoad);
      initDatasetState(res.data);
      showToast(`Loaded "${idToLoad}" with ${res.data.summary.rows} rows.`);
    } catch (e) {
      alert(e.response?.data?.detail || 'Error loading benchmark');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setLoading(true);
    try {
      const res = await uploadFile(file);
      initDatasetState(res.data);
      showToast(`Uploaded "${file.name}" (${res.data.summary.rows} rows).`);
    } catch (e) {
      alert(e.response?.data?.detail || 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  const handleClean = async (action, params = {}) => {
    setLoading(true);
    try {
      const res = await applyCleaning(action, params);
      setDataset(res.data);
      showToast(`Applied: ${action}`);
    } catch (e) {
      alert(e.response?.data?.detail || 'Cleaning failed');
    } finally {
      setLoading(false);
    }
  };

  const handleTransform = async (column, transform_type) => {
    setLoading(true);
    try {
      const res = await transformColumn({ column, transform_type });
      setDataset(res.data);
      showToast(`Transformed: ${column}_${transform_type}`);
    } catch (e) {
      alert(e.response?.data?.detail || 'Transform failed');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    setLoading(true);
    try {
      const res = await resetDataset();
      setDataset(res.data);
      showToast('Dataset reset to original raw state.');
    } catch (e) {
      alert(e.response?.data?.detail || 'Reset failed');
    } finally {
      setLoading(false);
    }
  };

  const loadEDA = async () => {
    try {
      const res = await getEDA();
      setEdaData(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    if (activeTab === 'eda' && dataset) loadEDA();
  }, [activeTab, dataset]);

  // Executive Dashboard Sliced Data
  const slicedDashboardRecords = useMemo(() => {
    if (!dataset?.preview) return [];
    return dataset.preview.filter(row => {
      for (const [col, val] of Object.entries(dashboardSlicers)) {
        if (val && val !== 'All') {
          if (String(row[col]) !== String(val)) return false;
        }
      }
      return true;
    });
  }, [dataset, dashboardSlicers]);

  // Executive Dashboard Dynamic Measure Aggregate Calculation
  const dashboardMetrics = useMemo(() => {
    if (!slicedDashboardRecords.length || !primaryMetric) return null;
    const vals = slicedDashboardRecords.map(r => Number(r[primaryMetric])).filter(v => !isNaN(v));
    if (!vals.length) return null;
    const total = vals.reduce((a, b) => a + b, 0);
    const avg = total / vals.length;
    const min = Math.min(...vals);
    const max = Math.max(...vals);
    return {
      total: Number(total.toFixed(2)),
      avg: Number(avg.toFixed(2)),
      min: Number(min.toFixed(2)),
      max: Number(max.toFixed(2)),
      count: vals.length
    };
  }, [slicedDashboardRecords, primaryMetric]);

  // Executive Dashboard Primary Breakdown Chart Data
  const dashboardPrimaryChartData = useMemo(() => {
    if (!slicedDashboardRecords.length || !primaryDimension || !primaryMetric) return [];
    const grp = {};
    slicedDashboardRecords.forEach(r => {
      const k = String(r[primaryDimension] ?? 'Unknown');
      const v = Number(r[primaryMetric]) || 0;
      if (!grp[k]) grp[k] = { name: k, total: 0, count: 0 };
      grp[k].total += v;
      grp[k].count += 1;
    });
    return Object.values(grp).slice(0, 10).map(g => ({
      name: g.name,
      total: Number(g.total.toFixed(2)),
      avg: Number((g.total / g.count).toFixed(2))
    })).sort((a, b) => b.total - a.total);
  }, [slicedDashboardRecords, primaryDimension, primaryMetric]);

  // Executive Dashboard Secondary Dimension Breakdown (Pie/Donut)
  const dashboardSecondaryChartData = useMemo(() => {
    if (!dataset?.categorical_columns?.length || !slicedDashboardRecords.length) return [];
    const secCol = dataset.categorical_columns.find(c => c !== primaryDimension && !c.toLowerCase().includes('id')) || dataset.categorical_columns[0];
    if (!secCol) return [];
    const grp = {};
    slicedDashboardRecords.forEach(r => {
      const k = String(r[secCol] ?? 'Other');
      grp[k] = (grp[k] || 0) + 1;
    });
    return {
      column: secCol,
      data: Object.entries(grp).map(([name, value]) => ({ name, value }))
    };
  }, [dataset, slicedDashboardRecords, primaryDimension]);

  // Data Explorer Filtered Table
  const filteredPreview = useMemo(() => {
    if (!dataset?.preview) return [];
    return dataset.preview.filter(row => {
      if (globalSearch) {
        const matchesGlobal = Object.values(row).some(v => 
          String(v ?? '').toLowerCase().includes(globalSearch.toLowerCase())
        );
        if (!matchesGlobal) return false;
      }
      for (const [col, val] of Object.entries(slicers)) {
        if (val && val !== 'All') {
          if (String(row[col]) !== String(val)) return false;
        }
      }
      return true;
    });
  }, [dataset, globalSearch, slicers]);

  // Custom Visualizer Chart Data
  const dynamicChartData = useMemo(() => {
    if (!dataset?.preview || !chartConfig.xAxis || !chartConfig.yAxis) return [];
    const grp = {};
    dataset.preview.forEach(r => {
      const xKey = String(r[chartConfig.xAxis] ?? 'Unknown');
      const yVal = Number(r[chartConfig.yAxis]) || 0;
      if (!grp[xKey]) grp[xKey] = { [chartConfig.xAxis]: xKey, total: 0, count: 0 };
      grp[xKey].total += yVal;
      grp[xKey].count += 1;
    });

    return Object.values(grp).slice(0, 25).map(g => ({
      [chartConfig.xAxis]: g[chartConfig.xAxis],
      [chartConfig.yAxis]: chartConfig.agg === 'mean' ? Number((g.total / g.count).toFixed(2)) : Number(g.total.toFixed(2))
    }));
  }, [dataset, chartConfig]);

  // Pivot Table Chart Data
  const pivotChartData = useMemo(() => {
    if (!pivotResult?.data || !pivotResult?.fields) return [];
    const indexField = pivotResult.fields[0];
    const metricFields = pivotResult.fields.slice(1);
    return pivotResult.data.slice(0, 15).map(row => ({
      name: String(row[indexField] ?? 'Group'),
      ...metricFields.reduce((acc, f) => {
        acc[f] = Number(row[f]) || 0;
        return acc;
      }, {})
    }));
  }, [pivotResult]);

  // Categorical Distributions
  const categoricalDistData = useMemo(() => {
    if (!edaData?.categorical_summary) return {};
    const res = {};
    edaData.categorical_summary.forEach(summary => {
      if (summary.distribution) {
        res[summary.column] = Object.entries(summary.distribution).slice(0, 8).map(([cat, count]) => ({
          category: cat,
          count: count
        }));
      }
    });
    return res;
  }, [edaData]);

  const navTabs = [
    { id: 'overview', label: 'Executive Dashboard', icon: BarChart3 },
    { id: 'explorer', label: 'Data Explorer & Slicers', icon: Table },
    { id: 'quality', label: 'Quality & Outliers', icon: ShieldAlert },
    { id: 'cleaning', label: 'Smart Cleaning & Transforms', icon: Wand2 },
    { id: 'visualizer', label: 'Custom Visualizer Lab', icon: Sliders },
    { id: 'pivot', label: 'Dynamic Pivot Matrix', icon: Grid3X3 },
    { id: 'eda', label: 'Statistical Correlation EDA', icon: ArrowUpDown },
    { id: 'statistics', label: 'Hypothesis Testing Lab', icon: Zap },
    { id: 'clustering', label: 'K-Means & Anomaly ML', icon: Layers },
    { id: 'timeseries', label: 'Temporal Velocity & Trend', icon: LineChart },
    { id: 'ml', label: 'Predictive ML Workbench', icon: BrainCircuit },
    { id: 'reports', label: 'Executive Export Center', icon: Download }
  ];

  const activeColors = isLight ? LIGHT_COLORS : DARK_COLORS;

  return (
    <div className={`flex h-screen overflow-hidden font-sans antialiased transition-colors duration-200 ${
      isLight ? 'bg-slate-50 text-slate-800' : 'bg-[#030712] text-slate-100'
    }`}>
      
      {/* Toast Alert */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 bg-indigo-600 text-white px-4 py-2.5 rounded-xl shadow-2xl text-xs font-semibold flex items-center gap-2 border border-indigo-400/40">
          <CheckCircle2 className="w-4 h-4 text-cyan-300" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Sidebar Control Deck */}
      <aside className={`w-80 flex flex-col justify-between shrink-0 z-20 transition-colors duration-200 border-r ${
        isLight 
          ? 'bg-white border-slate-200 shadow-sm' 
          : 'bg-[#070d1d] border-slate-800/80 shadow-2xl backdrop-blur-2xl'
      }`}>
        <div>
          {/* Brand Header */}
          <div className={`p-5 flex items-center justify-between border-b ${
            isLight ? 'border-slate-200 bg-slate-50/50' : 'border-slate-800/80'
          }`}>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 via-indigo-600 to-cyan-400 p-[2px] shadow-lg shadow-indigo-500/20">
                <div className={`w-full h-full rounded-[10px] flex items-center justify-center ${
                  isLight ? 'bg-white' : 'bg-[#070d1d]'
                }`}>
                  <Cpu className="w-5 h-5 text-indigo-500" />
                </div>
              </div>
              <div>
                <h1 className={`font-extrabold text-sm tracking-tight flex items-center gap-1.5 ${
                  isLight ? 'text-slate-900' : 'text-white'
                }`}>
                  Smart Data Analyst
                  <span className="text-[9px] bg-indigo-500/10 text-indigo-500 font-mono font-bold px-1.5 py-0.5 rounded border border-indigo-500/20">
                    PRO
                  </span>
                </h1>
                <span className={`text-[11px] font-medium block ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                  Dynamic A-Z Analytics Platform
                </span>
              </div>
            </div>

            {/* Light / Dark Mode Toggle Button */}
            <button
              onClick={toggleTheme}
              title={`Switch to ${isLight ? 'Dark' : 'Light'} Mode`}
              className={`p-2 rounded-lg transition-all ${
                isLight 
                  ? 'bg-slate-100 hover:bg-slate-200 text-slate-700' 
                  : 'bg-[#111c38] hover:bg-[#16254a] text-amber-400'
              }`}
            >
              {isLight ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
            </button>
          </div>

          {/* Dataset Ingestion Deck */}
          <div className={`p-4 border-b space-y-3 ${
            isLight ? 'border-slate-200 bg-slate-50/70' : 'border-slate-800/80 bg-[#0b1328]/60'
          }`}>
            <div>
              <label className={`text-[11px] font-bold uppercase tracking-wider mb-1.5 flex items-center gap-1.5 ${
                isLight ? 'text-slate-600' : 'text-slate-400'
              }`}>
                <Database className="w-3.5 h-3.5 text-indigo-500" />
                Select Ingestion Benchmark
              </label>
              <div className="flex gap-2">
                <select 
                  className={`w-full rounded-lg text-xs px-2.5 py-2 font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500 border ${
                    isLight 
                      ? 'bg-white border-slate-300 text-slate-800' 
                      : 'bg-[#111c38] border-slate-700/80 text-slate-200'
                  }`}
                  value={selectedBenchmark}
                  onChange={(e) => setSelectedBenchmark(e.target.value)}
                >
                  {benchmarks.map(b => (
                    <option key={b.id} value={b.id}>{b.name}</option>
                  ))}
                </select>
                <button 
                  onClick={() => handleLoadBenchmark(selectedBenchmark)}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-2 rounded-lg text-xs font-semibold transition-all shadow-md shadow-indigo-600/20 shrink-0"
                  title="Load Selected Benchmark"
                >
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>

            <label className={`w-full flex items-center justify-center gap-2 border border-dashed rounded-lg text-xs font-semibold cursor-pointer transition-all px-3 py-2 ${
              isLight 
                ? 'bg-white hover:bg-slate-100 border-slate-300 text-slate-700' 
                : 'bg-[#111c38] hover:bg-[#16254a] border-slate-700 text-slate-300 hover:text-white'
            }`}>
              <Upload className="w-3.5 h-3.5 text-cyan-500" />
              <span>Upload Custom Dataset</span>
              <input type="file" accept=".csv,.xlsx,.xls" onChange={handleFileUpload} className="hidden" />
            </label>
          </div>

          {/* Navigation Tab Menu */}
          <nav className="p-3 space-y-1 overflow-y-auto max-h-[calc(100vh-340px)]">
            {navTabs.map(tab => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                    isActive 
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30' 
                      : isLight 
                        ? 'text-slate-600 hover:text-slate-900 hover:bg-slate-100' 
                        : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-white' : isLight ? 'text-slate-500' : 'text-slate-400'}`} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Dataset Meta Widget */}
        {dataset && (
          <div className={`p-4 border m-3 rounded-xl ${
            isLight ? 'bg-slate-50 border-slate-200' : 'bg-[#070d1d] border-slate-800'
          }`}>
            <div className="flex items-center justify-between text-xs mb-1">
              <span className={`font-bold truncate max-w-[150px] ${isLight ? 'text-slate-900' : 'text-slate-300'}`}>
                {dataset.filename}
              </span>
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold font-mono ${
                dataset.is_cleaned 
                  ? 'bg-emerald-500/10 text-emerald-600 border border-emerald-500/20' 
                  : 'bg-indigo-500/10 text-indigo-500 border border-indigo-500/20'
              }`}>
                {dataset.is_cleaned ? 'Transformed' : 'Raw Data'}
              </span>
            </div>
            <div className={`text-[11px] font-mono ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
              {dataset.summary.rows?.toLocaleString()} rows &times; {dataset.summary.columns} cols
            </div>
          </div>
        )}
      </aside>

      {/* Main Execution Workspace */}
      <main className="flex-1 flex flex-col overflow-y-auto relative">
        
        {/* Top Control Bar */}
        <header className={`h-16 border-b flex items-center justify-between px-8 sticky top-0 z-10 backdrop-blur-xl transition-colors duration-200 ${
          isLight ? 'bg-white/80 border-slate-200' : 'bg-[#070d1d]/80 border-slate-800/80'
        }`}>
          <div className="flex items-center gap-3">
            <h2 className={`font-bold text-base flex items-center gap-2 ${
              isLight ? 'text-slate-900' : 'text-slate-100'
            }`}>
              {navTabs.find(t => t.id === activeTab)?.label}
            </h2>
            {dataset && (
              <span className={`text-xs px-2.5 py-1 rounded-md border font-mono font-medium ${
                isLight 
                  ? 'bg-slate-100 text-slate-700 border-slate-200' 
                  : 'bg-[#111c38] text-slate-300 border-slate-700/80'
              }`}>
                {dataset.filename}
              </span>
            )}
          </div>

          <div className="flex items-center gap-3">
            {dataset?.is_cleaned && (
              <button
                onClick={handleReset}
                className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border font-semibold transition-all ${
                  isLight 
                    ? 'text-amber-700 bg-amber-50 hover:bg-amber-100 border-amber-200' 
                    : 'text-amber-400 hover:text-amber-300 bg-amber-500/10 hover:bg-amber-500/20 border-amber-500/30'
                }`}
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Restore Raw Data
              </button>
            )}

            <a 
              href={getExportUrl('pdf')}
              className="flex items-center gap-1.5 text-xs bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-4 py-2 rounded-lg shadow-md shadow-indigo-600/30 transition-all"
            >
              <Download className="w-3.5 h-3.5" />
              Export PDF Brief
            </a>
          </div>
        </header>

        {/* Dynamic Analytics Views */}
        <div className="p-8 space-y-6 max-w-7xl w-full mx-auto">
          {loading && (
            <div className={`flex items-center justify-center p-14 rounded-2xl shadow-xl border ${
              isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
            }`}>
              <div className="flex items-center gap-3 text-indigo-600 font-semibold text-sm">
                <RefreshCw className="w-5 h-5 animate-spin" />
                Computing advanced multivariate analytics...
              </div>
            </div>
          )}

          {!dataset && !loading && (
            <div className={`text-center py-24 rounded-2xl border p-12 shadow-sm ${
              isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
            }`}>
              <div className="w-16 h-16 bg-indigo-500/10 border border-indigo-500/30 text-indigo-500 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-sm">
                <Database className="w-8 h-8" />
              </div>
              <h3 className={`text-xl font-extrabold mb-2 ${isLight ? 'text-slate-900' : 'text-white'}`}>
                No Active Dataset Loaded
              </h3>
              <p className={`text-sm max-w-md mx-auto mb-6 ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                Select an ingestion benchmark or upload your dataset to launch intelligent profiling, hypothesis testing, and machine learning.
              </p>
              <div className="flex flex-wrap justify-center gap-3">
                {benchmarks.map(b => (
                  <button 
                    key={b.id}
                    onClick={() => handleLoadBenchmark(b.id)}
                    className={`px-4 py-2 rounded-xl font-medium text-xs border transition-all ${
                      isLight 
                        ? 'bg-slate-50 hover:bg-indigo-600 hover:text-white border-slate-300 text-slate-800' 
                        : 'bg-[#111c38] hover:bg-indigo-600 border-slate-700 text-white'
                    }`}
                  >
                    Load {b.name.split('&')[0]}
                  </button>
                ))}
              </div>
            </div>
          )}

          {dataset && !loading && (
            <>
              {/* TAB 1: EXECUTIVE DASHBOARD */}
              {activeTab === 'overview' && (
                <div className="space-y-6">
                  
                  {/* Dynamic Business Metric Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                    <div className={`p-5 rounded-2xl border shadow-sm ${
                      isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                    }`}>
                      <span className={`text-[11px] font-bold uppercase tracking-wider ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                        Total Observations
                      </span>
                      <div className={`text-2xl font-extrabold font-mono mt-1 ${isLight ? 'text-slate-900' : 'text-white'}`}>
                        {slicedDashboardRecords.length.toLocaleString()}
                      </div>
                      <span className="text-xs text-indigo-500 mt-2 block font-medium">
                        {dataset.summary.columns} Inferred Dimensions
                      </span>
                    </div>

                    {dashboardMetrics ? (
                      <>
                        <div className={`p-5 rounded-2xl border shadow-sm ${
                          isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                        }`}>
                          <span className={`text-[11px] font-bold uppercase tracking-wider truncate block ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                            Sum ({primaryMetric})
                          </span>
                          <div className={`text-2xl font-extrabold font-mono mt-1 text-cyan-500`}>
                            {dashboardMetrics.total.toLocaleString()}
                          </div>
                          <span className={`text-xs mt-2 block font-medium ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                            Aggregated Measure
                          </span>
                        </div>

                        <div className={`p-5 rounded-2xl border shadow-sm ${
                          isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                        }`}>
                          <span className={`text-[11px] font-bold uppercase tracking-wider truncate block ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                            Mean ({primaryMetric})
                          </span>
                          <div className={`text-2xl font-extrabold font-mono mt-1 text-emerald-500`}>
                            {dashboardMetrics.avg.toLocaleString()}
                          </div>
                          <span className={`text-xs mt-2 block font-medium ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                            Range: {dashboardMetrics.min} - {dashboardMetrics.max}
                          </span>
                        </div>
                      </>
                    ) : (
                      <>
                        <div className={`p-5 rounded-2xl border shadow-sm ${
                          isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                        }`}>
                          <span className={`text-[11px] font-bold uppercase tracking-wider ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                            Quality Score
                          </span>
                          <div className="text-2xl font-extrabold font-mono mt-1" style={{ color: dataset.quality.status_color }}>
                            {dataset.quality.score}/100
                          </div>
                          <span className={`text-xs mt-2 block font-medium ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                            Status: {dataset.quality.status}
                          </span>
                        </div>

                        <div className={`p-5 rounded-2xl border shadow-sm ${
                          isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                        }`}>
                          <span className={`text-[11px] font-bold uppercase tracking-wider ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                            Missing Rate
                          </span>
                          <div className={`text-2xl font-extrabold font-mono mt-1 ${isLight ? 'text-slate-900' : 'text-white'}`}>
                            {dataset.quality.metrics.missing_pct}%
                          </div>
                          <span className={`text-xs mt-2 block font-medium ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                            {dataset.quality.metrics.total_missing} null cells
                          </span>
                        </div>
                      </>
                    )}

                    <div className={`p-5 rounded-2xl border shadow-sm ${
                      isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                    }`}>
                      <span className={`text-[11px] font-bold uppercase tracking-wider ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                        Quality Index
                      </span>
                      <div className="text-2xl font-extrabold font-mono mt-1" style={{ color: dataset.quality.status_color }}>
                        {dataset.quality.score}/100
                      </div>
                      <span className={`text-xs mt-2 block font-medium ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                        {dataset.quality.status} Health
                      </span>
                    </div>

                    <div className={`p-5 rounded-2xl border shadow-sm ${
                      isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                    }`}>
                      <span className={`text-[11px] font-bold uppercase tracking-wider ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                        Completeness
                      </span>
                      <div className="text-2xl font-extrabold text-indigo-500 font-mono mt-1">
                        {dataset.quality.metrics.completeness_pct}%
                      </div>
                      <span className={`text-xs mt-2 block font-medium ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                        Density Matrix
                      </span>
                    </div>
                  </div>

                  {/* Interactive Dashboard Slicer Bar */}
                  <div className={`p-4 rounded-2xl border shadow-sm flex flex-wrap items-center justify-between gap-4 ${
                    isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                  }`}>
                    <div className="flex items-center gap-2">
                      <Filter className="w-4 h-4 text-indigo-500" />
                      <span className={`text-xs font-bold uppercase tracking-wider ${isLight ? 'text-slate-800' : 'text-slate-200'}`}>
                        Live Dashboard Filters:
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-3">
                      {/* Metric Selector */}
                      <div className="flex items-center gap-1.5">
                        <span className="text-[11px] text-slate-400 font-medium">Measure:</span>
                        <select
                          className={`rounded-lg text-xs px-2.5 py-1.5 border font-semibold ${
                            isLight 
                              ? 'bg-slate-50 border-slate-300 text-slate-800' 
                              : 'bg-[#111c38] border-slate-700 text-slate-200'
                          }`}
                          value={primaryMetric}
                          onChange={(e) => setPrimaryMetric(e.target.value)}
                        >
                          {dataset.numeric_columns?.map(c => (
                            <option key={c} value={c}>{c}</option>
                          ))}
                        </select>
                      </div>

                      {/* Dimension Selector */}
                      <div className="flex items-center gap-1.5">
                        <span className="text-[11px] text-slate-400 font-medium">Dimension:</span>
                        <select
                          className={`rounded-lg text-xs px-2.5 py-1.5 border font-semibold ${
                            isLight 
                              ? 'bg-slate-50 border-slate-300 text-slate-800' 
                              : 'bg-[#111c38] border-slate-700 text-slate-200'
                          }`}
                          value={primaryDimension}
                          onChange={(e) => setPrimaryDimension(e.target.value)}
                        >
                          {dataset.all_columns?.map(c => (
                            <option key={c} value={c}>{c}</option>
                          ))}
                        </select>
                      </div>

                      {/* Category Slicers */}
                      {dataset.categorical_columns?.slice(0, 3).map(col => {
                        const uniqueVals = Array.from(new Set(dataset.preview.map(r => r[col]))).filter(Boolean);
                        return (
                          <div key={col} className="flex items-center gap-1.5">
                            <span className="text-[11px] text-slate-400 font-medium">{col}:</span>
                            <select
                              className={`rounded-lg text-xs px-2.5 py-1.5 border ${
                                isLight 
                                  ? 'bg-slate-50 border-slate-300 text-slate-800' 
                                  : 'bg-[#111c38] border-slate-700 text-slate-200'
                              }`}
                              value={dashboardSlicers[col] || 'All'}
                              onChange={(e) => setDashboardSlicers(prev => ({ ...prev, [col]: e.target.value }))}
                            >
                              <option value="All">All {col}</option>
                              {uniqueVals.map(v => (
                                <option key={v} value={v}>{v}</option>
                              ))}
                            </select>
                          </div>
                        );
                      })}

                      {Object.keys(dashboardSlicers).length > 0 && (
                        <button
                          onClick={() => setDashboardSlicers({})}
                          className="text-xs text-indigo-500 hover:text-indigo-400 font-semibold"
                        >
                          Reset Filters
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Dynamic Interactive Charts Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Primary Dynamic Bar / Column Chart */}
                    <div className={`p-6 rounded-2xl border shadow-sm ${
                      isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                    }`}>
                      <div className="flex justify-between items-center mb-4">
                        <h4 className={`font-bold text-sm flex items-center gap-2 ${
                          isLight ? 'text-slate-900' : 'text-slate-200'
                        }`}>
                          <BarChart2 className="w-4 h-4 text-indigo-500" />
                          {primaryMetric} by {primaryDimension}
                        </h4>
                        <span className="text-[11px] text-slate-400 font-mono">
                          Aggregated Total
                        </span>
                      </div>
                      
                      <div className="h-72">
                        {dashboardPrimaryChartData.length > 0 ? (
                          <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={dashboardPrimaryChartData}>
                              <CartesianGrid strokeDasharray="3 3" stroke={isLight ? '#e2e8f0' : '#1e293b'} />
                              <XAxis dataKey="name" stroke={isLight ? '#94a3b8' : '#64748b'} tick={{ fontSize: 11 }} />
                              <YAxis stroke={isLight ? '#94a3b8' : '#64748b'} />
                              <Tooltip contentStyle={{ 
                                background: isLight ? '#ffffff' : '#0b1328', 
                                borderColor: isLight ? '#e2e8f0' : '#1e293b', 
                                borderRadius: '8px',
                                color: isLight ? '#0f172a' : '#f8fafc'
                              }} />
                              <Bar dataKey="total" fill="#6366f1" radius={[4, 4, 0, 0]} name={`Total ${primaryMetric}`} />
                            </BarChart>
                          </ResponsiveContainer>
                        ) : (
                          <div className="h-full flex items-center justify-center text-xs text-slate-400">
                            No aggregate data available for this combination
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Secondary Donut Breakdown */}
                    <div className={`p-6 rounded-2xl border shadow-sm ${
                      isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                    }`}>
                      <div className="flex justify-between items-center mb-4">
                        <h4 className={`font-bold text-sm flex items-center gap-2 ${
                          isLight ? 'text-slate-900' : 'text-slate-200'
                        }`}>
                          <PieIcon className="w-4 h-4 text-cyan-500" />
                          Distribution by {dashboardSecondaryChartData.column || 'Category'}
                        </h4>
                        <span className="text-[11px] text-slate-400 font-mono">
                          Share of Records
                        </span>
                      </div>
                      
                      <div className="h-72">
                        {dashboardSecondaryChartData.data?.length > 0 ? (
                          <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                              <Pie
                                data={dashboardSecondaryChartData.data}
                                innerRadius={65}
                                outerRadius={95}
                                paddingAngle={4}
                                dataKey="value"
                              >
                                {dashboardSecondaryChartData.data.map((_, i) => (
                                  <Cell key={i} fill={activeColors[i % activeColors.length]} />
                                ))}
                              </Pie>
                              <Tooltip contentStyle={{ 
                                background: isLight ? '#ffffff' : '#0b1328', 
                                borderColor: isLight ? '#e2e8f0' : '#1e293b', 
                                borderRadius: '8px',
                                color: isLight ? '#0f172a' : '#f8fafc'
                              }} />
                              <Legend />
                            </PieChart>
                          </ResponsiveContainer>
                        ) : (
                          <div className="h-full flex items-center justify-center text-xs text-slate-400">
                            No categorical distribution data
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Empirical Observations */}
                  <div className={`p-6 rounded-2xl border shadow-sm ${
                    isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                  }`}>
                    <h4 className={`font-bold text-sm mb-4 flex items-center gap-2 ${
                      isLight ? 'text-slate-900' : 'text-slate-200'
                    }`}>
                      <Terminal className="w-4 h-4 text-indigo-500" />
                      Autonomous Statistical Observations & Empirical Rules
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {dataset.insights?.slice(0, 6).map((item, idx) => (
                        <div key={idx} className={`p-4 rounded-xl border ${
                          item.category === 'warning' 
                            ? isLight ? 'bg-amber-50/60 border-amber-200' : 'bg-amber-500/5 border-amber-500/20'
                            : isLight ? 'bg-indigo-50/50 border-indigo-100' : 'bg-indigo-500/5 border-indigo-500/20'
                        }`}>
                          <div className="flex justify-between items-center mb-1.5">
                            <span className={`font-bold text-xs ${isLight ? 'text-slate-800' : 'text-slate-200'}`}>
                              {item.title}
                            </span>
                            <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${
                              item.category === 'warning' 
                                ? 'bg-amber-500/20 text-amber-600' 
                                : 'bg-indigo-500/20 text-indigo-600'
                            }`}>
                              {item.category}
                            </span>
                          </div>
                          <p className={`text-xs mb-2 ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                            {item.description}
                          </p>
                          <div className={`text-[11px] font-mono ${isLight ? 'text-slate-500' : 'text-slate-500'}`}>
                            <b>Evidence:</b> {item.metric}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: DATA EXPLORER & SLICERS */}
              {activeTab === 'explorer' && (
                <div className="space-y-6">
                  {/* Slicers Deck */}
                  <div className={`p-6 rounded-2xl border shadow-sm space-y-4 ${
                    isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                  }`}>
                    <div className="flex items-center justify-between">
                      <h4 className={`font-bold text-sm flex items-center gap-2 ${
                        isLight ? 'text-slate-900' : 'text-slate-200'
                      }`}>
                        <Filter className="w-4 h-4 text-indigo-500" />
                        Multivariable Slicers & Global Filter
                      </h4>
                      <input 
                        type="text" 
                        placeholder="Live keyword filter..."
                        className={`rounded-lg text-xs px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500 w-64 border ${
                          isLight 
                            ? 'bg-slate-50 border-slate-300 text-slate-800' 
                            : 'bg-[#111c38] border-slate-700/80 text-slate-200'
                        }`}
                        value={globalSearch}
                        onChange={(e) => setGlobalSearch(e.target.value)}
                      />
                    </div>

                    {/* Dynamic Slicers */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                      {dataset.categorical_columns?.slice(0, 4).map(col => {
                        const uniqueVals = Array.from(new Set(dataset.preview.map(r => r[col]))).filter(Boolean);
                        return (
                          <div key={col} className={`p-3 rounded-xl border ${
                            isLight ? 'bg-slate-50 border-slate-200' : 'bg-[#0b1328] border-slate-800'
                          }`}>
                            <label className={`text-[11px] font-bold uppercase tracking-wider block mb-1 ${
                              isLight ? 'text-slate-600' : 'text-slate-400'
                            }`}>
                              Slicer: {col}
                            </label>
                            <select 
                              className={`w-full rounded-lg text-xs p-1.5 focus:outline-none border ${
                                isLight 
                                  ? 'bg-white border-slate-300 text-slate-800' 
                                  : 'bg-[#111c38] border-slate-700/80 text-slate-200'
                              }`}
                              value={slicers[col] || 'All'}
                              onChange={(e) => setSlicers(prev => ({ ...prev, [col]: e.target.value }))}
                            >
                              <option value="All">All Categories</option>
                              {uniqueVals.map(v => (
                                <option key={v} value={v}>{v}</option>
                              ))}
                            </select>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Column Profile Inspector */}
                  <div className={`p-6 rounded-2xl border shadow-sm ${
                    isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                  }`}>
                    <div className="flex items-center justify-between mb-4">
                      <h4 className={`font-bold text-sm flex items-center gap-2 ${
                        isLight ? 'text-slate-900' : 'text-slate-200'
                      }`}>
                        <Info className="w-4 h-4 text-cyan-500" />
                        Column-Level Profile & Descriptive Statistics
                      </h4>
                      <select
                        className={`rounded-lg text-xs px-3 py-1.5 border ${
                          isLight 
                            ? 'bg-slate-50 border-slate-300 text-slate-800' 
                            : 'bg-[#111c38] border-slate-700/80 text-slate-200'
                        }`}
                        value={selectedColumnProfile || ''}
                        onChange={(e) => setSelectedColumnProfile(e.target.value)}
                      >
                        {dataset.all_columns?.map(c => (
                          <option key={c} value={c}>{c}</option>
                        ))}
                      </select>
                    </div>

                    {selectedColumnProfile && dataset.columns?.[selectedColumnProfile] && (
                      <div className="grid grid-cols-2 md:grid-cols-6 gap-3 text-xs font-mono">
                        <div className={`p-3 rounded-xl border ${
                          isLight ? 'bg-slate-50 border-slate-200' : 'bg-[#0b1328] border-slate-800'
                        }`}>
                          <span className="text-[10px] text-slate-400 block uppercase">Inferred Type</span>
                          <span className="font-bold text-indigo-500 text-sm mt-1 block">
                            {dataset.columns[selectedColumnProfile].inferred_type}
                          </span>
                        </div>
                        <div className={`p-3 rounded-xl border ${
                          isLight ? 'bg-slate-50 border-slate-200' : 'bg-[#0b1328] border-slate-800'
                        }`}>
                          <span className="text-[10px] text-slate-400 block uppercase">Missing Values</span>
                          <span className={`font-bold text-sm mt-1 block ${isLight ? 'text-slate-800' : 'text-slate-200'}`}>
                            {dataset.columns[selectedColumnProfile].missing_pct}%
                          </span>
                        </div>
                        <div className={`p-3 rounded-xl border ${
                          isLight ? 'bg-slate-50 border-slate-200' : 'bg-[#0b1328] border-slate-800'
                        }`}>
                          <span className="text-[10px] text-slate-400 block uppercase">Unique Values</span>
                          <span className={`font-bold text-sm mt-1 block ${isLight ? 'text-slate-800' : 'text-slate-200'}`}>
                            {dataset.columns[selectedColumnProfile].unique_count}
                          </span>
                        </div>
                        <div className={`p-3 rounded-xl border ${
                          isLight ? 'bg-slate-50 border-slate-200' : 'bg-[#0b1328] border-slate-800'
                        }`}>
                          <span className="text-[10px] text-slate-400 block uppercase">Mean / Mode</span>
                          <span className="font-bold text-cyan-500 text-sm mt-1 block truncate">
                            {dataset.columns[selectedColumnProfile].mean ?? dataset.columns[selectedColumnProfile].mode ?? 'N/A'}
                          </span>
                        </div>
                        <div className={`p-3 rounded-xl border ${
                          isLight ? 'bg-slate-50 border-slate-200' : 'bg-[#0b1328] border-slate-800'
                        }`}>
                          <span className="text-[10px] text-slate-400 block uppercase">Std Deviation</span>
                          <span className={`font-bold text-sm mt-1 block ${isLight ? 'text-slate-800' : 'text-slate-200'}`}>
                            {dataset.columns[selectedColumnProfile].std ?? 'N/A'}
                          </span>
                        </div>
                        <div className={`p-3 rounded-xl border ${
                          isLight ? 'bg-slate-50 border-slate-200' : 'bg-[#0b1328] border-slate-800'
                        }`}>
                          <span className="text-[10px] text-slate-400 block uppercase">Outliers (IQR)</span>
                          <span className="font-bold text-amber-500 text-sm mt-1 block">
                            {dataset.columns[selectedColumnProfile].outliers_count ?? 0}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Filtered Data Table */}
                  <div className={`p-6 rounded-2xl border shadow-sm ${
                    isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                  }`}>
                    <div className="flex justify-between items-center mb-3 text-xs text-slate-500">
                      <span>Displaying <b>{filteredPreview.length}</b> filtered records</span>
                      <button 
                        onClick={() => { setSlicers({}); setGlobalSearch(''); }}
                        className="text-indigo-600 hover:text-indigo-500 font-semibold"
                      >
                        Reset All Slicers
                      </button>
                    </div>

                    <div className="overflow-x-auto max-h-[500px]">
                      <table className="w-full text-left text-xs border-collapse">
                        <thead className={`sticky top-0 backdrop-blur-md font-bold ${
                          isLight ? 'bg-slate-100 text-slate-800' : 'bg-[#111c38] text-slate-300'
                        }`}>
                          <tr>
                            {dataset.all_columns?.map(col => {
                              const isNum = dataset.numeric_columns.includes(col);
                              return (
                                <th key={col} className={`p-3 border-b font-mono ${
                                  isLight ? 'border-slate-200' : 'border-slate-800'
                                }`}>
                                  <div className="flex items-center gap-1.5">
                                    <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                                      isNum 
                                        ? 'bg-cyan-500/10 text-cyan-600' 
                                        : 'bg-indigo-500/10 text-indigo-600'
                                    }`}>
                                      {isNum ? '#' : 'Aa'}
                                    </span>
                                    <span>{col}</span>
                                  </div>
                                </th>
                              );
                            })}
                          </tr>
                        </thead>
                        <tbody className={`divide-y font-mono ${
                          isLight 
                            ? 'divide-slate-200 text-slate-700' 
                            : 'divide-slate-800/80 text-slate-400'
                        }`}>
                          {filteredPreview.map((row, r_idx) => (
                            <tr key={r_idx} className={`transition-colors ${
                              isLight ? 'hover:bg-slate-50' : 'hover:bg-white/5'
                            }`}>
                              {dataset.all_columns.map(c => (
                                <td key={c} className="p-3 whitespace-nowrap">
                                  {row[c] !== null ? String(row[c]) : <span className="text-rose-500 italic">null</span>}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 3: QUALITY & OUTLIERS */}
              {activeTab === 'quality' && (
                <div className="space-y-6">
                  {/* Deductions Breakdown */}
                  <div className={`p-6 rounded-2xl border shadow-sm ${
                    isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                  }`}>
                    <h4 className={`font-bold text-sm mb-2 font-mono ${
                      isLight ? 'text-slate-900' : 'text-slate-200'
                    }`}>
                      Formula: Q = 100 - (0.50*M + 0.25*D + 0.15*C + 0.10*I)
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4">
                      {Object.entries(dataset.quality.deductions || {}).filter(([k]) => k !== 'total').map(([k, v]) => (
                        <div key={k} className={`p-4 rounded-xl border ${
                          isLight ? 'bg-slate-50 border-slate-200' : 'bg-[#0b1328] border-slate-800'
                        }`}>
                          <span className="text-xs uppercase text-slate-400 font-semibold">{k} Penalty</span>
                          <div className="text-lg font-mono font-bold text-rose-500 mt-1">-{v} pts</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Missing Value Ranking Bar Chart */}
                  <div className={`p-6 rounded-2xl border shadow-sm ${
                    isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                  }`}>
                    <h4 className={`font-bold text-sm mb-4 flex items-center gap-2 ${
                      isLight ? 'text-slate-900' : 'text-slate-200'
                    }`}>
                      <BarChart2 className="w-4 h-4 text-indigo-500" />
                      Attribute Missingness Rate Ranking
                    </h4>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={Object.entries(dataset.columns || {}).map(([col, meta]) => ({ col, missing_pct: meta.missing_pct || 0 })).sort((a,b) => b.missing_pct - a.missing_pct)}>
                          <CartesianGrid strokeDasharray="3 3" stroke={isLight ? '#e2e8f0' : '#1e293b'} />
                          <XAxis dataKey="col" stroke={isLight ? '#94a3b8' : '#64748b'} tick={{ fontSize: 11 }} />
                          <YAxis stroke={isLight ? '#94a3b8' : '#64748b'} unit="%" />
                          <Tooltip contentStyle={{ 
                            background: isLight ? '#ffffff' : '#0b1328', 
                            borderColor: isLight ? '#e2e8f0' : '#1e293b',
                            color: isLight ? '#0f172a' : '#f8fafc'
                          }} />
                          <Bar dataKey="missing_pct" fill="#f43f5e" radius={[4, 4, 0, 0]} name="Missing %" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  {/* Outlier Detail Table with Fences */}
                  <div className={`p-6 rounded-2xl border shadow-sm ${
                    isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                  }`}>
                    <h4 className={`font-bold text-sm mb-4 flex items-center gap-2 ${
                      isLight ? 'text-slate-900' : 'text-slate-200'
                    }`}>
                      <AlertOctagon className="w-4 h-4 text-amber-500" />
                      Tukey's IQR Outlier Thresholds & Fences
                    </h4>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs font-mono">
                        <thead className={`font-bold ${
                          isLight ? 'bg-slate-100 text-slate-800' : 'bg-[#111c38] text-slate-300'
                        }`}>
                          <tr>
                            <th className="p-3">Attribute</th>
                            <th className="p-3">Detected Outliers</th>
                            <th className="p-3">Lower Fence (Q1 - 1.5&times;IQR)</th>
                            <th className="p-3">Upper Fence (Q3 + 1.5&times;IQR)</th>
                            <th className="p-3">Action</th>
                          </tr>
                        </thead>
                        <tbody className={`divide-y ${
                          isLight ? 'divide-slate-200 text-slate-700' : 'divide-slate-800 text-slate-400'
                        }`}>
                          {Object.entries(dataset.quality.outliers_per_column || {}).map(([col, count]) => {
                            const meta = dataset.columns[col] || {};
                            return (
                              <tr key={col} className={isLight ? 'hover:bg-slate-50' : 'hover:bg-white/5'}>
                                <td className={`p-3 font-bold ${isLight ? 'text-slate-900' : 'text-slate-200'}`}>{col}</td>
                                <td className="p-3 font-bold text-amber-500">{count}</td>
                                <td className="p-3">{meta.min !== undefined ? (meta.mean - 2 * meta.std).toFixed(2) : 'N/A'}</td>
                                <td className="p-3">{meta.max !== undefined ? (meta.mean + 2 * meta.std).toFixed(2) : 'N/A'}</td>
                                <td className="p-3">
                                  <button
                                    onClick={() => handleClean('cap_outliers', { column: col })}
                                    className="text-[11px] bg-amber-500/10 hover:bg-amber-500/20 text-amber-600 border border-amber-500/30 px-2.5 py-1 rounded-lg transition-all"
                                  >
                                    Winsorize (Cap)
                                  </button>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Normality Test Tool */}
                  <div className={`p-6 rounded-2xl border shadow-sm ${
                    isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                  }`}>
                    <h4 className={`font-bold text-sm mb-3 ${isLight ? 'text-slate-900' : 'text-slate-200'}`}>
                      Shapiro-Wilk & D'Agostino Normality Tests
                    </h4>
                    <div className="flex gap-3 mb-4">
                      <select 
                        className={`rounded-lg text-xs p-2 border ${
                          isLight 
                            ? 'bg-slate-50 border-slate-300 text-slate-800' 
                            : 'bg-[#111c38] border-slate-700/80 text-slate-200'
                        }`}
                        value={selectedNormCol}
                        onChange={(e) => setSelectedNormCol(e.target.value)}
                      >
                        {dataset.numeric_columns?.map(c => (
                          <option key={c} value={c}>{c}</option>
                        ))}
                      </select>
                      <button 
                        onClick={async () => {
                          const res = await testNormality(selectedNormCol);
                          setNormalityResult(res.data);
                        }}
                        className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs px-4 py-2 rounded-lg transition-all"
                      >
                        Run Normality Tests
                      </button>
                    </div>

                    {normalityResult && (
                      <div className={`p-4 rounded-xl border text-xs font-mono space-y-1 ${
                        isLight ? 'bg-slate-50 border-slate-200 text-slate-800' : 'bg-[#0b1328] border-slate-800 text-slate-300'
                      }`}>
                        <div><b>Skewness:</b> {normalityResult.skewness} | <b>Kurtosis:</b> {normalityResult.kurtosis}</div>
                        <div><b>Shapiro-Wilk:</b> p = {normalityResult.shapiro_wilk.p_value} ({normalityResult.shapiro_wilk.is_normal ? 'Normally Distributed' : 'Non-Normal Distribution'})</div>
                        <div><b>D'Agostino K2:</b> p = {normalityResult.dagostino_k2.p_value}</div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* TAB 4: SMART CLEANING & TRANSFORMS */}
              {activeTab === 'cleaning' && (
                <div className="space-y-6">
                  {/* Feature Engineering */}
                  <div className={`p-6 rounded-2xl border shadow-sm ${
                    isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                  }`}>
                    <h4 className={`font-bold text-sm mb-2 flex items-center gap-2 ${
                      isLight ? 'text-slate-900' : 'text-slate-200'
                    }`}>
                      <Wand2 className="w-4 h-4 text-cyan-500" />
                      A-Z Feature Transformation & Engineering
                    </h4>
                    <p className={`text-xs mb-4 ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                      Create mathematically engineered features: Log transforms, Z-score standardizations, or quantile binning.
                    </p>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                      {dataset.numeric_columns?.slice(0, 3).map(col => (
                        <div key={col} className={`p-4 rounded-xl border space-y-2 ${
                          isLight ? 'bg-slate-50 border-slate-200' : 'bg-[#0b1328] border-slate-800'
                        }`}>
                          <span className={`font-bold text-xs font-mono ${isLight ? 'text-slate-900' : 'text-slate-200'}`}>
                            {col}
                          </span>
                          <div className="flex gap-2">
                            <button 
                              onClick={() => handleTransform(col, 'log')}
                              className={`text-[11px] py-1.5 px-2.5 rounded-lg border transition-all ${
                                isLight 
                                  ? 'bg-white hover:bg-slate-100 border-slate-300 text-slate-700' 
                                  : 'bg-[#111c38] hover:bg-[#16254a] border-slate-700 text-slate-300'
                              }`}
                            >
                              Log(x)
                            </button>
                            <button 
                              onClick={() => handleTransform(col, 'zscore')}
                              className={`text-[11px] py-1.5 px-2.5 rounded-lg border transition-all ${
                                isLight 
                                  ? 'bg-white hover:bg-slate-100 border-slate-300 text-slate-700' 
                                  : 'bg-[#111c38] hover:bg-[#16254a] border-slate-700 text-slate-300'
                              }`}
                            >
                              Z-Score
                            </button>
                            <button 
                              onClick={() => handleTransform(col, 'binning')}
                              className={`text-[11px] py-1.5 px-2.5 rounded-lg border transition-all ${
                                isLight 
                                  ? 'bg-white hover:bg-slate-100 border-slate-300 text-slate-700' 
                                  : 'bg-[#111c38] hover:bg-[#16254a] border-slate-700 text-slate-300'
                              }`}
                            >
                              5-Quantile Bin
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Cleaning Presets */}
                  <div className={`p-6 rounded-2xl border shadow-sm ${
                    isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                  }`}>
                    <h4 className={`font-bold text-sm mb-4 ${isLight ? 'text-slate-900' : 'text-slate-200'}`}>
                      Data Hygiene Presets
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className={`p-4 rounded-xl border flex flex-col justify-between ${
                        isLight ? 'bg-slate-50 border-slate-200' : 'bg-[#0b1328] border-slate-800'
                      }`}>
                        <div>
                          <span className={`font-bold text-xs ${isLight ? 'text-slate-900' : 'text-slate-200'}`}>
                            Deduplicate Rows
                          </span>
                          <p className={`text-xs mt-1 ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                            Prunes duplicate records.
                          </p>
                        </div>
                        <button 
                          onClick={() => handleClean('drop_duplicates')}
                          className="mt-4 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold py-2 px-4 rounded-lg transition-all w-fit"
                        >
                          Execute Deduplication
                        </button>
                      </div>

                      {dataset.numeric_columns?.length > 0 && (
                        <div className={`p-4 rounded-xl border flex flex-col justify-between ${
                          isLight ? 'bg-slate-50 border-slate-200' : 'bg-[#0b1328] border-slate-800'
                        }`}>
                          <div>
                            <span className={`font-bold text-xs ${isLight ? 'text-slate-900' : 'text-slate-200'}`}>
                              Median Imputation
                            </span>
                            <p className={`text-xs mt-1 ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                              Fills nulls in '{dataset.numeric_columns[0]}' with median.
                            </p>
                          </div>
                          <button 
                            onClick={() => handleClean('impute_numeric', { column: dataset.numeric_columns[0], strategy: 'median' })}
                            className="mt-4 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold py-2 px-4 rounded-lg transition-all w-fit"
                          >
                            Impute Median
                          </button>
                        </div>
                      )}

                      <div className={`p-4 rounded-xl border flex flex-col justify-between ${
                        isLight ? 'bg-slate-50 border-slate-200' : 'bg-[#0b1328] border-slate-800'
                      }`}>
                        <div>
                          <span className={`font-bold text-xs ${isLight ? 'text-slate-900' : 'text-slate-200'}`}>
                            Whitespace Strip
                          </span>
                          <p className={`text-xs mt-1 ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                            Trims leading/trailing whitespace across string attributes.
                          </p>
                        </div>
                        <button 
                          onClick={() => handleClean('whitespace_clean')}
                          className="mt-4 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold py-2 px-4 rounded-lg transition-all w-fit"
                        >
                          Clean Strings
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Audit Trail */}
                  {dataset.cleaning_log?.length > 0 && (
                    <div className={`p-6 rounded-2xl border shadow-sm ${
                      isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                    }`}>
                      <h4 className={`font-bold text-sm mb-3 font-mono ${isLight ? 'text-slate-900' : 'text-slate-200'}`}>
                        Operations Audit Trail
                      </h4>
                      <div className="space-y-2">
                        {dataset.cleaning_log.map((log, idx) => (
                          <div key={idx} className={`p-3 rounded-lg flex items-center justify-between text-xs font-mono border ${
                            isLight ? 'bg-slate-50 border-slate-200' : 'bg-[#0b1328] border-slate-800'
                          }`}>
                            <span className={isLight ? 'text-slate-500' : 'text-slate-400'}>{log.timestamp}</span>
                            <span className="text-indigo-500 font-bold">{log.action}</span>
                            <span className={isLight ? 'text-slate-800' : 'text-slate-300'}>{log.description}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* TAB 5: CUSTOM DYNAMIC VISUALIZER LAB */}
              {activeTab === 'visualizer' && (
                <div className="space-y-6">
                  <div className={`p-6 rounded-2xl border shadow-sm ${
                    isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                  }`}>
                    <h4 className={`font-bold text-sm mb-4 flex items-center gap-2 ${
                      isLight ? 'text-slate-900' : 'text-slate-200'
                    }`}>
                      <Sliders className="w-4 h-4 text-indigo-500" />
                      Dynamic Chart Configuration Studio
                    </h4>

                    {/* Chart Controls */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                      <div>
                        <label className={`text-[11px] font-bold uppercase tracking-wider block mb-1 ${
                          isLight ? 'text-slate-600' : 'text-slate-400'
                        }`}>
                          Chart Type
                        </label>
                        <select 
                          className={`w-full rounded-lg text-xs p-2 border ${
                            isLight 
                              ? 'bg-slate-50 border-slate-300 text-slate-800' 
                              : 'bg-[#111c38] border-slate-700/80 text-slate-200'
                          }`}
                          value={chartConfig.chartType}
                          onChange={(e) => setChartConfig(prev => ({ ...prev, chartType: e.target.value }))}
                        >
                          <option value="bar">Bar Chart</option>
                          <option value="line">Line Trend Chart</option>
                          <option value="area">Area Volume Chart</option>
                          <option value="scatter">Scatter Plot</option>
                        </select>
                      </div>

                      <div>
                        <label className={`text-[11px] font-bold uppercase tracking-wider block mb-1 ${
                          isLight ? 'text-slate-600' : 'text-slate-400'
                        }`}>
                          X-Axis (Dimension)
                        </label>
                        <select 
                          className={`w-full rounded-lg text-xs p-2 border ${
                            isLight 
                              ? 'bg-slate-50 border-slate-300 text-slate-800' 
                              : 'bg-[#111c38] border-slate-700/80 text-slate-200'
                          }`}
                          value={chartConfig.xAxis}
                          onChange={(e) => setChartConfig(prev => ({ ...prev, xAxis: e.target.value }))}
                        >
                          {dataset.all_columns?.map(c => (
                            <option key={c} value={c}>{c}</option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className={`text-[11px] font-bold uppercase tracking-wider block mb-1 ${
                          isLight ? 'text-slate-600' : 'text-slate-400'
                        }`}>
                          Y-Axis (Measure)
                        </label>
                        <select 
                          className={`w-full rounded-lg text-xs p-2 border ${
                            isLight 
                              ? 'bg-slate-50 border-slate-300 text-slate-800' 
                              : 'bg-[#111c38] border-slate-700/80 text-slate-200'
                          }`}
                          value={chartConfig.yAxis}
                          onChange={(e) => setChartConfig(prev => ({ ...prev, yAxis: e.target.value }))}
                        >
                          {dataset.numeric_columns?.map(c => (
                            <option key={c} value={c}>{c}</option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className={`text-[11px] font-bold uppercase tracking-wider block mb-1 ${
                          isLight ? 'text-slate-600' : 'text-slate-400'
                        }`}>
                          Aggregation
                        </label>
                        <select 
                          className={`w-full rounded-lg text-xs p-2 border ${
                            isLight 
                              ? 'bg-slate-50 border-slate-300 text-slate-800' 
                              : 'bg-[#111c38] border-slate-700/80 text-slate-200'
                          }`}
                          value={chartConfig.agg}
                          onChange={(e) => setChartConfig(prev => ({ ...prev, agg: e.target.value }))}
                        >
                          <option value="mean">Mean (Average)</option>
                          <option value="sum">Sum (Total)</option>
                        </select>
                      </div>
                    </div>

                    {/* Chart Render Canvas */}
                    <div className="h-80 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        {chartConfig.chartType === 'bar' ? (
                          <BarChart data={dynamicChartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke={isLight ? '#e2e8f0' : '#1e293b'} />
                            <XAxis dataKey={chartConfig.xAxis} stroke={isLight ? '#94a3b8' : '#64748b'} tick={{ fontSize: 11 }} />
                            <YAxis stroke={isLight ? '#94a3b8' : '#64748b'} />
                            <Tooltip contentStyle={{ 
                              background: isLight ? '#ffffff' : '#0b1328', 
                              borderColor: isLight ? '#e2e8f0' : '#1e293b',
                              color: isLight ? '#0f172a' : '#f8fafc'
                            }} />
                            <Bar dataKey={chartConfig.yAxis} fill="#6366f1" radius={[4, 4, 0, 0]} />
                          </BarChart>
                        ) : chartConfig.chartType === 'line' ? (
                          <RechartsLine data={dynamicChartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke={isLight ? '#e2e8f0' : '#1e293b'} />
                            <XAxis dataKey={chartConfig.xAxis} stroke={isLight ? '#94a3b8' : '#64748b'} tick={{ fontSize: 11 }} />
                            <YAxis stroke={isLight ? '#94a3b8' : '#64748b'} />
                            <Tooltip contentStyle={{ 
                              background: isLight ? '#ffffff' : '#0b1328', 
                              borderColor: isLight ? '#e2e8f0' : '#1e293b',
                              color: isLight ? '#0f172a' : '#f8fafc'
                            }} />
                            <Line type="monotone" dataKey={chartConfig.yAxis} stroke="#06b6d4" strokeWidth={3} />
                          </RechartsLine>
                        ) : chartConfig.chartType === 'area' ? (
                          <AreaChart data={dynamicChartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke={isLight ? '#e2e8f0' : '#1e293b'} />
                            <XAxis dataKey={chartConfig.xAxis} stroke={isLight ? '#94a3b8' : '#64748b'} tick={{ fontSize: 11 }} />
                            <YAxis stroke={isLight ? '#94a3b8' : '#64748b'} />
                            <Tooltip contentStyle={{ 
                              background: isLight ? '#ffffff' : '#0b1328', 
                              borderColor: isLight ? '#e2e8f0' : '#1e293b',
                              color: isLight ? '#0f172a' : '#f8fafc'
                            }} />
                            <Area type="monotone" dataKey={chartConfig.yAxis} stroke="#10b981" fill="#10b981" fillOpacity={0.2} />
                          </AreaChart>
                        ) : (
                          <ScatterChart>
                            <CartesianGrid strokeDasharray="3 3" stroke={isLight ? '#e2e8f0' : '#1e293b'} />
                            <XAxis dataKey={chartConfig.xAxis} stroke={isLight ? '#94a3b8' : '#64748b'} tick={{ fontSize: 11 }} />
                            <YAxis dataKey={chartConfig.yAxis} stroke={isLight ? '#94a3b8' : '#64748b'} />
                            <Tooltip contentStyle={{ 
                              background: isLight ? '#ffffff' : '#0b1328', 
                              borderColor: isLight ? '#e2e8f0' : '#1e293b',
                              color: isLight ? '#0f172a' : '#f8fafc'
                            }} />
                            <Scatter data={dynamicChartData} fill="#ec4899" />
                          </ScatterChart>
                        )}
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 6: DYNAMIC PIVOT MATRIX */}
              {activeTab === 'pivot' && (
                <div className="space-y-6">
                  <div className={`p-6 rounded-2xl border shadow-sm ${
                    isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                  }`}>
                    <h4 className={`font-bold text-sm mb-4 flex items-center gap-2 ${
                      isLight ? 'text-slate-900' : 'text-slate-200'
                    }`}>
                      <Grid3X3 className="w-4 h-4 text-indigo-500" />
                      Multidimensional Pivot Table Builder
                    </h4>

                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                      <div>
                        <label className={`text-[11px] font-bold uppercase tracking-wider block mb-1 ${
                          isLight ? 'text-slate-600' : 'text-slate-400'
                        }`}>
                          Index (Row Groups)
                        </label>
                        <select 
                          className={`w-full rounded-lg text-xs p-2 border ${
                            isLight 
                              ? 'bg-slate-50 border-slate-300 text-slate-800' 
                              : 'bg-[#111c38] border-slate-700/80 text-slate-200'
                          }`}
                          value={pivotConfig.index}
                          onChange={(e) => setPivotConfig(prev => ({ ...prev, index: e.target.value }))}
                        >
                          {dataset.all_columns?.map(c => (
                            <option key={c} value={c}>{c}</option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className={`text-[11px] font-bold uppercase tracking-wider block mb-1 ${
                          isLight ? 'text-slate-600' : 'text-slate-400'
                        }`}>
                          Columns (Optional Pivot)
                        </label>
                        <select 
                          className={`w-full rounded-lg text-xs p-2 border ${
                            isLight 
                              ? 'bg-slate-50 border-slate-300 text-slate-800' 
                              : 'bg-[#111c38] border-slate-700/80 text-slate-200'
                          }`}
                          value={pivotConfig.columns}
                          onChange={(e) => setPivotConfig(prev => ({ ...prev, columns: e.target.value }))}
                        >
                          <option value="None">None (Flat Grouping)</option>
                          {dataset.categorical_columns?.map(c => (
                            <option key={c} value={c}>{c}</option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className={`text-[11px] font-bold uppercase tracking-wider block mb-1 ${
                          isLight ? 'text-slate-600' : 'text-slate-400'
                        }`}>
                          Aggregate Metric
                        </label>
                        <select 
                          className={`w-full rounded-lg text-xs p-2 border ${
                            isLight 
                              ? 'bg-slate-50 border-slate-300 text-slate-800' 
                              : 'bg-[#111c38] border-slate-700/80 text-slate-200'
                          }`}
                          value={pivotConfig.values}
                          onChange={(e) => setPivotConfig(prev => ({ ...prev, values: e.target.value }))}
                        >
                          {dataset.numeric_columns?.map(c => (
                            <option key={c} value={c}>{c}</option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className={`text-[11px] font-bold uppercase tracking-wider block mb-1 ${
                          isLight ? 'text-slate-600' : 'text-slate-400'
                        }`}>
                          Agg Function
                        </label>
                        <select 
                          className={`w-full rounded-lg text-xs p-2 border ${
                            isLight 
                              ? 'bg-slate-50 border-slate-300 text-slate-800' 
                              : 'bg-[#111c38] border-slate-700/80 text-slate-200'
                          }`}
                          value={pivotConfig.aggfunc}
                          onChange={(e) => setPivotConfig(prev => ({ ...prev, aggfunc: e.target.value }))}
                        >
                          <option value="mean">Mean (Average)</option>
                          <option value="sum">Sum</option>
                          <option value="count">Count</option>
                          <option value="min">Min</option>
                          <option value="max">Max</option>
                        </select>
                      </div>
                    </div>

                    <button 
                      onClick={async () => {
                        const res = await generatePivotTable(pivotConfig);
                        setPivotResult(res.data);
                      }}
                      className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs px-5 py-2 rounded-lg transition-all shadow-md shadow-indigo-600/30"
                    >
                      Generate Dynamic Pivot Table
                    </button>

                    {pivotResult && (
                      <div className="mt-6 space-y-6">
                        {pivotChartData.length > 0 && (
                          <div className={`p-4 rounded-xl border ${
                            isLight ? 'bg-slate-50 border-slate-200' : 'bg-[#0b1328] border-slate-800'
                          }`}>
                            <h5 className={`text-xs font-bold mb-3 ${isLight ? 'text-slate-800' : 'text-slate-300'}`}>
                              Pivot Visual Breakdown
                            </h5>
                            <div className="h-64">
                              <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={pivotChartData}>
                                  <CartesianGrid strokeDasharray="3 3" stroke={isLight ? '#e2e8f0' : '#1e293b'} />
                                  <XAxis dataKey="name" stroke={isLight ? '#94a3b8' : '#64748b'} tick={{ fontSize: 11 }} />
                                  <YAxis stroke={isLight ? '#94a3b8' : '#64748b'} />
                                  <Tooltip contentStyle={{ 
                                    background: isLight ? '#ffffff' : '#0b1328', 
                                    borderColor: isLight ? '#e2e8f0' : '#1e293b',
                                    color: isLight ? '#0f172a' : '#f8fafc'
                                  }} />
                                  {pivotResult.fields.slice(1).map((f, idx) => (
                                    <Bar key={f} dataKey={f} fill={activeColors[idx % activeColors.length]} radius={[4, 4, 0, 0]} />
                                  ))}
                                </BarChart>
                              </ResponsiveContainer>
                            </div>
                          </div>
                        )}

                        <div className="overflow-x-auto">
                          <table className="w-full text-left text-xs font-mono border-collapse">
                            <thead className={`font-bold ${
                              isLight ? 'bg-slate-100 text-slate-800' : 'bg-[#111c38] text-slate-200'
                            }`}>
                              <tr>
                                {pivotResult.fields?.map(f => (
                                  <th key={f} className={`p-3 border-b ${isLight ? 'border-slate-200' : 'border-slate-800'}`}>{f}</th>
                                ))}
                              </tr>
                            </thead>
                            <tbody className={`divide-y ${
                              isLight ? 'divide-slate-200 text-slate-700' : 'divide-slate-800/80 text-slate-400'
                            }`}>
                              {pivotResult.data?.map((r, idx) => (
                                <tr key={idx} className={isLight ? 'hover:bg-slate-50' : 'hover:bg-white/5'}>
                                  {pivotResult.fields.map(f => (
                                    <td key={f} className="p-3 whitespace-nowrap">{r[f]}</td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* TAB 7: STATISTICAL CORRELATION EDA */}
              {activeTab === 'eda' && (
                <div className="space-y-6">
                  {edaData && (
                    <>
                      {/* Heatmap Grid */}
                      {edaData.corr_matrix?.columns && edaData.corr_matrix.columns.length > 0 && (
                        <div className={`p-6 rounded-2xl border shadow-sm ${
                          isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                        }`}>
                          <h4 className={`font-bold text-sm mb-4 flex items-center gap-2 ${
                            isLight ? 'text-slate-900' : 'text-slate-200'
                          }`}>
                            <Activity className="w-4 h-4 text-indigo-500" />
                            Pairwise Pearson Correlation Heatmap Matrix
                          </h4>
                          <div className="overflow-x-auto">
                            <table className="text-xs font-mono border-collapse">
                              <thead>
                                <tr>
                                  <th className="p-2 border-b border-slate-300 text-left"></th>
                                  {edaData.corr_matrix.columns.map(c => (
                                    <th key={c} className={`p-2 border-b font-bold text-center truncate max-w-[90px] ${
                                      isLight ? 'border-slate-200 text-slate-800' : 'border-slate-800 text-slate-300'
                                    }`}>{c}</th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody>
                                {edaData.corr_matrix.columns.map((rowName, r_idx) => (
                                  <tr key={rowName}>
                                    <td className={`p-2 border-r font-bold whitespace-nowrap ${
                                      isLight ? 'border-slate-200 text-slate-800' : 'border-slate-800 text-slate-300'
                                    }`}>{rowName}</td>
                                    {edaData.corr_matrix.columns.map((colName, c_idx) => {
                                      const val = edaData.corr_matrix.z[r_idx]?.[c_idx];
                                      const isPos = val > 0;
                                      const absVal = Math.abs(val || 0);
                                      const bg = absVal === 1 
                                        ? 'rgba(99, 102, 241, 0.4)' 
                                        : isPos 
                                          ? `rgba(6, 182, 212, ${absVal * 0.7})` 
                                          : `rgba(244, 63, 94, ${absVal * 0.7})`;
                                      return (
                                        <td 
                                          key={colName} 
                                          className="p-2 text-center text-slate-900 font-bold rounded"
                                          style={{ background: bg }}
                                        >
                                          {val !== null && val !== undefined ? Number(val).toFixed(2) : '-'}
                                        </td>
                                      );
                                    })}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}

                      {/* Descriptive Stats */}
                      <div className={`p-6 rounded-2xl border shadow-sm ${
                        isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                      }`}>
                        <h4 className={`font-bold text-sm mb-4 ${isLight ? 'text-slate-900' : 'text-slate-200'}`}>
                          Descriptive Statistical Matrix
                        </h4>
                        <div className="overflow-x-auto">
                          <table className="w-full text-left text-xs font-mono">
                            <thead className={`font-bold ${
                              isLight ? 'bg-slate-100 text-slate-800' : 'bg-[#111c38] text-slate-300'
                            }`}>
                              <tr>
                                <th className="p-2.5">Attribute</th>
                                <th className="p-2.5">Mean</th>
                                <th className="p-2.5">Std</th>
                                <th className="p-2.5">Median</th>
                                <th className="p-2.5">Skewness</th>
                                <th className="p-2.5">Zeros</th>
                              </tr>
                            </thead>
                            <tbody className={`divide-y ${
                              isLight ? 'divide-slate-200 text-slate-700' : 'divide-slate-800 text-slate-400'
                            }`}>
                              {edaData.numeric_summary?.map((row, idx) => (
                                <tr key={idx} className={isLight ? 'hover:bg-slate-50' : 'hover:bg-white/5'}>
                                  <td className={`p-2.5 font-bold ${isLight ? 'text-slate-900' : 'text-slate-200'}`}>{row.index}</td>
                                  <td className="p-2.5">{row.mean}</td>
                                  <td className="p-2.5">{row.std}</td>
                                  <td className="p-2.5">{row.median}</td>
                                  <td className="p-2.5">{row.skewness}</td>
                                  <td className="p-2.5">{row.zeros}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>

                      {/* Frequency Charts */}
                      {Object.keys(categoricalDistData).length > 0 && (
                        <div className={`p-6 rounded-2xl border shadow-sm ${
                          isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                        }`}>
                          <h4 className={`font-bold text-sm mb-4 flex items-center gap-2 ${
                            isLight ? 'text-slate-900' : 'text-slate-200'
                          }`}>
                            <PieIcon className="w-4 h-4 text-cyan-500" />
                            Categorical Attribute Frequency Distributions
                          </h4>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {Object.entries(categoricalDistData).slice(0, 4).map(([catCol, chartData]) => (
                              <div key={catCol} className={`p-4 rounded-xl border ${
                                isLight ? 'bg-slate-50 border-slate-200' : 'bg-[#0b1328] border-slate-800'
                              }`}>
                                <span className={`font-bold text-xs block mb-2 ${isLight ? 'text-slate-800' : 'text-slate-300'}`}>
                                  {catCol}
                                </span>
                                <div className="h-44">
                                  <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={chartData}>
                                      <CartesianGrid strokeDasharray="3 3" stroke={isLight ? '#e2e8f0' : '#1e293b'} />
                                      <XAxis dataKey="category" stroke={isLight ? '#94a3b8' : '#64748b'} tick={{ fontSize: 10 }} />
                                      <YAxis stroke={isLight ? '#94a3b8' : '#64748b'} />
                                      <Tooltip contentStyle={{ 
                                        background: isLight ? '#ffffff' : '#0b1328', 
                                        borderColor: isLight ? '#e2e8f0' : '#1e293b',
                                        color: isLight ? '#0f172a' : '#f8fafc'
                                      }} />
                                      <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                                    </BarChart>
                                  </ResponsiveContainer>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Significant Associations */}
                      <div className={`p-6 rounded-2xl border shadow-sm ${
                        isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                      }`}>
                        <h4 className={`font-bold text-sm mb-4 ${isLight ? 'text-slate-900' : 'text-slate-200'}`}>
                          Pairwise Significant Associations (|r| &ge; 0.5)
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                          {edaData.top_correlations?.map((c, idx) => (
                            <div key={idx} className={`p-3 rounded-xl border text-xs ${
                              isLight ? 'bg-slate-50 border-slate-200' : 'bg-[#0b1328] border-slate-800'
                            }`}>
                              <div className="flex justify-between items-center mb-1">
                                <span className={`font-bold ${isLight ? 'text-slate-900' : 'text-slate-200'}`}>
                                  {c.feature_a} & {c.feature_b}
                                </span>
                                <span className="text-cyan-500 font-mono font-bold">r = {c.correlation}</span>
                              </div>
                              <span className={`text-[11px] ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                                {c.strength} {c.direction} Association
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </>
                  )}
                </div>
              )}

              {/* TAB 8: HYPOTHESIS TESTING */}
              {activeTab === 'statistics' && (
                <div className="space-y-6">
                  <div className={`p-6 rounded-2xl border shadow-sm ${
                    isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                  }`}>
                    <h4 className={`font-bold text-sm mb-2 ${isLight ? 'text-slate-900' : 'text-slate-200'}`}>
                      Scientific Hypothesis Testing Lab
                    </h4>
                    <p className={`text-xs mb-4 ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                      Select test type: Welch's two-sample t-test, Mann-Whitney non-parametric test, or Chi-Square contingency test.
                    </p>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                      <div>
                        <label className={`text-[11px] font-bold uppercase tracking-wider block mb-1 ${
                          isLight ? 'text-slate-600' : 'text-slate-400'
                        }`}>
                          Test Type
                        </label>
                        <select 
                          className={`w-full rounded-lg text-xs p-2 border ${
                            isLight 
                              ? 'bg-slate-50 border-slate-300 text-slate-800' 
                              : 'bg-[#111c38] border-slate-700/80 text-slate-200'
                          }`}
                          value={statConfig.test_type}
                          onChange={(e) => setStatConfig(prev => ({ ...prev, test_type: e.target.value }))}
                        >
                          <option value="ttest">Welch's Two-Sample t-Test</option>
                          <option value="mannwhitney">Mann-Whitney U Non-Parametric</option>
                          <option value="chisquare">Chi-Square Independence Test</option>
                        </select>
                      </div>

                      {statConfig.test_type !== 'chisquare' ? (
                        <>
                          <div>
                            <label className={`text-[11px] font-bold uppercase tracking-wider block mb-1 ${
                              isLight ? 'text-slate-600' : 'text-slate-400'
                            }`}>
                              Measure (Numeric Column)
                            </label>
                            <select 
                              className={`w-full rounded-lg text-xs p-2 border ${
                                isLight 
                                  ? 'bg-slate-50 border-slate-300 text-slate-800' 
                                  : 'bg-[#111c38] border-slate-700/80 text-slate-200'
                              }`}
                              value={statConfig.val_col}
                              onChange={(e) => setStatConfig(prev => ({ ...prev, val_col: e.target.value }))}
                            >
                              {dataset.numeric_columns?.map(c => (
                                <option key={c} value={c}>{c}</option>
                              ))}
                            </select>
                          </div>

                          <div>
                            <label className={`text-[11px] font-bold uppercase tracking-wider block mb-1 ${
                              isLight ? 'text-slate-600' : 'text-slate-400'
                            }`}>
                              Cohort Group Dimension
                            </label>
                            <select 
                              className={`w-full rounded-lg text-xs p-2 border ${
                                isLight 
                                  ? 'bg-slate-50 border-slate-300 text-slate-800' 
                                  : 'bg-[#111c38] border-slate-700/80 text-slate-200'
                              }`}
                              value={statConfig.grp_col}
                              onChange={(e) => {
                                const newGrp = e.target.value;
                                const vals = Array.from(new Set(dataset.preview.map(r => r[newGrp]))).filter(Boolean);
                                setStatConfig(prev => ({
                                  ...prev,
                                  grp_col: newGrp,
                                  grp_a: vals[0] ? String(vals[0]) : '',
                                  grp_b: vals[1] ? String(vals[1]) : ''
                                }));
                              }}
                            >
                              {dataset.categorical_columns?.map(c => (
                                <option key={c} value={c}>{c}</option>
                              ))}
                            </select>
                          </div>
                        </>
                      ) : (
                        <>
                          <div>
                            <label className={`text-[11px] font-bold uppercase tracking-wider block mb-1 ${
                              isLight ? 'text-slate-600' : 'text-slate-400'
                            }`}>
                              Categorical Variable A
                            </label>
                            <select 
                              className={`w-full rounded-lg text-xs p-2 border ${
                                isLight 
                                  ? 'bg-slate-50 border-slate-300 text-slate-800' 
                                  : 'bg-[#111c38] border-slate-700/80 text-slate-200'
                              }`}
                              value={statConfig.cat_a}
                              onChange={(e) => setStatConfig(prev => ({ ...prev, cat_a: e.target.value }))}
                            >
                              {dataset.categorical_columns?.map(c => (
                                <option key={c} value={c}>{c}</option>
                              ))}
                            </select>
                          </div>

                          <div>
                            <label className={`text-[11px] font-bold uppercase tracking-wider block mb-1 ${
                              isLight ? 'text-slate-600' : 'text-slate-400'
                            }`}>
                              Categorical Variable B
                            </label>
                            <select 
                              className={`w-full rounded-lg text-xs p-2 border ${
                                isLight 
                                  ? 'bg-slate-50 border-slate-300 text-slate-800' 
                                  : 'bg-[#111c38] border-slate-700/80 text-slate-200'
                              }`}
                              value={statConfig.cat_b}
                              onChange={(e) => setStatConfig(prev => ({ ...prev, cat_b: e.target.value }))}
                            >
                              {dataset.categorical_columns?.map(c => (
                                <option key={c} value={c}>{c}</option>
                              ))}
                            </select>
                          </div>
                        </>
                      )}
                    </div>

                    <button 
                      onClick={async () => {
                        const res = await runStatistics(statConfig);
                        setStatResult(res.data);
                      }}
                      className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs px-4 py-2 rounded-lg transition-all"
                    >
                      Execute Hypothesis Test
                    </button>

                    {statResult && !statResult.error && (
                      <div className={`mt-6 p-4 rounded-xl space-y-2 text-xs font-mono border ${
                        isLight 
                          ? 'bg-indigo-50/70 border-indigo-200 text-slate-800' 
                          : 'bg-indigo-500/10 border-indigo-500/20 text-slate-200'
                      }`}>
                        <div className="font-bold text-indigo-500">{statResult.test}</div>
                        <div><b>Statistic:</b> {statResult.stat_value} ({statResult.stat_name})</div>
                        <div><b>p-value:</b> {statResult.p_value}</div>
                        <div><b>Result:</b> {statResult.significant_at_05 ? '✅ Statistically Significant (p < 0.05)' : '❌ Not Statistically Significant'}</div>
                        {statResult.interpretation && <p className="font-sans mt-2">{statResult.interpretation}</p>}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* TAB 9: K-MEANS & ANOMALY ML */}
              {activeTab === 'clustering' && (
                <div className="space-y-6">
                  {/* K-Means */}
                  <div className={`p-6 rounded-2xl border shadow-sm ${
                    isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                  }`}>
                    <h4 className={`font-bold text-sm mb-2 ${isLight ? 'text-slate-900' : 'text-slate-200'}`}>
                      K-Means Customer & Record Segmentation
                    </h4>
                    <p className={`text-xs mb-4 ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                      Partitions observations into k unsupervised clusters with 2D PCA projection coordinates.
                    </p>

                    <div className="flex gap-4 mb-4 items-center">
                      <div className="flex items-center gap-2">
                        <label className={`text-xs ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>Clusters (k):</label>
                        <input 
                          type="number" 
                          min="2" 
                          max="8" 
                          value={clusterK} 
                          onChange={(e) => setClusterK(Number(e.target.value))} 
                          className={`text-xs px-2 py-1 rounded w-16 border ${
                            isLight 
                              ? 'bg-slate-50 border-slate-300 text-slate-800' 
                              : 'bg-[#111c38] border-slate-700 text-slate-200'
                          }`}
                        />
                      </div>
                      <button 
                        onClick={async () => {
                          if (selectedClusterFeatures.length >= 2) {
                            const res = await runClustering(selectedClusterFeatures, clusterK);
                            setClusterResult(res.data);
                          }
                        }}
                        className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs px-4 py-2 rounded-lg transition-all"
                      >
                        Fit K-Means (k={clusterK})
                      </button>
                    </div>

                    {clusterResult && !clusterResult.error && (
                      <div className="mt-6 space-y-4">
                        <div className="text-xs font-mono text-emerald-500 font-bold">
                          Silhouette Score: {clusterResult.silhouette_score}
                        </div>
                        <div className="h-64">
                          <ResponsiveContainer width="100%" height="100%">
                            <ScatterChart>
                              <CartesianGrid strokeDasharray="3 3" stroke={isLight ? '#e2e8f0' : '#1e293b'} />
                              <XAxis type="number" dataKey="PCA1" name="PCA1" stroke={isLight ? '#94a3b8' : '#64748b'} />
                              <YAxis type="number" dataKey="PCA2" name="PCA2" stroke={isLight ? '#94a3b8' : '#64748b'} />
                              <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ 
                                background: isLight ? '#ffffff' : '#0b1328', 
                                borderColor: isLight ? '#e2e8f0' : '#1e293b',
                                color: isLight ? '#0f172a' : '#f8fafc'
                              }} />
                              <Scatter name="Clusters" data={clusterResult.pca_df} fill="#6366f1" />
                            </ScatterChart>
                          </ResponsiveContainer>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Anomaly Detection */}
                  <div className={`p-6 rounded-2xl border shadow-sm ${
                    isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                  }`}>
                    <h4 className={`font-bold text-sm mb-2 flex items-center gap-2 ${
                      isLight ? 'text-slate-900' : 'text-slate-200'
                    }`}>
                      <ShieldAlert className="w-4 h-4 text-rose-500" />
                      Isolation Forest Unsupervised Anomaly Detection
                    </h4>
                    <p className={`text-xs mb-4 ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                      Identifies multivariate outliers using tree-based ensemble isolation path lengths.
                    </p>

                    <div className="flex gap-4 mb-4 items-center">
                      <div className="flex items-center gap-2">
                        <label className={`text-xs ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>Contamination Rate:</label>
                        <select
                          className={`text-xs px-2 py-1.5 rounded border ${
                            isLight 
                              ? 'bg-slate-50 border-slate-300 text-slate-800' 
                              : 'bg-[#111c38] border-slate-700 text-slate-200'
                          }`}
                          value={anomalyContamination}
                          onChange={(e) => setAnomalyContamination(Number(e.target.value))}
                        >
                          <option value="0.01">1% (Very Conservative)</option>
                          <option value="0.05">5% (Standard)</option>
                          <option value="0.10">10% (Aggressive)</option>
                        </select>
                      </div>
                      <button 
                        onClick={async () => {
                          if (selectedAnomalyFeatures.length >= 1) {
                            const res = await runAnomaly(selectedAnomalyFeatures, anomalyContamination);
                            setAnomalyResult(res.data);
                          }
                        }}
                        className="bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs px-4 py-2 rounded-lg transition-all"
                      >
                        Detect Anomalies
                      </button>
                    </div>

                    {anomalyResult && !anomalyResult.error && (
                      <div className="mt-4 space-y-3">
                        <div className="flex items-center gap-4 text-xs font-mono">
                          <span className="text-rose-500 font-bold">Detected Anomalies: {anomalyResult.anomaly_count}</span>
                          <span className={isLight ? 'text-slate-600' : 'text-slate-400'}>Total Analyzed: {anomalyResult.total_records}</span>
                        </div>
                        {anomalyResult.anomalies_df?.length > 0 && (
                          <div className="overflow-x-auto max-h-48">
                            <table className="w-full text-left text-xs font-mono border-collapse">
                              <thead className={isLight ? 'bg-slate-100 text-slate-800' : 'bg-[#111c38] text-slate-300'}>
                                <tr>
                                  {Object.keys(anomalyResult.anomalies_df[0]).slice(0, 6).map(k => (
                                    <th key={k} className="p-2">{k}</th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody className={`divide-y ${isLight ? 'divide-slate-200 text-slate-700' : 'divide-slate-800 text-slate-400'}`}>
                                {anomalyResult.anomalies_df.slice(0, 10).map((r, idx) => (
                                  <tr key={idx} className={isLight ? 'hover:bg-slate-50' : 'hover:bg-white/5'}>
                                    {Object.keys(anomalyResult.anomalies_df[0]).slice(0, 6).map(k => (
                                      <td key={k} className="p-2 whitespace-nowrap">{String(r[k])}</td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* TAB 10: TIME SERIES */}
              {activeTab === 'timeseries' && (
                <div className="space-y-6">
                  <div className={`p-6 rounded-2xl border shadow-sm ${
                    isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                  }`}>
                    <h4 className={`font-bold text-sm mb-2 ${isLight ? 'text-slate-900' : 'text-slate-200'}`}>
                      Chronological Resampling & Trend Analysis
                    </h4>
                    <p className={`text-xs mb-4 ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                      Evaluates weekly moving averages and temporal velocity across timestamp attributes.
                    </p>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                      <div>
                        <label className={`text-[11px] font-bold uppercase tracking-wider block mb-1 ${
                          isLight ? 'text-slate-600' : 'text-slate-400'
                        }`}>
                          Date Attribute
                        </label>
                        <select
                          className={`w-full rounded-lg text-xs p-2 border ${
                            isLight 
                              ? 'bg-slate-50 border-slate-300 text-slate-800' 
                              : 'bg-[#111c38] border-slate-700/80 text-slate-200'
                          }`}
                          value={tsDateCol}
                          onChange={(e) => setTsDateCol(e.target.value)}
                        >
                          {dataset.all_columns?.map(c => (
                            <option key={c} value={c}>{c}</option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className={`text-[11px] font-bold uppercase tracking-wider block mb-1 ${
                          isLight ? 'text-slate-600' : 'text-slate-400'
                        }`}>
                          Metric to Resample
                        </label>
                        <select
                          className={`w-full rounded-lg text-xs p-2 border ${
                            isLight 
                              ? 'bg-slate-50 border-slate-300 text-slate-800' 
                              : 'bg-[#111c38] border-slate-700/80 text-slate-200'
                          }`}
                          value={tsValCol}
                          onChange={(e) => setTsValCol(e.target.value)}
                        >
                          {dataset.numeric_columns?.map(c => (
                            <option key={c} value={c}>{c}</option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className={`text-[11px] font-bold uppercase tracking-wider block mb-1 ${
                          isLight ? 'text-slate-600' : 'text-slate-400'
                        }`}>
                          Frequency Cadence
                        </label>
                        <select
                          className={`w-full rounded-lg text-xs p-2 border ${
                            isLight 
                              ? 'bg-slate-50 border-slate-300 text-slate-800' 
                              : 'bg-[#111c38] border-slate-700/80 text-slate-200'
                          }`}
                          value={tsFreq}
                          onChange={(e) => setTsFreq(e.target.value)}
                        >
                          <option value="D">Daily ('D')</option>
                          <option value="W">Weekly ('W')</option>
                          <option value="M">Monthly ('M')</option>
                        </select>
                      </div>
                    </div>

                    <button 
                      onClick={async () => {
                        if (tsDateCol && tsValCol) {
                          const res = await runTimeSeries(tsDateCol, tsValCol, tsFreq);
                          setTsResult(res.data);
                        }
                      }}
                      className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs px-4 py-2 rounded-lg transition-all"
                    >
                      Run Resampling & Moving Average
                    </button>

                    {tsResult && !tsResult.error && (
                      <div className="mt-6 space-y-6">
                        <div className="h-64">
                          <ResponsiveContainer width="100%" height="100%">
                            <RechartsLine data={tsResult.resampled_df}>
                              <CartesianGrid strokeDasharray="3 3" stroke={isLight ? '#e2e8f0' : '#1e293b'} />
                              <XAxis dataKey={tsResult.date_col} stroke={isLight ? '#94a3b8' : '#64748b'} tick={{ fontSize: 10 }} />
                              <YAxis stroke={isLight ? '#94a3b8' : '#64748b'} />
                              <Tooltip contentStyle={{ 
                                background: isLight ? '#ffffff' : '#0b1328', 
                                borderColor: isLight ? '#e2e8f0' : '#1e293b',
                                color: isLight ? '#0f172a' : '#f8fafc'
                              }} />
                              <Line type="monotone" dataKey="mean" stroke="#6366f1" strokeWidth={2} name="Interval Mean" />
                              <Line type="monotone" dataKey="rolling_mean_3" stroke="#06b6d4" strokeWidth={2} strokeDasharray="5 5" name="3-Period Moving Avg" />
                            </RechartsLine>
                          </ResponsiveContainer>
                        </div>

                        {/* Growth Rate Bar Chart */}
                        <div className={`p-4 rounded-xl border ${
                          isLight ? 'bg-slate-50 border-slate-200' : 'bg-[#0b1328] border-slate-800'
                        }`}>
                          <h5 className={`text-xs font-bold mb-2 ${isLight ? 'text-slate-800' : 'text-slate-300'}`}>
                            Period-over-Period Growth Velocity (%)
                          </h5>
                          <div className="h-44">
                            <ResponsiveContainer width="100%" height="100%">
                              <BarChart data={tsResult.resampled_df}>
                                <CartesianGrid strokeDasharray="3 3" stroke={isLight ? '#e2e8f0' : '#1e293b'} />
                                <XAxis dataKey={tsResult.date_col} stroke={isLight ? '#94a3b8' : '#64748b'} tick={{ fontSize: 10 }} />
                                <YAxis stroke={isLight ? '#94a3b8' : '#64748b'} unit="%" />
                                <Tooltip contentStyle={{ 
                                  background: isLight ? '#ffffff' : '#0b1328', 
                                  borderColor: isLight ? '#e2e8f0' : '#1e293b',
                                  color: isLight ? '#0f172a' : '#f8fafc'
                                }} />
                                <Bar dataKey="growth_rate_pct" fill="#10b981" radius={[4, 4, 0, 0]} name="Growth Rate %" />
                              </BarChart>
                            </ResponsiveContainer>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* TAB 11: PREDICTIVE ML WORKBENCH */}
              {activeTab === 'ml' && (
                <div className="space-y-6">
                  <div className={`p-6 rounded-2xl border shadow-sm ${
                    isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                  }`}>
                    <h4 className={`font-bold text-sm mb-2 ${isLight ? 'text-slate-900' : 'text-slate-200'}`}>
                      Predictive Machine Learning Workbench
                    </h4>
                    <p className={`text-xs mb-4 ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                      Leakage-free baseline modeling pipeline with standard scaling, imputation, dummy encoding, and train/test splits.
                    </p>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                      <div>
                        <label className={`text-[11px] font-bold uppercase tracking-wider block mb-1 ${
                          isLight ? 'text-slate-600' : 'text-slate-400'
                        }`}>
                          Target Dimension
                        </label>
                        <select 
                          className={`w-full rounded-lg text-xs p-2 border ${
                            isLight 
                              ? 'bg-slate-50 border-slate-300 text-slate-800' 
                              : 'bg-[#111c38] border-slate-700/80 text-slate-200'
                          }`}
                          value={mlTarget}
                          onChange={(e) => setMlTarget(e.target.value)}
                        >
                          {dataset.all_columns?.map(c => (
                            <option key={c} value={c}>{c}</option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className={`text-[11px] font-bold uppercase tracking-wider block mb-1 ${
                          isLight ? 'text-slate-600' : 'text-slate-400'
                        }`}>
                          Modeling Paradigm
                        </label>
                        <select 
                          className={`w-full rounded-lg text-xs p-2 border ${
                            isLight 
                              ? 'bg-slate-50 border-slate-300 text-slate-800' 
                              : 'bg-[#111c38] border-slate-700/80 text-slate-200'
                          }`}
                          value={mlTaskType}
                          onChange={(e) => setMlTaskType(e.target.value)}
                        >
                          <option value="Classification">Supervised Classification</option>
                          <option value="Regression">Supervised Regression</option>
                        </select>
                      </div>

                      <div className="flex items-end">
                        <button 
                          onClick={async () => {
                            const feats = dataset.all_columns.filter(c => c !== mlTarget).slice(0, 6);
                            const res = await trainML(mlTarget, feats, mlTaskType);
                            setMlResult(res.data);
                          }}
                          className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs px-4 py-2.5 rounded-lg transition-all flex items-center justify-center gap-1.5"
                        >
                          <Play className="w-3.5 h-3.5" />
                          Train Benchmark Models
                        </button>
                      </div>
                    </div>

                    {mlResult && !mlResult.error && (
                      <div className="mt-6 space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {Object.entries(mlResult.benchmark || {}).map(([modelName, metrics]) => (
                            <div key={modelName} className={`p-4 rounded-xl border space-y-2 text-xs font-mono ${
                              isLight ? 'bg-slate-50 border-slate-200' : 'bg-[#0b1328] border-slate-800'
                            }`}>
                              <div className="font-bold text-indigo-500 text-sm">{modelName}</div>
                              {Object.entries(metrics).filter(([k]) => !['Confusion_Matrix', 'Feature_Importance'].includes(k)).map(([k, v]) => (
                                <div key={k} className="flex justify-between">
                                  <span className={isLight ? 'text-slate-500' : 'text-slate-400'}>{k}:</span>
                                  <span className={`font-bold ${isLight ? 'text-slate-900' : 'text-slate-200'}`}>{v}</span>
                                </div>
                              ))}
                            </div>
                          ))}
                        </div>

                        {/* Feature Importance */}
                        {Object.values(mlResult.benchmark || {}).some(m => m.Feature_Importance) && (
                          <div className={`p-4 rounded-xl border ${
                            isLight ? 'bg-slate-50 border-slate-200' : 'bg-[#0b1328] border-slate-800'
                          }`}>
                            <h5 className={`text-xs font-bold mb-3 ${isLight ? 'text-slate-800' : 'text-slate-300'}`}>
                              Top Predictive Feature Importances
                            </h5>
                            <div className="h-44">
                              <ResponsiveContainer width="100%" height="100%">
                                <BarChart 
                                  layout="vertical"
                                  data={Object.entries(
                                    Object.values(mlResult.benchmark || {}).find(m => m.Feature_Importance)?.Feature_Importance || {}
                                  ).slice(0, 6).map(([feat, imp]) => ({ feat, importance: Number(imp) }))}
                                >
                                  <CartesianGrid strokeDasharray="3 3" stroke={isLight ? '#e2e8f0' : '#1e293b'} />
                                  <XAxis type="number" stroke={isLight ? '#94a3b8' : '#64748b'} />
                                  <YAxis type="category" dataKey="feat" stroke={isLight ? '#94a3b8' : '#64748b'} tick={{ fontSize: 10 }} />
                                  <Tooltip contentStyle={{ 
                                    background: isLight ? '#ffffff' : '#0b1328', 
                                    borderColor: isLight ? '#e2e8f0' : '#1e293b',
                                    color: isLight ? '#0f172a' : '#f8fafc'
                                  }} />
                                  <Bar dataKey="importance" fill="#06b6d4" radius={[0, 4, 4, 0]} />
                                </BarChart>
                              </ResponsiveContainer>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* TAB 12: EXECUTIVE EXPORT CENTER */}
              {activeTab === 'reports' && (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className={`p-6 rounded-2xl border flex flex-col justify-between shadow-sm ${
                      isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                    }`}>
                      <div>
                        <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-500 flex items-center justify-center mb-3">
                          <FileSpreadsheet className="w-5 h-5" />
                        </div>
                        <h4 className={`font-bold text-sm mb-1 ${isLight ? 'text-slate-900' : 'text-slate-200'}`}>
                          Executive PDF Brief
                        </h4>
                        <p className={`text-xs ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                          Publication-ready ReportLab PDF document with health audits, deduction formulas, and statistical observations.
                        </p>
                      </div>
                      <a 
                        href={getExportUrl('pdf')}
                        className="mt-6 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold py-2.5 px-4 rounded-xl text-center transition-all shadow-md shadow-indigo-600/30"
                      >
                        Download PDF Document
                      </a>
                    </div>

                    <div className={`p-6 rounded-2xl border flex flex-col justify-between shadow-sm ${
                      isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                    }`}>
                      <div>
                        <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-500 flex items-center justify-center mb-3">
                          <Table className="w-5 h-5" />
                        </div>
                        <h4 className={`font-bold text-sm mb-1 ${isLight ? 'text-slate-900' : 'text-slate-200'}`}>
                          Cleaned Dataset (CSV)
                        </h4>
                        <p className={`text-xs ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                          Verified working dataset copy exported in clean UTF-8 comma-separated format.
                        </p>
                      </div>
                      <a 
                        href={getExportUrl('csv')}
                        className={`mt-6 border text-xs font-semibold py-2.5 px-4 rounded-xl text-center transition-all ${
                          isLight 
                            ? 'bg-slate-100 hover:bg-slate-200 text-slate-800 border-slate-300' 
                            : 'bg-[#111c38] hover:bg-[#16254a] border-slate-700 text-slate-200'
                        }`}
                      >
                        Download CSV File
                      </a>
                    </div>

                    <div className={`p-6 rounded-2xl border flex flex-col justify-between shadow-sm ${
                      isLight ? 'bg-white border-slate-200' : 'bg-[#070d1d] border-slate-800'
                    }`}>
                      <div>
                        <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-500 flex items-center justify-center mb-3">
                          <Download className="w-5 h-5" />
                        </div>
                        <h4 className={`font-bold text-sm mb-1 ${isLight ? 'text-slate-900' : 'text-slate-200'}`}>
                          Cleaned Excel (.xlsx)
                        </h4>
                        <p className={`text-xs ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                          Formatted Excel workbook generated with OpenPyXL for native spreadsheet workflows.
                        </p>
                      </div>
                      <a 
                        href={getExportUrl('excel')}
                        className={`mt-6 border text-xs font-semibold py-2.5 px-4 rounded-xl text-center transition-all ${
                          isLight 
                            ? 'bg-slate-100 hover:bg-slate-200 text-slate-800 border-slate-300' 
                            : 'bg-[#111c38] hover:bg-[#16254a] border-slate-700 text-slate-200'
                        }`}
                      >
                        Download Excel (.xlsx)
                      </a>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}