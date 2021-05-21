import tempfile
import os
import uuid
from PySide2 import QtWidgets, QtCore, QtGui
from pxr import Usd, UsdUtils, UsdGeom, Sdf, Pcp
import qtmax
import pymxs
from pathlib import Path
from enum import Enum
from collections import namedtuple
from functools import partial

APP_STYLE = QtWidgets.QApplication.style()
# APP_STYLE_SHEET = QtWidgets.QApplication.styleSheet()

mxs = pymxs.runtime
NODE_LIST = mxs.Name("nodeList")

THIS_PATH = Path(__file__)
ICONS_PATH = THIS_PATH.parent / "icons"
GEO_ICON = QtGui.QIcon(":TrackView/TreeView/Node_32.png")
SUBANIM_ICON = QtGui.QIcon(":CommandPanel/Motion/BipedRollout/EnableSubanims_32")

STAGE_ICON = QtGui.QIcon(str(ICONS_PATH / "USD_stage_100.png"))
USD_ICONS_IMAGE_MAP = {
    "Mesh":"out_USD_Mesh_100.png",
    "Xform":"out_USD_UsdGeomXformable_100.png",
    "Camera":"out_USD_Camera_100.png",
    "Capsule":"out_USD_Capsule_100.png",
    "Cone":"out_USD_Cone_100.png",
    "Cylinder":"out_USD_Cylinder_100.png",
    "Def":"out_USD_Def_100.png",
    "Geomsubset":"out_USD_GeomSubset_100.png",
    "Sphere":"out_USD_Sphere_100.png",
    "Light":"out_USD_UsdLuxLight_100.png",
    "Cube":"out_USD_Cube_100.png",
    "Scope":"out_USD_Scope_100.png"
}
USD_XFORM_ICON = QtGui.QIcon(str(ICONS_PATH / "out_USD_UsdGeomXformable_100.png"))
USD_MESH_ICON = QtGui.QIcon(str(ICONS_PATH / "out_USD_Mesh_100.png"))
USD_CAMERA_ICON = QtGui.QIcon(str(ICONS_PATH / "out_USD_Camera_100.png"))
USD_CAPSULE_ICON = QtGui.QIcon(str(ICONS_PATH / "out_USD_Capsule_100.png"))
USD_CONE_ICON = QtGui.QIcon(str(ICONS_PATH / "out_USD_Cone_100.png"))
USD_CUBE_ICON = QtGui.QIcon(str(ICONS_PATH / "out_USD_Cube_100.png"))
USD_CYLINDER_ICON = QtGui.QIcon(str(ICONS_PATH / "out_USD_Cylinder_100.png"))
USD_DEF_ICON = QtGui.QIcon(str(ICONS_PATH / "out_USD_Def_100.png"))
USD_GEOMSUBSET_ICON = QtGui.QIcon(str(ICONS_PATH / "out_USD_GeomSubset_100.png"))
USD_SPHERE_ICON = QtGui.QIcon(str(ICONS_PATH / "out_USD_Sphere_100.png"))
USD_LUXLIGHT_ICON = QtGui.QIcon(str(ICONS_PATH / "out_USD_UsdLuxLight_100.png"))
USD_SCOPE_ICON = QtGui.QIcon(str(ICONS_PATH / "out_USD_Scope_100.png"))

def qt_overlay_icon(base_image_path, overlay_image_path):
    base_image = QtGui.QImage(str(base_image_path))
    overlay_image = QtGui.QImage(str(overlay_image_path))
    image_with_overlay = QtGui.QImage(base_image.size(), QtGui.QImage.Format_ARGB32_Premultiplied)
    painter = QtGui.QPainter(image_with_overlay)
    # print(base_image.size().x() - overlay_image.size().x())
    # print(base_image.size().y() - overlay_image.size().y())
    painter.setCompositionMode(QtGui.QPainter.CompositionMode_Source)
    painter.fillRect(image_with_overlay.rect(), QtCore.Qt.transparent)

    painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
    painter.drawImage(0, 0, base_image)

    painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
    painter.drawImage(10, 10, overlay_image) #TODO: remove magic numbers

    painter.end()

    return QtGui.QIcon(QtGui.QPixmap(image_with_overlay))

# USD_XFORM_ARC_ICON = qt_overlay_icon((ICONS_PATH / "out_USD_UsdGeomXformable_100.png"), (ICONS_PATH / "out_USD_CompArcBadge_100.png"))

USD_ICON_MAP = {
    "Mesh": USD_MESH_ICON,
    "Xform": USD_XFORM_ICON,
    "Camera": USD_CAMERA_ICON,
    "Capsule": USD_CAPSULE_ICON,
    "Cone": USD_CONE_ICON,
    "Cylinder": USD_CYLINDER_ICON,
    "Def": USD_DEF_ICON,
    "Geomsubset": USD_GEOMSUBSET_ICON,
    "Sphere": USD_SPHERE_ICON,
    "Light": USD_LUXLIGHT_ICON,
    "Cube": USD_CUBE_ICON,
    "Scope": USD_SCOPE_ICON
}

USD_ICON_ARC_MAP = {}
for key, icon in USD_ICON_MAP.items():
    USD_ICON_ARC_MAP[key] = qt_overlay_icon((ICONS_PATH / USD_ICONS_IMAGE_MAP[key]), (ICONS_PATH / "out_USD_CompArcBadge_100.png"))
USD_ICON_ARCV_MAP = {}
for key, icon in USD_ICON_MAP.items():
    USD_ICON_ARCV_MAP[key] = qt_overlay_icon((ICONS_PATH / USD_ICONS_IMAGE_MAP[key]), (ICONS_PATH / "out_USD_CompArcBadgeV_100.png"))


ModelContext = namedtuple('ModelContext', ['include_child_nodes', 'include_subanims'], defaults=[True, False])
DEFAULT_MODEL_CONTEXT = ModelContext()

C_HIDDEN = 1
C_NAME = 0
C_TYPE = 2
C_VALUE = 3
C_VARIANT = 4

HIDEABLE_ROLE = QtCore.Qt.UserRole + 1

PRIM_TYPE_MAP = {
    "Sphere": UsdGeom.Sphere,
    "Cylinder": UsdGeom.Cylinder,
    "Capsule": UsdGeom.Capsule,
    "Camera": UsdGeom.Camera,
    "Cone": UsdGeom.Cone,
    "Cube": UsdGeom.Cube,
    "Scope": UsdGeom.Scope,
    "XForm": UsdGeom.Xform
}

"""
class SpinBoxDelegate(QtGui.QItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QtGui.QSpinBox(parent)
        editor.setMinimum(0)
        editor.setMaximum(100)

        return editor

    def setEditorData(self, spinBox, index):
        value = index.model().data(index, QtCore.Qt.EditRole)

        spinBox.setValue(value)

    def setModelData(self, spinBox, model, index):
        spinBox.interpretText()
        value = spinBox.value()

        model.setData(index, value, QtCore.Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
"""

def export_asset(root_node, export_path):
    """Export an asset from its root node."""
    import usd_callbacks

    export_options = mxs.USDExporter.CreateOptions()
    # update the post-export callback
    export_callback_options = usd_callbacks.UsdPostExportOptions(
        normalize_root_prims=True
    )
    usd_callbacks.update_export_callback(export_options, export_callback_options)

    print("Exporting {0}...".format(export_path))
    ret = mxs.USDExporter.ExportFile(
        export_path,
        exportOptions=export_options,
        contentSource=NODE_LIST,
        nodeList=[root_node]
    )

    return bool(ret)


class BaseChildFetcher(object):
    """Base child fetching for nodes"""
    enabled = True
    _fetched_attr_ = "_fetched_children_"

    @classmethod
    def fetched_count(cls, item):
        return getattr(item, cls._fetched_attr_, 0)

    @classmethod
    def set_fetched_count(cls, item, count):
        setattr(item, cls._fetched_attr_, count)

    @staticmethod
    def childCount(item):
        return len(item.node.children)

    @classmethod
    def hasChildren(cls, item):
        return cls.childCount(item) > 0

    @classmethod
    def remainder(cls, item):
        return cls.childCount(item) - cls.fetched_count(item)

    @classmethod
    def canFetchMore(cls, item):
        return cls.remainder(item) != 0

    @classmethod
    def fetchMore(cls, item, num_items, model_context):
        """TODO: This only really works when first building the tree.
        Need a way to fetch new items added later - and does not assume order is determined in the item.node list.
        Probably keep a list of fetched items - and loop though children until we find the new child."""
        to_fetch = min(num_items, cls.remainder(item))
        fetched_count = cls.fetched_count(item)
        for i in range(fetched_count, fetched_count + to_fetch):
            child_node = item.node.children[i]
            child_item = ItemBase.factory(child_node, parent=item, model_context=model_context)
        cls.set_fetched_count(item, fetched_count + to_fetch)

class SubanimFetcher(BaseChildFetcher):
    _fetched_attr_ = "_fetched_subanims_"

    @staticmethod
    def childCount(item):
        return item.node.numsubs

    @classmethod
    def fetchMore(cls, item, num_items, model_context):
        to_fetch = min(num_items, cls.remainder(item))
        fetched_count = cls.fetched_count(item)
        #print(f"Fetching {to_fetch} subanims for {item.name}")
        for i in range(fetched_count + 1, fetched_count + to_fetch + 1):
            subanim = mxs.getSubAnim(item.node, i)
            child_item = SubanimItem(subanim, parent=item, model_context=model_context)
        cls.set_fetched_count(item, fetched_count + to_fetch)

class StageNodeFetcher(BaseChildFetcher):
    _fetched_attr_ = "_fetched_root_prims_"

    @staticmethod
    def childCount(item):
        if item.root_prim:
            return len(item.root_prim.GetChildren())
        else:
            return 0

    @classmethod
    def fetchMore(cls, item, num_items, model_context):
        to_fetch = min(num_items, cls.remainder(item))
        fetched_count = cls.fetched_count(item)

        for i in range(fetched_count, fetched_count + num_items):
            child_prim = item.root_prim.GetChildren()[i]
            child_item = UsdPrimItem(child_prim, parent=item, model_context=model_context)
        cls.set_fetched_count(item, fetched_count + to_fetch)


class PrimFetcher(BaseChildFetcher):
    _fetched_attr_ = "_fetched_prims_"

    @staticmethod
    def childCount(item):
        return len(item.node.GetChildren())

    @classmethod
    def fetchMore(cls, item, num_items, model_context):
        to_fetch = min(num_items, cls.remainder(item))
        fetched_count = cls.fetched_count(item)

        #print(f"Fetch {to_fetch} prims from {item.name}")
        for i in range(fetched_count, fetched_count + num_items):
            child_prim = item.node.GetChildren()[i]
            child_item = UsdPrimItem(child_prim, parent=item, model_context=model_context)
        cls.set_fetched_count(item, fetched_count + to_fetch)


class ItemBase(object):
    icon = None
    _fetchers = [BaseChildFetcher, SubanimFetcher]
    #node_item_factory_map = {
    #    mxs.UsdStageObject : UsdStageObjectItem
    #}

    def __init__(self, node, parent=None, model_context=DEFAULT_MODEL_CONTEXT):
        super().__init__()
        self._parent = parent
        if self._parent:
            self._parent.appendRow(self)
        self._childItems = []
        self._fetched = 0
        self._node = node
        self.model_context = model_context
        self.set_context()
        self.column_data_map = (sorted([]))

    @staticmethod
    def factory(node, parent=None, model_context=DEFAULT_MODEL_CONTEXT):
        kls = ItemBase.node_item_factory_map.get(mxs.classOf(node), SceneNodeItem)
        return kls(node, parent=parent, model_context=model_context)


    def set_context(self):
        disabled_fetchers = []
        if not self.model_context.include_child_nodes:
            disabled_fetchers.append(BaseChildFetcher.__name__)
        if not self.model_context.include_subanims:
            disabled_fetchers.append(SubanimFetcher.__name__)
        self._disabled_fetchers = set(disabled_fetchers)

    @property
    def node(self):
        return self._node

    @property
    def can_hide(self):
        return False

    @property
    def hidden(self):
        return None

    @property
    def foreign(self):
        return False

    @property
    def tool_tip(self):
        return None

    def flags(self, column):
        flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        if column == C_VALUE:
            flags |= QtCore.Qt.ItemIsEditable
            #controller_value = self.controller_value
            #if isinstance(controller_value, bool):
            #    flags |= QtCore.Qt.ItemIsUserCheckable # | QtCore.Qt.ItemIsEditable
            #if isinstance(self.controller_value, number):
            #    flags |= QtCore.Qt.ItemIsEditable
        elif column == C_HIDDEN and self.can_hide:
            flags |= QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsUserCheckable

        return flags

    def setData(self, column, value, role):
        if column == C_VALUE:
            if role == QtCore.Qt.CheckStateRole:
                if self.controller:
                    self.controller_value = value
                    return True
            elif role == QtCore.Qt.EditRole:
                #if self.controller:
                self.controller_value = value
                return True
        if column == C_HIDDEN:
            self.hidden = value
            return True

        return False

    def data(self, column, role):
        if role == QtCore.Qt.DecorationRole and column == 0:
            return self.icon
        elif role == QtCore.Qt.DisplayRole:
            if column == C_NAME:
                return self.name
            elif column == C_TYPE:
                return self.node_type
            elif column == C_VALUE:
                return self.controller_value
            if column == C_HIDDEN:
                return self.hidden
        #elif role == QtCore.Qt.CheckStateRole:
        #    if self.is_checkable(column):
        #        if self.controller_value:
        #            return QtCore.Qt.CheckState.Checked
        #        else:
        #            return QtCore.Qt.CheckState.Unchecked
        #    return None
        elif role == QtCore.Qt.ForegroundRole:
            if self.foreign:
                if self.hidden:
                    return QtGui.QBrush(QtGui.QColor(QtCore.Qt.cyan).darker())
                else:
                    return QtGui.QBrush(QtGui.QColor(QtCore.Qt.cyan))
            if self.hidden:
                return QtGui.QBrush(QtGui.QColor(QtCore.Qt.darkGray))
        elif role == HIDEABLE_ROLE:
            return self.can_hide
        elif role == QtCore.Qt.ToolTipRole:
            return self.tool_tip
        elif role == QtCore.Qt.BackgroundRole:
            if self.has_selected_children:
                pass
                # return QtGui.QBrush(QtGui.QColor(QtCore.Qt.darkGray).darker(140))

    @property
    def has_selected_children(self):
        return True

    @property
    def name(self):
        return self._node.name

    @property
    def node_type(self):
        pass

    @property
    def controller_value(self):
        return None

    @controller_value.setter
    def controller_value(self, value):
        pass

    def is_checkable(self, column):
        return False

    def rowCount(self):
        return len(self._childItems)

    @property
    def node_children_count(self):
        return len(self.node.children)

    @property
    def fetchers(self):
        for fetcher in self._fetchers:
            if fetcher.__name__ not in self._disabled_fetchers:
                yield fetcher

    def hasChildren(self):
        return any([fetcher.hasChildren(self) for fetcher in self.fetchers])

    def remainderToFetch(self):
        return sum([fetcher.remainder(self) for fetcher in self.fetchers])

    def appendRow(self, item):
        if not item in self._childItems:
            self._childItems.append(item)

    def parent(self):
        return self._parent

    def child(self, row):
        return self._childItems[row]

    def indexOf(self, item):
        return self._childItems.index(item)

    def row(self):
        parent = self.parent()
        if self.parent():
            return parent.indexOf(self)
        return -1

    def canFetchMore(self):
        return self.remainderToFetch() > 0

    def fetchMore(self, num_items):
        for fetcher in self.fetchers:
            items_to_fetch = min(num_items, fetcher.remainder(self))
            if items_to_fetch:
                fetcher.fetchMore(self, items_to_fetch, self.model_context)


class SceneNodeItem(ItemBase):
    icon = GEO_ICON
    def __init__(self, scene_node, parent=None, model_context=DEFAULT_MODEL_CONTEXT):
        super(SceneNodeItem, self).__init__(scene_node, parent=parent, model_context=model_context)
        if scene_node:
            self.__anim_handle = mxs.GetHandleByAnim(scene_node)
        self.context_actions = []

    @property
    def node_type(self):
        return mxs.GetClassName(self.node)

    @property
    def node(self):
        return mxs.GetAnimByHandle(self.__anim_handle)

    @property
    def can_hide(self):
        return self.node != mxs.rootNode

    @property
    def hidden(self):
        if self.node == mxs.rootNode:
            return False
        return self.node.isHidden

    @hidden.setter
    def hidden(self, value):
        self.node.isHidden = value
        mxs.completeRedraw()
        return True

    def columnCount(self):
        return 3

    def export_item(self, edit_target_layer):
        # export to tmp usd file
        temp_dir = tempfile.gettempdir()
        tmp_file_name = str(uuid.uuid4())[:8] + "_tmp_usd.usd"
        tmp_file = os.path.join(temp_dir, tmp_file_name)
        export_asset(self.node, tmp_file)
        # get stage
        src_path = "/{0}".format(self.node.name) # DUMB - assumes root.
        dst_path = src_path
        src_stage = Usd.Stage.Open(tmp_file)
        src_layer_handle = src_stage.GetRootLayer()        
        Sdf.CopySpec(src_layer_handle, src_path, edit_target_layer, dst_path)


class UsdStageObjectItem(SceneNodeItem):
    icon = STAGE_ICON
    _fetchers = [BaseChildFetcher, SubanimFetcher, StageNodeFetcher]
    def __init__(self, scene_node, parent=None, model_context=DEFAULT_MODEL_CONTEXT):
        super(UsdStageObjectItem, self).__init__(scene_node, parent=parent, model_context=model_context)
        self._stage_path = self.node.FilePath
        self._cache_id = self.node.CacheId
        self._stage_cache = UsdUtils.StageCache.Get()
        self._stage = self._stage_cache.Find(Usd.StageCache.Id.FromLongInt(self._cache_id))
        #self._root_prim = self._stage.GetPrimAtPath("/")

    def __hash__(self):
        """Unique identifier of cache id + stage_path"""
        return (self._cache_id, str(self._stage_path))
    
    @property
    def root_prim(self):
        if self._stage:
            return self._stage.GetPrimAtPath("/")

    @property
    def controller_value(self):
        return self._stage_path

    def add_prim(self, type_name):
        if type_name == "Def":
            self._stage.DefinePrim(f"/{type_name}")
        else:
            prim = PRIM_TYPE_MAP[type_name].Define(self._stage, f"/{type_name}")


class UsdPrimItem(ItemBase):
    _fetchers = [PrimFetcher]

    def __init__(self, prim, parent=None, model_context=DEFAULT_MODEL_CONTEXT):
        super().__init__(prim, parent=parent, model_context=model_context)

    @property
    def prim(self):
        return self.node

    @property
    def icon(self):
        icon = USD_ICON_MAP.get(self.node_type, USD_DEF_ICON)
        if self.prim.HasVariantSets():
            icon = USD_ICON_ARCV_MAP.get(self.node_type)
        elif any([self.prim.HasAuthoredReferences(), self.prim.HasPayload(), self.prim.HasAuthoredInherits(), self.prim.HasAuthoredSpecializes()]):
            icon = USD_ICON_ARC_MAP.get(self.node_type)
        return icon

    @property
    def foreign(self):
        return True


    @property
    def node_type(self):
        type_name = self.node.GetTypeName()
        if not type_name:
            type_name = "Def"
        return type_name

    @property
    def can_hide(self):
        return True

    @property
    def hidden(self):
        val = UsdGeom.Imageable(self.node).ComputeVisibility()
        if val == UsdGeom.Tokens.invisible:
            return True
        return False

    @hidden.setter
    def hidden(self, value):
        if value:
            UsdGeom.Imageable(self.node).MakeInvisible()
        else:
            UsdGeom.Imageable(self.node).MakeVisible()

        mxs.completeRedraw()
        return True

    @property
    def name(self):
        return str(self.node.GetName())

    @property
    def controller_value(self):
        return str(self.node.GetPrimPath())

    @property
    def tool_tip(self):
        tool_tip = f"<strong>Prim Path:</strong> {self.node.GetPrimPath()}<br><strong>Type:</strong> {self.node_type}"
        if self.prim.HasAuthoredReferences():
            meta_data = self.prim.GetMetadata('references')
            tool_tip = f"{tool_tip}<br><strong>Has Authored References:</strong>"
            for item in meta_data.prependedItems:
                tool_tip = f"{tool_tip}<br>Prepend asset path: {item.assetPath}"
            #'addedItems', 'appendedItems', 'deletedItems', 'explicitItems', 'isExplicit', 'orderedItems', 'prependedItems'
            #UsdUtils.UsdUtilsExtractExternalReferences()
            # references = self.prim.GetReferences()
        return tool_tip

    @staticmethod
    def unique_name(stage, parent_path, name):
        new_path = parent_path.AppendChild(name)
        prim = stage.GetPrimAtPath(new_path)
        increment = 1
        while prim.IsValid():
            name_increment = f"{name}{increment}"
            new_path = parent_path.AppendChild(name_increment)
            increment += 1
            prim = stage.GetPrimAtPath(new_path)
        return new_path


    def add_prim(self, type_name):
        this_path = self.node.GetPrimPath()
        stage = self.node.GetStage()
        prim_path = self.unique_name(stage, this_path, type_name)
        if type_name == "Def":
            stage.DefinePrim(prim_path)
        else:
            prim = PRIM_TYPE_MAP[type_name].Define(stage, prim_path)

    @staticmethod
    def browse_for_ref():
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(caption="Reference File", filter="USD Files (*.usd *.usda *.usdc *.usdz);;ABC Files (*.abc)")
        if file_name:
            target_stage = Usd.Stage.Open(file_name)
            default_prim = target_stage.GetRootLayer().defaultPrim
            return (file_name, default_prim)

    def add_reference(self):
        res = self.browse_for_ref()
        if res:
            file_name, default_prim = res
            self._node.GetReferences().AddReference(assetPath=file_name, primPath=f"/{default_prim}")
            return True

    def add_variant_set(self):
        self._node.GetVariantSets().AddVariantSet("modelingVariant")
        return True
    
    def import_item(self):
        this_path = self.node.GetPrimPath()
        stage = self.node.GetStage()
        old_stage_mask = stage.GetPopulationMask()
        stage_mask = Usd.StagePopulationMask([this_path])
        stage.SetPopulationMask(stage_mask)
        stage_cache = UsdUtils.StageCache.Get()
        stage_id = stage_cache.GetId(stage).ToLongInt()
        import_option = mxs.USDImporter.CreateOptions()
        import_option.StageMask = [str(this_path)]
        mxs.USDImporter.ImportFromCache(stage_id, importOptions=import_option)
        stage.SetPopulationMask(old_stage_mask)        
        #self.node.hidden = True
        
    def add_payload(self):
        res = self.browse_for_ref()
        if res:
            file_name, default_prim = res
            self._node.GetPayloads().AddPayload(assetPath=file_name, primPath=f"/{default_prim}")
            return True


class SubanimItem(ItemBase):
    icon = SUBANIM_ICON
    _fetchers = [SubanimFetcher]

    def __init__(self, subanim, parent=None, model_context=DEFAULT_MODEL_CONTEXT):
        super().__init__(subanim, parent=parent, model_context=model_context)

    def data(self, column, role):
        if column == C_VALUE and role == QtCore.Qt.BackgroundRole and self.is_animated():
            return QtGui.QBrush(QtGui.QColor(QtCore.Qt.red))
        elif column == C_NAME and role in (QtCore.Qt.ForegroundRole, QtCore.Qt.TextAlignmentRole):
            if self.hasChildren():
                if QtCore.Qt.ForegroundRole:
                    return QtGui.QBrush(QtGui.QColor(QtCore.Qt.lightGray))
            else:
                if QtCore.Qt.TextAlignmentRole:
                    return QtCore.Qt.AlignRight


        return super().data(column, role)

    def is_animated(self):
        if mxs.isProperty(self.node, "isAnimated"):
            return self.node.isAnimated

    @property
    def hidden(self):
        return False

    @property
    def controller(self):
        return self.node.controller

    @property
    def controller_value(self):
        if self.controller:
            return self.controller.value
        else:
            value = self.node.value
            if value:
                return value
            elif mxs.isProperty(self.node.parent, self.name):
                return mxs.getProperty(self.node.parent, self.name)

    @controller_value.setter
    def controller_value(self, value):
        #print(f"Set controller value: {value}")
        mxs.setProperty(self.node.parent, self.name, float(value))
        return True
        #else:
        #    if self.node.value:
        #        self.node.value = value
        #    elif mxs.isProperty(self.node.parent, self.name):
        #        return mxs.setProperty(self.node.parent, self.name, value)
        #    else:
        #        print("Couldn't set value... :(")


    @property
    def node_type(self):
        if self.controller:
            return mxs.GetClassName(self.controller)
        elif mxs.isProperty(self.node.parent, self.name):
            track_value = mxs.getProperty(self.node.parent, self.name)
            _type = str(mxs.classOf(track_value))
            return _type


    def is_checkable(self, column):
        if column == C_VALUE and isinstance(self.controller_value, bool):
            return True
        return False


class SceneTreeModel(QtCore.QAbstractItemModel):

    def __init__(self, root_node=None, model_context=DEFAULT_MODEL_CONTEXT, parent=None):
        super(SceneTreeModel, self).__init__(parent=parent)
        self.root_item = ItemBase(None)
        self.scene_root = ItemBase.factory(root_node, parent=self.root_item, model_context=model_context)
        self.header_names = ["Name", "Vis", "Type", "Value"]
        self.model_context = model_context

    def iter_model(self, parent=QtCore.QModelIndex()):
        for i in range(0, self.rowCount(parent)):
            index = self.index(i, 0, parent)
            yield index
            if self.hasChildren(index):
                yield from self.iter_model(index)

    def add_item(self, parent, func):
        if not parent.isValid():
            return False
        func()
        self.fetchMore(parent)

    def import_item(self, parent, func):
        if not parent.isValid():
            return False
        func()

    def export_item(self, parent, func, edit_target_layer):
        if not parent.isValid():
            return False
        func(edit_target_layer)

    def columnCount(self, parent):
        return len(self.header_names)

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        item = index.internalPointer()
        column = index.column()
        changed = item.setData(column, value, role)
        if changed:
            self.dataChanged.emit(index, index)
            return True
        return False

    def data(self, index, role):
        if not index.isValid():
            return None
        item = index.internalPointer()
        column = index.column()
        return item.data(column, role)


    def flags(self, index):
        item = index.internalPointer()
        column = index.column()
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled
        return item.flags(column)

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            if section <= len(self.header_names):
                return self.header_names[section]

        return None

    def node_by_index(self, index):
        if not index.isValid():
            return None
        item = index.internalPointer()
        if item:
            return item.node

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            _parent = self.root_item
        else:
            _parent = parent.internalPointer()

        child_item = _parent.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        child_item = index.internalPointer()
        _parent = child_item.parent()
        if _parent:
            return self.createIndex(_parent.row(), 0, _parent)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0
        if not parent.isValid():
            _parent = self.root_item
        else:
            _parent = parent.internalPointer()
        return _parent.rowCount()

    def hasChildren(self, parent):
        if not parent.isValid():
            return True
        item = parent.internalPointer()
        return item.hasChildren()

    def canFetchMore(self, parent):
        if not parent.isValid():
            return False
        item = parent.internalPointer()
        return item.canFetchMore()

    def fetch_subanim_items(self, item):
        node = item.node
        for sub_i in range(1, node.numsubs + 1):
            subanim = mxs.getSubAnim(node, sub_i)
            child_item = SubanimItem(subanim, parent=item)
        item._fetched_node_subanims = node.numsubs

    def fetchMore(self, parent):
        if not parent.isValid():
            return
        item = parent.internalPointer()
        itemsToFetch = min(100, item.remainderToFetch())
        if itemsToFetch == 0:
            return
        first = item.rowCount()
        last = item.rowCount() + itemsToFetch - 1
        # print(f"About to insert {itemsToFetch} from rows {first} to {last}.")
        self.beginInsertRows(parent, first, last)
        item.fetchMore(itemsToFetch)
        self.endInsertRows()


class CheckBoxDelegate(QtWidgets.QStyledItemDelegate):
    """
    A delegate that places a fully functioning QCheckBox cell of the column to which it's applied.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        """
        Important, otherwise an editor is created if the user clicks in this cell.
        """
        return None

    def paint(self, painter, option, index):
        """
        Paint a checkbox without the label.
        """
        model = index.model()

        can_hide = index.model().data(index, HIDEABLE_ROLE)

        # draw the background
        APP_STYLE.drawPrimitive(QtWidgets.QStyle.PE_PanelItemViewItem, option, painter)
        if not can_hide:
            return

        checked = not index.model().data(index, QtCore.Qt.DisplayRole)

        check_box_style_option = QtWidgets.QStyleOptionButton()

        if option.state & QtWidgets.QStyle.State_MouseOver:
            check_box_style_option.state |= QtWidgets.QStyle.State_MouseOver

        if (index.flags() & QtCore.Qt.ItemIsEditable) > 0:
            check_box_style_option.state |= QtWidgets.QStyle.State_Enabled
        else:
            check_box_style_option.state |= QtWidgets.QStyle.State_ReadOnly

        if checked:
            check_box_style_option.state |= QtWidgets.QStyle.State_On
        else:
            check_box_style_option.state |= QtWidgets.QStyle.State_Off

        check_box_style_option.rect = self.getCheckBoxRect(option)

        if not index.flags() & QtCore.Qt.ItemIsEditable:
            check_box_style_option.state |= QtWidgets.QStyle.State_ReadOnly

        APP_STYLE.drawControl(QtWidgets.QStyle.CE_CheckBox, check_box_style_option, painter)

    #def sizeHint(self, option, index):
    #    data = index.data()
    #    if isinstance(data, bool):
    #        return self.getCheckBoxRect(option).size()
    #    else:
    #        return super().sizeHint(option, index)


    def getCheckBoxRect(self, option):
        check_box_style_option = QtWidgets.QStyleOptionButton()
        check_box_rect = APP_STYLE.subElementRect(QtWidgets.QStyle.SE_CheckBoxIndicator, check_box_style_option, None)
        check_box_point = QtCore.QPoint(option.rect.x() +
                             option.rect.width() / 2 -
                             check_box_rect.width() / 2,
                             option.rect.y() +
                             option.rect.height() / 2 -
                             check_box_rect.height() / 2)
        return QtCore.QRect(check_box_point, check_box_rect.size())

    def editorEvent(self, event, model, option, index):
        '''
        Change the data in the model and the state of the checkbox
        if the user presses the left mousebutton and this cell is editable. Otherwise do nothing.
        '''
        if not int(index.flags() & QtCore.Qt.ItemIsEditable) > 0:
            return False
            #return super().editorEvent(event, model, option, index)

        if event.type() == QtCore.QEvent.MouseButtonRelease and event.button() == QtCore.Qt.LeftButton:
            # Change the checkbox-state
            self.setModelData(None, model, index)
            return True

        return super().editorEvent(event, model, option, index)


    def setModelData (self, editor, model, index):
        '''
        The user wanted to change the old state in the opposite.
        '''
        data = index.data()
        if isinstance(data, bool):
            model.setData(index, 1 if int(data) == 0 else 0, QtCore.Qt.EditRole)
        else:
            super().setModelData(editor, model, index)


class MaxSceneTreeView(QtWidgets.QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)

    def max_node_context_menu(self, event, item, model_index):
        menu = QtWidgets.QMenu(self)
        source_model = self.model().sourceModel()
        stage_cache = UsdUtils.StageCache.Get()

        send_to_menu = menu.addMenu('Send To...')
        for stage in stage_cache.GetAllStages():
            edit_target = stage.GetEditTarget()
            edit_target_layer = edit_target.GetLayer()            
            export_prim_action = QtWidgets.QAction(edit_target_layer.GetDisplayName(), self)
            export_prim_callback = partial(source_model.export_item, model_index, item.export_item, edit_target_layer)
            export_prim_action.triggered.connect(export_prim_callback)
            send_to_menu.addAction(export_prim_action)
        menu.popup(event.globalPos())

    def usd_prim_context_menu(self, event, item, model_index):
        source_model = self.model().sourceModel()
        menu = QtWidgets.QMenu(self)
        add_prim_menu = menu.addMenu('Add New Prim')
        action_items = {
            'Scope': item.add_prim,
            # 'Def': item.add_prim,
            'XForm': item.add_prim,
            '-':None,
            'Capsule':item.add_prim,
            'Cone':item.add_prim,
            'Cube':item.add_prim,
            'Cylinder':item.add_prim,
            'Sphere':item.add_prim
        }
        for title, callback in action_items.items():
            if title == '-':
                add_prim_menu.addSeparator()
                continue
            action = QtWidgets.QAction(title, self)
            item_func = partial(callback, title)
            model_callback = partial(source_model.add_item, model_index, item_func)
            action.triggered.connect(model_callback)
            add_prim_menu.addAction(action)

        reference_menu = menu.addMenu('References')
        add_reference_action = QtWidgets.QAction("Add Reference", self)
        add_reference_callback = partial(source_model.add_item, model_index, item.add_reference)
        add_reference_action.triggered.connect(add_reference_callback)
        reference_menu.addAction(add_reference_action)

        payloads_menu = menu.addMenu('Payloads')
        add_payload_action = QtWidgets.QAction("Add Payload", self)
        add_payload_callback = partial(source_model.add_item, model_index, item.add_payload)
        add_payload_action.triggered.connect(add_payload_callback)
        payloads_menu.addAction(add_payload_action)

        variants_menu = menu.addMenu('Variants')
        add_variantset_action = QtWidgets.QAction("Add Variant Set", self)
        add_variantset_callback = partial(source_model.add_item, model_index, item.add_variant_set)
        add_variantset_action.triggered.connect(add_variantset_callback)
        variants_menu.addAction(add_variantset_action)
        
        _ = menu.addSeparator()
        
        import_prim_action = QtWidgets.QAction("Import", self)
        import_prim_callback = partial(source_model.import_item, model_index, item.import_item)
        import_prim_action.triggered.connect(import_prim_callback)
        menu.addAction(import_prim_action)
        
        menu.popup(event.globalPos())

    def contextMenuEvent(self, event):
        index = self.indexAt(event.pos())
        model = self.model()
        model_index = model.mapToSource(index)
        #~ print(model_index)
        if model_index.isValid():
            item = model_index.internalPointer()
            #~ print(item)
            if isinstance(item, (UsdPrimItem)):
                self.usd_prim_context_menu(event, item, model_index)
            elif isinstance(item, (SceneNodeItem)):
                self.max_node_context_menu(event, item, model_index)


class MaxSceneTreeWidget(QtWidgets.QWidget):
    """
    """
    def __init__(self, root=None, parent=None):
        super(MaxSceneTreeWidget, self).__init__(parent=parent)
        self.root_node = root
        layout = QtWidgets.QVBoxLayout()
        self.treeViewFilter = QtWidgets.QLineEdit(parent=parent)
        self.treeView = MaxSceneTreeView(parent=parent)
        self.model_context = ModelContext()
        self.include_subanims_check = QtWidgets.QCheckBox("Include Subanims")
        self.include_subanims_check.setChecked(self.model_context.include_subanims)
        layout.addWidget(self.include_subanims_check)
        layout.addWidget(self.treeViewFilter)
        layout.addWidget(self.treeView)
        self.setLayout(layout)
        self.build_view_model()
        self.treeView.hideColumn(C_TYPE)

        self.treeView.setIndentation(15)
        self.setWindowTitle('Scene Tree')
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.include_subanims_check.clicked.connect(self.include_subanims_change)
        self.expand_to_depth = 0
        self.treeView.expandToDepth(self.expand_to_depth)
        self.treeView.resizeColumnToContents(0)
        #self.treeView.setSortingEnabled(True)
        header = self.treeView.header()
        #self.treeView.header().setSectionResizeMode(C_NAME, QtWidgets.QHeaderView.Stretch)
        self.treeView.header().setSectionResizeMode(C_HIDDEN, QtWidgets.QHeaderView.ResizeToContents)
        self.treeView.header().setSectionResizeMode(C_TYPE, QtWidgets.QHeaderView.ResizeToContents)
        #self.treeView.header().setSectionResizeMode(C_VALUE, QtWidgets.QHeaderView.Interactive)
        #self.treeView.header().setStretchLastSection(False)
        self.register_callbacks()
        self.sel_model = self.treeView.selectionModel()
        self.sel_model.selectionChanged.connect(self.selection_handler)

    def selection_handler(selected, deselected):
        #~ print("selection handler", selected, deselected)        
        pass

    def get_selected(self):
        selected_indexes = self.treeView.selectionModel().selectedIndexes()
        model = self.treeView.model()
        for index in selected_indexes:
            if (index.row() != -1 and index.column() == 0):
                model_index = model.mapToSource(index)
                node = self._model.node_by_index(model_index)
                return node

    def closeEvent(self, event):
        print("closeEvent")
        self.remove_callbacks()
        event.accept()
        
    def remove_callbacks(self):
        print("Remove callbacks")
        mxs.callbacks.removeScripts(id=mxs.name('SceneTreeNodeCreated'))
        mxs.callbacks.removeScripts(id=mxs.name('SceneTreeNodeDeleted'))
        mxs.callbacks.removeScripts(id=mxs.name('SceneTreeNodeCloned'))
        mxs.callbacks.removeScripts(id=mxs.name('SceneTreeNodeSelection'))
        mxs.callbacks.removeScripts(id=mxs.name('SceneTreeOpenScene'))
        mxs.callbacks.removeScripts(id=mxs.name('SceneTreeNewScene'))
        mxs.callbacks.removeScripts(id=mxs.name('SceneTreeResetScene'))


    def register_callbacks(self):
        self.remove_callbacks()
        mxs.callbacks.addScript(mxs.Name('nodeCreated'), self.node_created, id=mxs.Name('SceneTreeNodeCreated'))
        mxs.callbacks.addScript(mxs.Name('nodePostDelete'), self.node_deleted, id=mxs.Name('SceneTreeNodeDeleted'))
        mxs.callbacks.addScript(mxs.Name('postNodesCloned'), self.node_deleted, id=mxs.Name('SceneTreeNodeCloned'))
        mxs.callbacks.addScript(mxs.Name('selectionSetChanged'), self.max_post_select, id=mxs.Name('SceneTreeNodeSelection'))
        mxs.callbacks.addScript(mxs.Name('filePostOpen'), self.max_new_scene, id=mxs.Name('SceneTreeOpenScene'))
        mxs.callbacks.addScript(mxs.Name('systemPostNew'), self.max_new_scene, id=mxs.Name('SceneTreeNewScene'))
        mxs.callbacks.addScript(mxs.Name('systemPostReset'), self.max_new_scene, id=mxs.Name('SceneTreeResetScene'))
        #mxs.callbacks.removeScripts(id=mxs.name('SceneTreeSelectionSetChange'))
        #mxs.callbacks.addScript(mxs.Name('selectionSetChanged'), self.max_selection_set_change, id=mxs.Name('SceneTreeSelectionSetChange'))

    def max_post_select(self):
        print("max_post_Select")
        # indexes_to_select = QtCore.QItemSelection()        
        # for sel in (s for s in mxs.selection):
        #     path = [sel]
        #     parent = sel.parent
        #     while parent:
        #         path.append(parent)
        #         parent = parent.parent
        #     root = QtCore.QModelIndex()
        #     current_index = self._model.index(0, 0, root)

        #     for node in reversed(path):
        #         for i in range(0, self._model.rowCount(current_index)):
        #             child_index = self._model.index(i, 0, current_index)
        #             child_node = self._model.node_by_index(child_index)
        #             if child_node == node:
        #                 current_index = child_index
        #                 proxy_index = self._proxy_model.mapFromSource(current_index)
        #                 if not proxy_index.isValid():
        #                     continue
        #                 if child_node == sel:
        #                     indexes_to_select.append(QtCore.QItemSelectionRange(proxy_index))
        #                     break                        
        #                 self.treeView.expand(proxy_index)
        #                 continue
        # if indexes_to_select:
        #     self.sel_model.select(indexes_to_select, QtCore.QItemSelectionModel.ClearAndSelect|QtCore.QItemSelectionModel.Rows)
        #     self.treeView.scrollTo(indexes_to_select.last().topLeft())

    def max_new_scene(self):
        notification = mxs.callbacks.notificationParam()
        print(f"New Scene: {notification}")
        self.rebuild_model()


    def node_created(self):
        notification = mxs.callbacks.notificationParam()
        print(f"Node Created: {notification}")
        self.rebuild_model()

    def node_deleted(self):
        notification = mxs.callbacks.notificationParam()
        print(f"Node Created: {notification}")
        self.rebuild_model()

    def sync_selection(self):
        selection_model = self.treeView.selectionModel()
        model = self.treeView.model()
        max_selection = mxs.selection

    def include_subanims_change(self, value):
        self._model.beginResetModel()
        self.model_context = ModelContext(include_subanims=value, include_child_nodes=self.model_context.include_child_nodes)
        self.build_view_model()
        self._model.endResetModel()
        self.treeView.expandToDepth(self.expand_to_depth)

    def rebuild_model(self):
        """The nuclear option."""
        self._model.beginResetModel()
        self.build_view_model()
        self._model.endResetModel()
        self.treeView.expandToDepth(self.expand_to_depth)

    def setup_max_callbacks(self):
        """ Setup 3ds Max node event callback """
        self._callback_item = pymxs.runtime.NodeEventCallback(all=self.callback_node_event)

    def teardown_max_callbacks(self):
        """ Remove registered 3ds Max callback """
        self._callback_item = None

    def build_view_model(self):
        """ Build view model of the scene graph """
        self._proxy_model = QtCore.QSortFilterProxyModel()
        if not self.root_node:
            self.root_node = pymxs.runtime.rootNode
        self._model = SceneTreeModel(self.root_node, model_context=self.model_context)
        self._proxy_model.setSourceModel(self._model)
        self._proxy_model.setDynamicSortFilter(True)
        self._proxy_model.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self._proxy_model.setFilterKeyColumn(C_NAME)
        self.treeView.setModel(self._proxy_model)
        # self.treeView.setSortingEnabled(True)

        self.treeView.setItemDelegateForColumn(C_HIDDEN, CheckBoxDelegate(parent=self))

        self.treeViewFilter.textChanged.connect(self._proxy_model.setFilterRegExp)
        print([index for index in self._model.iter_model()])

class MaxPicker(QtWidgets.QDialog):
    def __init__(self, root_node=None, parent=None):
        super(MaxPicker, self).__init__(parent=parent)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        self.scene_tree_widget = MaxSceneTreeWidget(root_node)
        layout.addWidget(self.scene_tree_widget)
        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        layout.addWidget(self.buttonBox)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def selected_prim(self):
        return self.scene_tree_widget.get_selected()

    @staticmethod
    def pick_prim_path_from_proxy(root=None):
        if not root:
            root = mxs.selection[0]
        dialog = MaxPicker(root)
        ret = dialog.exec_()
        selected = dialog.selected_prim()
        if ret:
            return str(selected.GetPrimPath())


class PyMaxDockWidget(QtWidgets.QDockWidget):
    def __init__(self, parent=None):
        super(PyMaxDockWidget, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.Tool)
        self.setWindowTitle('SceneTree')
        self.initUI()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

    def closeEvent(self, event):
        self.scene_tree.remove_callbacks()
        print("DockItemClosed")

    def initUI(self):
        main_layout = QtWidgets.QVBoxLayout()
        self.scene_tree = MaxSceneTreeWidget(parent=self)
        main_layout.addWidget(self.scene_tree)

        widget = QtWidgets.QWidget()
        widget.setLayout(main_layout)
        self.setWidget(widget)
        self.resize(250, 100)

def scene_tree_selected():
    main_window = pymxs.runtime.windows.getMAXHWND()
    parent_widget = QtWidgets.QWidget.find(main_window)
    if len(mxs.selection) == 0:
        return
    tool = MaxSceneTreeWidget(root=mxs.selection[0], parent=parent_widget)
    tool.show()

def main():
    main_window = qtmax.GetQMaxMainWindow()
    w = PyMaxDockWidget(parent=main_window)
    w.setFloating(True)
    w.adjustSize()
    size = w.size()
    size.setWidth(420)
    w.resize(size.width(), size.height())
    w.show()


if __name__ == "__main__":
    ItemBase.node_item_factory_map = {
        mxs.UsdStageObject : UsdStageObjectItem
    }
    main()
