from flask import Blueprint, request, jsonify
import jwt
from store import store

project_bp = Blueprint('project', __name__, url_prefix='/project')
SECRET_KEY = 'hello'

@project_bp.route('/create', methods=['POST'])
def create_project():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Authorization token required"}), 401
    
    token = auth_header.split()[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except:
        return jsonify({"error": "invalid token"}), 401
    
    data = request.json
    name = data.get('name')
    description = data.get('description')
    department = payload.get('department')
    role = payload.get('role')

    if not name or not description:
        return jsonify({"error": "missing fields"}), 400

    if role != 'manager' and role != 'admin':
        return jsonify({"error": "insufficient permissions"}), 403

    new_project = store.create_project(name=name, description=description, department=department)

    return jsonify({
        "message": f"Project {name} created successfully",
        "project_id": new_project["id"],
    })
    
@project_bp.route('/<int:project_id>/tasks', methods=['GET'])
def get_project_tasks(project_id):

    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Authorization token required"}), 401
    
    token = auth_header.split()[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except:
        return jsonify({"error": "invalid token"}), 401
    
    role = payload.get('role')
    department = payload.get('department')

    if role != 'manager' and role != 'admin':
        return jsonify({"error": "insufficient permissions"}), 403

    project = store.get_project(int(project_id))
    if not project or project.get("department") != department:
        return jsonify({"error": "project not found"}), 404

    # tasks linked to this project
    tasks_data = []
    # copy tasks safely
    for task in store.filter_tasks(
        role="admin",
        requester_user_id=int(payload.get('user_id')),
        requester_department=department,
    ):
        if task.get("project_id") == int(project_id):
            tasks_data.append({
                "id": task.get("id"),
                "title": task.get("title"),
                "description": task.get("description"),
                "status": task.get("status"),
                "due_date": task.get("due_date"),
                "timestamp": task.get("timestamp"),
            })

    return jsonify({
        "project_id": project["id"],
        "project_name": project["name"],
        "tasks": tasks_data,
    })
    
@project_bp.route('/<int:project_id>/assign_task', methods=['POST'])
def assign_task_to_project(project_id):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Authorization token required"}), 401
    
    token = auth_header.split()[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except:
        return jsonify({"error": "invalid token"}), 401
    
    role = payload.get('role')
    department = payload.get('department')
    data = request.json
    task_id = data.get('task_id')

    if not task_id:
        return jsonify({"error": "task_id is required"}), 400

    if role != 'manager' and role != 'admin':
        return jsonify({"error": "insufficient permissions"}), 403

    project = store.get_project(int(project_id))
    if not project or project.get("department") != department:
        return jsonify({"error": "project not found"}), 404

    task = store.get_task(int(task_id))
    if not task:
        return jsonify({"error": "task not found"}), 404

    store.update_task(int(task_id), {"project_id": int(project_id)})

    return jsonify({
        "message": f"Task {task.get('title')} assigned to project {project.get('name')} successfully"
    })
    
@project_bp.route('/list', methods=['GET'])
def list_projects():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Authorization token required"}), 401
    
    token = auth_header.split()[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except:
        return jsonify({"error": "invalid token"}), 401
    
    role = payload.get('role')
    department = payload.get('department')

    if role != 'manager' and role != 'admin':
        return jsonify({"error": "insufficient permissions"}), 403

    projects = store.list_projects(department=department)
    projects_data = []
    for project in projects:
        projects_data.append({
            "id": project["id"],
            "name": project["name"],
            "description": project.get("description"),
        })

    return jsonify({
        "projects": projects_data
    })
    
@project_bp.route('/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Authorization token required"}), 401
    
    token = auth_header.split()[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except:
        return jsonify({"error": "invalid token"}), 401
    
    department = payload.get('department')
    role = payload.get('role')
    data = request.json
    name = data.get('name')
    description = data.get('description')

    if role != 'manager' and role != 'admin':
        return jsonify({"error": "insufficient permissions"}), 403

    try:
        project = store.update_project(int(project_id), name=name, description=description, department=department)
    except KeyError:
        return jsonify({"error": "project not found"}), 404

    return jsonify({
        "message": f"Project {project['name']} updated successfully"
    })

    
@project_bp.route('/<int:project_id>/delete', methods=['DELETE'])
def delete_project(project_id):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Authorization token required"}), 401
    
    token = auth_header.split()[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except:
        return jsonify({"error": "invalid token"}), 401
    
    role = payload.get('role')
    department = payload.get('department')

    if role != 'admin' and role != 'manager':
        return jsonify({"error": "insufficient permissions"}), 403

    try:
        project = store.delete_project(int(project_id), department=department)
    except KeyError:
        return jsonify({"error": "project not found"}), 404

    return jsonify({
        "message": f"Project {project['name']} deleted successfully"
    })