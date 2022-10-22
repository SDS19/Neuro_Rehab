import canopen

"""class OD:
    def __init__(self, node_id, obj_dict_path):
        self.node_id = node_id
        self.obj_dict_path = obj_dict_path
        
        network = canopen.Network()
        node = network.add_node(node_id, obj_dict_path)
        
    def obj_dict(self):
        return node.object"""

network = canopen.Network()

node = network.add_node(1, 'OD/mclm.eds')

OD = node.object_dictionary


def list_entries():
    for obj in OD.values():
        print('0x%X: %s' % (obj.index, obj.name))
        if isinstance(obj, canopen.objectdictionary.Record):
            for subobj in obj.values():
                print('  %d: %s' % (subobj.subindex, subobj.name))


# list_entries()


device_name_obj = OD['Manufacturer Device Name']
# print(OD['Application Commands'])
vendor_id_obj = OD[0x1018][0]
print(vendor_id_obj)

''' test
device_type = node.sdo[0x1000]
print("The device type is 0x%X" % device_type.raw)
'''

