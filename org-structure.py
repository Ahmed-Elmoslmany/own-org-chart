import uuid
from datetime import datetime
from random import choice


class Org:
    def __init__(self, nodes):
        self.nodes = nodes
        self.org_hash = {}
        self.org_chart_structure = []
        
    
    def hash_node(self):
        for node in self.nodes:
            self.org_hash[node.id] = {'id': node.id, 'label': node.label, 'parent_id': node.parent_id, 'children': []}
    
    def build_org(self):
        self.hash_node()
        for node in self.nodes:
            if node.parent_id == None:
                self.org_chart_structure.append(self.org_hash[node.id])
            else:
                parent = self.org_hash[node.parent_id]
                parent['children'].append(self.org_hash[node.id])    
        

class Node:
    def __init__(self, label = '', parent_id = None):
        self.id = str(uuid.uuid4())
        self.label = label
        self.parent_id = parent_id    
    
    def __repr__(self):
        return f'node_id: {self.id} label: {self.label}, parent_id: {self.parent_id} children: {self.children}'          
        
        
if __name__ == '__main__':
    
    number_of_nodes = input('Enter the number of nodes: ')
    start_time = datetime.now()
    ceo = Node('ceo')
    all_nodes = [ceo]

    
    eng_head = Node('head_eng', ceo.id)
    hr_head = Node('hr_head', ceo.id)
    
    
    for i in range(1, int(number_of_nodes)):
        parent_node = choice(all_nodes)
        new_node = Node(f'node_{i}', parent_node.id)
        all_nodes.append(new_node)
    
    xyz_head = Node('xyz_head', ceo.id)

    # print(ceo.__repr__)
    
    org = Org(all_nodes)

    org.build_org()
    print(org.org_chart_structure) 
    
    end_time = datetime.now()

    time_taken = end_time - start_time
    
    print(f'code take: {time_taken} time, And the number of nodes is: {number_of_nodes}')