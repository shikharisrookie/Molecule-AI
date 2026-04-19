import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { Search, Upload, FlaskConical, ArrowRight, AlertCircle, FileText, X, Sparkles } from 'lucide-react';
import { predictMolecule, uploadDataset, getExampleMolecules } from '../utils/api';
import LoadingSpinner from '../components/UI/LoadingSpinner';

export default function MoleculeInputPage() {
  const navigate = useNavigate();
  const [smiles, setSmiles] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [examples, setExamples] = useState([]);
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadLoading, setUploadLoading] = useState(false);

  useEffect(() => {
    getExampleMolecules().then(data => setExamples(data.examples || [])).catch(() => {});
  }, []);

  const handleAnalyze = async () => {
    if (!smiles.trim()) {
      setError('Please enter a SMILES string');
      return;
    }
    setError('');
    setLoading(true);
    try {
      const result = await predictMolecule(smiles.trim());
      if (result.success) {
        // Store result and navigate to dashboard
        sessionStorage.setItem('predictionResult', JSON.stringify(result.prediction));
        sessionStorage.setItem('currentSmiles', smiles.trim());
        navigate('/dashboard');
      } else {
        setError(result.error || 'Invalid SMILES string. Please check your input.');
      }
    } catch (err) {
      setError('Failed to analyze molecule. Please check if the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleAnalyze();
  };

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;
    
    setUploadLoading(true);
    setError('');
    try {
      const result = await uploadDataset(file);
      if (result.success) {
        setUploadResult(result);
      } else {
        setError(result.error || 'Upload failed');
      }
    } catch (err) {
      setError('Failed to upload file. Please check the format.');
    } finally {
      setUploadLoading(false);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'] },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024,
  });

  return (
    <div className="section">
      <div className="container-narrow">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-100 dark:bg-primary-900/50 text-primary-700 dark:text-primary-300 text-sm font-medium mb-4">
            <FlaskConical className="w-4 h-4" />
            Molecule Analysis
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-surface-900 dark:text-surface-100 mb-3" id="analyze-title">
            Analyze Your <span className="gradient-text">Molecule</span>
          </h1>
          <p className="text-surface-500 dark:text-surface-400 max-w-xl mx-auto">
            Enter a SMILES string below or upload a CSV dataset to get AI-powered predictions.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* SMILES Input Section */}
          <div className="card">
            <h2 className="text-lg font-bold text-surface-900 dark:text-surface-100 mb-4 flex items-center gap-2">
              <Search className="w-5 h-5 text-primary-500" />
              Enter SMILES String
            </h2>
            <p className="text-sm text-surface-500 dark:text-surface-400 mb-4">
              SMILES is a way to describe chemical structures as text. Don't know SMILES? Try one of the examples below!
            </p>

            <div className="relative mb-4">
              <input
                type="text"
                value={smiles}
                onChange={e => { setSmiles(e.target.value); setError(''); }}
                onKeyDown={handleKeyDown}
                placeholder="e.g., CC(=O)OC1=CC=CC=C1C(=O)O"
                className="input-field font-mono text-sm pr-12"
                id="smiles-input"
                disabled={loading}
              />
              {smiles && (
                <button
                  onClick={() => { setSmiles(''); setError(''); }}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-surface-400 hover:text-surface-600"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {error && (
              <div className="flex items-start gap-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl mb-4 animate-scale-in">
                <AlertCircle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
              </div>
            )}

            <button
              onClick={handleAnalyze}
              disabled={loading || !smiles.trim()}
              className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              id="analyze-button"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Analyze Molecule
                </>
              )}
            </button>

            {/* Example Molecules */}
            <div className="mt-6">
              <h3 className="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Try an example:</h3>
              <div className="flex flex-wrap gap-2">
                {examples.map((ex, i) => (
                  <button
                    key={i}
                    onClick={() => { setSmiles(ex.smiles); setError(''); }}
                    className="px-3 py-1.5 text-xs font-medium rounded-lg bg-surface-100 dark:bg-surface-800 
                             text-surface-700 dark:text-surface-300 hover:bg-primary-100 dark:hover:bg-primary-900/50 
                             hover:text-primary-700 dark:hover:text-primary-300 transition-all"
                    title={ex.description}
                  >
                    {ex.name}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* File Upload Section */}
          <div className="card">
            <h2 className="text-lg font-bold text-surface-900 dark:text-surface-100 mb-4 flex items-center gap-2">
              <Upload className="w-5 h-5 text-accent-500" />
              Upload Dataset
            </h2>
            <p className="text-sm text-surface-500 dark:text-surface-400 mb-4">
              Upload a CSV file with SMILES strings to analyze multiple molecules at once.
            </p>

            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 ${
                isDragActive
                  ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                  : 'border-surface-300 dark:border-surface-600 hover:border-primary-400 hover:bg-surface-50 dark:hover:bg-surface-800/50'
              }`}
              id="file-dropzone"
            >
              <input {...getInputProps()} />
              {uploadLoading ? (
                <LoadingSpinner text="Uploading..." />
              ) : (
                <>
                  <Upload className={`w-10 h-10 mx-auto mb-3 ${isDragActive ? 'text-primary-500' : 'text-surface-400'}`} />
                  <p className="text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">
                    {isDragActive ? 'Drop your file here!' : 'Drag & drop a CSV file here'}
                  </p>
                  <p className="text-xs text-surface-400">or click to browse (max 50MB)</p>
                </>
              )}
            </div>

            {/* Upload Result */}
            {uploadResult && (
              <div className="mt-4 p-4 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-xl animate-scale-in">
                <div className="flex items-center gap-2 mb-2">
                  <FileText className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                  <span className="text-sm font-semibold text-emerald-700 dark:text-emerald-300">
                    Upload Successful!
                  </span>
                </div>
                <div className="text-xs text-emerald-600 dark:text-emerald-400 space-y-1">
                  <p>File: {uploadResult.filename}</p>
                  <p>Rows: {uploadResult.num_rows} | Columns: {uploadResult.num_columns}</p>
                  <p>Dataset ID: <code className="px-1 py-0.5 bg-emerald-100 dark:bg-emerald-800 rounded">{uploadResult.dataset_id}</code></p>
                  <p className="text-surface-500 mt-2">Columns: {uploadResult.columns?.join(', ')}</p>
                </div>
              </div>
            )}

            {/* Format Guide */}
            <div className="mt-4 p-4 bg-surface-50 dark:bg-surface-800/50 rounded-xl">
              <h4 className="text-xs font-semibold text-surface-700 dark:text-surface-300 mb-2">CSV Format:</h4>
              <code className="block text-xs font-mono text-surface-500 dark:text-surface-400 bg-surface-100 dark:bg-surface-800 p-2 rounded-lg">
                smiles,activity_label<br />
                CC(=O)OC1=CC=CC=C1C(=O)O,1<br />
                C1=CC=CC=C1,0
              </code>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
