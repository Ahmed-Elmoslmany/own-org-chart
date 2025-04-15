from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from random import choice
from collections import deque
from flask import request


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///org_chart.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class DBNode(db.Model):
    __tablename__ = 'nodes'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    label = db.Column(db.String(100))
    parent_id = db.Column(db.Integer, db.ForeignKey('nodes.id'))
    
    children = db.relationship("DBNode", back_populates="parent", foreign_keys=[parent_id])
    
    parent = db.relationship("DBNode", back_populates="children", remote_side=[id])
    
    def __repr__(self):
        return f'Node(id={self.id}, label={self.label}, parent_id={self.parent_id})'

class Org:
    def __init__(self, nodes=None):
        self.nodes = nodes or []
        self.org_hash = {}
        self.org_chart_structure = []
        
    @classmethod
    def save_to_db(self):
        db.session.add_all(self.nodes)
        db.session.commit()
            
    @classmethod
    def load_from_db(cls):
        nodes = DBNode.query.all()
        return cls(nodes)
        
    def hash_node(self):
        for node in self.nodes:
            self.org_hash[node.id] = {
                'id': node.id,
                'label': node.label,
                'parent_id': node.parent_id,
                'expanded': True,
                'children': []
            }
    
    def build_org(self):
        self.hash_node()
        for node in self.nodes:
            if node.parent_id is None:
                self.org_chart_structure.append(self.org_hash[node.id])
            else:
                parent = self.org_hash[node.parent_id]
                parent['children'].append(self.org_hash[node.id])

    def get_subtree(self, root_node_id, limit=10000):
        subtree_root = self.org_hash.get(root_node_id)
        if subtree_root is None:
            self.build_org()
            subtree_root = self.org_hash.get(root_node_id)
            if subtree_root is None:
                return None

        result = {
            'id': subtree_root['id'],
            'label': subtree_root['label'],
            'parent_id': subtree_root['parent_id'],
            'expanded': True,
            'children': []
        }

        node_count = 1
        queue = deque([(result, subtree_root.get('children', []))])

        while queue and node_count < limit:
            parent_result_node, original_children = queue.popleft()

            for child in original_children:
                if node_count >= limit:
                    break

                new_result_node = {
                    'id': child['id'],
                    'label': child['label'],
                    'parent_id': child['parent_id'],
                    'expanded': True,
                    'children': []
                }

                parent_result_node['children'].append(new_result_node)
                node_count += 1

                if child.get('children'):
                    queue.append((new_result_node, child['children']))

        return result

@app.route('/create_org/<int:num_nodes>')
def create_organization(num_nodes):
    start_time = datetime.now()
    
    start_database_init_time = datetime.now()
    db.drop_all()
    db.create_all()
    end_database_init_time = datetime.now()
    
    ceo = DBNode(label='ceo')
    db.session.add(ceo)
    db.session.flush()  
    all_nodes = [ceo]
    
    eng_head = DBNode(label='head_eng', parent_id=ceo.id)
    hr_head = DBNode(label='hr_head', parent_id=ceo.id)
    all_nodes.extend([eng_head, hr_head])
    
    start_node_creation_time = datetime.now()
    for i in range(1, num_nodes):
        parent_node = choice(all_nodes)
        new_node = DBNode(label=f'node_{i}', parent_id=parent_node.id)
        db.session.add(new_node)
        db.session.flush()
        all_nodes.append(new_node)
    db.session.flush()  
    end_node_creation_time = datetime.now()

    xyz_head = DBNode(label='xyz_head', parent_id=ceo.id)
    all_nodes.append(xyz_head)
    
    start_saving_nodes_time = datetime.now()
    
    org = Org(all_nodes)
    org.save_to_db()
    
    end_saving_nodes_time = datetime.now()

    
    start_building_org_time = datetime.now()

    org.build_org()
    
    end_building_org_time = datetime.now()

    end_time = datetime.now()
    time_taken = end_time - start_time
    
    return {
        'message': f'Created organization with {num_nodes} nodes',
        'db_init_time': str(end_database_init_time - start_database_init_time),
        'nodes_init_time': str(end_node_creation_time - start_node_creation_time),
        'saving_nodes_into_DB_time': str(end_saving_nodes_time - start_saving_nodes_time),
        'building_org_time': str(end_building_org_time - start_building_org_time),
        'total_time_taken': str(time_taken),
        # 'org_structure': org.org_chart_structure
    }

@app.route('/org_structure')
def get_org_structure():
    node_id = request.args.get('node_id', type=int)  
    limit = request.args.get('limit', default=10, type=int) 
    
    start_read_time = datetime.now()
    org = Org.load_from_db()
    end_read_time = datetime.now()
    
    if node_id:
        start_subtree_time = datetime.now()
        subtree = org.get_subtree(node_id, limit)
        end_subtree_time = datetime.now()
        return {
            'read_time': str(end_read_time - start_read_time),
            'subtree_time': str(end_subtree_time - start_subtree_time),
            'org_structure': subtree
        }
    else:
        org.build_org()
        return {'org_structure': 'org.org_chart_structure'}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)