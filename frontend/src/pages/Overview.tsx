import React from "react";
import { SystemMetadata, ModelMetrics } from "../types";
import { ShieldAlert, MapPin, Layers, ArrowRight, BarChart2, CheckCircle2 } from "lucide-react";

interface OverviewProps {
  metadata: SystemMetadata | null;
  metrics: ModelMetrics | null;
  setActiveTab: (tab: string) => void;
}

export const Overview: React.FC<OverviewProps> = ({
  metadata,
  metrics,
  setActiveTab,
}) => {
  const dist = metrics?.class_distribution || {
    very_high: 717,
    high: 4748,
    moderate: 1455,
    low: 5,
  };
  const total = 6925;

  return (
    <div className="space-y-6">
      {/* Top Banner / Academic Context */}
      <div className="bg-dark-900 border border-dark-800 p-6 rounded">
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
          <div>
            <div className="text-xs uppercase tracking-wider font-mono text-accent-cyan font-semibold mb-1">
              Decision Support System · Study Territory
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight">
              Gurugram Urban Flood Vulnerability Analytics
            </h1>
            <p className="text-sm text-slate-400 mt-1 max-w-3xl leading-relaxed">
              Empirical geospatial framework estimating relative flood susceptibility across Gurugram, Haryana.
              Integrates Copernicus 30m Digital Surface Model, 10m ESA WorldCover 2021 impervious fractions,
              official GMDA drainage corridors, and 10 years of ERA5-Land monsoon rainfall.
            </p>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab("map")}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-dark-800 hover:bg-dark-700 text-accent-cyan border border-dark-700 rounded text-xs font-medium transition"
            >
              <span>Explore Interactive Map</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Academic Prototype Notice */}
        <div className="mt-4 pt-4 border-t border-dark-800 flex items-start gap-2 text-xs text-slate-400">
          <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <span>
            <strong className="text-slate-300 font-medium">Academic Research Notice:</strong>{" "}
            This platform generates multi-criteria decision-support susceptibility scores. It does not provide real-time hydrological flood warnings or official disaster clearances.
          </span>
        </div>
      </div>

      {/* Grid of Key Empirical Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-dark-900 border border-dark-800 p-4 rounded">
          <div className="text-xs font-mono text-slate-400">Analysis Units</div>
          <div className="text-2xl font-bold font-mono text-white mt-1">6,925</div>
          <div className="text-xs text-slate-500 mt-1">500m × 500m grid cells</div>
        </div>

        <div className="bg-dark-900 border border-dark-800 p-4 rounded">
          <div className="text-xs font-mono text-slate-400">Historical Observations</div>
          <div className="text-2xl font-bold font-mono text-white mt-1">25 Points</div>
          <div className="text-xs text-emerald-400 mt-1">100% match in High/V-High FSI</div>
        </div>

        <div className="bg-dark-900 border border-dark-800 p-4 rounded">
          <div className="text-xs font-mono text-slate-400">Elevation Model</div>
          <div className="text-2xl font-bold font-mono text-white mt-1">30m GLO-30</div>
          <div className="text-xs text-slate-500 mt-1">Copernicus DSM surface</div>
        </div>

        <div className="bg-dark-900 border border-dark-800 p-4 rounded">
          <div className="text-xs font-mono text-slate-400">Monsoon Rainfall Baseline</div>
          <div className="text-2xl font-bold font-mono text-white mt-1">528.7 mm</div>
          <div className="text-xs text-slate-500 mt-1">10-year mean (2015–2024)</div>
        </div>
      </div>

      {/* Two-Column Detail Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Susceptibility Summary Card */}
        <div className="lg:col-span-2 bg-dark-900 border border-dark-800 p-5 rounded">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-base font-semibold text-white">
              Territorial Susceptibility Distribution
            </h2>
            <span className="text-xs font-mono text-slate-400">
              Evaluated Cells: 6,925
            </span>
          </div>

          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-rose-400 font-medium">Very High Susceptibility (FSI ≥ 0.75)</span>
                <span className="font-mono text-slate-300">
                  {dist.very_high} cells ({((dist.very_high / total) * 100).toFixed(1)}%)
                </span>
              </div>
              <div className="w-full bg-dark-800 h-2 rounded overflow-hidden">
                <div
                  className="bg-rose-500 h-2"
                  style={{ width: `${(dist.very_high / total) * 100}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-orange-400 font-medium">High Susceptibility (0.50 ≤ FSI &lt; 0.75)</span>
                <span className="font-mono text-slate-300">
                  {dist.high} cells ({((dist.high / total) * 100).toFixed(1)}%)
                </span>
              </div>
              <div className="w-full bg-dark-800 h-2 rounded overflow-hidden">
                <div
                  className="bg-orange-500 h-2"
                  style={{ width: `${(dist.high / total) * 100}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-amber-400 font-medium">Moderate Susceptibility (0.25 ≤ FSI &lt; 0.50)</span>
                <span className="font-mono text-slate-300">
                  {dist.moderate} cells ({((dist.moderate / total) * 100).toFixed(1)}%)
                </span>
              </div>
              <div className="w-full bg-dark-800 h-2 rounded overflow-hidden">
                <div
                  className="bg-amber-400 h-2"
                  style={{ width: `${(dist.moderate / total) * 100}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-emerald-400 font-medium">Low Susceptibility (FSI &lt; 0.25)</span>
                <span className="font-mono text-slate-300">
                  {dist.low} cells ({((dist.low / total) * 100).toFixed(1)}%)
                </span>
              </div>
              <div className="w-full bg-dark-800 h-2 rounded overflow-hidden">
                <div
                  className="bg-emerald-500 h-2"
                  style={{ width: `${(dist.low / total) * 100}%` }}
                />
              </div>
            </div>
          </div>

          <div className="mt-5 p-3 rounded bg-dark-850 border border-dark-800 text-xs text-slate-400 leading-relaxed">
            <strong className="text-slate-300">Hydrological Pattern Note:</strong> Very High and High susceptibility units concentrate along the low-lying Badshahpur Drain axis, Golf Course Extension corridor, and natural drainage depressions near Najafgarh basin where terrain slope is under 0.8° and impervious built-up fraction exceeds 65%.
          </div>
        </div>

        {/* Verified Data Sources Card */}
        <div className="bg-dark-900 border border-dark-800 p-5 rounded">
          <h2 className="text-base font-semibold text-white mb-3">
            Public Data Provenance
          </h2>

          <div className="space-y-3 text-xs">
            <div className="p-2.5 rounded bg-dark-850 border border-dark-800">
              <div className="font-medium text-slate-200">GMDA Flood Survey & GIS Infrastructure</div>
              <div className="text-slate-400 mt-0.5">25 Survey Points · 4 Drain Legs · 211 Waterbodies</div>
              <div className="text-emerald-400 font-mono text-[10px] mt-1">Verified Public FeatureServer</div>
            </div>

            <div className="p-2.5 rounded bg-dark-850 border border-dark-800">
              <div className="font-medium text-slate-200">Copernicus DEM GLO-30</div>
              <div className="text-slate-400 mt-0.5">30m Digital Surface Model · Elevation & Slope</div>
              <div className="text-emerald-400 font-mono text-[10px] mt-1">AWS Public COG Stream</div>
            </div>

            <div className="p-2.5 rounded bg-dark-850 border border-dark-800">
              <div className="font-medium text-slate-200">ESA WorldCover 2021</div>
              <div className="text-slate-400 mt-0.5">10m Land Cover · Built-Up, Veg & Water</div>
              <div className="text-emerald-400 font-mono text-[10px] mt-1">CC BY 4.0 Open License</div>
            </div>

            <div className="p-2.5 rounded bg-dark-850 border border-dark-800">
              <div className="font-medium text-slate-200">Open-Meteo ERA5-Land</div>
              <div className="text-slate-400 mt-0.5">3,561 Daily Observations (2015–2024)</div>
              <div className="text-emerald-400 font-mono text-[10px] mt-1">Free Open Access API</div>
            </div>
          </div>

          <button
            onClick={() => setActiveTab("data")}
            className="w-full mt-4 py-2 text-center text-xs text-accent-cyan hover:underline font-mono"
          >
            Inspect Detailed Data Registry →
          </button>
        </div>
      </div>
    </div>
  );
};
