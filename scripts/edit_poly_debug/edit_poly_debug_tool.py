import pymxs
from PySide2 import QtWidgets
rt = pymxs.runtime

class EditPolyDebugTool(QtWidgets.QDialog):
    def __init__(self, node, parent=None):
        super(EditPolyDebugTool, self).__init__(parent=parent)
        self.node = node
        self.node_name = node.name
        self.ep_modifier = node.modifiers[0]
        self.setupUI()
        
    def setupUI(self):
        layout = QtWidgets.QVBoxLayout(self)
        label = QtWidgets.QLabel(self.node_name + " Edit Poly operations:")
        layout.addWidget(label)
        
        self.epoly_delta_list = QtWidgets.QListWidget()
        num_ops = self.ep_modifier.NumDeltaOps()        
        
        for i in range(1, num_ops+1):
            op_name = self.ep_modifier.DeltaOpName(i)
            
            newItem = QtWidgets.QListWidgetItem()
            newItem.setText(str(i) + ": " + op_name)
            self.epoly_delta_list.addItem(newItem)

        layout.addWidget(self.epoly_delta_list)

        totals_label = QtWidgets.QLabel("Total delta operations: %s" % num_ops)
        layout.addWidget(totals_label)

        last_delta_index = self.ep_modifier.LastDeltaIndex
        
        delta_index_display = last_delta_index-1
        self.last_delta_index = QtWidgets.QLabel("Last delta index: %s" % delta_index_display)
        layout.addWidget(self.last_delta_index)
        self.epoly_delta_list.setCurrentRow(delta_index_display-1)
        self.epoly_delta_list.itemSelectionChanged.connect(self.selection_changed)
        # Set dialog layout
        self.setLayout(layout)

    def selection_changed(self):
        cur_row = self.epoly_delta_list.currentRow()
        cur_index = cur_row + 1
        self.ep_modifier.LastDeltaIndex = cur_index
        self.last_delta_index.setText("Last delta index: %s" % (cur_index))
        rt.redrawViews()
        
    def closeEvent(self, event):
        self.ep_modifier.LastDeltaIndex = self.ep_modifier.NumDeltaOps() + 1
        
def epoly_debug_dialog():
    selection = pymxs.runtime.selection
    if len(selection):
        node = selection[0]
        main_window_qwdgt = QtWidgets.QWidget.find(rt.windows.getMAXHWND())
        dialog = EditPolyDebugTool(node, parent=main_window_qwdgt)
        dialog.exec_()
        dialog.setFocus()

epoly_debug_dialog()