"""Validate packaged Tk scripts, including Tcl/Tk 9 DLL-embedded ZIP resources."""
from pathlib import Path
import re
import zipfile


def verify_tk_data(root: Path) -> str:
    base = root.resolve()
    # PyInstaller macOS separates code in Frameworks and data in Resources,
    # linked within the same application bundle. Never allow links outside it.
    permitted = base.parent if (base.name == 'Frameworks' and base.parent.name == 'Contents'
                               and base.parent.parent.suffix == '.app') else base
    script = base / '_tk_data/tk.tcl'
    if script.is_file() and script.resolve().is_relative_to(permitted):
        return 'external-scripts'
    for path in base.rglob('tk.tcl'):
        if ('Tk.framework' in path.parts and path.resolve().is_relative_to(permitted)
                and path.is_file()):
            return 'framework-scripts'
    native_name = re.compile(r'^(?:lib)?(?:tcl\d+tk|tk)[0-9.a-z_-]*\.(?:dll|dylib|so(?:\.\d+)*)$')
    for path in base.rglob('*'):
        if not path.is_file() or not (native_name.fullmatch(path.name.lower()) or path.name == 'Tk'):
            continue
        if not path.resolve().is_relative_to(permitted) or not zipfile.is_zipfile(path):
            continue
        with zipfile.ZipFile(path) as archive:
            if 'tk_library/tk.tcl' in archive.namelist():
                archive.read('tk_library/tk.tcl')  # Verify this script's CRC, not just the filename.
                return 'embedded-library-zip'
    raise FileNotFoundError('Dados Tk da interface: scripts externos, framework ou ZIP da biblioteca ausentes.')
