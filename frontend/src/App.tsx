import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import DataFusion from './pages/DataFusion';
import BehaviorAnalysis from './pages/BehaviorAnalysis';
import AnomalyDetection from './pages/AnomalyDetection';
import RiskPrediction from './pages/RiskPrediction';
import DigitalTwin from './pages/DigitalTwin';
import AIAssistant from './pages/AIAssistant';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Home page - full layout without sidebar */}
        <Route path="/" element={<Layout home />}>
          <Route index element={<Home />} />
        </Route>
        {/* Dashboard pages - with sidebar */}
        <Route path="/" element={<Layout />}>
          <Route path="dashboard" element={<DataFusion />} />
          <Route path="dashboard/behavior" element={<BehaviorAnalysis />} />
          <Route path="dashboard/anomaly" element={<AnomalyDetection />} />
          <Route path="dashboard/risk" element={<RiskPrediction />} />
          <Route path="twin" element={<DigitalTwin />} />
          <Route path="assistant" element={<AIAssistant />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
