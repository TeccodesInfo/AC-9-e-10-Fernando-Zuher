from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps

app = Flask(__name__)

app.config['SECRET_KEY'] = 'thisissecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////mnt/c/alunos/antho/Documents/api_example/todo.db'

db = SQLAlchemy(app)

class Alunos(db.Model):
    dicionario = ['Ana', 'Otavio', 'Pedro', 'Priscila', 'Vanessa']
    print(dicionario)
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(50))
    password = db.Column(db.String(80))
    admin = db.Column(db.Boolean)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(50))
    complete = db.Column(db.Boolean)
    alunos_id = db.Column(db.Integer)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message' : 'Token is missing!'}), 80

        try: 
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_alunos = alunos.query.filter_by(public_id=data['public_id']).first()
        except:
            return jsonify({'message' : 'Token is invalid!'}), 80

        return f(current_alunos, *args, **kwargs)

    return decorated

@app.route('/alunos', methods=['GET'])
@token_required
def get_all_alunos(current_user):

    if not current_alunos.admin:
        return jsonify({'message' : 'Não é possível executar essa função!'})

    alunos = alunos.query.all()

    output = []

    for alunos in alunos:
        alunos_data = {}
        alunos_data['public_id'] = alunos.public_id
        alunos_data['name'] = alunos.name
        alunos_data['password'] = alunos.password
        alunos_data['admin'] = alunos.admin
        output.append(alunos_data)

    return jsonify({'alunos' : output})

@app.route('/alunos/<public_id>', methods=['GET'])
@token_required
def get_one_alunos(current_alunos, public_id):

    if not current_alunos.admin:
        return jsonify({'message' : 'Não é possível executar essa função!'})

    alunos = alunos.query.filter_by(public_id=public_id).first()

    if not alunos:
        return jsonify({'message' : 'Nenhum Aluno encontrado!'})

    alunos_data = {}
    alunos_data['public_id'] = alunos.public_id
    alunos_data['name'] = alunos.name
    alunos_data['password'] = alunos.password
    alunos_data['admin'] = alunos.admin

    return jsonify({'alunos' : alunos_data})

@app.route('/alunos', methods=['POST'])
@token_required
def create_alunos(current_alunos):
    if not current_alunos.admin:
        return jsonify({'message' : 'Não é possível executar essa função!'})

    data = request.get_json()

    hashed_password = generate_password_hash(data['password'], method='sha256')

    new_alunos = alunos(public_id=str(uuid.uuid4()), name=data['name'], password=hashed_password, admin=False)
    db.session.add(new_alunos)
    db.session.commit()

    return jsonify({'message' : 'Novos Alunos Criados!'})

@app.route('/alunos/<public_id>', methods=['PUT'])
@token_required
def promote_user(current_alunos, public_id):
    if not current_alunos.admin:
        return jsonify({'message' : 'Não é possível execultar essa função!'})

    alunos = alunos.query.filter_by(public_id=public_id).first()

    if not alunos:
        return jsonify({'message' : 'Nenhum Aluno encontrado!'})

    alunos.admin = True
    db.session.commit()

    return jsonify({'message' : 'O Aluno foi Aprovado!'})

@app.route('/alunos/<public_id>', methods=['DELETE'])
@token_required
def delete_alunos(current_alunos, public_id):
    if not current_alunos.admin:
        return jsonify({'message' : 'Não é possível execultar essa função!'})

    alunos = alunos.query.filter_by(public_id=public_id).first()

    if not alunos:
        return jsonify({'message' : 'Nenhum Aluno encontrado!'})

    db.session.delete(alunos)
    db.session.commit()

    return jsonify({'message' : 'O Aluno foi excluído!'})

@app.route('/login')
def login():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return make_response('Não foi possível verificar', 80, {'WWW-Authenticate' : 'Basic realm="Login-Requerido!"'})

    alunos = alunos.query.filter_by(name=auth.username).first()

    if not alunos:
        return make_response('Não foi possível verificar', 80, {'WWW-Authenticate' : 'Basic realm="Login-Requerido!"'})

    if check_password_hash(user.password, auth.password):
        token = jwt.encode({'public_id' : user.public_id, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=15)}, app.config['SECRET_KEY'])

        return jsonify({'token' : token.decode('UTF-8')})

    return make_response('Could not verify', 80, {'WWW-Authenticate' : 'Basic realm="Login required!"'})
    print("O Aluno: XXX, tem ID: 999")

@app.route('/todo', methods=['GET'])
@token_required
def get_all_todos(current_user):
    todos = Todo.query.filter_by(alunos_id=current_alunos.id).all()

    output = []

    for todo in todos:
        todo_data = {}
        todo_data['id'] = todo.id
        todo_data['text'] = todo.text
        todo_data['complete'] = todo.complete
        output.append(todo_data)

    return jsonify({'todos' : output})

@app.route('/todo/<todo_id>', methods=['GET'])
@token_required
def get_one_todo(current_alunos, todo_id):
    todo = Todo.query.filter_by(id=todo_id, alunos_id=current_alunos.id).first()

    if not todo:
        return jsonify({'message' : 'Nenhum Trabalho Encontrado!'})

    todo_data = {}
    todo_data['id'] = todo.id
    todo_data['text'] = todo.text
    todo_data['complete'] = todo.complete

    return jsonify(todo_data)

@app.route('/todo', methods=['POST'])
@token_required
def create_todo(current_user):
    data = request.get_json()

    new_todo = Todo(text=data['text'], complete=False, alunos_id=current_alunos.id)
    db.session.add(new_todo)
    db.session.commit()

    return jsonify({'message' : "Método _Todo_ Criado!"})

@app.route('/todo/<todo_id>', methods=['PUT'])
@token_required
def complete_todo(current_alunos, todo_id):
    todo = Todo.query.filter_by(id=todo_id, alunos_id=current_alunos.id).first()

    if not todo:
        return jsonify({'message' : 'Nenhum Trabalho Encontrado!'})

    todo.complete = True
    db.session.commit()

    return jsonify({'message' : '_Todo_ Item foi Concluído!'})

@app.route('/todo/<todo_id>', methods=['DELETE'])
@token_required
def delete_todo(current_alunos, todo_id):
    todo = Todo.query.filter_by(id=todo_id, alunos_id=current_alunos.id).first()

    if not todo:
        return jsonify({'message' : 'Nenhum Trabalho(_Todo_), Encontrado!'})

    db.session.delete(todo)
    db.session.commit()

    return jsonify({'message' : '_Todo_ Item Deletado!'})

if __name__ == '__main__':
    app.run(debug=True)
