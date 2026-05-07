import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Cell } from 'recharts';
import { Activity, Shield, Droplets, Brain, Clock, Database, CheckCircle, AlertTriangle, TrendingUp, Cpu } from 'lucide-react';
import { getModels, getTrainingReport } from '../utils/api';
import LoadingSpinner from '../components/UI/LoadingSpinner';

const MODEL_META = {
  activity_bbbp: {
    name: 'BBB Penetration',
    icon: <Brain className="w-5 h-5" />,
    color: '#6366f1',
    gradient: 'from-indigo-500 to-violet-600',
    description: 'Predicts if a molecule can cross the blood-brain barrier',
    dataset: 'BBBP (MoleculeNet)',
    primaryMetric: 'roc_auc',
    primaryLabel: 'ROC-AUC',
  },
  toxicity_tox21: {
    name: 'Toxicity (Tox21)',
    icon: <Shield className="w-5 h-5" />,
    color: '#ef4444',
    gradient: 'from-rose-500 to-red-600',
    description: '12-endpoint toxicity panel (nuclear receptors + stress response)',
    dataset: 'Tox21 (NIH/MoleculeNet)',
    primaryMetric: 'mean_roc_auc',
    primaryLabel: 'Mean AUC',
  },
  solubility_esol: {
    name: 'Solubility',
    icon: <Droplets className="w-5 h-5" />,
    color: '#06b6d4',
    gradient: 'from-cyan-500 to-teal-600',
    description: 'Predicts aqueous solubility (logS) of a molecule',
    dataset: 'ESOL (MoleculeNet)',
    primaryMetric: 'r2',
    primaryLabel: 'R²',
  },
  activity_bace: {
    name: 'BACE-1 Inhibition',
    icon: <Activity className="w-5 h-5" />,
    color: '#f59e0b',
    gradient: 'from-amber-500 to-orange-600',
    description: 'Predicts beta-secretase 1 inhibition (Alzheimer\'s target)',
    dataset: 'BACE (MoleculeNet)',
    primaryMetric: 'roc_auc',
    primaryLabel: 'ROC-AUC',
  },
};

const TOX_ENDPOINT_NAMES = {
  'NR-AR': 'Androgen Receptor',
  'NR-AR-LBD': 'AR Ligand Binding',
  'NR-AhR': 'Aryl Hydrocarbon Receptor',
  'NR-Aromatase': 'Aromatase',
  'NR-ER': 'Estrogen Receptor',
  'NR-ER-LBD': 'ER Ligand Binding',
  'NR-PPAR-gamma': 'PPAR-gamma',
  'SR-ARE': 'Antioxidant Response',
  'SR-ATAD5': 'Genotoxicity',
  'SR-HSE': 'Heat Shock Response',
  'SR-MMP': 'Mitochondrial Membrane',
  'SR-p53': 'Tumor Suppressor p53',
};

function ScoreGauge({ value, label, color, maxValue = 1 }) {
  const percentage = Math.min((value / maxValue) * 100, 100);
  const displayValue = maxValue === 1 ? (value * 100).toFixed(1) + '%' : value.toFixed(3);
  
  return (
    <div className="flex flex-col items-center">
      <div className="relative w-20 h-20">
        <svg className="w-20 h-20 transform -rotate-90" viewBox="0 0 72 72">
          <circle cx="36" cy="36" r="30" fill="none" stroke="currentColor" strokeWidth="6" className="text-surface-200 dark:text-surface-700" />
          <circle cx="36" cy="36" r="30" fill="none" stroke={color} strokeWidth="6" strokeLinecap="round"
            strokeDasharray={`${percentage * 1.885} 188.5`}
            className="transition-all duration-1000 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-sm font-bold text-surface-900 dark:text-surface-100">{displayValue}</span>
        </div>
      </div>
      <span className="text-xs text-surface-500 dark:text-surface-400 mt-1 font-medium">{label}</span>
    </div>
  );
}

function MetricBar({ label, value, maxValue = 1, color }) {
  const pct = Math.min((value / maxValue) * 100, 100);
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-surface-600 dark:text-surface-400 font-medium">{label}</span>
        <span className="text-surface-900 dark:text-surface-100 font-semibold">{(value * 100).toFixed(1)}%</span>
      </div>
      <div className="h-2.5 bg-surface-200 dark:bg-surface-700 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all duration-1000 ease-out" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
    </div>
  );
}

export default function ModelPerformancePage() {
  const [models, setModels] = useState([]);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedModel, setSelectedModel] = useState(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const [modelsRes, reportRes] = await Promise.all([getModels(), getTrainingReport()]);
        
        if (modelsRes.success) setModels(modelsRes.models);
        if (reportRes.success) setReport(reportRes.report);
      } catch (err) {
        setError('Failed to load model data. Make sure the backend is running.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner text="Loading model metrics..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="card text-center max-w-md">
          <AlertTriangle className="w-12 h-12 text-amber-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-surface-900 dark:text-surface-100 mb-2">Connection Error</h2>
          <p className="text-surface-500 dark:text-surface-400">{error}</p>
        </div>
      </div>
    );
  }

  // Build summary data for the overview chart
  const overviewData = models.map(m => {
    const meta = MODEL_META[m.model_id] || {};
    const metrics = m.metrics || {};
    let score = 0;
    if (metrics.roc_auc) score = metrics.roc_auc;
    else if (metrics.mean_roc_auc) score = metrics.mean_roc_auc;
    else if (metrics.r2) score = metrics.r2;

    return {
      name: meta.name || m.model_id,
      score: parseFloat((score * 100).toFixed(1)),
      color: meta.color || '#6366f1',
      model_id: m.model_id,
    };
  });

  // Radar chart data
  const radarData = models.map(m => {
    const meta = MODEL_META[m.model_id] || {};
    const metrics = m.metrics || {};
    let score = metrics.roc_auc || metrics.mean_roc_auc || metrics.r2 || 0;
    return { subject: meta.name || m.model_id, score: parseFloat((score * 100).toFixed(1)), fullMark: 100 };
  });

  // Tox21 endpoint chart data
  const toxModel = report?.models?.toxicity_tox21;
  const toxEndpointData = toxModel?.endpoint_metrics
    ? Object.entries(toxModel.endpoint_metrics).map(([key, val]) => ({
        name: TOX_ENDPOINT_NAMES[key] || key,
        endpoint: key,
        auc: parseFloat((val.roc_auc * 100).toFixed(1)),
        accuracy: parseFloat((val.accuracy * 100).toFixed(1)),
        color: val.roc_auc >= 0.85 ? '#10b981' : val.roc_auc >= 0.75 ? '#f59e0b' : '#ef4444',
      }))
    : [];

  const totalMolecules = report ? Object.values(report.models).reduce((sum, m) => sum + (m.total_molecules || 0), 0) : 0;
  const trainingTime = report?.total_time_seconds ? report.total_time_seconds.toFixed(1) : '—';

  return (
    <div className="section bg-surface-50 dark:bg-surface-950 min-h-screen">
      <div className="container-narrow">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-100 dark:bg-primary-900/50 text-primary-700 dark:text-primary-300 text-sm font-medium mb-4">
            <TrendingUp className="w-4 h-4" />
            Model Transparency
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-surface-900 dark:text-surface-100 mb-3">
            Model <span className="gradient-text">Performance</span>
          </h1>
          <p className="text-surface-500 dark:text-surface-400 max-w-2xl mx-auto">
            All models are trained on peer-reviewed MoleculeNet benchmark datasets using XGBoost with 2048-bit Morgan fingerprints and scaffold splitting.
          </p>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
          {[
            { icon: <Cpu className="w-5 h-5" />, label: 'Models Trained', value: report?.n_models_trained || models.length, color: 'text-indigo-500' },
            { icon: <Database className="w-5 h-5" />, label: 'Total Molecules', value: totalMolecules.toLocaleString(), color: 'text-cyan-500' },
            { icon: <Clock className="w-5 h-5" />, label: 'Training Time', value: `${trainingTime}s`, color: 'text-amber-500' },
            { icon: <CheckCircle className="w-5 h-5" />, label: 'Errors', value: report?.n_errors ?? '—', color: 'text-emerald-500' },
          ].map((stat, i) => (
            <div key={i} className="card text-center">
              <div className={`${stat.color} mx-auto mb-2`}>{stat.icon}</div>
              <div className="text-2xl font-bold text-surface-900 dark:text-surface-100">{stat.value}</div>
              <div className="text-xs text-surface-500 dark:text-surface-400">{stat.label}</div>
            </div>
          ))}
        </div>

        {/* Overview Chart */}
        <div className="card mb-10">
          <h2 className="text-lg font-bold text-surface-900 dark:text-surface-100 mb-6">Model Score Comparison</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Bar chart */}
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={overviewData} layout="vertical" margin={{ left: 20, right: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="text-surface-200 dark:text-surface-700" />
                  <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 12 }} stroke="currentColor" className="text-surface-400" />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 12 }} width={100} stroke="currentColor" className="text-surface-400" />
                  <Tooltip contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 8px 30px rgba(0,0,0,0.12)' }}
                    formatter={(val) => [`${val}%`, 'Score']} />
                  <Bar dataKey="score" radius={[0, 6, 6, 0]} barSize={24}>
                    {overviewData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Radar chart */}
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData}>
                  <PolarGrid stroke="currentColor" className="text-surface-200 dark:text-surface-700" />
                  <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11 }} stroke="currentColor" className="text-surface-500" />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 10 }} stroke="currentColor" className="text-surface-400" />
                  <Radar dataKey="score" stroke="#6366f1" fill="#6366f1" fillOpacity={0.25} strokeWidth={2} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Individual Model Cards */}
        <h2 className="text-lg font-bold text-surface-900 dark:text-surface-100 mb-4">Detailed Model Metrics</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
          {models.map(m => {
            const meta = MODEL_META[m.model_id] || { name: m.model_id, color: '#6366f1', gradient: 'from-indigo-500 to-violet-600' };
            const metrics = m.metrics || {};
            const isClassification = metrics.task_type === 'classification' || metrics.task_type === 'multilabel_classification';

            return (
              <div key={m.model_id} className="card-hover cursor-pointer" onClick={() => setSelectedModel(selectedModel === m.model_id ? null : m.model_id)}>
                {/* Card header */}
                <div className="flex items-start gap-3 mb-4">
                  <div className={`w-10 h-10 rounded-xl bg-gradient-to-r ${meta.gradient} flex items-center justify-center text-white shrink-0`}>
                    {meta.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-bold text-surface-900 dark:text-surface-100">{meta.name}</h3>
                    <p className="text-xs text-surface-500 dark:text-surface-400">{meta.description}</p>
                  </div>
                  <ScoreGauge
                    value={metrics[meta.primaryMetric] || 0}
                    label={meta.primaryLabel}
                    color={meta.color}
                    maxValue={1}
                  />
                </div>

                {/* Quick stats */}
                <div className="flex flex-wrap gap-2 mb-3">
                  <span className="badge-info">{meta.dataset}</span>
                  <span className="badge bg-surface-100 dark:bg-surface-800 text-surface-600 dark:text-surface-300">
                    {(metrics.total_molecules || metrics.train_samples || 0).toLocaleString()} molecules
                  </span>
                  <span className="badge bg-surface-100 dark:bg-surface-800 text-surface-600 dark:text-surface-300">
                    {metrics.model_type || 'xgboost'}
                  </span>
                  {metrics.use_scaffold_split && (
                    <span className="badge-success">Scaffold Split</span>
                  )}
                </div>

                {/* Detailed metrics */}
                {isClassification && metrics.task_type !== 'multilabel_classification' && (
                  <div className="space-y-2 mt-4">
                    <MetricBar label="ROC-AUC" value={metrics.roc_auc || 0} color={meta.color} />
                    <MetricBar label="Accuracy" value={metrics.accuracy || 0} color={meta.color} />
                    <MetricBar label="Precision" value={metrics.precision || 0} color={meta.color} />
                    <MetricBar label="Recall" value={metrics.recall || 0} color={meta.color} />
                    <MetricBar label="F1 Score" value={metrics.f1_score || 0} color={meta.color} />
                  </div>
                )}

                {metrics.task_type === 'regression' && (
                  <div className="grid grid-cols-3 gap-3 mt-4">
                    {[
                      { label: 'R²', value: metrics.r2?.toFixed(4) },
                      { label: 'RMSE', value: metrics.rmse?.toFixed(4) },
                      { label: 'MAE', value: metrics.mae?.toFixed(4) },
                    ].map((s, i) => (
                      <div key={i} className="text-center p-2 rounded-lg bg-surface-50 dark:bg-surface-800/50">
                        <div className="text-lg font-bold text-surface-900 dark:text-surface-100">{s.value || '—'}</div>
                        <div className="text-xs text-surface-500">{s.label}</div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Multilabel (Tox21) — show endpoint count */}
                {metrics.task_type === 'multilabel_classification' && (
                  <div className="mt-4 text-sm text-surface-500 dark:text-surface-400 flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-emerald-500" />
                    {metrics.n_trained}/{metrics.n_endpoints} endpoints trained • Click to expand
                  </div>
                )}

                {/* Expanded Tox21 details */}
                {selectedModel === m.model_id && metrics.task_type === 'multilabel_classification' && toxEndpointData.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-surface-200 dark:border-surface-700 animate-slide-down">
                    <h4 className="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Tox21 Endpoint AUC Scores</h4>
                    <div className="h-72">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={toxEndpointData} layout="vertical" margin={{ left: 10, right: 20 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="text-surface-200 dark:text-surface-700" />
                          <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10 }} stroke="currentColor" className="text-surface-400" />
                          <YAxis type="category" dataKey="name" tick={{ fontSize: 10 }} width={130} stroke="currentColor" className="text-surface-400" />
                          <Tooltip formatter={(val) => [`${val}%`, 'AUC']} contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 8px 30px rgba(0,0,0,0.12)' }} />
                          <Bar dataKey="auc" radius={[0, 4, 4, 0]} barSize={16}>
                            {toxEndpointData.map((entry, i) => (
                              <Cell key={i} fill={entry.color} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}

                {/* Trained timestamp */}
                {metrics.trained_at && (
                  <div className="mt-3 text-xs text-surface-400 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    Trained: {new Date(metrics.trained_at).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Training Info */}
        {report && (
          <div className="card text-center text-sm text-surface-500 dark:text-surface-400">
            <p>
              Training completed on{' '}
              <strong className="text-surface-700 dark:text-surface-300">
                {new Date(report.completed_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
              </strong>{' '}
              in <strong className="text-surface-700 dark:text-surface-300">{trainingTime} seconds</strong> •{' '}
              All models use XGBoost with 2048-bit Morgan fingerprints
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
