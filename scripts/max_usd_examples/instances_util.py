from collections import defaultdict

import pymxs
mxs = pymxs.runtime
IM = mxs.InstanceMgr
OPS = mxs.maxops

INSTANCE = mxs.name("instance")

def del_hierarchy(node):
    for child in node.children:
        del_hierarchy(child)
    mxs.delete(node)

def replace_with_clone(nodes, original):
    """Replace nodes with specified node by instance"""
    if not nodes:
        return
    print("Original: ", original)
    print("Replacing : %s copy nodes" % len(nodes))
    for node in nodes:
        tx = node.transform
        _, cloned_nodes = OPS.clonenodes(original, expandHierarchy=True, cloneType=INSTANCE, newNodes=pymxs.byref(None))
        cloned_nodes[0].transform = tx
        cloned_nodes[0].name = node.name
        del_hierarchy(node)

def gen_id_for(node):
    # Create a uniuqe id for this node based on node properties.
    # A node should be instanceable with other nodes of same id.
    node_id = tuple()

    class_id = mxs.classOf(node)
    bounding_box = mxs.nodeGetBoundingBox(node, node.transform)
    bounding_box_1_str = ("{:0.3f}, {:0.3f}, {:0.3f}".format(bounding_box[0][0], bounding_box[0][1], bounding_box[0][2]))
    bounding_box_2_str = ("{:0.3f}, {:0.3f}, {:0.3f}".format(bounding_box[1][0], bounding_box[1][1], bounding_box[1][2]))
    bounding_box_str = ("BoundingBox({0}, {1})".format(bounding_box_1_str, bounding_box_2_str))
    node_id = node_id + (class_id, bounding_box_str)

    if mxs.isKindOf(node, mxs.GeometryClass):
        node_id = node_id + (
            node.mesh.numverts,
            node.mesh.numfaces,
            node.mesh.numtverts,
            node.mesh.numcpvverts
        )

    children_ids = []
    for child in node.children:
        children_ids.append(gen_id_for(child))

    if children_ids:
        node_id = node_id + tuple(children_ids)

    return node_id


def find_and_replace_instanceable_nodes(nodes):
    #TODO: ignore nodes that are instanced already!
    d = defaultdict(list)
    for node in nodes:
        node_id = gen_id_for(node)
        d[node_id].append(node)    
    for key, values in d.items():
        print(key)
        replace_with_clone(values[1:], values[0])    

def replace_root_copies_with_instances():
    root_items = [item for item in mxs.rootNode.children]
    find_and_replace_instanceable_nodes(root_items)

if __name__ == "__main__":
    find_and_replace_instanceable_nodes(mxs.selection)
