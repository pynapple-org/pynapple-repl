import pathlib
import tomlkit
import re
import libcst as cst
from libcst.metadata import MetadataWrapper


NUMBA_DECORATORS = {"jit", "njit", "vectorize", "guvectorize", "generated_jit", "cfunc", "stencil"}
NUMBA_MODULE = "numba"


class NumbaStripperCST(cst.CSTTransformer):
    def leave_Import(self, original_node, updated_node):
        names = [
            n for n in updated_node.names
            if n.name.value != NUMBA_MODULE
        ]
        return updated_node.with_changes(names=names) if names else cst.RemoveFromParent()

    def leave_ImportFrom(self, original_node, updated_node):
        if original_node.module and original_node.module.value == NUMBA_MODULE:
            return cst.RemoveFromParent()
        return updated_node

    def leave_FunctionDef(self, original_node, updated_node):
        new_decorators = []
        for dec in updated_node.decorators:
            # Simple case: @jit
            if isinstance(dec.decorator, cst.Name) and dec.decorator.value in NUMBA_DECORATORS:
                continue
            # Qualified: @numba.jit
            if isinstance(dec.decorator, cst.Attribute):
                if (isinstance(dec.decorator.value, cst.Name) and
                    dec.decorator.value.value == NUMBA_MODULE and
                    dec.decorator.attr.value in NUMBA_DECORATORS):
                    continue
            # Call: @jit(...)
            if isinstance(dec.decorator, cst.Call):
                base = dec.decorator.func
                if isinstance(base, cst.Name) and base.value in NUMBA_DECORATORS:
                    continue
                if isinstance(base, cst.Attribute) and isinstance(base.value, cst.Name):
                    if base.value.value == NUMBA_MODULE and base.attr.value in NUMBA_DECORATORS:
                        continue
            new_decorators.append(dec)

        return updated_node.with_changes(decorators=new_decorators)


def strip_numba(source: str) -> str:
    module = cst.parse_module(source)
    wrapper = MetadataWrapper(module)
    modified = wrapper.visit(NumbaStripperCST())
    return modified.code


def strip_numba_folder_tree(
        base_path: str | pathlib.Path,
        out_base_path: str | pathlib.Path,
        extension=".py"
):
    """Iterate over dirs and strip numba."""
    out_base_path = pathlib.Path(out_base_path)
    out_base_path.mkdir(parents=True, exist_ok=True)
    base_path = pathlib.Path(base_path)
    for path in base_path.rglob(f"*{extension}"):
        with open(path.as_posix(), "r") as f:
            source = f.read()

        stripped = strip_numba(source)
        new_path = out_base_path / path.relative_to(base_path)
        new_path.parent.mkdir(parents=True, exist_ok=True)
        with open(new_path.as_posix(), "w") as f:
            f.write(stripped)
    print("Strip Completed!")



def strip_numba_from_pyproject(pyproject_path, out_path):
    pyproject_path = pathlib.Path(pyproject_path)
    content = pyproject_path.read_text()
    doc = tomlkit.parse(content)

    pattern = re.compile("^numba\s*[><=!~]{1,3}\s*\d+(\.\d+)*$")
    # Try both standard and Poetry-style dependencies
    for section in ("project", ):
        if section in doc:
            deps_section = doc[section].get("dependencies")
            keep_dep = [dep for dep in deps_section if not re.match(pattern, dep)]
            doc[section]["dependencies"] = keep_dep

    # remove dynamic version
    if "dynamic" in doc["project"]:
        doc["project"].pop("dynamic")
        doc["project"]["version"] = "0.8.4"

    tools = doc.get("tool", {})
    if "setuptools_scm" in  tools:
        tools.pop("setuptools_scm")

    # Changing repo name
    doc['project']['name'] = "pynapple-repl"

    # Write the modified file back
    new_path = pathlib.Path(out_path) / pyproject_path.name
    new_path.write_text(tomlkit.dumps(doc))



if __name__ == "__main__":
    path = "/Users/ebalzani/Code/strip_jit/test_pynapple/"
    out_path = "/Users/ebalzani/Code/strip_jit/strip_output"
    strip_numba_folder_tree(path, out_path)
