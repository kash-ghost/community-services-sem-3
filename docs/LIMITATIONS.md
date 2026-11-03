# SCIENTIFIC LIMITATIONS & HONESTY DISCLOSURE
## Flood Vulnerability Prediction Framework — Gurugram, Haryana

To adhere to the rigorous anti-vibe-coding and academic integrity protocols of this framework, this document enumerates all known data constraints, sensor limitations, and operational boundaries.

---

## 1. Ground Truth Observation Bias (GMDA Data)

* **Temporal Gap**: In the GMDA Flood Survey v2 FeatureServer layer, the `surveydate` attribute is `NULL` across all 25 records. It is physically impossible to link these surveyed waterlogging sites to specific storm events or historical rainfall return periods.
* **Presence-Only Bias**: The GMDA records indicate spots where municipal personnel surveyed or reported waterlogging; they do not represent an exhaustive census of all flooded surfaces in Gurugram, nor do they record locations verified *not* to have flooded (no true negative controls).
* **Mitigation**: These points are strictly utilized as an independent qualitative spatial validation overlay. They are **never** converted into fake pseudo-absence labels for machine learning.

---

## 2. Digital Surface Model (DSM) vs. Bare-Earth DTM

* **Structure Infiltration**: Copernicus DEM GLO-30 is a Digital Surface Model derived from radar interferometry. In dense urban sectors of Gurugram (e.g. Cyber City, Golf Course Road), rooftop elevations and highway flyovers inflate pixel elevation values by 15–40 meters above bare earth.
* **Micro-Topography**: Street-level drainage curb dynamics and minor depression hollows smaller than 30 meters are not resolved.
* **Mitigation**: Aggregating median elevations within 500m × 500m cells attenuates high-frequency rooftop noise, representing macroscopic catchment slope rather than individual street curbs.

---

## 3. Land Cover Temporal Vintage

* **2021 Epoch**: The land cover baseline originates from ESA WorldCover 2021 (10m). Gurugram is experiencing rapid real estate expansion, particularly along the Dwarka Expressway, Southern Peripheral Road (SPR), and New Gurugram sectors (Sectors 75–115).
* **Impervious Underestimation**: Surfaces paved between 2022 and 2026 are categorized under their 2021 land cover class (predominantly cropland or bare soil), slightly understating runoff coefficients in newest sectors.

---

## 4. Drainage Network Representation

* **Trunk vs. Tertiary**: The model integrates official GMDA primary drain legs (Badshahpur drain, Leg I, Leg II, Leg III) and Najafgarh corridor links. Tertiary roadside drains, municipal storm sewer pipes, and choked culverts are unmapped in open GIS layers.
* **Drainage Maintenance**: The index assumes designed gravity drainage functionality; it cannot account for localized blockage caused by siltation, solid waste dumping, or construction debris.

---

## 5. Precipitation Spatial Resolution

* **ERA5-Land Grid Scale**: Open-Meteo precipitation data is derived from ECMWF ERA5-Land reanalysis at ~9 km resolution. Monsoon convective thunderstorms across the National Capital Region (NCR) frequently demonstrate acute micro-scale spatial variability (e.g., intense 80 mm downpours in eastern Gurugram while Manesar receives 10 mm).
* **Mitigation**: Precipitation is treated as a uniform regional climatological baseline (528.7 mm annual monsoon mean) with low AHP weight (2%), leaving spatial differentiation to topography and impervious surface cover.
