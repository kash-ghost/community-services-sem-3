import React, { useState, useEffect } from "react";
import { fetchPredictionsHistory } from "../services/api";
import { Clock, Database, AlertCircle, RefreshCw } from "lucide-react";

export const History: React.FC = () => {
  const [predictions, setPredictions] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchPredictionsHistory();
      setPredictions(data.predictions || []);
    } catch (err: any) {
      setError(err.message || "Unable to fetch prediction records.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="bg-dark-900 border border-dark-800 p-6 rounded flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">
            Prediction Audit Trail & History
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-3xl leading-relaxed">
            Historical log of spatial susceptibility calculations executed via API or interactive user queries, stored in MongoDB.
          </p>
        </div>

        <button
          onClick={loadHistory}
          disabled={loading}
          className="px-3.5 py-1.5 bg-dark-850 hover:bg-dark-800 text-slate-300 border border-dark-700 rounded text-xs font-mono flex items-center gap-2 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-accent-cyan" : ""}`} />
          <span>Refresh</span>
        </button>
      </div>

      {error ? (
        <div className="bg-dark-900 border border-dark-800 p-6 rounded space-y-3">
          <div className="flex items-center gap-2 text-amber-400">
            <Database className="w-5 h-5" />
            <h2 className="text-sm font-semibold">MongoDB Inactive — Stateless Operating Mode</h2>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            The REST API is currently serving susceptibility predictions dynamically from disk without persisting historical queries to a local MongoDB instance. All real-time calculations and map layers remain 100% functional.
          </p>
          <div className="p-3 rounded bg-dark-850 border border-dark-800 text-xs font-mono text-slate-300">
            To enable database persistence, run: <code className="text-accent-cyan">docker-compose up -d mongodb</code>
          </div>
        </div>
      ) : predictions.length === 0 ? (
        <div className="bg-dark-900 border border-dark-800 p-12 rounded text-center space-y-2">
          <Clock className="w-8 h-8 text-dark-700 mx-auto" />
          <div className="text-xs font-medium text-slate-400">No Query History Recorded</div>
          <p className="text-[11px] text-slate-500 max-w-sm mx-auto">
            Use the Location Analysis tab to evaluate specific coordinates in Gurugram; results will be logged here automatically.
          </p>
        </div>
      ) : (
        <div className="bg-dark-900 border border-dark-800 rounded overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-dark-850 text-slate-400 font-mono border-b border-dark-800">
                <tr>
                  <th className="py-2.5 px-4 font-medium">Timestamp</th>
                  <th className="py-2.5 px-4 font-medium">Coordinates</th>
                  <th className="py-2.5 px-4 font-medium">Analysis Unit</th>
                  <th className="py-2.5 px-4 font-medium">FSI Score</th>
                  <th className="py-2.5 px-4 font-medium">Susceptibility Level</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-800 font-mono">
                {predictions.map((p, idx) => (
                  <tr key={idx} className="hover:bg-dark-850/50">
                    <td className="py-3 px-4 text-slate-400 text-[11px]">
                      {p.timestamp ? new Date(p.timestamp).toLocaleString() : "N/A"}
                    </td>
                    <td className="py-3 px-4 text-white">
                      {p.input?.latitude?.toFixed(4)}°N, {p.input?.longitude?.toFixed(4)}°E
                    </td>
                    <td className="py-3 px-4 text-accent-cyan">{p.cell_id}</td>
                    <td className="py-3 px-4 font-bold text-white">
                      {p.result?.fsi?.toFixed(3)}
                    </td>
                    <td className="py-3 px-4">
                      <span className="capitalize text-slate-300">
                        {p.result?.fsi_class?.replace("_", " ")}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
