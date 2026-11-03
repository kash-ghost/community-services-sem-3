import React, { useState } from "react";
import { predictLocation } from "../services/api";
import { PredictionResult } from "../types";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { MapPin, Search, AlertCircle, CheckCircle2, Info } from "lucide-react";

export const LocationAnalysis: React.FC = () => {
  const [lat, setLat] = useState<string>("28.4595");
  const [lon, setLon] = useState<string>("77.0266");
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const presets = [
    { label: "IFFCO Chowk (NH-48)", lat: 28.472, lon: 77.0725 },
    { label: "Subhash Chowk (Sohna Rd)", lat: 28.435, lon: 77.0375 },
    { label: "Hero Honda Chowk", lat: 28.439, lon: 77.005 },
    { label: "Golf Course Extension", lat: 28.405, lon: 77.095 },
    { label: "Badshahpur Drainage Axis", lat: 28.386, lon: 77.02 },
  ];

  const handlePredict = async (latitude?: number, longitude?: number) => {
    const queryLat = latitude !== undefined ? latitude : parseFloat(lat);
    const queryLon = longitude !== undefined ? longitude : parseFloat(lon);

    if (isNaN(queryLat) || isNaN(queryLon)) {
      setError("Please provide valid numeric coordinates.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const resp = await predictLocation(queryLat, queryLon);
      setResult(resp);
    } catch (err: any) {
      setError(err.message || "Failed to calculate susceptibility.");
    } finally {
      setLoading(false);
    }
  };

  const getFsiBadgeColor = (cls: string) => {
    switch (cls) {
      case "very_high":
        return "bg-rose-950/80 text-rose-300 border-rose-800";
      case "high":
        return "bg-orange-950/80 text-orange-300 border-orange-800";
      case "moderate":
        return "bg-amber-950/80 text-amber-300 border-amber-800";
      case "low":
        return "bg-emerald-950/80 text-emerald-300 border-emerald-800";
      default:
        return "bg-slate-800 text-slate-300 border-slate-700";
    }
  };

  // Prepare chart data for contributions
  const contribData = result
    ? Object.entries(result.feature_contributions).map(([k, v]) => ({
        name: k.replace("_m", "").replace("_frac", "").replace("_deg", "").replace("_", " "),
        contribution: (v as number) * 100,
      }))
    : [];

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="bg-dark-900 border border-dark-800 p-6 rounded">
        <h1 className="text-xl font-bold text-white tracking-tight">
          Location Susceptibility Inference
        </h1>
        <p className="text-sm text-slate-400 mt-1 max-w-3xl leading-relaxed">
          Evaluate relative flood susceptibility for any coordinate across the Gurugram study area. Extracts spatial attributes from the 500m analysis unit and provides factor contribution breakdown.
        </p>
      </div>

      {/* Query Form + Quick Presets */}
      <div className="bg-dark-900 border border-dark-800 p-5 rounded space-y-4">
        <div className="flex flex-col sm:flex-row items-end gap-3">
          <div className="flex-1 space-y-1">
            <label className="text-xs font-mono text-slate-400">
              Latitude (°N, [28.20 – 28.55])
            </label>
            <input
              type="text"
              value={lat}
              onChange={(e) => setLat(e.target.value)}
              className="w-full bg-dark-850 border border-dark-700 text-white rounded px-3 py-2 text-xs font-mono focus:border-accent-cyan outline-none"
              placeholder="e.g. 28.4595"
            />
          </div>

          <div className="flex-1 space-y-1">
            <label className="text-xs font-mono text-slate-400">
              Longitude (°E, [76.80 – 77.25])
            </label>
            <input
              type="text"
              value={lon}
              onChange={(e) => setLon(e.target.value)}
              className="w-full bg-dark-850 border border-dark-700 text-white rounded px-3 py-2 text-xs font-mono focus:border-accent-cyan outline-none"
              placeholder="e.g. 77.0266"
            />
          </div>

          <button
            onClick={() => handlePredict()}
            disabled={loading}
            className="w-full sm:w-auto px-5 py-2 bg-dark-800 hover:bg-dark-700 text-accent-cyan border border-dark-700 rounded text-xs font-medium font-mono flex items-center justify-center gap-2 transition disabled:opacity-50"
          >
            <Search className="w-3.5 h-3.5" />
            <span>{loading ? "Calculating..." : "Compute FSI"}</span>
          </button>
        </div>

        {/* Quick Focus Hotspots */}
        <div className="pt-3 border-t border-dark-800 flex flex-wrap items-center gap-2">
          <span className="text-xs text-slate-500 font-mono">Focal Hotspots:</span>
          {presets.map((p, idx) => (
            <button
              key={idx}
              onClick={() => {
                setLat(p.lat.toString());
                setLon(p.lon.toString());
                handlePredict(p.lat, p.lon);
              }}
              className="px-2.5 py-1 text-xs rounded bg-dark-850 hover:bg-dark-800 border border-dark-700 text-slate-300 transition"
            >
              {p.label}
            </button>
          ))}
        </div>

        {error && (
          <div className="p-3 rounded bg-rose-950/60 border border-rose-800 text-xs text-rose-300 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Prediction Output Results */}
      {result && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main FSI Score & Feature Matrix */}
          <div className="bg-dark-900 border border-dark-800 p-5 rounded space-y-4">
            <div className="flex justify-between items-start border-b border-dark-800 pb-3">
              <div>
                <div className="text-[10px] font-mono text-slate-500 uppercase">
                  Cell Location
                </div>
                <div className="text-base font-bold font-mono text-white mt-0.5">
                  Unit {result.cell_id}
                </div>
              </div>

              <span
                className={`px-3 py-1 text-xs font-mono font-semibold rounded border ${getFsiBadgeColor(
                  result.result.fsi_class
                )}`}
              >
                {result.result.fsi_class_label}
              </span>
            </div>

            <div className="bg-dark-850 p-4 rounded border border-dark-800 flex justify-between items-center">
              <div>
                <div className="text-xs text-slate-400">Susceptibility Index</div>
                <div className="text-xs font-mono text-slate-500 mt-0.5">
                  Scale: 0.000 – 1.000
                </div>
              </div>
              <div className="text-3xl font-bold font-mono text-accent-cyan">
                {result.result.fsi.toFixed(4)}
              </div>
            </div>

            {/* Extracted Feature Metrics */}
            <div className="space-y-2 pt-2">
              <div className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Extracted Environmental Features
              </div>

              <div className="p-3 rounded bg-dark-850 border border-dark-800 space-y-2 text-xs font-mono">
                <div className="flex justify-between">
                  <span className="text-slate-400">Copernicus Elevation:</span>
                  <span className="text-white">{result.features.elevation_m} m</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Terrain Slope:</span>
                  <span className="text-white">{result.features.slope_deg}°</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">ESA Built-Up Surface:</span>
                  <span className="text-white">
                    {result.features.built_up_frac !== null && result.features.built_up_frac !== undefined
                      ? `${(result.features.built_up_frac * 100).toFixed(1)}%`
                      : "N/A"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Vegetation Cover:</span>
                  <span className="text-white">
                    {result.features.veg_frac !== null && result.features.veg_frac !== undefined
                      ? `${(result.features.veg_frac * 100).toFixed(1)}%`
                      : "N/A"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Distance to Drain:</span>
                  <span className="text-white">
                    {result.features.dist_to_drain_m !== null && result.features.dist_to_drain_m !== undefined
                      ? `${Math.round(result.features.dist_to_drain_m)} m`
                      : "N/A"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Distance to Water:</span>
                  <span className="text-white">
                    {result.features.dist_to_water_m !== null && result.features.dist_to_water_m !== undefined
                      ? `${Math.round(result.features.dist_to_water_m)} m`
                      : "N/A"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Monsoon Rainfall:</span>
                  <span className="text-white">{result.features.monsoon_rainfall_mm} mm</span>
                </div>
              </div>
            </div>
          </div>

          {/* Contributing Factors Bar Chart & Caveats */}
          <div className="lg:col-span-2 bg-dark-900 border border-dark-800 p-5 rounded space-y-4">
            <h2 className="text-base font-semibold text-white">
              Relative Factor Contribution Breakdown
            </h2>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={contribData} layout="vertical" margin={{ left: 20, right: 20 }}>
                  <XAxis type="number" stroke="#64748b" tick={{ fontSize: 11 }} unit="%" />
                  <YAxis dataKey="name" type="category" stroke="#cbd5e1" tick={{ fontSize: 11 }} width={95} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#141d30", borderColor: "#273552", borderRadius: 4, fontSize: 12 }}
                    formatter={(val: number) => [`${val.toFixed(2)}%`, "Weighted Contribution"]}
                  />
                  <Bar dataKey="contribution" fill="#38bdf8" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="pt-3 border-t border-dark-800 space-y-2">
              <div className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <Info className="w-4 h-4 text-accent-cyan" />
                <span>Decision Support Disclaimers & Provenance</span>
              </div>
              <ul className="text-xs text-slate-400 space-y-1 list-disc pl-4 leading-relaxed">
                {result.limitations.map((lim, i) => (
                  <li key={i}>{lim}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
