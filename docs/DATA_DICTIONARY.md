# DATA DICTIONARY
## Flood Vulnerability Prediction Framework — Gurugram, Haryana

This dictionary defines all variables, attributes, data types, physical units, sources, and valid ranges utilized across the data-processing, GIS, and analytical layers.

---

## 1. Primary Feature Table (`data/processed/features.parquet`)

| Feature Name | Type | Physical Unit | Valid Range | Source Dataset | Directionality / Description |
|---|---|---|---|---|---|
| `cell_id` | String | Identifier | `C_RRR_CCC` | Derived Grid | Unique grid identifier with row and column indices. |
| `centroid_lon` | Float | Decimal Degrees | [76.80, 77.25] | Grid Geometry | Centroid longitude coordinate (WGS84). |
| `centroid_lat` | Float | Decimal Degrees | [28.20, 28.55] | Grid Geometry | Centroid latitude coordinate (WGS84). |
| `elevation_m` | Float | Meters (MSL) | [187.5, 346.8] | Copernicus DEM GLO-30 | Median ground elevation within the 500m cell. **Inverted**: Lower elevation implies increased surface runoff pooling. |
| `slope_deg` | Float | Degrees | [0.0, 35.0] | Derived from DEM | Mean surface slope gradient. **Inverted**: Flatter surfaces (&lt;1.0°) impede gravity drainage. |
| `built_up_frac` | Float | Proportion [0, 1] | [0.0, 1.0] | ESA WorldCover 2021 (Class 50) | Fraction of cell occupied by impermeable urban structures, asphalt, and concrete. |
| `veg_frac` | Float | Proportion [0, 1] | [0.0, 1.0] | ESA WorldCover 2021 (Classes 10, 20, 30) | Permeable vegetative cover (trees, shrubland, grassland). **Inverted**: Higher vegetation aids soil infiltration. |
| `water_frac` | Float | Proportion [0, 1] | [0.0, 1.0] | ESA WorldCover 2021 (Class 80) | Surface water fraction (permanent ponds, detention basins). |
| `dist_to_water_m` | Float | Meters | [0.0, 30000.0] | GMDA 1980 Waterbodies | Euclidean distance from cell centroid to nearest mapped waterbody or pond. **Inverted**: Proximity increases waterlogging risk. |
| `dist_to_drain_m` | Float | Meters | [0.0, 32000.0] | GMDA Drain Legs | Euclidean distance from cell centroid to nearest primary trunk drainage artery. **Inverted**: Direct proximity to over-capacity drains correlates with backflow risk. |
| `monsoon_rainfall_mm`| Float | Millimeters | [0.0, 1500.0] | Open-Meteo (ERA5-Land) | 10-year mean annual monsoon season precipitation (June to September). Spatially uniform baseline (528.7 mm). |
| `fsi` | Float | Normalized Index | [0.0, 1.0] | Multi-Criteria AHP Formula | Composite Flood Susceptibility Index score. |
| `fsi_class` | Categorical | Class String | `low`, `moderate`, `high`, `very_high` | Classification Thresholds | Qualitative category assigned via equal intervals (0.25 steps). |

---

## 2. Target Observation Layer (`data/processed/gmda_survey_points.geojson`)

Authoritative field survey points queried from GMDA ArcGIS FeatureServer:

| Attribute | Type | Description | Observed Quality in Audit |
|---|---|---|---|
| `objectid` | Integer | System sequential primary key. | Populated (100%) |
| `surveyid` | String | Internal GMDA survey identifier. | Populated (100%) |
| `surveytype` | String | Classification of site (`Waterlogging`, `Gully Trap`). | 24 Waterlogging, 1 Gully Trap |
| `waterloggingtype` | String | Specific surface context (`Road`, `Surface Water`, `Sewerage`). | Null in 96% of records |
| `remarks` | String | Inspector field notes (e.g. `GMDA Jurisdiction`). | Populated in select points |
| `zone` | String | Administrative municipal zone (I, II, III, IV). | Populated in 1 record |
| `sector` | String | Gurugram urban sector identifier. | Null in 96% of records |
| `surveydate` | Date/Timestamp | Timestamp when waterlogging was verified. | **NULL across all 25 records (100% missing)** |

---

## 3. Database Schema (`predictions` Collection in MongoDB)

| Field | BSON Type | Description |
|---|---|---|
| `_id` | ObjectId | MongoDB internal document key. |
| `timestamp` | ISO String | UTC timestamp when prediction was generated. |
| `prediction_id` | String | Deterministic tracking ID (`pred_{cell_id}_{lat}_{lon}`). |
| `model_version` | String | Pipeline version used (`fsi_v1.0`). |
| `prediction_mode` | String | Methodological mode (`susceptibility_index`). |
| `input` | Object | Requested coordinates `{ latitude: Number, longitude: Number }`. |
| `cell_id` | String | Matching 500m analysis cell. |
| `result` | Object | `{ fsi: Number, fsi_class: String, fsi_class_label: String }`. |
| `features` | Object | Extracted physical feature attributes for the query cell. |
| `feature_contributions` | Object | Relative percentage contributions of each factor to final FSI. |
| `limitations` | Array of Strings | Disclaimers and scientific provenance warnings attached to the output. |
