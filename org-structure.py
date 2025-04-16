from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from random import choice, randint
import time
import math

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///path_tree.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class PathNode(db.Model):
    __tablename__ = 'path_nodes'
    
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100))
    path = db.Column(db.String(1000), index=True)  # Stores materialized path (e.g., "1.5.12")
    depth = db.Column(db.Integer)  # Cache depth for easier queries
    
    def __repr__(self):
        return f'PathNode(id={self.id}, label={self.label}, path={self.path})'
    
    def to_dict(self, include_children=False):
        result = {
            'id': self.id,
            'label': self.label,
            'path': self.path,
            'depth': self.depth
        }
        if include_children:
            result['children'] = [child.to_dict() for child in self.get_children()]
        return result
    
    def get_children(self):
        return PathNode.query.filter(
            PathNode.path.startswith(self.path + '.'),
            PathNode.depth == self.depth + 1,
            PathNode.path.like(f"{self.path}.%")
        ).all()
    
    def get_descendants(self, limit=None):
        query = PathNode.query.filter(
            PathNode.path.startswith(self.path + '.')
        )
        if limit:
            query = query.limit(limit)
        return query.all()
    
    def get_parent(self):
        if self.depth == 0:
            return None
        parent_path = '.'.join(self.path.split('.')[:-1])
        return PathNode.query.filter_by(path=parent_path).first()

class PathTree:
    def __init__(self):
        self.node_count = 0
        self.batch_size = 1000  
    
    def create_root(self):
        root = PathNode(label='root', path='1', depth=0)
        db.session.add(root)
        db.session.commit()
        self.node_count = 1
        return root
    
    def add_child(self, parent, label=None):
        new_id = self._get_next_id()
        new_path = f"{parent.path}.{new_id}"
        child = PathNode(
            label=label or f"node_{new_id}",
            path=new_path,
            depth=parent.depth + 1
        )
        db.session.add(child)
        return child
    
    def _get_next_id(self):
        self.node_count += 1
        return self.node_count
    
    def generate_random_tree(self, total_nodes):
        start_time = time.time()
        
        db.drop_all()
        db.create_all()
        
        root = self.create_root()
        nodes = [root]
        
        available_nodes = [root]
        
        batch = []
        while self.node_count < total_nodes:
            parent = choice(available_nodes)
            
            new_node = self.add_child(parent)
            batch.append(new_node)
            nodes.append(new_node)
            
            if randint(0, 100) < 70:
                available_nodes.append(new_node)
            
            if len(batch) >= self.batch_size:
                db.session.commit()
                batch = []
                
                if randint(0, 100) < 30:
                    available_nodes = [
                        n for n in available_nodes 
                        if len(n.get_children()) > 0 or randint(0, 100) < 50
                    ]
        
        if batch:
            db.session.commit()
        
        end_time = time.time()
        return {
            'message': f'Generated tree with {self.node_count} nodes',
            'time_taken': end_time - start_time,
            'root_id': root.id
        }
    
    def get_subtree(self, node_id, limit=10000):
        start_time = time.time()
        
        root_node = PathNode.query.get(node_id)
        if not root_node:
            return None
        
        descendants = root_node.get_descendants(limit=limit)
        
        node_map = {root_node.id: root_node.to_dict()}
        node_map[root_node.id]['children'] = []
        
        for node in descendants:
            node_map[node.id] = node.to_dict()
            node_map[node.id]['children'] = []
            
            parent_path = '.'.join(node.path.split('.')[:-1])
            parent_id = int(parent_path.split('.')[-1])
            
            if parent_id in node_map:
                node_map[parent_id]['children'].append(node_map[node.id])
        
        end_time = time.time()
        return {
            'time_taken': end_time - start_time,
            'node_count': len(descendants) + 1,
            'tree': node_map[root_node.id]
        }

@app.route('/create_tree/<int:num_nodes>')
def create_tree(num_nodes):
    tree = PathTree()
    return tree.generate_random_tree(num_nodes)

@app.route('/subtree/<int:node_id>')
def get_subtree(node_id):
    limit = request.args.get('limit', default=10000, type=int)
    tree = PathTree()
    return tree.get_subtree(node_id, limit)

@app.route('/node/<int:node_id>')
def get_node(node_id):
    node = PathNode.query.get_or_404(node_id)
    return node.to_dict(include_children=True)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)