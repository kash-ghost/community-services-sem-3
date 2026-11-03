# ARCHITECTURE & SYSTEM DESIGN
## Flood Vulnerability Prediction Framework — Gurugram, Haryana

```
+-----------------------------------------------------------------------------------+
|                                 CLIENT TIER                                       |
|                                                                                   |
|   React 18 + TypeScript + Tailwind CSS (Vite SPA)                                 |
|   - Leaflet Geospatial Viewer (Dark Matter Basemap, 500m Grid, GMDA Survey Overlay) |
|   - Analytical Dashboard & Recharts Factor Contributions                          |
|   - Location Analysis & Sensitivity Exploration Tool                              |
+------------------------------------------+----------------------------------------+
                                           | HTTP REST / JSON
                                           v
+-----------------------------------------------------------------------------------+
|                              BACKEND API TIER                                     |
|                                                                                   |
|   Flask 3.1 REST Service (Python 3.13)                                            |
|   - CORS Middleware & Blueprints (/api/v1)                                        |
|   - Boundary Validation & Coordinate Geo-Hashing                                  |
|   - Spatial KdTree / Centroid Interpolation Service                               |
|   - Transparent Factor Decomposition Engine                                       |
+--------------------+-------------------------------------+------------------------+
                     |                                     |
                     v                                     v
+----------------------------------+     +------------------------------------------+
|       PERSISTENCE TIER           |     |         GIS & ANALYTICAL PIPELINE        |
|                                  |     |                                          |
|  MongoDB (Local / Docker)        |     |  - Rasterio, GeoPandas, Shapely, PyProj  |
|  - Database: flood_vulnerability |     |  - 6,925 500m Grid Cells (EPSG:32643)    |
|  - Collection: predictions       |     |  - Copernicus DEM GLO-30 Merge           |
|  - Query audit logging           |     |  - ESA WorldCover 10m Land Cover         |
|  - Graceful stateless fallback   |     |  - GMDA Authoritative Drain Trunk Vector |
+----------------------------------+     |  - Open-Meteo ERA5-Land Rainfall Series  |
                                         +------------------------------------------+
```

---

## 1. Modular Monorepo Organization

```text
flood-vulnerability-framework/
├── backend/                  # Flask REST application
│   ├── app.py                # Server entry point & CORS configuration
│   ├── routes/api.py         # Versioned REST endpoints (/api/v1)
│   ├── services/predictor.py # Spatial feature lookup & FSI engine
│   ├── schemas/prediction.py # Payload validation schemas
│   └── database/mongo.py     # MongoDB client with offline fallback
├── frontend/                 # React 18 + TypeScript + Vite SPA
│   ├── src/
│   │   ├── components/       # Navbar, Status indicators
│   │   ├── pages/            # Overview, InteractiveMap, DataExplorer, ModelLab, LocationAnalysis, History
│   │   ├── services/api.ts   # REST client
│   │   └── types/index.ts    # TypeScript interfaces
│   └── dist/                 # Production compiled bundle
├── data/
│   ├── raw/                  # Preserved raw data (GMDA GeoJSON, DEM TIFFs, Rainfall JSON)
│   ├── processed/            # Processed Parquet feature table, Grid GeoJSON, Daily CSVs
│   └── reports/              # Reproducible JSON audit logs, sensitivity reports, quality reports
├── ml/                       # Reproducible data engineering & analysis scripts
│   ├── inspect_sources.py    # Remote GIS endpoint audit
│   ├── download_data.py      # Automated data acquisition
│   ├── preprocess.py         # Merging, clipping, and raster/vector harmonization
│   ├── build_features.py     # 500m grid generation & FSI calculation
│   ├── build_labels.py       # Empirical target label evaluation scaffold
│   ├── train.py              # Supervised ML training module (Random Forest & LR)
│   └── evaluate.py           # Sensitivity analysis & GMDA spatial validation
├── models/                   # Config artifacts & serialized model weights
│   └── fsi_config.json       # Weighting parameters, bounds, and thresholds
├── tests/                    # Pytest test suite
│   ├── unit/                 # Coordinate validation & boundary tests
│   └── integration/          # API endpoint and database integration tests
├── docs/                     # Academic documentation and methodology
└── docker-compose.yml        # Containerized MongoDB & multi-tier orchestration
```

---

## 2. Design Patterns & Architectural Decisions

1. **Separation of Raw and Derived Assets**:
   Raw datasets downloaded from remote sources (`data/raw/`) are treated as immutable. Derived grids and aggregated statistics are deposited into `data/processed/`.

2. **Stateless Fallback for Persistence**:
   `backend/database/mongo.py` pings MongoDB with a 2000ms timeout. If MongoDB is inactive, the API gracefully operates statelessly, serving spatial predictions from parquet and disk while alerting the frontend via a status badge.

3. **Windowed Raster Reads**:
   Rather than loading multi-gigabyte regional rasters into memory, `ml/build_features.py` leverages `rasterio.windows.from_bounds` to slice exact cell bounding boxes in milliseconds.

4. **Coordinate System Consistency**:
   - Storage and API exchange: `EPSG:4326` (WGS84 decimal degrees).
   - Distance and spatial area computations: `EPSG:32643` (UTM Zone 43N, meters).
