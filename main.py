from download_pynapple import download_pynapple_and_unzip
from strip_numba import strip_numba_folder_tree,strip_numba_from_pyproject


if __name__ == '__main__':
    fold_download = "/Users/ebalzani/Code/strip_jit/download_nap"
    pynapple_fold = download_pynapple_and_unzip(fold_download) / "pynapple"
    out = "/Users/ebalzani/Code/strip_jit/strip_output"

    # strip numba from the code
    strip_numba_folder_tree(pynapple_fold, out)

    path_pyproject = "/Users/ebalzani/Code/strip_jit/download_nap/pynapple-main/pyproject.toml"
    path_new = "/Users/ebalzani/Code/strip_jit/strip_output"

    # remove dynamic version & numba from deps
    strip_numba_from_pyproject(path_pyproject, path_new)

