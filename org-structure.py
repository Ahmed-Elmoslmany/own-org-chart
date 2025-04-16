from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from random import choice, randint
import time
from sqlalchemy import exc
import math

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///path_tree.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class PathNode(db.Model):
    __tablename__ = 'path_nodes'
    
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100))
    path = db.Column(db.String(1000), index=True)  
    depth = db.Column(db.Integer) 
    
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
        self.node_counter = 1  
        self.batch_size = 5000  
        self.max_depth = 10  
        self.max_children = 20 
    
    def _bulk_insert(self, nodes):
        """Optimized bulk insert using SQLAlchemy core for maximum performance"""
        try:
            db.session.bulk_save_objects(nodes)
            db.session.commit()
        except exc.SQLAlchemyError as e:
            db.session.rollback()
            raise e
    
    def create_root(self):
        root = PathNode(id=1, label='root', path='1', depth=0)
        db.session.add(root)
        db.session.commit()
        return root
    
    def generate_optimized_tree(self, total_nodes):
        start_time = time.time()
        
        db.drop_all()
        db.create_all()
        
        root = self.create_root()
        nodes = {1: root}
        available_nodes = [root]
        batch = []
        
        labels = [f"node_{i}" for i in range(2, total_nodes + 1)]
        
        depth_distribution = {0: 1}
        
        while self.node_counter < total_nodes and available_nodes:
            parent = choice(available_nodes)
            
            if (parent.depth >= self.max_depth or 
                len(parent.path.split('.')) >= self.max_children):
                available_nodes.remove(parent)
                continue
            
            self.node_counter += 1
            new_id = self.node_counter
            new_path = f"{parent.path}.{new_id}"
            new_depth = parent.depth + 1
            
            new_node = PathNode(
                id=new_id,
                label=labels.pop(0),
                path=new_path,
                depth=new_depth
            )
            
            batch.append(new_node)
            nodes[new_id] = new_node
            
            depth_distribution[new_depth] = depth_distribution.get(new_depth, 0) + 1
            
            prob = 0.7 - (0.1 * new_depth)  
            if randint(0, 100) < (prob * 100):
                available_nodes.append(new_node)
            
            if len(batch) >= self.batch_size:
                self._bulk_insert(batch)
                batch = []
                
                if len(available_nodes) > 1000:
                    available_nodes = [
                        n for n in available_nodes 
                        if randint(0, 100) < 70 or n.depth < 3
                    ]
        
        if batch:
            self._bulk_insert(batch)
        
        try:
            db.session.execute("CREATE INDEX idx_path ON path_nodes (path)")
            db.session.execute("CREATE INDEX idx_depth ON path_nodes (depth)")
            db.session.commit()
        except exc.SQLAlchemyError:
            db.session.rollback()
        
        end_time = time.time()
        return {
            'message': f'Generated tree with {self.node_counter} nodes',
            'time_taken': f'{end_time - start_time:.2f} seconds',
            # 'depth_distribution': depth_distribution,
            'root_id': root.id
        }

    
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
def create_fast_tree(num_nodes):
    tree = PathTree()
    return tree.generate_optimized_tree(num_nodes)

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