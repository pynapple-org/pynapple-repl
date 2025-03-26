import json
from pathlib import Path

# Path to your JSON file
json_path = Path("dist/extensions/@jupyterlite/pyodide-kernel-extension/static/pypi/all.json")

# Load the existing JSON content
with json_path.open("r", encoding="utf-8") as f:
    data = json.load(f)

# Entry to append
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
            }
        ]
    }
}

# Add or update the 'pynapple' entry
data["pynapple"] = pynapple_entry

# Save the updated JSON back to file
with json_path.open("w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
