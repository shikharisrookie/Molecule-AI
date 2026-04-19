import { Link } from 'react-router-dom';
import { FlaskConical, Atom, BarChart3, Eye, Sparkles, ArrowRight, Shield, Zap, Brain } from 'lucide-react';

const features = [
  {
    icon: <Atom className="w-6 h-6" />,
    title: 'Molecular Analysis',
    description: 'Enter any molecule using SMILES notation and instantly get detailed physicochemical properties and drug-likeness scores.',
    color: 'from-blue-500 to-indigo-600',
  },
  {
    icon: <Brain className="w-6 h-6" />,
    title: 'AI Predictions',
    description: 'Our ML models predict biological activity, toxicity risk, and drug-likeness using molecular fingerprints and XGBoost.',
    color: 'from-purple-500 to-pink-600',
  },
  {
    icon: <Eye className="w-6 h-6" />,
    title: '3D Visualization',
    description: 'View interactive 3D molecular structures with different rendering styles — stick, ball-and-stick, and surface views.',
    color: 'from-teal-500 to-emerald-600',
  },
  {
    icon: <BarChart3 className="w-6 h-6" />,
    title: 'Visual Analytics',
    description: 'Understand your results through intuitive charts, radar plots, and color-coded risk indicators — no PhD required.',
    color: 'from-orange-500 to-red-600',
  },
  {
    icon: <Shield className="w-6 h-6" />,
    title: 'Toxicity Screening',
    description: 'Get early toxicity risk assessments to filter out potentially harmful compounds before expensive lab testing.',
    color: 'from-rose-500 to-red-600',
  },
  {
    icon: <Zap className="w-6 h-6" />,
    title: 'Batch Processing',
    description: 'Upload CSV datasets with thousands of molecules and get predictions for all of them in seconds.',
    color: 'from-amber-500 to-orange-600',
  },
];

const steps = [
  { step: '01', title: 'Input Your Molecule', description: 'Enter a SMILES string or upload a CSV file with molecular data', icon: '🧪' },
  { step: '02', title: 'AI Analyzes It', description: 'Our models extract molecular features and predict drug properties', icon: '🤖' },
  { step: '03', title: 'Get Clear Results', description: 'View predictions, scores, and 3D structures in simple language', icon: '📊' },
];

export default function HomePage() {
  return (
    <div>
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="gradient-hero absolute inset-0 opacity-90" />
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PHBhdGggZD0iTTM2IDM0djJIMjR2LTJoMTJ6bTAtNHYySDI0di0yaDEyem0wLTR2MkgyNHYtMmgxMnoiLz48L2c+PC9nPjwvc3ZnPg==')] opacity-30" />
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 md:py-36">
          <div className="text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 text-white/90 text-sm font-medium mb-8 animate-fade-in">
              <Sparkles className="w-4 h-4" />
              AI-Powered Drug Discovery Platform
            </div>
            
            <h1 className="text-4xl md:text-6xl lg:text-7xl font-extrabold text-white mb-6 tracking-tight animate-slide-up" id="hero-title">
              Discover the Next
              <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-200 to-cyan-200">
                Breakthrough Drug
              </span>
            </h1>
            
            <p className="text-lg md:text-xl text-white/80 max-w-2xl mx-auto mb-10 leading-relaxed animate-slide-up" style={{ animationDelay: '0.1s' }}>
              Analyze molecules, predict drug properties, and visualize structures — all powered by machine learning. 
              No chemistry degree needed.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-slide-up" style={{ animationDelay: '0.2s' }}>
              <Link to="/analyze" className="px-8 py-4 bg-white text-primary-700 font-bold rounded-xl shadow-2xl hover:shadow-3xl hover:scale-105 transition-all duration-300 flex items-center gap-2 text-lg" id="cta-analyze">
                Start Analyzing
                <ArrowRight className="w-5 h-5" />
              </Link>
              <Link to="/about" className="px-8 py-4 bg-white/10 backdrop-blur-sm border border-white/30 text-white font-semibold rounded-xl hover:bg-white/20 transition-all duration-300" id="cta-learn">
                Learn More
              </Link>
            </div>
          </div>

          {/* Floating molecules decoration */}
          <div className="hidden lg:block absolute top-20 left-10 w-20 h-20 rounded-full bg-teal-400/20 animate-float blur-sm" />
          <div className="hidden lg:block absolute bottom-20 right-10 w-32 h-32 rounded-full bg-purple-400/15 animate-float blur-sm" style={{ animationDelay: '2s' }} />
          <div className="hidden lg:block absolute top-40 right-20 w-16 h-16 rounded-full bg-cyan-400/20 animate-float blur-sm" style={{ animationDelay: '4s' }} />
        </div>
      </section>

      {/* What is Drug Discovery */}
      <section className="section bg-white dark:bg-surface-950">
        <div className="container-narrow">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-surface-900 dark:text-surface-100 mb-4">
              What is <span className="gradient-text">Drug Discovery</span>?
            </h2>
            <p className="text-lg text-surface-600 dark:text-surface-400 max-w-3xl mx-auto leading-relaxed">
              Drug discovery is the process of finding new medications. Scientists test thousands of chemical compounds 
              to find ones that can treat diseases safely. Our AI platform accelerates this process by predicting which 
              molecules are most likely to become effective drugs — <strong>saving years of research</strong>.
            </p>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="section bg-surface-50 dark:bg-surface-900">
        <div className="container-narrow">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-surface-900 dark:text-surface-100 mb-4">
              How It Works
            </h2>
            <p className="text-surface-600 dark:text-surface-400">Three simple steps to analyze any molecule</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {steps.map((s, i) => (
              <div key={i} className="relative text-center">
                <div className="text-5xl mb-4">{s.icon}</div>
                <div className="text-xs font-bold text-primary-500 tracking-widest mb-2">{s.step}</div>
                <h3 className="text-xl font-bold text-surface-900 dark:text-surface-100 mb-2">{s.title}</h3>
                <p className="text-surface-500 dark:text-surface-400 text-sm">{s.description}</p>
                {i < steps.length - 1 && (
                  <div className="hidden md:block absolute top-8 -right-4 text-surface-300 dark:text-surface-600">
                    <ArrowRight className="w-8 h-8" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="section bg-white dark:bg-surface-950">
        <div className="container-narrow">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-surface-900 dark:text-surface-100 mb-4">
              Powerful <span className="gradient-text">Features</span>
            </h2>
            <p className="text-surface-600 dark:text-surface-400">Everything you need for molecular analysis</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, i) => (
              <div
                key={i}
                className="card-hover group"
                style={{ animationDelay: `${i * 0.1}s` }}
              >
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-r ${feature.color} flex items-center justify-center text-white mb-4 group-hover:scale-110 transition-transform duration-300`}>
                  {feature.icon}
                </div>
                <h3 className="text-lg font-bold text-surface-900 dark:text-surface-100 mb-2">{feature.title}</h3>
                <p className="text-sm text-surface-500 dark:text-surface-400 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="section relative overflow-hidden">
        <div className="absolute inset-0 gradient-hero opacity-90" />
        <div className="relative container-narrow text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
            Ready to Discover?
          </h2>
          <p className="text-lg text-white/80 mb-8 max-w-2xl mx-auto">
            Start analyzing molecules right now — enter a SMILES string or try one of our example compounds.
          </p>
          <Link to="/analyze" className="inline-flex items-center gap-2 px-8 py-4 bg-white text-primary-700 font-bold rounded-xl shadow-2xl hover:scale-105 transition-all duration-300 text-lg" id="cta-bottom">
            Get Started Free
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>
    </div>
  );
}
