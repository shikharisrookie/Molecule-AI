import { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, FlaskConical, RotateCw, Maximize2 } from 'lucide-react';
import { getMoleculeInfo } from '../utils/api';
import LoadingSpinner from '../components/UI/LoadingSpinner';

const STYLES = [
  { key: 'stick', label: 'Stick', config: { stick: { radius: 0.15 } } },
  { key: 'ball-stick', label: 'Ball & Stick', config: { stick: { radius: 0.1 }, sphere: { scale: 0.3 } } },
  { key: 'sphere', label: 'Sphere', config: { sphere: { scale: 0.5 } } },
  { key: 'line', label: 'Line', config: { line: {} } },
];

const COLORS = [
  { key: 'default', label: 'Element Colors' },
  { key: 'chain', label: 'Chain', scheme: 'chainHetatm' },
  { key: 'spectrum', label: 'Spectrum', scheme: 'spectrum' },
];

export default function VisualizationPage() {
  const navigate = useNavigate();
  const viewerRef = useRef(null);
  const viewerInstance = useRef(null);
  const [smiles, setSmiles] = useState('');
  const [molData, setMolData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeStyle, setActiveStyle] = useState('stick');
  const [error, setError] = useState('');
  const [lib3Dmol, setLib3Dmol] = useState(null);

  // Load 3Dmol.js dynamically
  useEffect(() => {
    const script = document.createElement('script');
    script.src = 'https://3dmol.org/build/3Dmol-min.js';
    script.async = true;
    script.onload = () => setLib3Dmol(window.$3Dmol);
    document.head.appendChild(script);
    return () => { if (document.head.contains(script)) document.head.removeChild(script); };
  }, []);

  // Load smiles from session
  useEffect(() => {
    const stored = sessionStorage.getItem('currentSmiles');
    if (stored) {
      setSmiles(stored);
      loadMolecule(stored);
    }
  }, []);

  const loadMolecule = async (smi) => {
    if (!smi.trim()) return;
    setLoading(true);
    setError('');
    try {
      const data = await getMoleculeInfo(smi.trim());
      if (data.success && data.mol_block_3d) {
        setMolData(data);
        sessionStorage.setItem('currentSmiles', smi.trim());
      } else {
        setError(data.error || 'Could not generate 3D structure for this molecule.');
      }
    } catch (err) {
      setError('Failed to load molecule data.');
    } finally {
      setLoading(false);
    }
  };

  // Render 3D viewer when data is available
  useEffect(() => {
    if (!lib3Dmol || !molData?.mol_block_3d || !viewerRef.current) return;

    // Clear existing
    if (viewerInstance.current) {
      viewerInstance.current.clear();
    }

    const viewer = lib3Dmol.createViewer(viewerRef.current, {
      backgroundColor: document.documentElement.classList.contains('dark') ? '#0f172a' : '#ffffff',
      antialias: true,
    });

    viewer.addModel(molData.mol_block_3d, 'sdf');
    const styleConfig = STYLES.find(s => s.key === activeStyle)?.config || { stick: {} };
    viewer.setStyle({}, styleConfig);
    viewer.zoomTo();
    viewer.render();
    viewer.zoom(0.8, 1000);

    viewerInstance.current = viewer;

    return () => {
      if (viewerInstance.current) {
        viewerInstance.current.clear();
        viewerInstance.current = null;
      }
    };
  }, [lib3Dmol, molData, activeStyle]);

  const handleStyleChange = (styleKey) => {
    setActiveStyle(styleKey);
    if (viewerInstance.current && molData) {
      const styleConfig = STYLES.find(s => s.key === styleKey)?.config || { stick: {} };
      viewerInstance.current.setStyle({}, styleConfig);
      viewerInstance.current.render();
    }
  };

  const resetView = () => {
    if (viewerInstance.current) {
      viewerInstance.current.zoomTo();
      viewerInstance.current.render();
    }
  };

  return (
    <div className="section">
      <div className="container-narrow">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-sm text-surface-500 hover:text-primary-600 mb-2 transition-colors">
              <ArrowLeft className="w-4 h-4" /> Back
            </button>
            <h1 className="text-2xl md:text-3xl font-bold text-surface-900 dark:text-surface-100" id="viz-title">
              3D Molecule <span className="gradient-text">Viewer</span>
            </h1>
          </div>
        </div>

        {/* SMILES Input */}
        <div className="card mb-6">
          <div className="flex gap-3">
            <input
              type="text"
              value={smiles}
              onChange={e => setSmiles(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && loadMolecule(smiles)}
              placeholder="Enter SMILES string..."
              className="input-field font-mono text-sm flex-1"
              id="viz-smiles-input"
            />
            <button onClick={() => loadMolecule(smiles)} className="btn-primary flex items-center gap-2 text-sm whitespace-nowrap" id="viz-load-button">
              <FlaskConical className="w-4 h-4" />
              Load
            </button>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl mb-6 text-sm text-red-600 dark:text-red-400">
            {error}
          </div>
        )}

        {loading && <LoadingSpinner text="Generating 3D structure..." />}

        {molData && !loading && (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* 3D Viewer */}
            <div className="lg:col-span-3">
              <div className="card p-0 overflow-hidden">
                <div className="flex items-center justify-between p-3 border-b border-surface-200 dark:border-surface-700">
                  <div className="flex gap-2">
                    {STYLES.map(s => (
                      <button
                        key={s.key}
                        onClick={() => handleStyleChange(s.key)}
                        className={`px-3 py-1 text-xs font-medium rounded-lg transition-all ${
                          activeStyle === s.key
                            ? 'bg-primary-100 dark:bg-primary-900/50 text-primary-700 dark:text-primary-300'
                            : 'text-surface-500 hover:bg-surface-100 dark:hover:bg-surface-800'
                        }`}
                      >
                        {s.label}
                      </button>
                    ))}
                  </div>
                  <button onClick={resetView} className="p-1.5 rounded-lg hover:bg-surface-100 dark:hover:bg-surface-800 text-surface-500" title="Reset view">
                    <RotateCw className="w-4 h-4" />
                  </button>
                </div>
                <div
                  ref={viewerRef}
                  className="w-full"
                  style={{ height: '500px', position: 'relative' }}
                  id="mol-viewer-3d"
                />
              </div>
            </div>

            {/* Info Sidebar */}
            <div className="space-y-4">
              <div className="card">
                <h3 className="text-sm font-bold text-surface-900 dark:text-surface-100 mb-3">Molecule Info</h3>
                <div className="space-y-2 text-xs">
                  <div>
                    <span className="text-surface-500 dark:text-surface-400">Formula:</span>
                    <p className="font-mono font-semibold text-surface-800 dark:text-surface-200">{molData.formula}</p>
                  </div>
                  <div>
                    <span className="text-surface-500 dark:text-surface-400">Mol. Weight:</span>
                    <p className="font-semibold text-surface-800 dark:text-surface-200">{molData.molecular_properties?.molecular_weight} g/mol</p>
                  </div>
                  <div>
                    <span className="text-surface-500 dark:text-surface-400">LogP:</span>
                    <p className="font-semibold text-surface-800 dark:text-surface-200">{molData.molecular_properties?.logp}</p>
                  </div>
                  <div>
                    <span className="text-surface-500 dark:text-surface-400">QED Score:</span>
                    <p className="font-semibold text-surface-800 dark:text-surface-200">{molData.molecular_properties?.qed_score}</p>
                  </div>
                </div>
              </div>

              {/* 2D Structure */}
              {molData.svg_2d && (
                <div className="card p-3">
                  <h3 className="text-sm font-bold text-surface-900 dark:text-surface-100 mb-2">2D View</h3>
                  <div className="bg-white rounded-lg p-2 flex justify-center" dangerouslySetInnerHTML={{ __html: molData.svg_2d }} />
                </div>
              )}

              <div className="card">
                <h3 className="text-sm font-bold text-surface-900 dark:text-surface-100 mb-2">Controls</h3>
                <ul className="text-xs text-surface-500 dark:text-surface-400 space-y-1">
                  <li>🖱️ <strong>Rotate:</strong> Click & drag</li>
                  <li>🔍 <strong>Zoom:</strong> Scroll wheel</li>
                  <li>✋ <strong>Pan:</strong> Right click & drag</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {!molData && !loading && !error && (
          <div className="card text-center py-16">
            <FlaskConical className="w-16 h-16 text-surface-300 dark:text-surface-600 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-surface-900 dark:text-surface-100 mb-2">No Molecule Loaded</h2>
            <p className="text-surface-500 dark:text-surface-400 mb-6">Enter a SMILES string above or analyze a molecule first.</p>
            <Link to="/analyze" className="btn-primary inline-flex items-center gap-2">
              Analyze a Molecule
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
