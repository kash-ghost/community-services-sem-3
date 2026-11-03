import React, { useState, useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  CircleMarker,
  Popup,
  useMap,
} from "react-leaflet";
import { fetchAreas, fetchObservations } from "../services/api";
import { GMDAPoint, GridCellFeature } from "../types";
import { Layers, Filter, Eye, AlertCircle, Info } from "lucide-react";

export const InteractiveMap: React.FC = () => {
  const [gridData, setGridData] = useState<any | null>(null);
  const [observations, setObservations] = useState<GMDAPoint[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedCell, setSelectedCell] = useState<any | null>(null);

  // Layer Visibility Controls
  const [showGrid, setShowGrid] = useState<boolean>(true);
  const [showObservations, setShowObservations] = useState<boolean>(true);
  const [classFilter, setClassFilter] = useState<string>("all");
  const [minFsi, setMinFsi] = useState<number>(0);

  useEffect(() => {
    async function loadMapData() {
      setLoading(true);
      try {
        const [areasResp, obsResp] = await Promise.all([
          fetchAreas(),
          fetchObservations(),
        ]);
        setGridData(areasResp);
        setObservations(obsResp.features || []);
      } catch (err) {
        console.error("Error loading map layers:", err);
      } finally {
        setLoading(false);
      }
    }
    loadMapData();
  }, []);

  const getFsiColor = (fsi: number, fsiClass: string) => {
    switch (fsiClass) {
      case "very_high":
        return "#ef4444";
      case "high":
        return "#f97316";
      case "moderate":
        return "#eab308";
      case "low":
        return "#10b981";
      default:
        return "#64748b";
    }
  };

  const styleGridFeature = (feature: any) => {
    const props = feature.properties;
    const fsi = props.fsi || 0;
    const fsiClass = props.fsi_class || "unknown";

    // Filter check
    if (classFilter !== "all" && fsiClass !== classFilter) {
      return { stroke: false, fillOpacity: 0 };
    }
    if (fsi < minFsi) {
      return { stroke: false, fillOpacity: 0 };
    }

    return {
      fillColor: getFsiColor(fsi, fsiClass),
      weight: 0.5,
      opacity: 0.6,
      color: "#1e293b",
      fillOpacity: 0.45,
    };
  };

  const onEachCell = (feature: any, layer: any) => {
    layer.on({
      click: () => {
        setSelectedCell(feature.properties);
      },
    });
  };

  return (
    <div className="space-y-4">
      {/* Control bar */}
      <div className="bg-dark-900 border border-dark-800 p-4 rounded flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-4 text-xs">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-accent-cyan" />
            <span className="font-semibold text-white">Active Layers:</span>
          </div>

          <label className="flex items-center gap-1.5 cursor-pointer text-slate-300">
            <input
              type="checkbox"
              checked={showGrid}
              onChange={(e) => setShowGrid(e.target.checked)}
              className="rounded bg-dark-800 border-dark-700 text-accent-cyan"
            />
            <span>500m Susceptibility Grid (6,925 Units)</span>
          </label>

          <label className="flex items-center gap-1.5 cursor-pointer text-slate-300">
            <input
              type="checkbox"
              checked={showObservations}
              onChange={(e) => setShowObservations(e.target.checked)}
              className="rounded bg-dark-800 border-dark-700 text-accent-cyan"
            />
            <span>GMDA Observed Points (25 Sites)</span>
          </label>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <div className="flex items-center gap-1.5 text-slate-400">
            <Filter className="w-3.5 h-3.5" />
            <span>Class:</span>
          </div>
          <select
            value={classFilter}
            onChange={(e) => setClassFilter(e.target.value)}
            className="bg-dark-850 border border-dark-700 text-slate-200 rounded px-2 py-1 text-xs font-mono"
          >
            <option value="all">All Classes</option>
            <option value="very_high">Very High Only</option>
            <option value="high">High Only</option>
            <option value="moderate">Moderate Only</option>
            <option value="low">Low Only</option>
          </select>

          <div className="flex items-center gap-2 text-slate-400">
            <span>Min FSI:</span>
            <input
              type="range"
              min="0"
              max="0.8"
              step="0.05"
              value={minFsi}
              onChange={(e) => setMinFsi(parseFloat(e.target.value))}
              className="w-20 accent-accent-cyan cursor-pointer"
            />
            <span className="font-mono text-white w-8">{minFsi.toFixed(2)}</span>
          </div>
        </div>
      </div>

      {/* Map + Inspector Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Main Leaflet Map */}
        <div className="lg:col-span-3 bg-dark-900 border border-dark-800 rounded h-[620px] relative overflow-hidden">
          {loading && (
            <div className="absolute inset-0 bg-dark-950/80 z-20 flex items-center justify-center">
              <div className="text-center font-mono text-xs text-accent-cyan">
                Rendering Gurugram GIS Layers...
              </div>
            </div>
          )}

          <MapContainer
            center={[28.4595, 77.0266]}
            zoom={12}
            scrollWheelZoom={true}
            className="w-full h-full"
          >
            {/* CartoDB Dark Matter basemap */}
            <TileLayer
              attribution='&copy; <a href="https://carto.com/">CARTO</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              maxZoom={19}
            />

            {/* 500m Susceptibility Grid */}
            {showGrid && gridData && (
              <GeoJSON
                data={gridData}
                style={styleGridFeature}
                onEachFeature={onEachCell}
              />
            )}

            {/* GMDA Waterlogging Points */}
            {showObservations &&
              observations.map((pt, idx) => {
                const [lon, lat] = pt.geometry.coordinates;
                return (
                  <CircleMarker
                    key={idx}
                    center={[lat, lon]}
                    radius={5}
                    pathOptions={{
                      color: "#38bdf8",
                      fillColor: "#0284c7",
                      fillOpacity: 0.9,
                      weight: 2,
                    }}
                  >
                    <Popup>
                      <div className="text-xs space-y-1 font-sans">
                        <div className="font-bold text-accent-cyan font-mono">
                          GMDA Waterlogging Site #{pt.properties.objectid}
                        </div>
                        <div>
                          <strong className="text-slate-400">Type:</strong>{" "}
                          {pt.properties.surveytype}
                        </div>
                        {pt.properties.zone && (
                          <div>
                            <strong className="text-slate-400">Zone:</strong>{" "}
                            {pt.properties.zone}
                          </div>
                        )}
                        {pt.properties.remarks && (
                          <div>
                            <strong className="text-slate-400">Remarks:</strong>{" "}
                            {pt.properties.remarks}
                          </div>
                        )}
                        <div className="text-[10px] text-amber-300 font-mono mt-1 pt-1 border-t border-dark-700">
                          surveydate: NULL (undated field record)
                        </div>
                      </div>
                    </Popup>
                  </CircleMarker>
                );
              })}
          </MapContainer>

          {/* Map Legend Overlay */}
          <div className="absolute bottom-4 left-4 z-10 bg-dark-900/90 backdrop-blur border border-dark-800 p-3 rounded text-xs space-y-2 pointer-events-auto font-mono">
            <div className="font-semibold text-slate-200">Susceptibility (FSI)</div>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1.5">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded bg-rose-500 inline-block" />
                <span className="text-slate-300">Very High (≥ 0.75)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded bg-orange-500 inline-block" />
                <span className="text-slate-300">High (0.50–0.75)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded bg-amber-400 inline-block" />
                <span className="text-slate-300">Moderate (0.25–0.50)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded bg-emerald-500 inline-block" />
                <span className="text-slate-300">Low (&lt; 0.25)</span>
              </div>
            </div>
            <div className="pt-2 border-t border-dark-800 flex items-center gap-2 text-slate-300">
              <span className="w-2.5 h-2.5 rounded-full bg-accent-blue border border-white inline-block" />
              <span>GMDA Survey Point (25 Verified)</span>
            </div>
          </div>
        </div>

        {/* Location Inspector Panel */}
        <div className="bg-dark-900 border border-dark-800 p-4 rounded h-[620px] overflow-y-auto space-y-4">
          <div className="flex items-center gap-2 border-b border-dark-800 pb-3">
            <Info className="w-4 h-4 text-accent-cyan" />
            <h3 className="text-sm font-semibold text-white">Unit Inspector</h3>
          </div>

          {selectedCell ? (
            <div className="space-y-4 text-xs">
              <div className="bg-dark-850 p-3 rounded border border-dark-800">
                <div className="text-[10px] font-mono text-slate-500 uppercase">
                  Cell Identifier
                </div>
                <div className="text-base font-bold font-mono text-white mt-0.5">
                  {selectedCell.cell_id}
                </div>
                <div className="text-[11px] font-mono text-slate-400 mt-1">
                  Centroid: {selectedCell.centroid_lat?.toFixed(5)}°N,{" "}
                  {selectedCell.centroid_lon?.toFixed(5)}°E
                </div>
              </div>

              {/* FSI Score Badge */}
              <div className="bg-dark-850 p-3 rounded border border-dark-800">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Susceptibility Score</span>
                  <span className="font-mono text-lg font-bold text-accent-cyan">
                    {selectedCell.fsi?.toFixed(3)}
                  </span>
                </div>
                <div className="mt-2 text-xs font-semibold capitalize flex items-center gap-2">
                  <span
                    className="w-2.5 h-2.5 rounded-full"
                    style={{
                      backgroundColor: getFsiColor(
                        selectedCell.fsi,
                        selectedCell.fsi_class
                      ),
                    }}
                  />
                  <span className="text-white">
                    {selectedCell.fsi_class?.replace("_", " ")} Susceptibility
                  </span>
                </div>
              </div>

              {/* Extracted Physical Attributes */}
              <div className="space-y-2">
                <div className="font-semibold text-slate-300 text-[11px] uppercase tracking-wide">
                  Physical Feature Matrix
                </div>

                <div className="p-2 rounded bg-dark-850 border border-dark-800 space-y-1.5 font-mono text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-slate-400">DEM Elevation:</span>
                    <span className="text-slate-200">
                      {selectedCell.elevation_m !== undefined
                        ? `${selectedCell.elevation_m} m`
                        : "N/A"}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-slate-400">Surface Slope:</span>
                    <span className="text-slate-200">
                      {selectedCell.slope_deg !== undefined
                        ? `${selectedCell.slope_deg}°`
                        : "N/A"}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-slate-400">Built-Up Fraction:</span>
                    <span className="text-slate-200">
                      {selectedCell.built_up_frac !== undefined
                        ? `${(selectedCell.built_up_frac * 100).toFixed(1)}%`
                        : "N/A"}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-slate-400">Vegetation Fraction:</span>
                    <span className="text-slate-200">
                      {selectedCell.veg_frac !== undefined
                        ? `${(selectedCell.veg_frac * 100).toFixed(1)}%`
                        : "N/A"}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-slate-400">Distance to Drain:</span>
                    <span className="text-slate-200">
                      {selectedCell.dist_to_drain_m !== undefined
                        ? `${Math.round(selectedCell.dist_to_drain_m)} m`
                        : "N/A"}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-slate-400">Distance to Water:</span>
                    <span className="text-slate-200">
                      {selectedCell.dist_to_water_m !== undefined
                        ? `${Math.round(selectedCell.dist_to_water_m)} m`
                        : "N/A"}
                    </span>
                  </div>
                </div>
              </div>

              <div className="p-2.5 rounded bg-dark-850 border border-dark-800 text-[11px] text-slate-400 leading-relaxed">
                Click any other cell on the map to inspect its terrain elevation, drainage proximity, and susceptibility factors.
              </div>
            </div>
          ) : (
            <div className="h-[480px] flex flex-col items-center justify-center text-center p-4 text-slate-500 space-y-2">
              <Eye className="w-8 h-8 text-dark-700" />
              <div className="text-xs font-medium text-slate-400">
                No Unit Selected
              </div>
              <p className="text-[11px] max-w-xs text-slate-500">
                Click any 500m grid cell on the map to inspect its real environmental features and relative susceptibility score.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
