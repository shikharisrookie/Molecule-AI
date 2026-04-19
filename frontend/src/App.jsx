import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import Navbar from './components/Layout/Navbar';
import Footer from './components/Layout/Footer';
import HomePage from './pages/HomePage';
import MoleculeInputPage from './pages/MoleculeInputPage';
import PredictionDashboard from './pages/PredictionDashboard';
import VisualizationPage from './pages/VisualizationPage';
import AboutPage from './pages/AboutPage';

function App() {
  return (
    <ThemeProvider>
      <Router>
        <div className="min-h-screen flex flex-col">
          <Navbar />
          <main className="flex-1 pt-16">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/analyze" element={<MoleculeInputPage />} />
              <Route path="/dashboard" element={<PredictionDashboard />} />
              <Route path="/visualize" element={<VisualizationPage />} />
              <Route path="/about" element={<AboutPage />} />
            </Routes>
          </main>
          <Footer />
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;
