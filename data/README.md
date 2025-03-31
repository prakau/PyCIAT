# Data Directory Structure

This directory contains data files used by PyCIAT (Python Crop Impact Assessment Tool). The actual data files are not included in the repository but should be organized as follows:

```
data/
├── climate/                    # Climate data files
│   ├── gcm_nex_cmip6/         # NEX-GDDP-CMIP6 downscaled data
│   └── cordex_sa_iitm_rcm/    # CORDEX South Asia RCM outputs
├── experimental/              # Experimental data
│   └── maize_trials.csv      # Crop trial data for calibration
├── gis/                      # GIS data files
│   ├── districts.shp         # Administrative boundaries
│   ├── karnataka.shp        # State boundary
│   └── karnataka_soils.shp  # Soil map units
├── soil_profiles/            # Soil profile data
│   └── profiles.json        # Detailed soil profiles
└── templates/               # Template files for model setup
    ├── dssat/              # DSSAT template files
    ├── apsim/             # APSIM template files
    └── stics/             # STICS template files

```

## Data Sources

1. **Climate Data**
   - NEX-GDDP-CMIP6: https://www.nasa.gov/nex/gddp
   - CORDEX South Asia: https://cordex.org/domains/region-6-south-asia/

2. **Soil Data**
   - Soil profiles should follow FAO/ISRIC standards
   - GIS data should be in standard shapefile format

3. **Experimental Data**
   - Field trial data should include:
     - Location (lat/lon)
     - Management details
     - Observed phenology
     - Measured yields
     - Treatment information

## Data Requirements

### Climate Data
- Variables: tasmax, tasmin, pr, rsds, sfcWind, hurs
- Format: NetCDF
- Resolution: Daily
- Coordinates: Regular lat/lon grid

### Soil Data
- Required properties:
  - Layer depths
  - Texture (sand, silt, clay %)
  - Bulk density
  - Organic carbon
  - pH
  - CEC (optional)

### GIS Data
- Coordinate system: WGS84 (EPSG:4326)
- Format: ESRI Shapefile
- Required attributes documented in respective README files

## Data Processing

Data processing scripts can be found in:
- `scripts/01_prepare_climate_data.py`
- `src/soil_processing.py`

For detailed instructions on data preparation and processing, refer to the documentation.

## Contributing Data

If you wish to contribute data:
1. Follow the structure outlined above
2. Include metadata and source information
3. Ensure data quality and completeness
4. Submit via pull request

## Notes

- Large data files should not be committed to the repository
- Use the provided scripts to download and process public datasets
- Keep sensitive or proprietary data separate from the repository
