import pooch
import zipfile
import pathlib


def download_pynapple_and_unzip(path: str) -> pathlib.Path:
    """Download from pynapple main."""
    path = pathlib.Path(path)
    retriever = pooch.create(
            path=path,
            base_url="https://github.com/pynapple-org/pynapple/archive/refs/heads/",
            registry={"main.zip": None},
            retry_if_failed=2,
            allow_updates="POOCH_ALLOW_UPDATES",
        )
    retriever.fetch("main.zip")

    with zipfile.ZipFile(path / "main.zip", "r") as zip_ref:
        zip_ref.extractall(path.as_posix())

    top_level_dirs = {pathlib.Path(name).parts[0] for name in zip_ref.namelist()}
    assert len(top_level_dirs) == 1
    return path / top_level_dirs.pop()




