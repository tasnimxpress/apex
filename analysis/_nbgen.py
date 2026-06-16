"""Build-time helper: assemble an .ipynb from (type, source) cell specs.
Not imported by the notebooks themselves -- only by the make_*.py builders."""
import nbformat as nbf

def md(text):
    return nbf.v4.new_markdown_cell(text)

def code(text):
    return nbf.v4.new_code_cell(text)

def build(cells, path, kernel="apex"):
    nb = nbf.v4.new_notebook()
    nb.cells = list(cells)
    nb.metadata["kernelspec"] = {"name": kernel, "display_name": "apex", "language": "python"}
    nb.metadata["language_info"] = {"name": "python"}
    with open(path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    return path
