from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.types import UserDefinedType
from sqlalchemy import text
from datetime import datetime
from random import choice, randint
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://root:root@localhost/org_chart_ltree'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Candidate:

    @property
    def names(self):
        return ["ahmed", "moahmed", "islam", "mostafa", "kamal"]
    
    @property
    def employment_types(self):
        return ['full_time', "part_time"]
    
    @property
    def titles(self):
        return ['CEO', "SWE", "CTO", "Ay haga :)"]

    def pick_name(self):
        index = datetime.now().second % len(self.names)
        return self.names[index]
    
    def pick_employment_type(self):
        index = datetime.now().second % len(self.employment_types)
        return self.employment_types[index]
    
    def pick_title(self):
        index = datetime.now().second % len(self.titles)
        return self.titles[index]
        

class Ltree(UserDefinedType):
    def get_col_spec(self, **kw):
        return "LTREE"
    
    class comparator_factory(UserDefinedType.Comparator):
        def descendant_of(self, other):
            return self.op("<@")(other)

        def ancestor_of(self, other):
            return self.op(">@")(other)

    def bind_processor(self, dialect):
        def process(value):
            return value
        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            return value
        return process


class LtreeNode(db.Model):
    __tablename__ = 'ltree_nodes'

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100))
    title = db.Column(db.String(50))
    employment_type = db.Column(db.String(50))
    hire_date = db.Column(db.DateTime, default=datetime.now)
    path = db.Column(Ltree(), nullable=False) 
    depth = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'label': self.label,
            'name': self.name,
            'title': self.title,
            'employment_type' : self.employment_type,
            'hire_date': self.hire_date,
            'path': self.path,
            'depth': self.depth
        }
    

class LtreeTree:
    def __init__(self):
        self.node_counter = 1
        self.batch_size = 5000
        self.max_depth = 15
        self.max_children = 20

    def create_root(self):
        root = LtreeNode(id=1, label='root', path='1', depth=0)
        db.session.add(root)
        db.session.commit()
        return root

    def _bulk_insert(self, nodes):
        try:
            db.session.bulk_save_objects(nodes)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    def generate_tree(self, total_nodes):
        db.drop_all()
        db.create_all()
        setup_ltree_extension()  
        self.node_counter = 1

        start = time.time()
        root = self.create_root()
        nodes = [root]
        available_nodes = [root]

        labels = [f"node_{i}" for i in range(2, total_nodes + 1)]
        batch = []

        while self.node_counter < total_nodes and available_nodes:
            parent = choice(available_nodes)

            if parent.depth >= self.max_depth:
                available_nodes.remove(parent)
                continue

            self.node_counter += 1
            new_id = self.node_counter
            new_path = f"{parent.path}.{new_id}"
            new_depth = parent.depth + 1
            
            candidate = Candidate()

            new_node = LtreeNode(
                id=new_id,
                label=labels.pop(0),
                name=candidate.pick_name(),
                title=candidate.pick_title(),
                employment_type=candidate.pick_employment_type(),
                path=new_path,
                depth=new_depth,
            )

            batch.append(new_node)

            prob = 0.7 - (0.05 * new_depth)
            if randint(0, 100) < (prob * 100):
                available_nodes.append(new_node)

            if len(batch) >= self.batch_size:
                self._bulk_insert(batch)
                batch = []

        if batch:
            self._bulk_insert(batch)

        end = time.time()
        return {
            "message": f"Created tree with {self.node_counter} nodes",
            "time_taken": f"{end - start:.2f}s"
        }

    def get_subtree(self, node_id, limit=None):
        start = time.time()
        root = db.session.get(LtreeNode, node_id)
        if not root:
            return {"error": "Node not found"}

        rows = db.session.query(LtreeNode).filter(
            LtreeNode.path.descendant_of(root.path)
        ).order_by(LtreeNode.depth).limit(limit).all()

        node_dict = {node.id: node.to_dict() for node in rows}
        path_map = {str(node.path): node.id for node in rows}

        for node in node_dict.values():
            node["children"] = []

        root_nodes = []

        for node in rows:
            path_parts = str(node.path).split('.')
            if len(path_parts) > 1:
                parent_path = '.'.join(path_parts[:-1])
                parent_id = path_map.get(parent_path)
                if parent_id:
                    node_dict[parent_id]["children"].append(node_dict[node.id])
            else:
                root_nodes.append(node_dict[node.id])
        end = time.time()

        return {
            "node_count": len(rows),
            "time_taken": end - start,
            "root_id": root.id,
            "tree": node_dict[root.id] 
        }

    def add_node(self, data):
        # print(data.get('parent_id'))
        parent_id = data.get('parent_id')
        parent = db.session.get(LtreeNode, str(parent_id))
        candidate = Candidate()
        
        
        if not parent:
            root = LtreeNode(
                label=data.get('label'),
                name=candidate.pick_name(),
                title=candidate.pick_title(),
                employment_type=candidate.pick_employment_type(),
                path='',
                depth=0
            )

            db.session.add(root)
            db.session.flush()
            root.path = f"{root.id}"
            db.session.commit()

            return {
                "message": "you are create a new node as root",
                "node": root.to_dict()
            }

        new_depth = parent.depth + 1

        new_node = LtreeNode(
            label=data.get('label'),
            name=candidate.pick_name(),
            title=candidate.pick_title(),
            employment_type=candidate.pick_employment_type(),
            path='',
            depth=new_depth
        )
        db.session.add(new_node)
        db.session.flush()
        new_node.path = f"{parent.path}.{new_node.id}"
        db.session.commit()
        print(new_node.id)
        # f"{parent.path}.{new_id}"

        print(parent.path)

        return {
            "node": new_node.to_dict()
        }


def setup_ltree_extension():
    with db.engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS ltree"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ltree_path ON ltree_nodes USING GIST (path)"))


@app.route('/create_tree/<int:num_nodes>',  methods=['POST'])
def create_tree(num_nodes):
    tree = LtreeTree()
    return tree.generate_tree(num_nodes)

@app.route('/subtree/<int:node_id>')
def get_subtree(node_id):
    limit = request.args.get('limit', default=10000, type=int)
    tree = LtreeTree()
    return tree.get_subtree(node_id, limit)

@app.route('/tree', methods=['POST'])
def add_node():
    # print(request.get_json())
    tree = LtreeTree()
    return tree.add_node(request.get_json())

if __name__ == '__main__':
    with app.app_context():
        with db.engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS ltree"))
        db.create_all()
        setup_ltree_extension() 

    app.run(debug=True)
