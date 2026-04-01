from flask import Blueprint, request, jsonify
from db.models import Task, Project
from db.db import session_local
import jwt
# from store import store  # In-memory mode (currently disabled)

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

    with session_local() as session:
        if role != 'manager' and role != 'admin':
            return jsonify({"error": "insufficient permissions"}), 403
        new_project = Project(name=name, description=description, department=department)
        session.add(new_project)
        session.commit()

        return jsonify({
            "message": f"Project {name} created successfully",
            "project_id": new_project.id
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

    with session_local() as session:
        if role != 'manager' and role != 'admin':
            return jsonify({"error": "insufficient permissions"}), 403
        project = session.query(Project).filter_by(id=project_id, department=department).first()
        if not project:
            return jsonify({"error": "project not found"}), 404

        tasks = session.query(Task).filter(Task.project_id == project_id).all()

        tasks_data = []
        for task in tasks:
            tasks_data.append({
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "due_date": task.due_date,
                "timestamp": task.timestamp
            })

        return jsonify({
            "project_id": project.id,
            "project_name": project.name,
            "tasks": tasks_data
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

    with session_local() as session:
        if role != 'manager' and role != 'admin':
            return jsonify({"error": "insufficient permissions"}), 403
        project = session.query(Project).filter_by(id=project_id, department=department).first()
        if not project:
            return jsonify({"error": "project not found"}), 404

        task = session.query(Task).filter_by(id=task_id).first()
        if not task:
            return jsonify({"error": "task not found"}), 404

        project.tasks.append(task)
        session.commit()

        return jsonify({
            "message": f"Task {task.title} assigned to project {project.name} successfully"
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

    with session_local() as session:
        if role != 'manager' and role != 'admin':
            return jsonify({"error": "insufficient permissions"}), 403
        projects = session.query(Project).filter_by(department=department).all()
        projects_data = []
        for project in projects:
            projects_data.append({
                "id": project.id,
                "name": project.name,
                "description": project.description
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

    with session_local() as session:
        if role != 'manager' and role != 'admin':
            return jsonify({"error": "insufficient permissions"}), 403
        project = session.query(Project).filter_by(id=project_id, department=department).first()
        if not project:
            return jsonify({"error": "project not found"}), 404

        if name:
            project.name = name
        if description:
            project.description = description

        session.commit()

        return jsonify({
            "message": f"Project {project.name} updated successfully"
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

    with session_local() as session:
        if role != 'admin' and role != 'manager':
            return jsonify({"error": "insufficient permissions"}), 403
        project = session.query(Project).filter_by(id=project_id, department=department).first()
        if not project:
            return jsonify({"error": "project not found"}), 404

        session.delete(project)
        session.commit()

        return jsonify({
            "message": f"Project {project.name} deleted successfully"
        })