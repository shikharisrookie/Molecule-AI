import { useState } from 'react';
import { Search, Pill, ArrowRight, FlaskConical, Percent, Activity } from 'lucide-react';
import { searchSimilar } from '../utils/api';
import LoadingSpinner from '../components/UI/LoadingSpinner';

export default function SimilarityPage() {
  const [smiles, setSmiles] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async () => {
    if (!smiles.trim()) { setError('Please enter a SMILES string'); return; }
    setError('');
    setLoading(true);
    try {
      const data = await searchSimilar(smiles.trim(), 15);
      if (data.success) {
        setResults(data.similar_molecules);
      } else {
        setError(data.error || 'Search failed');
      }
    } catch {
      setError('Failed to search. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  const getSimilarityColor = (sim) => {
    if (sim >= 0.85) return 'text-emerald-600 dark:text-emerald-400';
    if (sim >= 0.5) return 'text-amber-600 dark:text-amber-400';
    return 'text-surface-500';
  };

  const getSimilarityBg = (sim) => {
    if (sim >= 0.85) return 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800';
    if (sim >= 0.5) return 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800';
    return 'bg-surface-50 dark:bg-surface-800/50 border-surface-200 dark:border-surface-700';
  };

  return (
    <div className="section">
      <div className="container-narrow">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-100 dark:bg-teal-900/50 text-teal-700 dark:text-teal-300 text-sm font-medium mb-4">
            <Search className="w-4 h-4" />
            Drug Similarity
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-surface-900 dark:text-surface-100 mb-3" id="similarity-title">
            Find <span className="gradient-text">Similar Drugs</span>
          </h1>
          <p className="text-surface-500 dark:text-surface-400 max-w-xl mx-auto">
            Enter a molecule and discover structurally similar FDA-approved drugs using Tanimoto similarity.
          </p>
        </div>

        {/* Search Input */}
        <div className="card mb-8">
          <div className="flex gap-3">
            <input
              type="text"
              value={smiles}
              onChange={e => { setSmiles(e.target.value); setError(''); }}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
              placeholder="Enter SMILES string (e.g., CC(=O)OC1=CC=CC=C1C(=O)O for Aspirin)"
              className="input-field font-mono text-sm flex-1"
              id="similarity-input"
              disabled={loading}
            />
            <button
              onClick={handleSearch}
              disabled={loading || !smiles.trim()}
              className="btn-primary flex items-center gap-2 text-sm whitespace-nowrap disabled:opacity-50"
              id="similarity-search-button"
            >
              <Search className="w-4 h-4" />
              Search
            </button>
          </div>
          {error && (
            <p className="text-sm text-red-500 mt-2">{error}</p>
          )}
        </div>

        {loading && <LoadingSpinner text="Searching approved drug database..." />}

        {/* Results */}
        {results && !loading && (
          <div>
            <h2 className="text-lg font-bold text-surface-900 dark:text-surface-100 mb-4 flex items-center gap-2">
              <Pill className="w-5 h-5 text-teal-500" />
              {results.length} Similar Drugs Found
            </h2>

            {results.length === 0 ? (
              <div className="card text-center py-12">
                <FlaskConical className="w-12 h-12 text-surface-300 dark:text-surface-600 mx-auto mb-3" />
                <p className="text-surface-500 dark:text-surface-400">
                  No similar drugs found above the similarity threshold. Try a different molecule.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {results.map((drug, i) => (
                  <div
                    key={i}
                    className={`p-4 rounded-xl border transition-all hover:shadow-md ${getSimilarityBg(drug.similarity)}`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h3 className="font-bold text-surface-900 dark:text-surface-100 flex items-center gap-2">
                          <Pill className="w-4 h-4 text-teal-500" />
                          {drug.name}
                        </h3>
                        <p className="text-xs text-surface-500 dark:text-surface-400 mt-1">
                          {drug.indication}
                        </p>
                      </div>
                      <div className={`text-right ${getSimilarityColor(drug.similarity)}`}>
                        <div className="text-2xl font-bold">
                          {(drug.similarity * 100).toFixed(0)}%
                        </div>
                        <div className="text-xs opacity-75">similarity</div>
                      </div>
                    </div>

                    {/* Similarity bar */}
                    <div className="mt-3">
                      <div className="w-full bg-surface-200 dark:bg-surface-700 rounded-full h-1.5">
                        <div
                          className={`h-1.5 rounded-full transition-all duration-700 ${
                            drug.similarity >= 0.85 ? 'bg-emerald-500' :
                            drug.similarity >= 0.5 ? 'bg-amber-500' : 'bg-surface-400'
                          }`}
                          style={{ width: `${drug.similarity * 100}%` }}
                        />
                      </div>
                    </div>

                    <code className="block text-xs font-mono text-surface-400 mt-2 truncate" title={drug.smiles}>
                      {drug.smiles}
                    </code>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
