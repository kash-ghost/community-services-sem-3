import React, { useState, useEffect } from "react";
import { SystemMetadata } from "../types";
import { Database, AlertTriangle, CheckCircle, ExternalLink, FileText } from "lucide-react";

interface DataExplorerProps {
  metadata: SystemMetadata | null;
}

export const DataExplorer: React.FC<DataExplorerProps> = ({ metadata }) => {
  const sources = [
    {
      id: "DS-001",
      name: "GMDA Flood Survey v2 (Waterlogging Locations)",
      origin: "Gurugram Metropolitan Development Authority (GMDA)",
      url: "https://onemapdepts.gmda.gov.in/server/rest/services/flood_survey_2/FeatureServer/0",
      type: "Vector (Point Feature Layer)",
      records: "25 features (24 Waterlogging, 1 Gully Trap)",
      temporal: "Undated (surveydate is NULL across all records)",
      resolution: "Spatial coordinates in WGS84 (EPSG:4326)",
      access: "Publicly accessible ArcGIS REST endpoint",
      limitations: "Zero survey dates; cannot correlate with specific rainfall events; presence-only records with no confirmed non-flooded counterfactuals.",
      verified: true,
    },
    {
      id: "DS-002",
      name: "Open-Meteo Historical Weather API (ERA5-Land)",
      origin: "European Centre for Medium-Range Weather Forecasts (ECMWF) via Open-Meteo",
      url: "https://archive-api.open-meteo.com/v1/archive",
      type: "Tabular Time-Series (CSV & JSON)",
      records: "3,561 daily records (2015-01-01 to 2024-09-30)",
      temporal: "10 monsoon seasons (June–September totals)",
      resolution: "0.1° (~9 km) downscaled reanalysis",
      access: "Open Access (CC BY 4.0)",
      limitations: "Reanalysis estimate rather than ground rain gauge station; smoothed convective precipitation peaks; spatially uniform across 500m study grid.",
      verified: true,
    },
    {
      id: "DS-004",
      name: "Copernicus DEM GLO-30",
      origin: "Copernicus Space Component / European Space Agency",
      url: "https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com",
      type: "Raster GeoTIFF (Cloud-Optimized GeoTIFF)",
      records: "2 tiles merged: N28_00_E076_00 and N28_00_E077_00",
      temporal: "Static terrain representation (2010–2015 baseline)",
      resolution: "30-meter ground pixel resolution (1 arc-second)",
      access: "Free Open Access via AWS S3",
      limitations: "Surface Model (DSM) rather than bare-earth DTM; includes building heights and tree canopies which slightly inflate urban core elevations.",
      verified: true,
    },
    {
      id: "DS-005",
      name: "ESA WorldCover 2021 v200",
      origin: "European Space Agency (ESA) & Consortium",
      url: "https://esa-worldcover.s3.eu-central-1.amazonaws.com",
      type: "10m Land Cover Classification Raster",
      records: "Tile ESA_WorldCover_10m_2021_v200_N27E075_Map.tif",
      temporal: "2021 single-epoch baseline",
      resolution: "10-meter Sentinel-1 & Sentinel-2 composite",
      access: "CC BY 4.0 Open License",
      limitations: "2021 baseline; rapid peri-urban construction along Dwarka Expressway and Southern Peripheral Road after 2021 is not reflected.",
      verified: true,
    },
    {
      id: "DS-006",
      name: "GMDA Authoritative GIS Drainage Infrastructure",
      origin: "GMDA OneMap Official GIS Server",
      url: "https://onemapdepts.gmda.gov.in/server/rest/services/Water_Infrastructure_with_Runoff/MapServer",
      type: "Vector (Drain Legs, Najafgarh Corridor, 1980 Waterbodies)",
      records: "4 Drain Legs, 211 Water Bodies, 36 Municipal Wards, 10 Watersheds",
      temporal: "Official master plan drainage alignment",
      resolution: "Meter-precision engineering cadastral lines",
      access: "Publicly accessible GMDA MapServer",
      limitations: "Captures major trunk drain corridors (Badshahpur, Leg I, II, III); secondary municipal roadside culverts are partially unmapped.",
      verified: true,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Title & Provenance Overview */}
      <div className="bg-dark-900 border border-dark-800 p-6 rounded">
        <h1 className="text-xl font-bold text-white tracking-tight">
          Data Provenance & Quality Explorer
        </h1>
        <p className="text-sm text-slate-400 mt-1 max-w-3xl leading-relaxed">
          Comprehensive register of genuine public datasets acquired, preprocessed, and integrated into the Gurugram flood vulnerability analysis. All sources were verified live against remote servers.
        </p>
      </div>

      {/* Dataset Audit Cards */}
      <div className="space-y-4">
        {sources.map((s) => (
          <div key={s.id} className="bg-dark-900 border border-dark-800 p-5 rounded space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-dark-800 pb-3">
              <div className="flex items-center gap-3">
                <span className="font-mono text-xs px-2 py-0.5 rounded bg-dark-800 text-accent-cyan border border-dark-700">
                  {s.id}
                </span>
                <h2 className="text-base font-semibold text-white">{s.name}</h2>
              </div>
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800 text-emerald-400">
                  <CheckCircle className="w-3 h-3" />
                  Verified Empirical
                </span>
                <a
                  href={s.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-slate-400 hover:text-white p-1"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs font-mono">
              <div>
                <span className="text-slate-500">Source:</span>{" "}
                <span className="text-slate-300 font-sans">{s.origin}</span>
              </div>
              <div>
                <span className="text-slate-500">Coverage:</span>{" "}
                <span className="text-slate-300 font-sans">{s.records}</span>
              </div>
              <div>
                <span className="text-slate-500">Resolution:</span>{" "}
                <span className="text-slate-300 font-sans">{s.resolution}</span>
              </div>
            </div>

            {/* Quality Warnings & Documented Limitations */}
            <div className="p-3 rounded bg-dark-850 border border-dark-800 flex items-start gap-2.5 text-xs">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <strong className="text-slate-300 font-medium">Documented Data Limitations:</strong>{" "}
                <span className="text-slate-400 leading-relaxed">{s.limitations}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Target Feasibility Disclosure */}
      <div className="bg-dark-900 border border-dark-800 p-5 rounded space-y-3">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <FileText className="w-4 h-4 text-accent-cyan" />
          <span>Scientific Disclosure: Supervised ML Target Feasibility</span>
        </h3>
        <p className="text-xs text-slate-400 leading-relaxed">
          The project audit established that while GMDA publishes 25 field survey points with coordinates in Gurugram, all 25 survey dates are null and no confirmed non-flooded negative samples exist in public records. Creating an un-validated supervised classification model on this data would violate scientific reproducibility rules. Consequently, the framework executes a Multi-Criteria Susceptibility Index (FSI) utilizing published AHP weighting schemes, leaving the ML pipeline scaffold ready for when temporal flood extent records become available.
        </p>
      </div>
    </div>
  );
};
