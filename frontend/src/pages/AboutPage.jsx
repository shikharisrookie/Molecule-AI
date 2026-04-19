import { useState } from 'react';
import { BookOpen, ChevronDown, ChevronUp, ExternalLink, FlaskConical, Brain, Database, Code } from 'lucide-react';

const glossary = [
  { term: 'SMILES', definition: 'Simplified Molecular Input Line Entry System — a way to write chemical structures as text. For example, "CCO" represents ethanol (drinking alcohol).', example: 'CC(=O)OC1=CC=CC=C1C(=O)O → Aspirin' },
  { term: 'Drug-Likeness (QED)', definition: 'A score from 0 to 1 that estimates how similar a molecule is to known drugs. Higher values suggest the molecule has properties commonly found in successful medications.', example: 'Aspirin has a QED of about 0.55' },
  { term: 'Toxicity', definition: 'How harmful a substance can be to living organisms. Our model predicts potential toxicity risk based on molecular structure, helping filter out dangerous compounds early.', example: 'Classified as Low, Medium, or High risk' },
  { term: 'LogP', definition: 'A measure of how well a molecule dissolves in fat versus water. Drugs need to cross fatty cell membranes, so an ideal LogP is between 0 and 5.', example: 'Water-soluble = low LogP, Fat-soluble = high LogP' },
  { term: 'Lipinski\'s Rule of Five', definition: 'A set of guidelines that predict whether a drug can be taken orally. A molecule should have: MW ≤ 500, LogP ≤ 5, ≤ 5 H-bond donors, ≤ 10 H-bond acceptors. Violating these rules makes oral absorption less likely.', example: 'Zero violations = good oral drug candidate' },
  { term: 'Molecular Fingerprint', definition: 'A numerical representation of a molecule\'s structure. Think of it like a barcode — it encodes which chemical features are present and is used by our AI model to make predictions.', example: 'Morgan/ECFP fingerprints with 2048 bits' },
  { term: 'Biological Activity', definition: 'Whether a molecule can interact with biological targets (like proteins) to produce a therapeutic effect. Our model predicts the probability that a molecule is biologically active.', example: 'Active compounds may become drug candidates' },
  { term: 'TPSA', definition: 'Topological Polar Surface Area — the surface area of a molecule\'s polar parts. Lower TPSA generally means the molecule can cross cell membranes more easily.', example: 'Ideal TPSA for oral drugs: < 140 Å²' },
];

const faqs = [
  { q: 'Do I need a chemistry background to use this?', a: 'Not at all! Our platform is designed to be accessible to everyone. We explain all scientific terms in simple language and provide example molecules you can try instantly.' },
  { q: 'How accurate are the predictions?', a: 'Our XGBoost model is trained on bioactivity data and achieves good accuracy on test sets. However, these are computational predictions and should be used as a screening tool — not as a replacement for laboratory testing.' },
  { q: 'What is a SMILES string?', a: 'SMILES is a text-based notation for chemical structures. For example, water is "O", ethanol is "CCO", and aspirin is "CC(=O)OC1=CC=CC=C1C(=O)O". You can find SMILES strings on PubChem or ChemSpider.' },
  { q: 'Can I upload my own dataset?', a: 'Yes! Upload a CSV file with a column of SMILES strings and an activity label column (0 or 1). You can then train a custom model on your data.' },
  { q: 'What ML model is used?', a: 'We use XGBoost (gradient-boosted trees) trained on Morgan molecular fingerprints (2048-bit ECFP4) combined with physicochemical descriptors. The model predicts binary activity classification.' },
];

function GlossaryItem({ item }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border border-surface-200 dark:border-surface-700 rounded-xl overflow-hidden transition-all">
      <button onClick={() => setOpen(!open)} className="w-full flex items-center justify-between p-4 text-left hover:bg-surface-50 dark:hover:bg-surface-800/50 transition-colors">
        <span className="font-semibold text-surface-900 dark:text-surface-100">{item.term}</span>
        {open ? <ChevronUp className="w-4 h-4 text-surface-400" /> : <ChevronDown className="w-4 h-4 text-surface-400" />}
      </button>
      {open && (
        <div className="px-4 pb-4 animate-slide-down">
          <p className="text-sm text-surface-600 dark:text-surface-400 mb-2">{item.definition}</p>
          {item.example && (
            <p className="text-xs text-primary-600 dark:text-primary-400 bg-primary-50 dark:bg-primary-900/30 px-3 py-1.5 rounded-lg inline-block">
              💡 {item.example}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export default function AboutPage() {
  return (
    <div className="section">
      <div className="container-narrow">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-100 dark:bg-primary-900/50 text-primary-700 dark:text-primary-300 text-sm font-medium mb-4">
            <BookOpen className="w-4 h-4" />
            Documentation
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-surface-900 dark:text-surface-100 mb-3" id="about-title">
            About <span className="gradient-text">MoleculeAI</span>
          </h1>
          <p className="text-surface-500 dark:text-surface-400 max-w-2xl mx-auto">
            Everything you need to know about how the platform works, the science behind it, and how to get the most out of your analysis.
          </p>
        </div>

        {/* How the Model Works */}
        <div className="card mb-8">
          <h2 className="text-xl font-bold text-surface-900 dark:text-surface-100 mb-6 flex items-center gap-2">
            <Brain className="w-5 h-5 text-primary-500" />
            How the AI Model Works
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center p-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-r from-blue-500 to-indigo-600 flex items-center justify-center text-white mx-auto mb-3">
                <FlaskConical className="w-6 h-6" />
              </div>
              <h3 className="font-semibold text-surface-900 dark:text-surface-100 mb-2">1. Feature Extraction</h3>
              <p className="text-sm text-surface-500 dark:text-surface-400">
                Your molecule's SMILES string is converted into a numerical "fingerprint" — a 2048-bit vector that captures its structural features, plus 9 physicochemical properties.
              </p>
            </div>
            <div className="text-center p-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-r from-purple-500 to-pink-600 flex items-center justify-center text-white mx-auto mb-3">
                <Brain className="w-6 h-6" />
              </div>
              <h3 className="font-semibold text-surface-900 dark:text-surface-100 mb-2">2. AI Prediction</h3>
              <p className="text-sm text-surface-500 dark:text-surface-400">
                An XGBoost model (a type of gradient-boosted decision tree) analyzes the fingerprint to predict biological activity. Drug-likeness and toxicity are assessed using additional molecular rules.
              </p>
            </div>
            <div className="text-center p-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-r from-teal-500 to-emerald-600 flex items-center justify-center text-white mx-auto mb-3">
                <Database className="w-6 h-6" />
              </div>
              <h3 className="font-semibold text-surface-900 dark:text-surface-100 mb-2">3. Result Generation</h3>
              <p className="text-sm text-surface-500 dark:text-surface-400">
                Results are combined into an easy-to-read dashboard with scores, charts, and plain-language summaries. All predictions are saved to your history for later reference.
              </p>
            </div>
          </div>
        </div>

        {/* Tech Stack */}
        <div className="card mb-8">
          <h2 className="text-xl font-bold text-surface-900 dark:text-surface-100 mb-4 flex items-center gap-2">
            <Code className="w-5 h-5 text-accent-500" />
            Technology Stack
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { name: 'React', desc: 'Frontend UI' },
              { name: 'FastAPI', desc: 'Backend API' },
              { name: 'RDKit', desc: 'Chemistry' },
              { name: 'XGBoost', desc: 'ML Model' },
              { name: 'TailwindCSS', desc: 'Styling' },
              { name: '3Dmol.js', desc: '3D Viewer' },
              { name: 'Recharts', desc: 'Charts' },
              { name: 'SQLite', desc: 'Database' },
            ].map((tech, i) => (
              <div key={i} className="p-3 bg-surface-50 dark:bg-surface-800/50 rounded-xl text-center">
                <p className="font-semibold text-surface-900 dark:text-surface-100 text-sm">{tech.name}</p>
                <p className="text-xs text-surface-500 dark:text-surface-400">{tech.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Glossary */}
        <div className="mb-8">
          <h2 className="text-xl font-bold text-surface-900 dark:text-surface-100 mb-4 flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-primary-500" />
            Glossary of Terms
          </h2>
          <div className="space-y-2">
            {glossary.map((item, i) => (
              <GlossaryItem key={i} item={item} />
            ))}
          </div>
        </div>

        {/* FAQ */}
        <div className="mb-8">
          <h2 className="text-xl font-bold text-surface-900 dark:text-surface-100 mb-4">Frequently Asked Questions</h2>
          <div className="space-y-4">
            {faqs.map((faq, i) => (
              <div key={i} className="card">
                <h3 className="font-semibold text-surface-900 dark:text-surface-100 mb-2">{faq.q}</h3>
                <p className="text-sm text-surface-500 dark:text-surface-400">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>

        {/* API Docs Link */}
        <div className="card text-center">
          <h2 className="text-lg font-bold text-surface-900 dark:text-surface-100 mb-2">API Documentation</h2>
          <p className="text-sm text-surface-500 dark:text-surface-400 mb-4">
            Full API documentation is auto-generated with Swagger UI.
          </p>
          <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer" className="btn-primary inline-flex items-center gap-2">
            <ExternalLink className="w-4 h-4" />
            Open Swagger Docs
          </a>
        </div>
      </div>
    </div>
  );
}
