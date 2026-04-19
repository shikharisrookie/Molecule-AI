import { FlaskConical, Heart } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Footer() {
  return (
    <footer className="border-t border-surface-200 dark:border-surface-800 bg-white/50 dark:bg-surface-950/50 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center">
                <FlaskConical className="w-4 h-4 text-white" />
              </div>
              <span className="text-lg font-bold gradient-text">MoleculeAI</span>
            </div>
            <p className="text-sm text-surface-500 dark:text-surface-400 leading-relaxed">
              AI-powered drug discovery platform making molecular analysis accessible to everyone.
            </p>
          </div>

          {/* Links */}
          <div>
            <h3 className="font-semibold text-surface-900 dark:text-surface-100 mb-4">Platform</h3>
            <div className="space-y-2">
              <Link to="/analyze" className="block text-sm text-surface-500 dark:text-surface-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors">Analyze Molecules</Link>
              <Link to="/dashboard" className="block text-sm text-surface-500 dark:text-surface-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors">Prediction Dashboard</Link>
              <Link to="/visualize" className="block text-sm text-surface-500 dark:text-surface-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors">3D Molecule Viewer</Link>
              <Link to="/about" className="block text-sm text-surface-500 dark:text-surface-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors">Documentation</Link>
            </div>
          </div>

          {/* Resources */}
          <div>
            <h3 className="font-semibold text-surface-900 dark:text-surface-100 mb-4">Resources</h3>
            <div className="space-y-2">
              <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer" className="block text-sm text-surface-500 dark:text-surface-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors">API Documentation</a>
              <a href="https://www.rdkit.org/" target="_blank" rel="noreferrer" className="block text-sm text-surface-500 dark:text-surface-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors">RDKit</a>
              <a href="https://3dmol.org/" target="_blank" rel="noreferrer" className="block text-sm text-surface-500 dark:text-surface-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors">3Dmol.js</a>
            </div>
          </div>
        </div>

        <div className="mt-10 pt-6 border-t border-surface-200 dark:border-surface-800 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-sm text-surface-400 dark:text-surface-500">
            © {new Date().getFullYear()} MoleculeAI. Built for drug discovery research.
          </p>
          <p className="text-sm text-surface-400 dark:text-surface-500 flex items-center gap-1">
            Made with <Heart className="w-3.5 h-3.5 text-red-500 fill-red-500" /> for science
          </p>
        </div>
      </div>
    </footer>
  );
}
