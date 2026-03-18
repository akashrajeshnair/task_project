from flask import Blueprint, request, jsonify
import jwt
from store import store

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

    new_task = store.create_task(
        title=title,
        description=description,
        priority=priority,
        due_date=due_date,
        status=status,
        project_id=project_id,
        comments=comments,
    )

    if assigned_employees:
        # only assign existing users
        valid_ids = []
        for emp_id in assigned_employees:
            if store.get_user(int(emp_id)):
                valid_ids.append(int(emp_id))
        store.set_task_assignees(int(new_task["id"]), valid_ids)

    return jsonify({"message": "Task created successfully", "task_id": new_task["id"]}), 201


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

    task = store.get_task(int(id))
    if not task:
        return jsonify({"error": "Task not found"}), 404

    assignees = store.get_task_assignees(int(id))
    if int(user_id) not in assignees:
        return jsonify({"error": "Task not found"}), 404

    return jsonify({
        "id": task["id"],
        "title": task.get("title"),
        "description": task.get("description"),
        "priority": task.get("priority"),
        "due_date": task.get("due_date"),
        "status": task.get("status"),
        "assigned_employees": assignees,
        "project_id": task.get("project_id"),
        "comments": task.get("comments"),
        "timestamp": task.get("timestamp"),
    })
        
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

    tasks = store.tasks_for_user(int(user_id))
    task_list = []
    for task in tasks:
        tid = int(task["id"])
        task_list.append({
            "id": tid,
            "title": task.get("title"),
            "description": task.get("description"),
            "priority": task.get("priority"),
            "due_date": task.get("due_date"),
            "status": task.get("status"),
            "assigned_employees": store.get_task_assignees(tid),
            "project_id": task.get("project_id"),
            "comments": task.get("comments"),
            "timestamp": task.get("timestamp"),
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

    tasks = store.filter_tasks(
        role=role,
        requester_user_id=int(user_id),
        requester_department=department,
        status=status,
        priority=priority,
        due_date=due_date,
        assigned_employee=int(assigned_employee) if assigned_employee is not None else None,
    )

    task_list = []
    for task in tasks:
        tid = int(task["id"])
        task_list.append({
            "id": tid,
            "title": task.get("title"),
            "description": task.get("description"),
            "priority": task.get("priority"),
            "due_date": task.get("due_date"),
            "status": task.get("status"),
            "assigned_employees": store.get_task_assignees(tid),
            "project_id": task.get("project_id"),
            "comments": task.get("comments"),
            "timestamp": task.get("timestamp"),
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
    user_id = payload.get('user_id')
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

    task = store.get_task(int(id))
    if not task:
        return jsonify({"error": "Task not found"}), 404

    store.update_task(int(id), {
        "title": title,
        "description": description,
        "priority": priority,
        "due_date": due_date,
        "status": status,
        "project_id": project_id,
        "comments": comments,
    })

    if assigned_employees is not None:
        valid_ids = []
        for emp_id in assigned_employees:
            if store.get_user(int(emp_id)):
                valid_ids.append(int(emp_id))
        store.set_task_assignees(int(id), valid_ids)

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

    task = store.get_task(int(id))
    if not task:
        return jsonify({"error": "Task not found"}), 404

    assignees = store.get_task_assignees(int(id))
    if role == 'employee':
        if int(user_id) not in assignees:
            return jsonify({"error": "Task not found or access denied"}), 404
    elif role == 'manager':
        # managers can delete tasks assigned to employees of their department
        dept_user_ids = {
            u["id"] for u in (store.get_user(uid) for uid in assignees) if u and u.get("department") == department
        }
        if not dept_user_ids:
            return jsonify({"error": "Task not found"}), 404

    store.delete_task(int(id))
    return jsonify({"message": "Task deleted successfully"})