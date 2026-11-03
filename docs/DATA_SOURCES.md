# DATA SOURCES REGISTER
# Flood Vulnerability Prediction Framework — Gurugram, Haryana

## How to read this file
Each entry documents a dataset used in or considered for this project.
Fields: Source, URL, Access, License, Spatial resolution, Temporal coverage,
        Acquisition date, Processing steps, Limitations, Status.

---

## DS-001: GMDA Flood Survey v2 (Waterlogging Points)
| Field | Value |
|---|---|
| Source | Gurugram Metropolitan Development Authority (GMDA) |
| URL | https://onemapdepts.gmda.gov.in/server/rest/services/flood_survey_2/FeatureServer/0 |
| Access | Publicly accessible ArcGIS REST endpoint; no authentication required |
| License | Government of India GIS data; no explicit open license found. Used under implied public disclosure for academic research. |
| Geometry type | Point (EPSG:4326) |
| Record count | 25 (verified 2026-10-20) |
| Spatial coverage | 76.97°E–77.25°E, 28.26°N–28.55°N |
| Temporal coverage | UNKNOWN — surveydate NULL for all 25 records |
| Acquisition date | 2026-10-20 |
| Raw file | data/raw/gmda/flood_survey_v2_raw.geojson |
| Processing steps | Direct GeoJSON export via /query?f=geojson; no reprojection needed |
| Limitations | Only 25 records; no survey dates; zone/ward empty for 24/25; no negative observations; cannot support supervised classification |
| Status | Downloaded and saved |

---

## DS-002: Open-Meteo Historical Weather API (Rainfall)
| Field | Value |
|---|---|
| Source | Open-Meteo (https://open-meteo.com) — backed by ERA5-Land reanalysis (ECMWF) |
| URL | https://archive-api.open-meteo.com/v1/archive |
| Access | Fully open; no registration, no API key |
| License | Free for non-commercial use (CC BY 4.0 attribution); ERA5-Land underlying license: Copernicus |
| Format | JSON (daily totals) |
| Spatial resolution | ~9 km (ERA5-Land grid) |
| Temporal coverage | 1940–present (hourly); daily aggregates available |
| Parameters acquired | precipitation_sum (daily, mm), rain, temperature_2m_max, temperature_2m_min |
| Study period | 2015-01-01 to 2024-09-30 |
| Study location | lat=28.4595, lon=77.0266 (Gurugram centroid) |
| Acquisition date | Phase 2 (pending) |
| Raw file | data/raw/rainfall/openmeteo_gurugram_2015_2024.json |
| Processing steps | HTTP GET → parse JSON → extract daily_data → save CSV |
| Limitations | Reanalysis data; not station observations; monsoon convection may be spatially smoothed; single point (no spatial variation within study area) |
| Status | Pending Phase 2 download |

---

## DS-003: IMD Pune Gridded Rainfall (0.25° Daily)
| Field | Value |
|---|---|
| Source | India Meteorological Department, Pune — Climate Research Division |
| URL | https://www.imdpune.gov.in/Clim_Pred_LRF_New/Grided_Data_Download.html |
| Access | Open; no registration for direct file download |
| License | IMD / Government of India — free for academic research |
| Format | NetCDF (.nc) or Binary |
| Spatial resolution | 0.25°×0.25° (~27.5 km) |
| Temporal coverage | 1901–present (annual files) |
| Study period | 2015–2024 |
| Acquisition date | Phase 2 (pending) |
| Raw file | data/raw/rainfall/imd_gridded_<year>.nc |
| Python tooling | pip install imddata; imd.get_data(var='rf', start='2015-01-01', end='2024-09-30') |
| Limitations | Coarse 0.25° resolution; does not resolve sub-district rainfall variation |
| Status | Pending Phase 2 download |

---

## DS-004: Copernicus DEM GLO-30
| Field | Value |
|---|---|
| Source | Copernicus Programme / European Space Agency |
| URL | https://dataspace.copernicus.eu/ (portal) |
| S3 (no login) | s3://copernicus-dem-30m/ (AWS eu-central-1) |
| Direct HTTPS tile | https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com/Copernicus_DSM_COG_10_N28_00_E077_00_DEM/Copernicus_DSM_COG_10_N28_00_E077_00_DEM.tif |
| Access | Open; no registration required for S3/HTTPS COG access |
| License | Copernicus DEM License — free for academic and commercial use |
| Format | Cloud Optimized GeoTIFF (COG) |
| Spatial resolution | 30 m (1 arc-second) |
| Type | DSM (Digital Surface Model — includes buildings and vegetation) |
| Temporal coverage | ~2010–2015 acquisition (static) |
| Acquisition date | Phase 2 (pending) |
| Raw file | data/raw/elevation/cop_dem_glg30_gurugram.tif |
| Processing steps | Partial read via rasterio window; clip to study bbox; compute slope; aggregate to 500m grid cells |
| Limitations | DSM not DTM — building heights inflate elevation in urban areas; 30m nominal but urban DSM error can exceed 5m |
| Status | Pending Phase 2 download |

---

## DS-005: ESA WorldCover v2 (10m Land Cover, 2021)
| Field | Value |
|---|---|
| Source | European Space Agency (ESA) — WorldCover project |
| URL | https://esa-worldcover.org/ |
| Zenodo DOI | 10.5281/zenodo.7254221 |
| S3 bucket | s3://esa-worldcover (public COG tiles) |
| Access | Open; no registration required via Zenodo or S3 |
| License | CC BY 4.0 |
| Format | GeoTIFF (COG), 3°×3° tiles |
| Spatial resolution | 10 m |
| Temporal coverage | 2021 (single epoch) |
| Classes | 11 classes: Built-up (50), Tree cover (10), Cropland (40), Permanent water bodies (80), etc. |
| Gurugram tile | N27E075 or N27E078 — need to verify |
| Acquisition date | Phase 2 (pending) |
| Raw file | data/raw/landcover/esa_worldcover_2021_gurugram.tif |
| Processing steps | Download tile covering bbox; clip to study area; compute per-cell fractions for built-up, water, vegetation |
| Limitations | 2021 vintage; Gurugram urbanisation is rapid — built-up extent has changed since 2021 |
| Status | Pending Phase 2 download |

---

## DS-006: OpenStreetMap — Drainage and Water Bodies
| Field | Value |
|---|---|
| Source | OpenStreetMap contributors |
| Access | Open Database Licence (ODbL) |
| Acquisition method | Overpass Turbo API (https://overpass-turbo.eu/) or Geofabrik extract |
| Overpass endpoint | https://overpass-api.de/api/interpreter |
| Features extracted | waterway=drain, waterway=ditch, waterway=canal, natural=water, natural=wetland |
| Spatial coverage | Custom bbox: [76.80, 28.20, 77.25, 28.55] |
| Acquisition date | Phase 2 (pending) |
| Raw files | data/raw/landcover/osm_waterways_gurugram.geojson, osm_water_polygons_gurugram.geojson |
| Processing steps | Overpass query → GeoJSON → dissolve → compute distance raster to 500m grid |
| Limitations | OSM drain coverage in Gurugram is incomplete — informal stormwater channels and katcha drains are under-mapped |
| Status | Pending Phase 2 download |
