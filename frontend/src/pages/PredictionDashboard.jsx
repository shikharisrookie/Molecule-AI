import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend, Tooltip as RechartTooltip, Cell } from 'recharts';
import { ArrowLeft, Eye, Download, CheckCircle, AlertTriangle, XCircle, FlaskConical, Atom, TrendingUp, ShieldAlert, Info, Droplets, Brain, Search, Shield, Beaker } from 'lucide-react';
import Tooltip from '../components/UI/Tooltip';
import { getMoleculeInfo, exportHistory, searchSimilar } from '../utils/api';

const PROPERTY_EXPLANATIONS = {
  molecular_weight: "The mass of the molecule. Most successful drugs weigh less than 500 g/mol.",
  logp: "How easily the molecule dissolves in fat vs water. A value between 0-5 is ideal.",
  hbd: "Parts that can donate hydrogen bonds. Fewer donors (≤5) means better absorption.",
  hba: "Parts that can accept hydrogen bonds. Fewer acceptors (≤10) is preferred.",
  tpsa: "Polar surface area. Lower values suggest better membrane penetration.",
  rotatable_bonds: "Flexible connections. Fewer (≤10) often means better bioavailability.",
  aromatic_rings: "Ring-shaped structures. Most drugs have 1-3 aromatic rings.",
  qed_score: "Overall drug-likeness from 0 to 1. Most approved drugs score above 0.3.",
  lipinski_violations: "Lipinski Rule violations. Zero means likely good oral drug.",
};

function ScoreGauge({ value, max = 1, label, color, size = 'lg' }) {
  const pct = Math.min(value / max, 1) * 100;
  const circumference = 2 * Math.PI * 40;
  const offset = circumference - (pct / 100) * circumference;
  const sz = size === 'lg' ? 'w-28 h-28' : 'w-20 h-20';
  const textSz = size === 'lg' ? 'text-2xl' : 'text-lg';

  return (
    <div className="flex flex-col items-center gap-2">
      <div className={`relative ${sz}`}>
        <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" strokeWidth="8" className="text-surface-200 dark:text-surface-700" />
          <circle cx="50" cy="50" r="40" fill="none" stroke={color} strokeWidth="8" strokeLinecap="round"
            strokeDasharray={circumference} strokeDashoffset={offset}
            style={{ transition: 'stroke-dashoffset 1s ease' }} />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={`${textSz} font-bold text-surface-900 dark:text-surface-100`}>
            {typeof value === 'number' ? (value * 100).toFixed(0) : value}
            <span className="text-xs text-surface-400">%</span>
          </span>
        </div>
      </div>
      <span className="text-xs font-medium text-surface-500 dark:text-surface-400">{label}</span>
    </div>
  );
}

function VerdictBanner({ verdict, summary }) {
  const config = {
    Promising: { icon: <CheckCircle className="w-6 h-6" />, bg: 'bg-emerald-50 dark:bg-emerald-900/20', border: 'border-emerald-200 dark:border-emerald-800', text: 'text-emerald-700 dark:text-emerald-300', iconColor: 'text-emerald-500' },
    Moderate: { icon: <AlertTriangle className="w-6 h-6" />, bg: 'bg-amber-50 dark:bg-amber-900/20', border: 'border-amber-200 dark:border-amber-800', text: 'text-amber-700 dark:text-amber-300', iconColor: 'text-amber-500' },
    Poor: { icon: <XCircle className="w-6 h-6" />, bg: 'bg-red-50 dark:bg-red-900/20', border: 'border-red-200 dark:border-red-800', text: 'text-red-700 dark:text-red-300', iconColor: 'text-red-500' },
  };
  const c = config[verdict] || config.Moderate;

  return (
    <div className={`p-4 rounded-xl border ${c.bg} ${c.border} animate-scale-in`}>
      <div className="flex items-start gap-3">
        <div className={c.iconColor}>{c.icon}</div>
        <div>
          <h3 className={`font-bold ${c.text} mb-1`}>Verdict: {verdict}</h3>
          <p className={`text-sm ${c.text} opacity-80`}>{summary}</p>
        </div>
      </div>
    </div>
  );
}

export default function PredictionDashboard() {
  const navigate = useNavigate();
  const [prediction, setPrediction] = useState(null);
  const [moleculeInfo, setMoleculeInfo] = useState(null);
  const [similarDrugs, setSimilarDrugs] = useState([]);

  useEffect(() => {
    const stored = sessionStorage.getItem('predictionResult');
    if (stored) {
      const p = JSON.parse(stored);
      setPrediction(p);
      // Also fetch molecule info for 3D viewer
      getMoleculeInfo(p.canonical_smiles || p.smiles).then(data => {
        if (data.success) setMoleculeInfo(data);
      }).catch(() => {});
      // Fetch similar drugs
      searchSimilar(p.canonical_smiles || p.smiles, 5).then(data => {
        if (data.success) setSimilarDrugs(data.similar_molecules || []);
      }).catch(() => {});
    }
  }, []);

  if (!prediction) {
    return (
      <div className="section">
        <div className="container-narrow text-center">
          <div className="card max-w-md mx-auto">
            <FlaskConical className="w-12 h-12 text-surface-300 dark:text-surface-600 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-surface-900 dark:text-surface-100 mb-2">No Prediction Yet</h2>
            <p className="text-surface-500 dark:text-surface-400 mb-6">Analyze a molecule first to see results here.</p>
            <Link to="/analyze" className="btn-primary inline-flex items-center gap-2">
              <FlaskConical className="w-4 h-4" />
              Analyze a Molecule
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const props = prediction.molecular_properties;
  
  // Radar chart data
  const radarData = [
    { property: 'Drug-likeness', value: prediction.drug_likeness_score * 100, ideal: 50 },
    { property: 'Activity', value: prediction.activity_probability * 100, ideal: 70 },
    { property: 'Safety', value: (1 - prediction.toxicity_score) * 100, ideal: 80 },
    { property: 'Lipinski', value: ((4 - props.lipinski_violations) / 4) * 100, ideal: 100 },
    { property: 'Bioavail.', value: Math.min(props.tpsa / 1.4, 100), ideal: 70 },
  ];

  // Property comparison chart
  const barData = [
    { name: 'MW', value: props.molecular_weight, ideal: 500, unit: 'g/mol', fill: props.molecular_weight <= 500 ? '#10b981' : '#ef4444' },
    { name: 'LogP', value: Math.abs(props.logp), ideal: 5, unit: '', fill: props.logp >= 0 && props.logp <= 5 ? '#10b981' : '#ef4444' },
    { name: 'HBD', value: props.hbd, ideal: 5, unit: '', fill: props.hbd <= 5 ? '#10b981' : '#ef4444' },
    { name: 'HBA', value: props.hba, ideal: 10, unit: '', fill: props.hba <= 10 ? '#10b981' : '#ef4444' },
    { name: 'RotBonds', value: props.rotatable_bonds, ideal: 10, unit: '', fill: props.rotatable_bonds <= 10 ? '#10b981' : '#ef4444' },
  ];

  const toxColor = prediction.toxicity_score < 0.3 ? '#10b981' : prediction.toxicity_score < 0.6 ? '#f59e0b' : '#ef4444';
  const actColor = prediction.activity_probability >= 0.7 ? '#10b981' : prediction.activity_probability >= 0.4 ? '#f59e0b' : '#ef4444';
  const drugColor = prediction.drug_likeness_score >= 0.5 ? '#10b981' : prediction.drug_likeness_score >= 0.3 ? '#f59e0b' : '#ef4444';

  return (
    <div className="section">
      <div className="container-narrow">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <button onClick={() => navigate('/analyze')} className="flex items-center gap-1 text-sm text-surface-500 hover:text-primary-600 mb-2 transition-colors">
              <ArrowLeft className="w-4 h-4" /> Back to Input
            </button>
            <h1 className="text-2xl md:text-3xl font-bold text-surface-900 dark:text-surface-100" id="dashboard-title">
              Prediction Results
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <Link to="/visualize" className="btn-secondary flex items-center gap-2 text-sm" id="view-3d-button">
              <Eye className="w-4 h-4" /> View 3D
            </Link>
            <button onClick={() => exportHistory('csv')} className="btn-secondary flex items-center gap-2 text-sm" id="export-button">
              <Download className="w-4 h-4" /> Export CSV
            </button>
          </div>
        </div>

        {/* Molecule Info */}
        <div className="card mb-6">
          <div className="flex items-center gap-3 flex-wrap">
            <span className="text-xs font-semibold text-surface-500 dark:text-surface-400">SMILES:</span>
            <code className="text-sm font-mono text-primary-600 dark:text-primary-400 bg-primary-50 dark:bg-primary-900/30 px-3 py-1 rounded-lg break-all">
              {prediction.canonical_smiles}
            </code>
            {prediction.confidence != null && (
              <span className={`ml-auto text-xs font-medium px-2 py-1 rounded-full ${
                prediction.confidence >= 0.75 ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300' :
                prediction.confidence >= 0.5 ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300' :
                'bg-surface-100 dark:bg-surface-800 text-surface-600 dark:text-surface-400'
              }`}>
                Model confidence: {(prediction.confidence * 100).toFixed(0)}%
              </span>
            )}
          </div>
        </div>

        {/* Verdict Banner */}
        <div className="mb-6">
          <VerdictBanner verdict={prediction.verdict} summary={prediction.plain_language_summary} />
        </div>

        {/* Score Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="card text-center">
            <ScoreGauge value={prediction.drug_likeness_score} label="Drug-Likeness" color={drugColor} />
            <p className="text-xs text-surface-500 dark:text-surface-400 mt-2">QED Score — higher is better</p>
          </div>
          <div className="card text-center">
            <ScoreGauge value={1 - prediction.toxicity_score} label="Safety Score" color={toxColor} />
            <div className="mt-2">
              <span className={`badge ${prediction.toxicity_risk === 'Low' ? 'badge-success' : prediction.toxicity_risk === 'Medium' ? 'badge-warning' : 'badge-danger'}`}>
                {prediction.toxicity_risk} Risk
              </span>
            </div>
          </div>
          <div className="card text-center">
            <ScoreGauge value={prediction.activity_probability} label="Activity" color={actColor} />
            <p className="text-xs text-surface-500 dark:text-surface-400 mt-2">Probability of biological activity</p>
          </div>
        </div>

        {/* NEW: Extended Predictions Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          {/* BBB Penetration */}
          {prediction.bbb_penetration != null && (
            <div className="card py-4">
              <div className="flex items-center gap-2 mb-2">
                <Brain className="w-4 h-4 text-indigo-500" />
                <span className="text-sm font-bold text-surface-900 dark:text-surface-100">BBB Penetration</span>
              </div>
              <div className="text-2xl font-bold text-surface-900 dark:text-surface-100">
                {(prediction.bbb_penetration * 100).toFixed(0)}%
              </div>
              <p className="text-xs text-surface-500 dark:text-surface-400 mt-1">
                {prediction.bbb_penetration >= 0.7 ? 'Likely crosses blood-brain barrier' :
                 prediction.bbb_penetration >= 0.4 ? 'Uncertain BBB penetration' :
                 'Unlikely to cross BBB'}
              </p>
            </div>
          )}

          {/* Solubility */}
          {prediction.solubility && (
            <div className="card py-4">
              <div className="flex items-center gap-2 mb-2">
                <Droplets className="w-4 h-4 text-blue-500" />
                <span className="text-sm font-bold text-surface-900 dark:text-surface-100">Solubility</span>
              </div>
              <div className="text-2xl font-bold text-surface-900 dark:text-surface-100">
                {prediction.solubility.log_s?.toFixed(2)}
                <span className="text-sm font-normal text-surface-400 ml-1">logS</span>
              </div>
              <span className={`inline-block mt-1 text-xs font-medium px-2 py-0.5 rounded-full ${
                prediction.solubility.category === 'Very Soluble' || prediction.solubility.category === 'Soluble'
                  ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300'
                  : prediction.solubility.category === 'Moderately Soluble'
                  ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300'
                  : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
              }`}>
                {prediction.solubility.category}
              </span>
            </div>
          )}

          {/* BACE Inhibition */}
          {prediction.bace_inhibition != null && (
            <div className="card py-4">
              <div className="flex items-center gap-2 mb-2">
                <Beaker className="w-4 h-4 text-violet-500" />
                <span className="text-sm font-bold text-surface-900 dark:text-surface-100">BACE-1 Inhibition</span>
              </div>
              <div className="text-2xl font-bold text-surface-900 dark:text-surface-100">
                {(prediction.bace_inhibition * 100).toFixed(0)}%
              </div>
              <p className="text-xs text-surface-500 dark:text-surface-400 mt-1">
                Alzheimer's target (β-secretase)
              </p>
            </div>
          )}
        </div>

        {/* NEW: Toxicity Profile (Tox21) */}
        {prediction.toxicity_profile && Object.keys(prediction.toxicity_profile.endpoint_scores || {}).length > 0 && (
          <div className="card mb-8">
            <h3 className="text-sm font-bold text-surface-900 dark:text-surface-100 mb-4 flex items-center gap-2">
              <Shield className="w-4 h-4 text-rose-500" /> Toxicity Profile (Tox21 — 12 Endpoints)
            </h3>
            {prediction.toxicity_profile.high_risk_endpoints?.length > 0 && (
              <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-sm text-red-700 dark:text-red-300">
                ⚠️ High-risk endpoints: {prediction.toxicity_profile.high_risk_endpoints.join(', ')}
              </div>
            )}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {Object.entries(prediction.toxicity_profile.endpoint_scores).map(([endpoint, score]) => (
                <div key={endpoint} className={`p-3 rounded-lg border ${
                  score > 0.5 ? 'bg-red-50 dark:bg-red-900/10 border-red-200 dark:border-red-800' :
                  score > 0.3 ? 'bg-amber-50 dark:bg-amber-900/10 border-amber-200 dark:border-amber-800' :
                  'bg-emerald-50 dark:bg-emerald-900/10 border-emerald-200 dark:border-emerald-800'
                }`}>
                  <div className="text-xs font-medium text-surface-600 dark:text-surface-400 mb-1 truncate" title={endpoint}>
                    {endpoint}
                  </div>
                  <div className={`text-lg font-bold ${
                    score > 0.5 ? 'text-red-600 dark:text-red-400' :
                    score > 0.3 ? 'text-amber-600 dark:text-amber-400' :
                    'text-emerald-600 dark:text-emerald-400'
                  }`}>
                    {(score * 100).toFixed(0)}%
                  </div>
                  <div className="w-full bg-surface-200 dark:bg-surface-700 rounded-full h-1 mt-1">
                    <div className={`h-1 rounded-full ${
                      score > 0.5 ? 'bg-red-500' : score > 0.3 ? 'bg-amber-500' : 'bg-emerald-500'
                    }`} style={{ width: `${score * 100}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tips */}
        {prediction.tips && prediction.tips.length > 0 && (
          <div className="card mb-8">
            <h3 className="text-sm font-bold text-surface-900 dark:text-surface-100 mb-3 flex items-center gap-2">
              <Info className="w-4 h-4 text-primary-500" /> Key Insights
            </h3>
            <ul className="space-y-2">
              {prediction.tips.map((tip, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-surface-600 dark:text-surface-400">
                  <span className="text-primary-500 mt-1">•</span>
                  {tip}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Radar Chart */}
          <div className="card">
            <h3 className="text-sm font-bold text-surface-900 dark:text-surface-100 mb-4 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-primary-500" /> Property Radar
            </h3>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#94a3b8" strokeOpacity={0.2} />
                  <PolarAngleAxis dataKey="property" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} />
                  <Radar name="Molecule" dataKey="value" stroke="#6366f1" fill="#6366f1" fillOpacity={0.3} strokeWidth={2} />
                  <Radar name="Ideal" dataKey="ideal" stroke="#14b8a6" fill="#14b8a6" fillOpacity={0.1} strokeDasharray="5 5" />
                  <RechartTooltip />
                  <Legend />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Bar Chart */}
          <div className="card">
            <h3 className="text-sm font-bold text-surface-900 dark:text-surface-100 mb-4 flex items-center gap-2">
              <Atom className="w-4 h-4 text-accent-500" /> Lipinski Properties
            </h3>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={barData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#94a3b8" strokeOpacity={0.1} />
                  <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                  <YAxis dataKey="name" type="category" tick={{ fill: '#94a3b8', fontSize: 11 }} width={60} />
                  <RechartTooltip formatter={(value, name, props) => [value.toFixed(2), props.payload.name]} />
                  <Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={20}>
                    {barData.map((entry, idx) => <Cell key={idx} fill={entry.fill} />)}
                  </Bar>
                  <Bar dataKey="ideal" fill="#94a3b8" fillOpacity={0.2} radius={[0, 6, 6, 0]} barSize={20} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <p className="text-xs text-surface-400 mt-2">Green = within ideal range, Red = exceeds limit, Gray = threshold</p>
          </div>
        </div>

        {/* Similar Drugs */}
        {similarDrugs.length > 0 && (
          <div className="card mb-8">
            <h3 className="text-sm font-bold text-surface-900 dark:text-surface-100 mb-4 flex items-center gap-2">
              <Search className="w-4 h-4 text-teal-500" /> Similar Approved Drugs
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {similarDrugs.slice(0, 6).map((drug, i) => (
                <div key={i} className="p-3 rounded-xl bg-surface-50 dark:bg-surface-800/50 border border-surface-200 dark:border-surface-700">
                  <div className="flex justify-between items-start">
                    <span className="font-semibold text-sm text-surface-900 dark:text-surface-100">{drug.name}</span>
                    <span className={`text-sm font-bold ${
                      drug.similarity >= 0.5 ? 'text-emerald-600 dark:text-emerald-400' : 'text-surface-500'
                    }`}>
                      {(drug.similarity * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-xs text-surface-500 dark:text-surface-400 mt-1">{drug.indication}</p>
                </div>
              ))}
            </div>
            <Link to="/similarity" className="inline-flex items-center gap-1 text-sm text-primary-600 dark:text-primary-400 hover:underline mt-3">
              View all similar drugs →
            </Link>
          </div>
        )}

        {/* Properties Table */}
        <div className="card mb-6">
          <h3 className="text-sm font-bold text-surface-900 dark:text-surface-100 mb-4 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-accent-500" /> Molecular Properties
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface-200 dark:border-surface-700">
                  <th className="py-2 px-3 text-left text-xs font-semibold text-surface-500 dark:text-surface-400">Property</th>
                  <th className="py-2 px-3 text-left text-xs font-semibold text-surface-500 dark:text-surface-400">Value</th>
                  <th className="py-2 px-3 text-left text-xs font-semibold text-surface-500 dark:text-surface-400 hidden md:table-cell">What It Means</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(props).map(([key, value]) => (
                  <tr key={key} className="border-b border-surface-100 dark:border-surface-800 hover:bg-surface-50 dark:hover:bg-surface-800/50 transition-colors">
                    <td className="py-3 px-3">
                      <Tooltip text={PROPERTY_EXPLANATIONS[key] || ''}>
                        <span className="font-medium text-surface-700 dark:text-surface-300">
                          {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </span>
                      </Tooltip>
                    </td>
                    <td className="py-3 px-3 font-mono text-surface-900 dark:text-surface-100">
                      {typeof value === 'number' ? value.toFixed(value % 1 === 0 ? 0 : 2) : value}
                    </td>
                    <td className="py-3 px-3 text-surface-500 dark:text-surface-400 text-xs hidden md:table-cell">
                      {PROPERTY_EXPLANATIONS[key] || ''}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Model Versions */}
        {prediction.model_versions && Object.keys(prediction.model_versions).length > 0 && (
          <div className="card mb-6">
            <h3 className="text-xs font-bold text-surface-500 dark:text-surface-400 mb-3 uppercase tracking-wider">
              Models Used
            </h3>
            <div className="flex flex-wrap gap-2">
              {Object.entries(prediction.model_versions).map(([key, value]) => (
                <span key={key} className="text-xs px-2 py-1 rounded-full bg-surface-100 dark:bg-surface-800 text-surface-600 dark:text-surface-400">
                  {key}: {value}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* 2D Structure Preview */}
        {moleculeInfo?.svg_2d && (
          <div className="card">
            <h3 className="text-sm font-bold text-surface-900 dark:text-surface-100 mb-4">2D Structure</h3>
            <div className="flex justify-center bg-white rounded-xl p-4" dangerouslySetInnerHTML={{ __html: moleculeInfo.svg_2d }} />
          </div>
        )}
      </div>
    </div>
  );
}
