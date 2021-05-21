try:
    from PySide2 import QtWidgets, QtCore,  QtGui
except ImportError:
    import PySide
    QtWidgets = PySide.QtGui
import pymxs
import time

RT = pymxs.runtime
SCENE_ROOT = RT.rootScene
TRACK_VIEW_NODES = RT.getsubanimnames(RT.trackViewNodes)
CLEANERS = {}

class Meta(type):
    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        Meta.register_class(cls)
        return cls

    def register_class(target_class):
        if not target_class.__name__ == 'CleanupBase':
            CLEANERS[target_class.__name__] = target_class

class CleanupBase(object):
    __metaclass__ = Meta
    def __init__(self):
        self.label = ''
        self.category = ''

    def is_per_trackview_node(self):
        """Should this be instantiated per track node?"""
        return False

    def count(self):
        return 0

    def cleanup(self):
        pass

#~ class CleanupNoteTracks(CleanupBase):
    #~ def __init__(self):
        #~ self.label = 'NoteTracks'
        #~ self.category = 'MotionClip Manager'

    #~ @staticmethod
    #~ def recurse_subanim_controllers(controller, callback):
        #~ subanimnames = rt.getsubanimnames(controller)
        #~ for name in subanimnames:
            #~ subanim = controller[name]
            #~ ctrl = rt.getPropertyController(controller, subanim.name)
            #~ callback(ctrl)
            #~ self.recurse_subanim_controllers(ctrl)

    #~ def countNoteTracksRecursive(self, tvnode, path, found):
        #~ # function to recursively count the number of note tracks under a tvnode
        #~ # found will contain datapairs of path of tvnode and number of note tracks on tvnode when number is not zero
        #~ count = 0
        #~ if (tvnode != None):
            #~ count = RT.numNoteTracks(tvnode)
            #~ if count:
                #~ #format "path: %; # note tracks: %\n" path count
                #~ found.append(path, count)

            #~ path = path + "." + tvnode.name
            #~ for i in range(tvnode.numsubs):
                #~ count += (self.countNoteTracksRecursive(tvnode[i], path, found))
                
        #~ return count

    #~ def count(self):
        #~ """
        #~ function to count the number of note tracks under 'trackViewNodes'
        #~ found will contain datapairs of path of tvnode and number of note tracks on tvnode when number is not zero
        #~ """
        #~ count = 0
        #~ found = []
        #~ for trackIndex in RT.getsubanimnames(RT.trackViewNodes):
            #~ print('TrackIndex: %s\n' % trackIndex)
            #~ tvnode = RT.trackViewNodes[trackIndex]
            #~ count += (self.countNoteTracksRecursive(tvnode, tvnode.name, found))
        #~ return count
    
    #~ def cleanup(self):
        #~ for attr_index in range(self.count(), 0, -1):
            #~ rt.custAttributes.delete(SCENE_ROOT, attr_index)

class CleanupOrphanedClips(CleanupBase):
    """TODO: make sure clipassociations are orphaned for count..."""
    def __init__(self):
        self.label = 'Orphaned Clips'
        self.category = 'Motionclip Manager'
        self.clipAssociations = None
        
        motion_clip_master_instance = None
        motion_clip_master_subAnim = RT.trackViewNodes["Max_MotionClip_Manager"]
        if motion_clip_master_subAnim:
            motion_clip_master_instance = motion_clip_master_subAnim.object
            self.clipAssociations = motion_clip_master_instance.clipassociations

    def count(self):
        if self.clipAssociations:
            return self.clipAssociations.count
        else:
            return 0
    
    def cleanup(self):
        if not self.clipAssociations:
            return
        # we will move the used clip associations to the beginning of the clipassociations param array and then
        # set the param array's count to the number of used clip associations
        good_clip_index = 0 
        for i in range(1, self.count()):
            ca = self.clipAssociations[i]
            if ca.bipNode is not None or any(ca.nodes):
                good_clip_index += 1
                if i != good_clip_index:
                    self.clipAssociations[good_clip_index] = ca

        if (self.clipAssociations.count != good_clip_index):
            self.clipAssociations.count = good_clip_index


class CleanupOrphanedLayers(CleanupBase):
    def __init__(self):
        self.label = 'Orphaned Layers'
        self.category = 'Anim Layers Control Manager'
        self.orphaned_layers = self._get_orphaned_layers()
        
    @staticmethod
    def _get_orphaned_layers():
        orphaned_layers = set()
        num_anim_layers = RT.AnimLayerManager.getLayerCount()
        for index in range(1, num_anim_layers):
            RT.AnimLayerManager.setLayerActive(index)
            nodes = []
            RT.AnimLayerManager.getActiveLayersNodes(nodes)
            if len(nodes) == 0:
                orphaned_layers.add(index+1)
            else:
                print(nodes)
        return orphaned_layers

    def count(self):
        return len(self.orphaned_layers)
        
    def cleanup(self):
        for index in sorted(self.orphaned_layers, reverse=True):
            layer_name = RT.AnimLayerManager.getLayerName(index)
            print('Delete layer #%i: %s' % (index, layer_name))
            RT.AnimLayerManager.deleteLayer(index)
        self.orphaned_layers = self._get_orphaned_layers()

class CleanupCustomAttrs(CleanupBase):
    def __init__(self, node, name=None):
        self._node = node
        self._name = name or self._node.name
        self.label = '%s' % self._name
        self.category = 'Custom Attributes'

    def count(self):
        return RT.custattributes.count(self._node)
    
    def cleanup(self):
        for attr_index in range(self.count(), 0, -1):
            RT.custAttributes.delete(self._node, attr_index)

class CleanupItemWidget(QtWidgets.QWidget):
    def __init__(self, cleanupobj, parent=None):
        super(CleanupItemWidget, self).__init__(parent=parent)
        self.cleanupobj = cleanupobj

        layout = QtWidgets.QHBoxLayout(self)
        
        self._checkbox = QtWidgets.QCheckBox(cleanupobj.label)
        
        self._checkbox.setChecked(True)
        self._count_label = QtWidgets.QLabel(str(cleanupobj.count()))
        self._clean_btn = QtWidgets.QToolButton()
        self._clean_btn.setText('Clean')
        layout.addWidget(self._checkbox, stretch=1)
        layout.addWidget(self._count_label)
        layout.addWidget(self._clean_btn)
        self._clean_btn.clicked.connect(self.cleanup_click)
        self.setLayout(layout)
        layout.setMargin(0)

    def cleanup_click(self):
        RT.setWaitCursor()
        #RT.progressStart('Cleaning %s...' % self.cleanupobj.label)
        self.do_cleanup()
        #RT.progressEnd()
        RT.setArrowCursor()

    def checked(self):
        return self._checkbox.checkState()
        
    def do_cleanup(self, progress=None):
        print(self.cleanupobj.label)
        self.cleanupobj.cleanup()
        self._count_label.setText(str(self.cleanupobj.count()))


class SceneCleanupTool(QtWidgets.QDialog):
    """TODO: Progressbar"""   
    def __init__(self, parent=None):
        super(SceneCleanupTool, self).__init__(parent=parent)
        self.cleaners = []
        self.cleaners.append(CleanupCustomAttrs(SCENE_ROOT, 'Scene Root'))
        
        for track_view_node in TRACK_VIEW_NODES:
            self.cleaners.append(CleanupCustomAttrs(RT.trackViewNodes[track_view_node], track_view_node))

        self.cleaners.append(CleanupOrphanedClips())
        self.cleaners.append(CleanupOrphanedLayers())
        
        self.cleaner_widgets = []
        self._group_boxes = {}
        
        self.setupUI()
        #self.adjustSize()
        self.setWindowTitle('Scene Cleanup Tool')
        self.setWindowFlags(QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)


    def setupUI(self):
        layout = QtWidgets.QVBoxLayout(self)

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        # scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        layout.addWidget(scroll_area)
        scroll_area_widget = QtWidgets.QWidget()
        sroll_area_layout = QtWidgets.QVBoxLayout()
        scroll_area_widget.setLayout(sroll_area_layout)
        scroll_area.setWidget(scroll_area_widget)
        
        self.cleaners.sort(key = lambda x: x.category)
        last_category = None
        groupBox = None
        form_layout = None

        for cleaner in self.cleaners:
            category = cleaner.category
            
            if not category == last_category:
                groupBox = QtWidgets.QGroupBox(category)
                groupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum))
                sroll_area_layout.addWidget(groupBox)
                form_layout = QtWidgets.QFormLayout()
                groupBox.setLayout(form_layout)
        
            widget = CleanupItemWidget(cleaner)
            form_layout.addRow(widget)
            self.cleaner_widgets.append(widget)
            last_category = category

        spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        sroll_area_layout.addItem(spacer)
        
        default_buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.YesToAll|QtWidgets.QDialogButtonBox.Cancel)
        default_buttons.button(QtWidgets.QDialogButtonBox.StandardButton.YesToAll).clicked.connect(self.yes_to_all)
        default_buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel).clicked.connect(self.close)
        
        layout.addWidget(default_buttons)
        # Set dialog layout
        self.setLayout(layout)
        
    def yes_to_all(self):
        RT.setWaitCursor()
        #RT.progressStart('Cleaning Scene...')
        for cleaner_widget in self.cleaner_widgets:
            if cleaner_widget.checked():
                cleaner_widget.do_cleanup()
        #RT.progressEnd()
        RT.setArrowCursor()

def main():
    try:
        import pymxs
        main_window = pymxs.runtime.windows.getMAXHWND()
        try:
            parent = QtWidgets.QWidget.find(main_window)
        except TypeError:
            import MaxPlus
            parent = MaxPlus.GetQMaxWindow()

        tool = SceneCleanupTool(parent=parent)
        tool.show()

    except ImportError:
        import sys

        app = QtWidgets.QApplication(sys.argv)
        parent = None
        tool = SceneCleanupTool(parent=parent)
        tool.show()


if __name__ == "__main__":
    main()
