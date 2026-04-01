from flask import Blueprint, request, jsonify
from db.models import Task, task_assignments, User
from db.db import session_local
import jwt
# from store import store  # In-memory mode (currently disabled)

task_bp = Blueprint('task', __name__, url_prefix='/task')
SECRET_KEY = 'hello'

@task_bp.route('/create-task', methods=['POST'])
def create_task():
    auth_header = request.headers.get('Authorization')

    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Authorization token required"}), 401
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except:
        return jsonify({"error": "invalid token"}), 401
    role = payload.get('role')

    data = request.json
    title = data.get('title')
    description = data.get('description')
    priority = data.get('priority')
    due_date = data.get('due_date')
    status = data.get('status')
    assigned_employees = data.get('assigned_employees')
    project_id = data.get('project_id')
    comments = data.get('comments')
    
    if role != 'employee' and role != 'manager' and role != 'admin':
        return jsonify({"error": "Access denied. Insufficient permissions"}), 403

    with session_local() as session:
        new_task = Task(
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            status=status,
            project_id=project_id,
            comments=comments
        )
        session.add(new_task)
        session.commit()

        if assigned_employees:
            for emp_id in assigned_employees:
                employee = session.query(User).filter_by(id=emp_id).first()
                if employee:
                    new_task.assigned_employees.append(employee)
            session.commit()

        return jsonify({"message": "Task created successfully", "task_id": new_task.id}), 201


@task_bp.route('/view-task/<int:id>', methods=['GET'])
def get_task_details(id):
    auth_header = request.headers.get('Authorization')

    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Authorization token required"}), 401
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except:
        return jsonify({"error": "invalid token"}), 401
    user_id = payload.get('user_id')
    role = payload.get('role')
    
    if role != 'employee' and role != 'manager' and role != 'admin':
        return jsonify({"error": "Access denied. Insufficient permissions"}), 403

    with session_local() as session:
        task = session.query(Task).join(task_assignments).filter(Task.id == id, task_assignments.c.user_id == user_id).first()
        if task:
            return jsonify({
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "priority": task.priority,
                "due_date": task.due_date,
                "status": task.status,
                "assigned_employees": [emp.id for emp in task.assigned_employees],
                "project_id": task.project_id,
                "comments": task.comments,
                "timestamp": task.timestamp
            })
        else:
            return jsonify({"error": "Task not found"}), 404
        
@task_bp.route('/list-tasks', methods=['GET'])
def get_my_tasklist():
    auth_header = request.headers.get('Authorization')

    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Authorization token required"}), 401
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except:
        return jsonify({"error": "invalid token"}), 401
    user_id = payload.get('user_id')
    role = payload.get('role')
    
    if role != 'employee' and role != 'manager' and role != 'admin':
        return jsonify({"error": "Access denied. Insufficient permissions"}), 403

    with session_local() as session:
        tasks = session.query(Task).join(task_assignments).filter(task_assignments.c.user_id == user_id).all()
        task_list = []
        for task in tasks:
            task_list.append({
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "priority": task.priority,
                "due_date": task.due_date,
                "status": task.status,
                "assigned_employees": [emp.id for emp in task.assigned_employees],
                "project_id": task.project_id,
                "comments": task.comments,
                "timestamp": task.timestamp
            })
        return jsonify(task_list)



@task_bp.route('/filter-tasks', methods=['POST'])
def filter_tasks():
    auth_header = request.headers.get('Authorization')

    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Authorization token required"}), 401
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except:
        return jsonify({"error": "invalid token"}), 401
    user_id = payload.get('user_id')
    role = payload.get('role')
    department = payload.get('department')
    
    if role != 'employee' and role != 'manager' and role != 'admin':
        return jsonify({"error": "Access denied. Insufficient permissions"}), 403

    data = request.json
    status = data.get('status')
    priority = data.get('priority')
    due_date = data.get('due_date')
    assigned_employee = data.get('assigned_employee')

    with session_local() as session:
        query = session.query(Task)

        if role == 'employee':
            query = query.join(task_assignments).filter(task_assignments.c.user_id == user_id)
        elif role == 'manager':
            query = query.join(task_assignments).join(User).filter(User.department == department)
        else:
            if assigned_employee:
                query = query.join(task_assignments)

        if status:
            query = query.filter(Task.status == status)
        if priority:
            query = query.filter(Task.priority == priority)
        if due_date:
            query = query.filter(Task.due_date == due_date)
        if assigned_employee:
            if role != 'employee' or assigned_employee != user_id:
                query = query.filter(task_assignments.c.user_id == assigned_employee)

        tasks = query.all()

        task_list = []
        for task in tasks:
            task_list.append({
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "priority": task.priority,
                "due_date": task.due_date,
                "status": task.status,
                "assigned_employees": [emp.id for emp in task.assigned_employees],
                "project_id": task.project_id,
                "comments": task.comments,
                "timestamp": task.timestamp
            })
        return jsonify(task_list)
    
@task_bp.route('/update-task/<int:id>', methods=['PUT'])
def update_task(id):
    auth_header = request.headers.get('Authorization')

    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Authorization token required"}), 401
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except:
        return jsonify({"error": "invalid token"}), 401
    payload.get('user_id')
    role = payload.get('role')

    if role != 'employee' and role != 'manager' and role != 'admin':
        return jsonify({"error": "Access denied. Insufficient permissions"}), 403

    data = request.json
    title = data.get('title')
    description = data.get('description')
    priority = data.get('priority')
    due_date = data.get('due_date')
    status = data.get('status')
    assigned_employees = data.get('assigned_employees')
    project_id = data.get('project_id')
    comments = data.get('comments')

    with session_local() as session:
        task = session.query(Task).filter_by(id=id).first()
        if not task:
            return jsonify({"error": "Task not found"}), 404

        if title:
            task.title = title
        if description:
            task.description = description
        if priority:
            task.priority = priority
        if due_date:
            task.due_date = due_date
        if status:
            task.status = status
        if project_id:
            task.project_id = project_id
        if comments:
            task.comments = comments

        if assigned_employees is not None:
            task.assigned_employees.clear()
            for emp_id in assigned_employees:
                employee = session.query(User).filter_by(id=emp_id).first()
                if employee:
                    task.assigned_employees.append(employee)

        session.commit()
        return jsonify({"message": "Task updated successfully"})
    
@task_bp.route('/delete-task/<int:id>', methods=['DELETE'])
def delete_task(id):
    auth_header = request.headers.get('Authorization')

    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Authorization token required"}), 401
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except:
        return jsonify({"error": "invalid token"}), 401
    user_id = payload.get('user_id')
    department = payload.get('department')
    role = payload.get('role')

    if role != 'employee' and role != 'manager' and role != 'admin':
        return jsonify({"error": "Access denied. Insufficient permissions"}), 403

    with session_local() as session:
        if role == 'employee':
            task = session.query(Task).join(task_assignments).filter(Task.id == id, task_assignments.c.user_id == user_id).first()
            if not task:
                return jsonify({"error": "Task not found or access denied"}), 404
        elif role == 'manager':
            task = session.query(Task).join(task_assignments).join(User).filter(Task.id == id, User.department == department).first()
            if not task:
                return jsonify({"error": "Task not found"}), 404
        else:
            task = session.query(Task).filter_by(id=id).first()
        if not task:
            return jsonify({"error": "Task not found"}), 404

        session.delete(task)
        session.commit()
        return jsonify({"message": "Task deleted successfully"})