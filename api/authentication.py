from flask import Blueprint, request, jsonify
from functools import wraps
import jwt
import datetime
import bcrypt
from store import store

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
SECRET_KEY = 'hello'

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')
    department = data.get('department')

    if not username or not password or not role or not department:
        return jsonify({"error": "missing fields"}), 400
    
    # auth_header = request.headers.get('Authorization')

    existing_user = store.get_user_by_username(username)
    if existing_user:
        return jsonify({"error": "user already exists"}), 400

    b_password = password.encode()
    s = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(b_password, s)

    try:
        new_user = store.create_user(
            username=username,
            password_hash=hashed_password.decode(),
            role=role,
            department=department,
        )
    except ValueError:
        return jsonify({"error": "user already exists"}), 400

    return jsonify({
        "message": f"User {username} created successfully",
        "user_id": new_user["id"],
    })
    
@auth_bp.route('/login', methods=['POST'])
def login():
    global user_id
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "username and password required"}), 400
    
    user = store.get_user_by_username(username)
    if not user:
        return jsonify({"error": "user not found"}), 404

    b_password = password.encode()
    db_password = user["password"]
    if not bcrypt.checkpw(b_password, db_password.encode()):
        return jsonify({"error": "wrong password"}), 401

    payload = {
        "user_id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "department": user["department"],
        "exp": datetime.datetime.now() + datetime.timedelta(hours=1),
    }

    user_id = user["id"]
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

    return jsonify({
        "message": f"Welcome {username}",
        "user_id": user["id"],
        "role": user["role"],
        "token": token,
        "department": user["department"],
    })
    
@auth_bp.route('/update', methods=['PUT'])
def update_user():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Authorization token required"}), 401
    
    token = auth_header.split()[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except:
        return jsonify({"error": "invalid token"}), 401
    
    user_id = payload.get('user_id')
    data = request.json
    new_password = data.get('password')

    if not new_password:
        return jsonify({"error": "new password required"}), 400
    
    user = store.get_user(int(user_id))
    if not user:
        return jsonify({"error": "user not found"}), 404

    b_password = new_password.encode()
    s = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(b_password, s)

    store.update_user_password(int(user_id), hashed_password.decode())

    return jsonify({
        "message": f"User {user['username']} password updated successfully"
    })
    
@auth_bp.route('/delete', methods=['DELETE'])
def delete_user():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Authorization token required"}), 401
    
    token = auth_header.split()[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except:
        return jsonify({"error": "invalid token"}), 401
    
    user_id = payload.get('user_id')

    user = store.get_user(int(user_id))
    if not user:
        return jsonify({"error": "user not found"}), 404

    store.delete_user(int(user_id))

    return jsonify({
        "message": f"User {user['username']} deleted successfully"
    })