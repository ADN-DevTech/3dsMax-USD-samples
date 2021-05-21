import pymxs
from pxr import Usd, UsdUtils, UsdGeom
from collections import namedtuple
from functools import partial
import os

mxs = pymxs.runtime

EXPORT_CALLBACK_ID = mxs.name("export_helper_complete_callback")
ON_EXPORT_COMPLETE = mxs.Name("OnExportComplete")
IMPORT_CALLBACK_ID = mxs.name("import_helper_complete_callback")
ON_IMPORT_COMPLETE = mxs.Name("onImportComplete")

# Options ##########################################

UsdPostExportOptions = namedtuple(
    "UsdPostExportOptions",
    ["normalize_root_prims", "handle_reference_placeholders", "asset_list", "project_helper"],
    defaults=[False, False, set(), None],
)

UsdPostImportOptions = namedtuple("ModelContext", ["handle_purposes"], defaults=[True])

default_post_export_options = UsdPostExportOptions()
default_post_import_options = UsdPostImportOptions()

# Utils ############################################


def get_usd_purpose(node):
    # type: (mxs.runtime.MaxWrapper) -> str
    """Get USD purpose from a node"""
    purpose = "default"
    num_cust_attrs = mxs.custAttributes.count(node)
    if num_cust_attrs != 0:
        for i in range(1, num_cust_attrs + 1):  # maxscript 1-index
            attr = mxs.custAttributes.get(node, i)
            if mxs.hasProperty(attr, "usd_purpose"):
                return mxs.getProperty(attr, "usd_purpose")
    return purpose


def max_dict_to_dict(max_dict):
    # type: (mxs.runtime.MaxWrapper) -> dict
    """Util to convert Max dict to python dict."""
    return {key: max_dict[key] for key in max_dict.keys}


# Optional functions ##################################


def handle_guide_node(node):
    # type: (mxs.runtime.MaxWrapper) -> None
    """Set xray and renderable values for a guide node."""
    node.xray = True
    node.renderable = False


def handle_imported_purposes(prims_to_nodes):
    # type: (dict) -> None
    """Given a dictionary mapping imported prims to nodes, handle supported purposes.
    Currently only handling 'guide' purpose."""
    for _, node in prims_to_nodes.items():
        purpose = get_usd_purpose(node)
        if purpose == "guide":
            handle_guide_node(node)

def exported_root_prims(stage, prims_to_nodes, root_prim_path):
    # type: (Usd.Stage, dict, str) -> list[Usd.Prim]
    """Get a list of exported root prims"""
    root = stage.GetPrimAtPath(root_prim_path)
    prim_paths = list(prims_to_nodes.keys())
    return [prim for prim in root.GetChildren() if prim.GetPrimPath() in prim_paths]


def normalize_stage_root_prims(stage, prims_to_nodes, export_options):
    # type: (Usd.Stage, dict, mxs.runtime.MaxWrapper) -> None
    """Normalize (zero-out) exported stage root prims post export."""
    if hasattr(export_options, "RootPrimPath"):
        root_prim_path = export_options.RootPrimPath
    else:
        root_prim_path = "/"
    for prim in exported_root_prims(stage, prims_to_nodes, root_prim_path):
        xform = UsdGeom.Xform(prim)
        xform.ClearXformOpOrder()

def handle_reference_placeholders(stage, prims_to_nodes, post_export_options):
    # type: (Usd.Stage, dict, UsdPostExportOptions) -> None
    asset_list = post_export_options.asset_list
    project_helper = post_export_options.project_helper
    flatten_placeholders = {}
    for asset in asset_list:
        for node in asset.placeholders:
            flatten_placeholders[node] = asset

    for prim_path, node in prims_to_nodes.items():
        if node in flatten_placeholders:
            asset_helper = flatten_placeholders[node]
            asset_path = os.path.join(project_helper.assets_path(), asset_helper.relative_path)
            if not os.path.exists(asset_path):
                print("Asset does not exist: {0}".format(asset_path))
                continue
            target_stage = Usd.Stage.Open(asset_path)
            default_prim = target_stage.GetRootLayer().defaultPrim
            placeholder_prim = stage.GetPrimAtPath(prim_path)
            ref_prim_path = f"/{default_prim}"
            # print(asset_path, ref_prim_path)
            placeholder_prim.GetReferences().AddReference(assetPath=asset_path)
            # print(prim_path, asset_path)


# Callbacks #####################################


def export_complete_callback(
    stageId, conversionInfo, usd_filename, export_options, post_export_options=default_post_export_options
):
    # type: (int, mxs.Struct, UsdPostExportOptions, str, mxs.Struct) -> None
    """Export complete callback."""
    cache = UsdUtils.StageCache.Get()
    stage = cache.Find(Usd.StageCache.Id.FromLongInt(int(stageId)))
    prims_to_nodes = max_dict_to_dict(conversionInfo.primsToNodes)

    if post_export_options.normalize_root_prims:
        normalize_stage_root_prims(stage, prims_to_nodes, export_options)
    if post_export_options.handle_reference_placeholders:
        handle_reference_placeholders(stage, prims_to_nodes, post_export_options)

# Update callbacks #####################################


def update_export_callback(exportOptions, post_export_options=default_post_export_options):
    # type: (mxs.Struct, UsdPostExportOptions) -> None
    """Update export options with a fresh callback. Removes the previous callback to avoid duplication."""
    # Remove previous callback if it exists.
    exportOptions.UnregisterCallbacks(id=EXPORT_CALLBACK_ID)

    # Add fresh callback - using a partial to specify post-export options.
    export_complete_partial = partial(
        export_complete_callback, post_export_options=post_export_options
    )
    exportOptions.RegisterCallback(
        export_complete_partial,
        EXPORT_CALLBACK_ID,
        ON_EXPORT_COMPLETE,
    )


# main ###################


def main():
    pass


if __name__ == "__main__":
    main()