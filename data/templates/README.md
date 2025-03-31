# Model Templates

This directory contains template files for setting up crop model simulations.

## Structure

```
templates/
├── dssat/              # DSSAT template files
│   ├── maize.mzx      # Maize experiment template
│   ├── soil.sol       # Soil profile template
│   └── weather.wth    # Weather data template
├── apsim/             # APSIM template files
│   ├── maize.apsimx   # Maize simulation template
│   └── met.met        # APSIM weather template
└── stics/             # STICS template files
    ├── maize.tec      # Technical parameters
    ├── usm.xml        # Simulation unit template
    └── climat.txt     # Climate data template
```

## Usage

These templates are used by PyCIAT to generate model-specific input files. The framework automatically:
1. Fills in site-specific parameters
2. Converts weather data to model formats
3. Translates soil profiles to model representations
4. Sets up management scenarios

## Template Variables

Templates use a standardized set of placeholders that PyCIAT replaces with actual values:

### Common Variables
- `{{LATITUDE}}`
- `{{LONGITUDE}}`
- `{{ELEVATION}}`
- `{{SOWING_DATE}}`
- `{{HARVEST_DATE}}`
- `{{CULTIVAR_ID}}`

### Soil Parameters
- `{{SOIL_ID}}`
- `{{LAYER_DEPTHS}}`
- `{{CLAY_PCT}}`
- `{{SAND_PCT}}`
- `{{BULK_DENSITY}}`
- `{{ORGANIC_CARBON}}`

### Management
- `{{FERTILIZER_N}}`
- `{{IRRIGATION_SCHEDULE}}`
- `{{ROW_SPACING}}`
- `{{PLANT_DENSITY}}`

## Contributing Templates

To add new templates:
1. Follow the model's standard file format
2. Use the standard placeholder variables
3. Document any model-specific requirements
4. Test with sample data
5. Submit via pull request

## Model-Specific Notes

### DSSAT
- Use DSSAT v4.8 file formats
- Include cultivar coefficients
- Follow IBSNAT standards

### APSIM
- Compatible with APSIM Classic and Next Gen
- Use XML/JSON format as appropriate
- Include manager scripts if needed

### STICS
- Follow STICS v9+ conventions
- Include parameter ranges
- Document dependencies

## Quality Control

All templates should:
- Be validated against model specifications
- Include sample values for testing
- Document units and ranges
- Have clear error messages for invalid values
