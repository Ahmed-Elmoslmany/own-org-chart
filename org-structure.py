from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc, func
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tree.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Path(db.Model):
    __tablename__ = 'paths'
    
    id = db.Column(db.Integer, primary_key=True)
    node_id = db.Column(db.Integer, db.ForeignKey('nodes.id'))
    path = db.Column(db.Integer, index=True) 
    depth = db.Column(db.Integer)

    def __repr__(self):
        return f'Path(id={self.id}, node_id={self.node_id}, path={self.path}, depth={self.depth})'

class Node(db.Model):
    __tablename__ = 'nodes'
    
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100))
    paths = db.relationship('Path', backref='node', lazy='joined', cascade='all, delete-orphan')

    def __repr__(self):
        return f'Node(id={self.id}, label={self.label})'
    
    def get_full_path(self):
        """Calculate full path by traversing up the path hierarchy"""
        path_ids = [str(self.id)]
        current_path = self.paths[0] if self.paths else None
        
        while current_path and current_path.path: 
            parent_path = Path.query.get(current_path.path)
            if parent_path:
                path_ids.append(str(parent_path.node_id))
                current_path = parent_path.node.paths[0] if parent_path.node.paths else None
            else:
                break
        
        return '.'.join(reversed(path_ids))
    
    def to_dict(self, include_children=False):
        result = {
            'id': self.id,
            'label': self.label,
            'path': self.get_full_path(),
            'depth': self.paths[0].depth if self.paths else 0
        }
        if include_children:
            result['children'] = [child.to_dict() for child in self.get_children()]
        return result
    
    def get_children(self):
        """Get direct children by finding paths that reference this node's path"""
        if not self.paths:
            return []
        current_path_id = self.paths[0].id
        child_paths = Path.query.filter_by(path=current_path_id).options(
            db.joinedload(Path.node)
        ).all()
        return [path.node for path in child_paths]
    
    def get_descendants(self, limit=None):
        """Get all descendants using recursive path traversal"""
        if not self.paths:
            return []
        
        path_cte = db.session.query(Path).filter(
            Path.id == self.paths[0].id
        ).cte(recursive=True)
        
        path_cte = path_cte.union_all(
            db.session.query(Path).filter(
                Path.path == path_cte.c.id
            )
        )
        
        query = db.session.query(Node).join(
            path_cte, Node.id == path_cte.c.node_id
        ).filter(Node.id != self.id)
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def get_parent(self):
        """Get parent node by following path reference"""
        if not self.paths or not self.paths[0].path:
            return None
        parent_path = Path.query.get(self.paths[0].path)
        return parent_path.node if parent_path else None

class PathTree:
    def __init__(self):
        self.node_counter = 1  
        self.batch_size = 5000  
        self.max_depth = 20  
        self.max_children = 30
        self.path_counter = 1
    
    def _bulk_insert(self, nodes, paths):
        """Optimized bulk insert"""
        try:
            db.session.bulk_save_objects(nodes)
            db.session.bulk_save_objects(paths)
            db.session.commit()
        except exc.SQLAlchemyError as e:
            db.session.rollback()
            raise e
    
    def create_root(self):
        root = Node(id=1, label='root')
        root_path = Path(id=1, node_id=root.id, path=0, depth=0)  # path=0 indicates root
        db.session.add(root)
        db.session.add(root_path)
        db.session.commit()
        self.path_counter += 1
        return root
    
    def generate_optimized_tree(self, total_nodes):
        start_time = time.time()

        db.drop_all()
        db.create_all()

        self.max_depth = 10
        self.max_children = 10
        self.path_counter = 2
        self.node_counter = 1

        root = self.create_root()
        available_nodes = [root]
        node_batch = []
        path_batch = []

        labels = [f"node_{i}" for i in range(2, total_nodes + 1)]
        depth_distribution = {0: 1}

        while self.node_counter < total_nodes and available_nodes:
            available_nodes.sort(key=lambda n: n.paths[0].depth, reverse=True)
            parent = available_nodes[0]  # always choose the deepest available node
            parent_path = parent.paths[0]

            if (parent_path.depth >= self.max_depth or 
                Path.query.filter_by(path=parent_path.id).count() >= self.max_children):
                available_nodes.remove(parent)
                continue

            self.node_counter += 1
            new_id = self.node_counter
            new_depth = parent_path.depth + 1

            new_node = Node(id=new_id, label=labels.pop(0))
            new_path = Path(
                id=self.path_counter,
                node_id=new_id,
                path=parent_path.id,
                depth=new_depth
            )
            new_node.paths = [new_path]

            node_batch.append(new_node)
            path_batch.append(new_path)
            self.path_counter += 1

            depth_distribution[new_depth] = depth_distribution.get(new_depth, 0) + 1

            if new_depth < self.max_depth:
                available_nodes.append(new_node)

            if len(node_batch) >= self.batch_size:
                self._bulk_insert(node_batch, path_batch)
                node_batch = []
                path_batch = []

                if len(available_nodes) > 1000:
                    available_nodes = [
                        n for n in available_nodes 
                        if n.paths[0].depth < self.max_depth
                    ]

        if node_batch:
            self._bulk_insert(node_batch, path_batch)

        try:
            db.session.execute("CREATE INDEX idx_path ON paths (path)")
            db.session.execute("CREATE INDEX idx_depth ON paths (depth)")
            db.session.commit()
        except exc.SQLAlchemyError:
            db.session.rollback()

        end_time = time.time()
        return {
            'message': f'Generated tree with {self.node_counter} nodes',
            'time_taken': f'{end_time - start_time:.2f} seconds',
            'depth_distribution': depth_distribution,
            'root_id': root.id
        }

   
    def add_child(self, parent, label=None):
        self.node_counter += 1
        new_id = self.node_counter
        
        new_node = Node(id=new_id, label=label or f"node_{new_id}")
        new_path = Path(
            id=self.path_counter,
            node_id=new_id,
            path=parent.paths[0].id,
            depth=parent.paths[0].depth + 1
        )
        
        db.session.add(new_node)
        db.session.add(new_path)
        db.session.commit()
        self.path_counter += 1
        return new_node
    
    def get_subtree(self, node_id, limit=10000):
        start_time = time.time()
        
        root_node = db.session.query(Node).options(
            db.joinedload(Node.paths)
        ).get(node_id)
        
        if not root_node or not root_node.paths:
            return {
                'error': 'Node not found or has no path',
                'time_taken': time.time() - start_time
            }
        
        root_path_id = root_node.paths[0].id
        
        path_cte = db.session.query(Path).filter(
            Path.id == root_path_id
        ).cte(recursive=True)
        
        path_cte = path_cte.union_all(
            db.session.query(Path).filter(
                Path.path == path_cte.c.id
            )
        )
        
        query = db.session.query(Node).join(
            path_cte, Node.id == path_cte.c.node_id
        ).options(
            db.joinedload(Node.paths)
        )
        
        if limit:
            query = query.limit(limit)
            
        descendants = query.all()
        
        node_map = {root_node.id: root_node.to_dict()}
        node_map[root_node.id]['children'] = []
        
        for node in descendants:
            if node.id == root_node.id:
                continue  
                
            node_map[node.id] = node.to_dict()
            node_map[node.id]['children'] = []
            
            parent_path_id = node.paths[0].path
            parent_path = Path.query.get(parent_path_id)
            if parent_path and parent_path.node_id in node_map:
                node_map[parent_path.node_id]['children'].append(node_map[node.id])
        
        end_time = time.time()
        return {
            'time_taken': end_time - start_time,
            'node_count': len(descendants),
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
    node = db.session.query(Node).options(
        db.joinedload(Node.paths)
    ).get_or_404(node_id)
    return node.to_dict(include_children=True)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)