# KageTheKing

A Python package scaffold for the KageTheKing project.

## Install

```bash
pip install -e .
```

## Run

```bash
python -m KageTheKing
```

## Package API

```python
from KageTheKing import run

print(run())
```

## CI / CD

This repository includes GitHub Actions workflows:

- Continuous Integration: [/.github/workflows/python-app.yml](.github/workflows/python-app.yml#L1) — runs tests on push and pull requests.
- Publish to PyPI: [/.github/workflows/publish-pypi.yml](.github/workflows/publish-pypi.yml#L1) — builds and uploads releases (requires `PYPI_API_TOKEN` secret).
