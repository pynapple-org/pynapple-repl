import os
import sys
sys.path.append("scripts")
from download_pynapple import download_pynapple_and_unzip
from strip_numba import strip_numba_folder_tree,strip_numba_from_pyproject
import subprocess

if __name__ == '__main__':
    fold_download = "download_nap"
    pynapple_fold = download_pynapple_and_unzip(fold_download) / "pynapple"
    out = "pynapple-repl"

    # strip numba from the code
    strip_numba_folder_tree(pynapple_fold, out)

    path_pyproject = "download_nap/pynapple-main/pyproject.toml"
    path_new = out

    # remove dynamic version & numba from deps
    strip_numba_from_pyproject(path_pyproject, path_new)

    # create the wheel file
    result = subprocess.run(["python", "-m", "build"], cwd=out, capture_output=True, text=True)

    # Twine check
    result = subprocess.run(["twine", "check", "dist/*"], cwd=out, capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)

    # Twine upload