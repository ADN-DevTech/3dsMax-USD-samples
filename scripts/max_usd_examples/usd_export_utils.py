"""USD Export utilities for USD Export modifier and helper."""

import os
from datetime import datetime, timezone
from pathlib import Path
from collections import namedtuple
from contextlib import contextmanager
from PySide2 import QtWidgets
import subprocess
import traceback
import itertools
import pymxs
try:
    import typing
except ImportError:
    # this is just for type hints
    pass

import usd_callbacks
import usd_material_export
from usdMakeFileVariantModelAsset import CreateModelStage
from pxr import UsdGeom


# For active development
if os.getenv("USD_DEV"):
    from imp import reload
    reload(usd_callbacks)


@contextmanager
def cwd(path):
    oldpwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(oldpwd)


# 3ds Max python runtime alias
mxs = pymxs.runtime

NO_PROMPT = mxs.Name("noPrompt")
NODE_LIST = mxs.Name("nodeList")
EXPORT_ALIAS = mxs.Name("export")
UP_AXIS_MAP = {1: "Z-Up", 2: "Y-Up"}
UP_AXIS_USD_MAP = {1: UsdGeom.Tokens.z, 2: UsdGeom.Tokens.y}
MODEL_KINDS = ["component", "group", "assembly"]

FILE_FORMAT_MAP = {
    ".usda": mxs.Name("ascii"),
    ".usd": mxs.Name("binary"),
    ".usdc": mxs.Name("binary"),
    ".usdz": mxs.Name("usdz")
}

ModifierState = namedtuple("ModifierState", "enabled enabledInViews enabledInRenders")


class PerserveStackContext(object):
    """A context manager to preserve modifier state during export operations"""

    def __init__(self, modifier, nodes):
        self._current_mod_object = mxs.modPanel.getCurrentObject()
        mxs.suspendEditing(which=mxs.Name("modify"), alwaysSuspend=True)
        self._stack_states_map = {}
        for node in nodes:
            self.add_obj_stack_state(node)

    def add_obj_stack_state(self, obj):
        stack_states = []
        for modifier in obj.modifiers:
            state = ModifierState(
                modifier.enabled, modifier.enabledInViews, modifier.enabledInRenders
            )
            stack_states.append(state)
        self._stack_states_map[obj] = stack_states

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        # On exit we restore the state of all modifiers on the stack.
        for obj, stack_states in self._stack_states_map.items():
            for i, state in enumerate(stack_states):
                mod = obj.modifiers[i]
                mod.enabled = state.enabled
                mod.enabledInViews = state.enabledInViews
                mod.enabledInRenders = state.enabledInRenders
        mxs.resumeEditing(which=mxs.Name("modify"), alwaysSuspend=True)
        if self._current_mod_object:
            mxs.modPanel.setCurrentObject(self._current_mod_object)


def get_last_modified(filename):
    # type: (Path) -> datetime
    stat_result = filename.stat()
    modified = datetime.fromtimestamp(stat_result.st_mtime, tz=timezone.utc)
    return modified


def find_usd_bins():
    # type: () -> Path
    """Return the path of the Max USD bins"""
    plugin_count = mxs.pluginManager.pluginDllCount
    for i in range(1, plugin_count):
        name = mxs.pluginManager.pluginDllName(i)
        if name.lower() == "usdexport.dle":
            dll_path = Path(mxs.pluginManager.pluginDllFullPath(i))
            return Path(dll_path.parent)
    # Cannot find the path, raise exception.
    raise FileNotFoundError("USD bin path path not found.")


def open_in_usd_view(filename):
    # type: (str) -> None
    """Open the file in USD View"""
    export_filename = Path(filename)
    if filename == "":
        return
    valid = validate_export_filename(export_filename)
    if not valid:
        return
    export_filename = resolve_export_filename(export_filename)
    if not export_filename.exists():
        main_window_qwdgt = QtWidgets.QWidget.find(mxs.windows.getMAXHWND())
        QtWidgets.QMessageBox.warning(
            main_window_qwdgt,
            "Export USD",
            f"File does not exist.\nFilename: {export_filename}"
        )
        return
    bins_dir = find_usd_bins()
    max_root = Path(mxs.getdir(mxs.name("maxroot")))
    max_python = max_root / "Python37" / "python.exe"
    # USD for 3ds Max ships with a RunUsdTool convenience batch script.
    run_usd_tool = bins_dir / "RunUsdTool.bat"
    usd_tool_wrapper = bins_dir / "UsdToolWrapper.py"
    if not run_usd_tool.exists():
        raise FileNotFoundError(run_usd_tool)
    try:
        args = [str(max_python), str(usd_tool_wrapper), "UsdView", str(filename)]
        subprocess.Popen(args, cwd=str(bins_dir)) # capture_output=False, check=False,
    except OSError as e:
        traceback.print_exc()
        print(e)
    except ValueError as e:
        traceback.print_exc()
        print(e)



def validate_export_overwrite(export_filename):
    # type: (Path) -> bool
    """Validate with user that we can overwrite file if it exists.
    Returns True to continue"""
    if export_filename.exists():
        main_window_qwdgt = QtWidgets.QWidget.find(mxs.windows.getMAXHWND())
        return_button = QtWidgets.QMessageBox.question(
            main_window_qwdgt,
            "Export USD",
            f"Overwrite existing file?\nFilename: {export_filename}\nDate Modified: {get_last_modified(export_filename).ctime()}",
            QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel,
            QtWidgets.QMessageBox.Cancel,
        )
        if return_button == QtWidgets.QMessageBox.Cancel:
            return False
    return True


def recurse_scene_tree(node):
    # type: (mxs.runtime.MaxWrapper) -> Path
    """Recursive scene tree iteratetor from a node."""
    for child in node.Children:
        yield from recurse_scene_tree(child)
    yield node


def init_export_options_from_mod(modifier):
    # type: (mxs.runtime.MaxWrapper) -> mxs.UsdExporter.ExportOptions
    """Initialize and return an ExportOptions struct from this modifier paramters."""
    export_options = mxs.UsdExporter.CreateOptions()
    export_options.Meshes = getattr(modifier, "exportMeshes", True)
    export_options.Lights = getattr(modifier, "exportLights", True)
    export_options.Cameras = getattr(modifier, "exportCameras", True)
    export_options.Materials = getattr(modifier, "exportMaterials", True)
    upAxis = getattr(modifier, "upAxis", 1)
    export_options.UpAxis = UP_AXIS_MAP[upAxis]
    if not mxs.superClassOf(modifier) == mxs.helper:
        # for referencing the root level prim needs to be an xform
        export_options.RootPrimPath = "/AssetRoot"
    return export_options

def get_modifier_index(node, mod):
    # type: (mxs.runtime.MaxWrapper, mxs.runtime.MaxWrapper) -> int
    """Get the index of the modifier for this node"""
    index = mxs.findItem(node.modifiers, mod)
    if index:
        return index - 1


def disable_modifiers_above_mod(modifier, nodes):
    # type: (mxs.runtime.MaxWrapper, mxs.runtime.MaxWrapper) -> int
    """Disable all modifiers above given modifier for given nodes."""
    for node in nodes:
        mod_idx = get_modifier_index(node, modifier)
        for idx in range(mod_idx, 0, -1):
            node.modifiers[idx - 1].enabled = False

def invalid_filename_warning(export_filename, reason):
    # type: (Path, str) -> bool
    msg = f"Invalid filename: {export_filename}\n{reason}"
    main_window_qwdgt = QtWidgets.QWidget.find(mxs.windows.getMAXHWND())
    QtWidgets.QMessageBox.warning(
                main_window_qwdgt,
                "Export USD",
                msg
            )

def validate_export_filename(export_filename, show_warning=True):
    # type: (Path, bool) -> typing.Tuple[bool, str]
    valid = True
    reason = "Path is valid."
    if export_filename.suffix and not export_filename.suffix in FILE_FORMAT_MAP:
        reason = "Unsupported file suffix."
        valid = False
    if export_filename.is_dir():
        reason = "Filename is a directory."
        valid = False

    if not valid and show_warning:
        invalid_filename_warning(export_filename, reason)

    return valid, reason

def resolve_export_filename(export_filename):
    # type: (Path) -> Path
    """Resolve and sanitize the input string for filename"""
    # make sure extension is specified
    if not export_filename.suffix:
        export_filename = export_filename.with_suffix(".usd")

    # always lowercase suffix
    export_filename = export_filename.with_suffix(export_filename.suffix.lower())

    resolved_filename = export_filename
    # resolve to an absolute path
    if not export_filename.is_absolute():
        # If not absolute, resolve relative to curent maxfile        
        max_file_path = mxs.maxFilePath
        if max_file_path:
            export_dir = Path(max_file_path)
            resolved_filename = export_dir / export_filename
        else:
            export_dir = Path(mxs.getDir(EXPORT_ALIAS))
            # if no maxfilepath, then resort to project export path
            resolved_filename = export_dir / export_filename
    return resolved_filename

def export_variants_from_helper(helper, nodes, export_filename):
    # type: (mxs.runtime.MaxWrapper, list, bool) -> None
    """Export USD file from this modifier instance"""
    #TODO: validate all names are unique in nodelist.
    # Export the variants to temp files.
    exported_variants = []
    for variant_root in helper.variantNodes:
        export_dir = export_filename.parent
        variant_usd = export_dir / (variant_root.name + ".usd")
        export_asset(variant_root, nodes=[variant_root], export_filename=variant_usd)
        exported_variants.append(str(variant_usd))

    model_kind = "component" # MODEL_KINDS[helper.modelKind-1]
    variant_set_name = helper.variantSetName
    stage = CreateModelStage(export_filename.stem,
                             assetIdentifier=None, # will use assetname
                             kind=model_kind,
                             filesToReference=exported_variants,
                             variantSetName=variant_set_name,
                             defaultVariantSelection=None)

    if stage:
        UsdGeom.SetStageUpAxis(stage, UP_AXIS_USD_MAP[1]) # max is Z-UP
        stage.GetRootLayer().Save()
    else:
        print("Failed to create stage for usd variant.")

def export_from_modify_panel(modifier, nodes, overwrite=None, export_filename=None):
    # type: (mxs.runtime.MaxWrapper, list, bool, Path) -> None
    """Validate and resolve export filename then export USD file from modify panel."""    
    if not export_filename:
        raw_export_filename = Path(modifier.exportFileName)
        if not validate_export_filename(raw_export_filename):
            return
        export_filename = resolve_export_filename(raw_export_filename)
        if overwrite == None and not validate_export_overwrite(export_filename):
            return
    if mxs.classOf(modifier) == mxs.usdVariantModelAssetHelper:
        export_variants_from_helper(modifier, nodes, export_filename)
    else:
        export_asset(modifier, nodes, export_filename)

def export_asset(modifier, nodes, export_filename):
    # type: (mxs.runtime.MaxWrapper, list, Path) -> None
    """Do the export from modify panel for modifier or helpers."""
    # Instantiate export options from the modifier settings
    export_options = init_export_options_from_mod(modifier)
    export_options.FileFormat = FILE_FORMAT_MAP[export_filename.suffix]

    # update the post-export callback
    export_normalized = getattr(modifier, "exportNormalized", True)
    export_callback_options = usd_callbacks.UsdPostExportOptions(
        normalize_root_prims=export_normalized
    )
    usd_callbacks.update_export_callback(export_options, export_callback_options)

    # The modifier can be instanced on multiple nodes, so we get a list of nodes.
    export_node_list = nodes

    # Get all the children of this node if user wants to include them.
    # Export helper always exports all children, modifier is is optional.
    export_children = getattr(modifier, "exportChildren", True)

    bake_textures_before = usd_material_export._material_export_options["bake"]
    bake_textures = getattr(modifier, "bake", False)
    usd_material_export._material_export_options["bake"] = bake_textures

    if export_children:
        export_node_list = list(
            itertools.chain.from_iterable(
                (recurse_scene_tree(node) for node in export_node_list)
            )
        )

    with PerserveStackContext(modifier, nodes):
        if (mxs.hasProperty(modifier, "exportEndResult") and not modifier.exportEndResult):
            disable_modifiers_above_mod(modifier, nodes)
        res = mxs.USDExporter.exportFile(
            export_filename,
            contentSource=NODE_LIST,
            nodeList=export_node_list,
            exportOptions=export_options)
        if res:
            print(f"Exported: {export_filename}")
        else:
            print(f"Not exported: {export_filename} - {res}")

    usd_material_export._material_export_options["bake"] = bake_textures_before

def main():
    pass


if __name__ == "__main__":
    main()