# Framework Documentation

This directory contains the framework's documentation built using Sphinx.

## Structure

```
docs/
├── _build/          # Generated documentation
├── _static/         # Static files (images, css, etc.)
├── _templates/      # Custom templates
├── figures/         # Documentation figures
├── api/             # API reference documentation
├── guides/          # User guides and tutorials
└── examples/        # Example use cases
```

## Building Documentation

1. Install documentation requirements:
```bash
pip install -r requirements-docs.txt
```

2. Build HTML documentation:
```bash
make html
```

3. Build PDF documentation (requires LaTeX):
```bash
make latexpdf
```

## Writing Documentation

### Adding New Pages

1. Create a new .rst file in the appropriate directory
2. Add the file to the toctree in `index.rst`
3. Run `make html` to verify

### Adding API Documentation

1. Add new modules to `api/` directory
2. Use autodoc directives to include docstrings
3. Update `api/index.rst` toctree

### Style Guide

- Use reStructuredText format
- Follow NumPy docstring style
- Include examples in docstrings
- Link to related documentation
- Add cross-references when appropriate

### Image Guidelines

1. Save images in `figures/` directory
2. Use SVG for diagrams when possible
3. Include alt text for accessibility
4. Optimize PNG/JPG files

## Checking Documentation

1. Check for broken links:
```bash
make linkcheck
```

2. Check for consistency:
```bash
make doctest
```

3. Run spell check:
```bash
make spelling
```

## Publishing

The documentation is automatically built and published to GitHub Pages when:
1. Changes are pushed to main branch
2. Pull requests are merged
3. Release tags are created

## Local Preview

Start a local server to preview:
```bash
python -m http.server -d _build/html
```

Then visit http://localhost:8000

## Contributing

1. Follow the style guide
2. Test build locally
3. Submit pull request
4. Update relevant sections

## Notes

- Keep examples up to date
- Maintain version compatibility
- Test code snippets
- Update changelog
