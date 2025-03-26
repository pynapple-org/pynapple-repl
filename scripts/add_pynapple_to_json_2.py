from pathlib import Path
from jupyterlite_pyodide_kernel.addons import piplite

# Paths
json_path = Path(
    "dist/extensions/@jupyterlite/pyodide-kernel-extension/static/pypi/all.json"
)
wheel_path = Path("dist/extensions/@jupyterlite/pyodide-kernel-extension/static/pypi/")
lite_json_path = Path("dist/jupyter-lite.json")
piplite.write_wheel_index(wheel_path)
