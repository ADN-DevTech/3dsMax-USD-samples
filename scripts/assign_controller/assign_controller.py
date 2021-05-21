import pymxs
from PySide2 import QtWidgets, QtCore
import shiboken2

rt = pymxs.runtime
main_window_qwdgt = QtWidgets.QWidget.find(rt.windows.getMAXHWND())
main_window = shiboken2.wrapInstance(shiboken2.getCppPointer(main_window_qwdgt)[0], QtWidgets.QMainWindow)
rt.clearListener()

assign_controller_widgets = []
SCENE_ROOT = rt.rootnode
    
class AssignControllerDialog(QtWidgets.QDialog):
    def __init__(self, track, parent=None):
        pass
    
class AssignControllerWidget(QtWidgets.QWidget):
    TrackRole = QtCore.Qt.UserRole + 1
    ControllerRole = QtCore.Qt.UserRole + 2
    SubanimRole = ControllerRole + 1
    
    def __init__(self, parent=None):
        super(AssignControllerWidget, self).__init__(parent)
        self.node = None
        self.tree_widget = None
        self.assign_button = None
        self.setup_ui()
        #self.setup_max_callbacks()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        self.assign_button = QtWidgets.QToolButton()
        self.assign_button.clicked.connect(self.assign_controller)
        self.assign_button.setText('Assign Controller')
        layout.addWidget(self.assign_button)
        self.tree_widget = QtWidgets.QTreeWidget()
        self.tree_widget.setRootIsDecorated(False)
        self.tree_widget.setHeaderLabels(['Track', 'Controller', 'Value'])
        layout.addWidget(self.tree_widget)
        self.refresh()

    def refresh(self):
        selection = rt.selection
        #if len(selection) == 1:
        #    self.node = selection[0]
        #else:
        self.node = SCENE_ROOT
        #~ print(str(rt.classOf(track)))
        self.tree_widget.clear()        
        root_item = self.recurse_scene_tree(self.node)
        self.tree_widget.insertTopLevelItem(0, root_item)        
        
        self.tree_widget.setColumnCount(3)
        self.tree_widget.expandAll()
        self.tree_widget.resizeColumnToContents(0)

    def iter_controller_super_classes(self):
        for sc in rt.superclasses:
            if str(sc).lower().endswith('controller'):
                yield sc
    
    def get_controllers_of_type(self, ctrl_type):
        print(ctrl_type)
        type_name = str(ctrl_type).lower()
        if type_name == "double":
            type_name = "float"
        elif type_name == "booleanclass":
            type_name = "float"
            
        super_class = None
        for ctrl_super in self.iter_controller_super_classes():
            ctrl_super_name = str(ctrl_super).lower()
            print(ctrl_super_name)
            if ctrl_super_name.startswith(type_name):
                super_class = ctrl_super
                break
        if super_class:
            return list(super_class.classes)

    def assign_controller(self):
        selection = self.tree_widget.selectedItems()
        if len(selection) == 1:
            selected = selection[0]
            subanim = selected.data(0, self.SubanimRole)
            if subanim:
                track_value = rt.getProperty(subanim.parent, subanim.name)
                track_type = rt.classOf(track_value)
                compatible_controllers = sorted(list(self.get_controllers_of_type(track_type)))

                ctrls_map = {}
                for ctrl in compatible_controllers:
                    if ctrl.creatable:
                        inst = rt.createInstance(ctrl)
                        ctrl_name = rt.getClassName(inst)
                        ctrls_map[ctrl_name] = ctrl
                    
                items = sorted(list(ctrls_map.keys()))
                
                item, ok = QtWidgets.QInputDialog().getItem(self, f"Assign {track_type} Controller",
                                                     "Controllers:", items, 0, False)
                if ok:
                    ctrl_to_create = ctrls_map[item]
                    #rt.setPropertyController(subanim.parent, subanim.name, ctrl_to_create())
                    print(f"subanim: {subanim}")
                    print(f"subanim idx: {subanim.index}")
                    print(f"subanim val: {subanim.value}")
                    print(f"subanim obj: {subanim.object}")
                    print(f"subanim parent: {subanim.parent}")
                    print(f"subanim name: {subanim.name}")
                    print(f"controller class: {ctrl_to_create}")
                    new_ctrl = ctrl_to_create()
                    print(f"controller instance: {new_ctrl}")
                    rt.setProperty(subanim.parent, subanim.name, new_ctrl)
                    #subanim.controller = ctrl_to_create()

    def create_item_from_node(self, node, parent_item=None):
        item = QtWidgets.QTreeWidgetItem(parent_item)
        item.setText(0, node.Name)
        return item

    def iter_scene_tree(root):
        yield root
        yield from root.children      

    def recurse_scene_tree(self, node, parent_item=None):
        item = self.create_item_from_node(node, parent_item)
        self.recurse_subanims(node, item)
        #if not node == rt.rootNode:
        #    tm_controller = rt.getTMController(node)
        #    if tm_controller:                
        #        self.recurse_subanim_controllers("Transform", tm_controller, parent=item)

        for child in node.Children:            
            self.recurse_scene_tree(child, item)
        
        # indicates rootness
        if not parent_item:
            return item

    def get_track_value(self, track):
        if track and not (isinstance(track.value, pymxs.MXSWrapperBase)):
            return track.value

    def create_item_from_track(self, track_name, controller, parent_item=None):
        track_value = self.get_track_value(controller)
        item_values = [track_name, rt.getClassName(controller), str(track_value)]
        item = QtWidgets.QTreeWidgetItem(parent_item, item_values)
        item.setData(0, self.ControllerRole, controller)
        item.setData(0, self.TrackRole, track_name)

    def create_item_from_subanim(self, subanim, parent_item=None):
        value = ""
        controller_name = ""

        if subanim.controller:
            value = subanim.controller.value
            controller_name = rt.GetClassName(subanim.controller)
        
        item_values = [subanim.name, controller_name, str(value)]
        item = QtWidgets.QTreeWidgetItem(parent_item, item_values)
        item.setData(0, self.SubanimRole, subanim)
        return item

    def recurse_subanims(self, root, parent_item=None):
        for sub_i in range(1, root.numsubs+1):
            subanim = rt.getSubAnim(root, sub_i)
            child_item = self.create_item_from_subanim(subanim, parent_item)
            self.recurse_subanims(subanim, child_item)

    def iter_subanims(self, root):
        for sub_i in range(1, root.numsubs+1):
            subanim = rt.getSubAnim(root, sub_i)
            yield subanim
            yield from self.iter_subanims(subanim)
        
    def recurse_subanim_controllers(self, track_name, controller, parent=None):
        sub_anim_names = rt.getsubanimnames(controller)
        for name in sub_anim_names:
            subanim = controller[name]
            ctrl = rt.getPropertyController(controller, subanim.name)
            val = None
            if not ctrl:
                return
            if ctrl and (isinstance(ctrl.vale, pymxs.MXSWrapperBase)):
                val = None
            elif ctrl:
                val = str(ctrl.value)
                
            values = [subanim.name, rt.getClassName(ctrl), val]
            item = QtWidgets.QTreeWidgetItem(parent, values)
            item.setData(0, self.ControllerRole, ctrl)
            item.setData(0, self.TrackRole, subanim)
            self.recurse_subanim_controllers(subanim.name, ctrl, item)

    def setup_max_callbacks(self):
        """ Setup 3ds Max node event callback """
        self._callback_item = rt.NodeEventCallback(selectionChanged=self.callback_node_event)

    def teardown_max_callbacks(self):
        """ Remove registered 3ds Max callback """
        self._callback_item = None

    def callback_node_event(self, event, node):
        """ Method called on selection changed event generated in 3ds Max """
        self.refresh()

    def closeEvent(self, event):
        #self.teardown_max_callbacks()
        super(AssignControllerWidget, self).closeEvent(event)

    def hideEvent(self, event):
        super(AssignControllerWidget, self).hideEvent(event)
        #self.close()


if __name__ == '__main__':
    dialog = QtWidgets.QDialog(parent=main_window)
    layout = QtWidgets.QVBoxLayout()
    dialog.setLayout(layout)
    dialog.setWindowTitle('Assign Controller')
    assign_controller_widget = AssignControllerWidget()
    layout.addWidget(assign_controller_widget)
    dialog.adjustSize()
    dialog.show()
    
    controller_super_classes = rt.apropos("controller:super")
    #~ print(controller_super_classes)
    controller_classes = rt.showClass("*:*controller*")
    #~ print(controller_classes)