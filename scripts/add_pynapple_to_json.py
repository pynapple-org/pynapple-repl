import json
import hashlib
from pathlib import Path

# Paths
json_path = Path("dist/extensions/@jupyterlite/pyodide-kernel-extension/static/pypi/all.json")
wheel_path = Path("dist/extensions/@jupyterlite/pyodide-kernel-extension/static/pypi/pynapple-0.8.5-py3-none-any.whl")
lite_json_path = Path("dist/jupyter-lite.json")

# Load the wheel file and compute digests
with wheel_path.open("rb") as f:
    content = f.read()
    md5 = hashlib.md5(content).hexdigest()
    sha256 = hashlib.sha256(content).hexdigest()

# Load existing JSON
with json_path.open("r", encoding="utf-8") as f:
    data = json.load(f)

# Construct the entry
pynapple_entry = {
    "releases": {
        "0.8.5": [
            {
                "comment_text": "",
                "downloads": -1,
                "filename": "pynapple-0.8.5-py3-none-any.whl",
                "has_sig": False,
                "packagetype": "bdist_wheel",
                "python_version": "py3",
                "requires_python": ">=3.10",
                "url": "./pynapple-0.8.5-py3-none-any.whl",
                "yanked": False,
                "yanked_reason": None,
                "digests": {
                    "md5": md5,
                    "sha256": sha256
                },
                "md5_digest": md5
            }
        ]
    }
}

# Add or update the 'pynapple' entry
data["pynapple"] = pynapple_entry

# Save the updated JSON back to file
with json_path.open("w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print("✅ Updated all.json with pynapple@0.8.5 and hashes.")

# ---- Update jupyter-lite.json ----
with lite_json_path.open("r", encoding="utf-8") as f:
    lite_data = json.load(f)

kernel_cfg = lite_data.setdefault("litePluginSettings", {}).setdefault(
    "@jupyterlite/pyodide-kernel-extension:kernel", {}
)

url_base = "./extensions/@jupyterlite/pyodide-kernel-extension/static/pypi/all.json"
full_url = f"{url_base}?sha256={sha256}"

# Avoid duplicates
if full_url not in kernel_cfg.get("pipliteUrls", []):
    kernel_cfg.setdefault("pipliteUrls", []).append(full_url)

# Add pre-install dependency
if "dependencies" not in kernel_cfg:
    kernel_cfg["dependencies"] = []

if "pynapple" not in kernel_cfg["dependencies"]:
    kernel_cfg["dependencies"].append("pynapple")

# Save updated lite config
with lite_json_path.open("w", encoding="utf-8") as f:
    json.dump(lite_data, f, indent=2)