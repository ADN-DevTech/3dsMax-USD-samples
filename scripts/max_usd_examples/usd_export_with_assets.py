from pxr import Tf
import os
from pathlib import Path
import pymxs
import usd_export_utils
import usd_callbacks
try:
    from typing import Iterator
except ImportError:
    # It's ok, just for typehints script editor!
    pass

mxs = pymxs.runtime
instsance_man = mxs.InstanceMgr
# build my list of nodes to convert

ASSETS_DIR = "assets"
NOPROMPT = mxs.Name("noprompt")
NODELIST = mxs.Name("nodeList")
INSTANCE = mxs.Name("instance")

def partition(filter, iterable):
     # type: (function, Iterator) -> tuple[list, list]
    """Partition an iterable with a filter."""
    trues = []
    falses = []
    for item in iterable:
        if filter(item):
            trues.append(item)
        else:
            falses.append(item)
    return trues, falses

class AssetHelper():
    """Helper class for asset exporting"""
    def __init__(self, asset_name, root_node):
        # type: (AssetHelper, str, pymxs.MXSWrapperBase) -> None
        self._asset_name = asset_name
        self.root_node = root_node
        self.instances = []
        self.placeholders = []

    @property
    def asset_name(self):
        return Tf.MakeValidIdentifier(self._asset_name)

    @property
    def relative_path(self):
        return os.path.join(self.asset_name, (self.asset_name + ".usd"))

    @property
    def node_list(self):
        """Return a list of all children recursive, including root."""
        return list(
            usd_export_utils.recurse_scene_tree(self.root_node)
        )

    def __hash__(self):
        return hash((self.root_node, self.asset_name))

    def __repr__(self):
        return "<AssetHelper: {0}:{1}>".format(self.asset_name, self.root_node)

    def create_placeholders(self, usd_cust_attr=None):
        # type: (AssetHelper) -> None        
        for node in self.instances:
            placeholder = mxs.Point()
            placeholder.transform = node.transform
            placeholder.name = node.name
            self.placeholders.append(placeholder)
            # if usd_cust_attr:
            #     mxs.custAttributes.add(placeholder.baseObject, usd_cust_attr)        

    def cleanup(self):
        mxs.delete(self.placeholders)

class ProjectHelper():
    """Helper class to define a project."""
    def __init__(self, project_root, assets_dir=ASSETS_DIR):
        self.project_root = project_root
        self.assets_dir = assets_dir

    def assets_path(self):
        return os.path.join(self.project_root, self.assets_dir)

def iter_root_instances(root_items):
     # type: (list) -> list
    """Iterate over all items at the root level, returns lists of instances."""
    items_copy = root_items.copy()
    while items_copy:
        item = items_copy[0]
        _, instances = instsance_man.GetInstances(item, pymxs.byref(None))
        root_instances = (instance for instance in instances if instance in items_copy)
        for instance in root_instances:
            items_copy.remove(instance)
        yield instances

def export_asset(asset_helper, project_options, update=False):
    # type: (AssetHelper, ProjectHelper, bool) -> bool
    """Export an asset from its root node."""
    export_path = os.path.join(project_options.assets_path(), asset_helper.relative_path)
    if os.path.exists(export_path) and not update:
        return

    export_options = mxs.USDExporter.CreateOptions()
    if hasattr(export_options, "RootPrimPath"):
        export_options.RootPrimPath = "/AssetRoot"
    # update the post-export callback
    export_callback_options = usd_callbacks.UsdPostExportOptions(
        normalize_root_prims=True
    )
    usd_callbacks.update_export_callback(export_options, export_callback_options)

    print("Exporting {0}...".format(export_path))
    ret = mxs.USDExporter.ExportFile(
        export_path,
        exportOptions=export_options,
        contentSource=NODELIST,
        nodeList=asset_helper.node_list
    )

    return bool(ret)

def _export_scene_with_placeholder_assets(export_path, asset_list, project_helper):
    # type: (str, list, ProjectHelper) -> bool
    """Export an asset from its root node."""
    export_options = mxs.USDExporter.CreateOptions()
    export_filename = Path(export_path)
    export_options.FileFormat = usd_export_utils.FILE_FORMAT_MAP[export_filename.suffix]

    # expand hierarchy on all remaining nodes to get full set of nodes to export
    export_node_list = []
    for asset in asset_list:
        if asset.placeholders:
            export_node_list.extend(asset.placeholders)
        else:
            export_node_list.extend(asset.node_list)

    # update the post-export callback
    export_callback_options = usd_callbacks.UsdPostExportOptions(
        handle_reference_placeholders=True,
        asset_list=set(asset_list),
        project_helper=project_helper
    )
    usd_callbacks.update_export_callback(export_options, export_callback_options)

    # export scene
    print("Exporting {0}...".format(export_path))
    ret = mxs.USDExporter.ExportFile(
        export_path,
        exportOptions=export_options,
        contentSource=NODELIST,
        nodeList=export_node_list
    )
    print(ret)
    return bool(ret)


def generate_root_asset_helpers(root_items):
    # type: (list) -> Iterator[AssetHelper]
    """Gather list of assets to export"""
    for instance_set in iter_root_instances(root_items):
        root_node = instance_set[0]
        asset_helper = AssetHelper(root_node.name, root_node)
        asset_helper.instances = instance_set
        yield asset_helper

class AssetFilter():
    def __init__(self, all=False, instances=True, groups=True, helpers=True):
        self.all = all
        self.instances = instances
        self.groups = groups
        self.helpers = helpers

    def filter(self, asset):
        # cull out anything we don't want to export as assets
        if self.is_camera(asset):
            return False
        elif self.is_light(asset):
            return False
        elif self.is_target(asset):
            return False
        elif self.is_scene_helper(asset):
            return False
        
        if self.all and (self.is_geo(asset) or self.has_children(asset)):
            return True
        elif self.instances and self.is_instance(asset):
            return True
        elif self.groups and self.is_group(asset):
            return True
        elif self.helpers and self.is_helper(asset):
            return True

    @staticmethod
    def is_scene_helper(asset):
        # type: (AssetHelper) -> bool
        return mxs.classOf(asset.root_node) == mxs.usdExportSceneHelper        

    @staticmethod
    def has_children(asset):
        # type: (AssetHelper) -> bool
        return len(asset.root_node.children) > 0

    @staticmethod
    def is_geo(asset):
        # type: (AssetHelper) -> bool
        return mxs.superClassOf(asset.root_node) == mxs.GeometryClass

    @staticmethod
    def is_target(asset):
        # type: (AssetHelper) -> bool
        return mxs.classOf(asset.root_node) == mxs.Targetobject

    @staticmethod
    def is_light(asset):
        # type: (AssetHelper) -> bool
        return mxs.superClassOf(asset.root_node) == mxs.light

    @staticmethod
    def is_camera(asset):
        # type: (AssetHelper) -> bool
        return mxs.superClassOf(asset.root_node) == mxs.camera

    @staticmethod
    def is_instance(asset):
        # type: (AssetHelper) -> bool
        return len(asset.instances) > 1

    @staticmethod
    def is_group(asset):
        # type: (AssetHelper) -> bool
        return mxs.isGroupHead(asset.root_node)

    @staticmethod
    def is_helper(asset):
        # type: (AssetHelper) -> bool
        """Asset root is a helper AND has children"""
        _is_helper = mxs.superClassOf(asset.root_node) == mxs.helper
        _has_children = len(asset.root_node.children) > 0
        return _is_helper and _has_children

class AssetPlaceholdersContext(object):
    """Exports a scene with root-level nodes as assets."""
    def __init__(self, asset_helpers):
        # type: (AssetPlaceholdersContext, list[AssetHelper]) -> Iterator[AssetHelper]
        self.usd_cust_attr = self.create_usd_cust_attr()
        self.asset_helpers = asset_helpers

    @staticmethod
    def create_usd_cust_attr():
        usd_ca_cmd = '''attributes "UsdCustAttribPlaceholder"
        (
            parameters USD_TMP
            (
                usd_kind type:#string default:"component" animateable:False
            )
        )'''
        attr = mxs.execute(usd_ca_cmd)
        return attr


    def __enter__(self):
        for asset_helper in self.asset_helpers:
            asset_helper.create_placeholders(usd_cust_attr=self.usd_cust_attr)
        return self

    def __exit__(self, type, value, traceback):
        for asset in self.asset_helpers:
            asset.cleanup()
        if self.usd_cust_attr:
            mxs.custAttributes.deleteDef(self.usd_cust_attr)


def export_from_helper(_node, export_scene=True, overwrite=False):
    raw_export_filename = Path(_node.exportFileName)
    if not usd_export_utils.validate_export_filename(raw_export_filename):
        return
    export_filename = usd_export_utils.resolve_export_filename(raw_export_filename)
    if overwrite == None and not usd_export_utils.validate_export_overwrite(export_filename):
        return

    update_existing_assets = _node.assetUpdateExisting
    split_scene = _node.splitScene
    if split_scene:
        export_split_scene(_node, export_filename, export_scene=export_scene, update_existing_assets=update_existing_assets)
    else:
        print("Exporting: {}".format(export_filename))
        export_options = mxs.USDExporter.CreateOptions()
        mxs.USDExporter.ExportFile(
            export_filename,
            exportOptions=export_options
        )


def export_split_scene(_node, export_filename, export_scene=True, update_existing_assets=False):
    project_helper = ProjectHelper(os.path.dirname(export_filename), _node.assetsFolder)    

    filter_obj = AssetFilter(all=_node.assetFilterAll, groups=_node.assetFilterGroups, helpers=_node.assetFilterHelpers, instances=_node.assetFilterInstances)
    filter_func = filter_obj.filter

    root_items = [item for item in mxs.rootNode.children]
    root_assets = [asset for asset in generate_root_asset_helpers(root_items)]

    # export filetered assets as assets...
    filtered_assets = []
    for asset in filter(filter_func, root_assets):
        filtered_assets.append(asset)
        export_asset(asset, project_helper, update=update_existing_assets)

    if export_scene:
        with AssetPlaceholdersContext(filtered_assets):            
            _export_scene_with_placeholder_assets(export_filename, root_assets, project_helper)

if __name__ == "__main__":
    from importlib import reload
    import usd_material_export

    reload(usd_callbacks)
    reload(usd_export_utils)
    reload(usd_material_export)
    reload(usd_callbacks)

    mxs.clearListener()
    root_items = [item for item in mxs.rootNode.children]
    root_assets = [asset for asset in generate_root_asset_helpers(root_items)]
    project_helper = ProjectHelper(mxs.pathConfig.getCurrentProjectFolder())
    asset_filter = AssetFilter(all=True, groups=True, helpers=True, instances=True)
    # export filetered assets as assets...
    for asset in filter(asset_filter.filter, root_assets):
        export_asset(asset, project_helper, update=True)

    with AssetPlaceholdersContext(root_assets) as context:
        export_path = os.path.join(project_helper.project_root, "test_split_scene.usd")
        _export_scene_with_placeholder_assets(export_path, root_assets, project_helper)
