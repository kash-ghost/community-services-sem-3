import React, { useState, useEffect } from "react";
import { Navbar } from "./components/Navbar";
import { Overview } from "./pages/Overview";
import { InteractiveMap } from "./pages/InteractiveMap";
import { DataExplorer } from "./pages/DataExplorer";
import { ModelLab } from "./pages/ModelLab";
import { LocationAnalysis } from "./pages/LocationAnalysis";
import { History } from "./pages/History";
import { fetchHealth, fetchMetadata, fetchModelMetrics } from "./services/api";
import { SystemMetadata, ModelMetrics } from "./types";

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>("overview");
  const [metadata, setMetadata] = useState<SystemMetadata | null>(null);
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
  const [dbConnected, setDbConnected] = useState<boolean>(false);
  const [modelVersion, setModelVersion] = useState<string>("fsi_v1.0");

  useEffect(() => {
    async function initApp() {
      try {
        const health = await fetchHealth();
        setDbConnected(health.database === "connected");
        setModelVersion(health.model || "fsi_v1.0");
      } catch (err) {
        console.warn("Backend not yet connected:", err);
      }

      try {
        const meta = await fetchMetadata();
        setMetadata(meta);
      } catch (err) {
        console.warn("Metadata unavailable:", err);
      }

      try {
        const met = await fetchModelMetrics();
        setMetrics(met);
      } catch (err) {
        console.warn("Metrics unavailable:", err);
      }
    }
    initApp();
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-dark-950 text-slate-200">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        dbConnected={dbConnected}
        modelVersion={modelVersion}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === "overview" && (
          <Overview metadata={metadata} metrics={metrics} setActiveTab={setActiveTab} />
        )}
        {activeTab === "map" && <InteractiveMap />}
        {activeTab === "data" && <DataExplorer metadata={metadata} />}
        {activeTab === "model" && <ModelLab metrics={metrics} />}
        {activeTab === "location" && <LocationAnalysis />}
        {activeTab === "history" && <History />}
      </main>

      <footer className="border-t border-dark-800 bg-dark-900 py-4 text-xs font-mono text-slate-500 text-center">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row justify-between items-center gap-2">
          <span>**Research Prototype Notice**

This platform is an academic and NGO collaboration prototype developed to assess relative urban flood susceptibility across Gurugram, Haryana, using publicly available government GIS and meteorological datasets.

The framework uses an Analytical Hierarchy Process (AHP)-based Flood Susceptibility Index (FSI). Its outputs are intended for research, educational demonstrations, and preliminary decision-support discussions.

This platform is not an operational flood forecasting or early-warning system. Its susceptibility classifications should not be interpreted as predictions or guarantees of actual flooding. Further independent field validation and technical development are required before operational use.</span>
          <span>Gurugram Urban Flood Vulnerability Analytics · Academic Prototype</span>
          <span>Data Sources: GMDA · Copernicus DEM · ESA WorldCover · Open-Meteo</span>
        </div>
      </footer>
    </div>
  );
};

export default App;
