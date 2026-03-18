"""In-memory data store for the app.

This replaces the previous SQLAlchemy/MySQL persistence layer.

Contract
- Data is stored in-process (lost on restart).
- IDs are auto-incrementing integers.
- Callers get/put plain dicts (JSON-friendly).
- Thread-safety: writes are guarded by a single lock.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from threading import RLock
from typing import Dict, List, Optional, Set, Tuple


def _utcnow_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass
class MemoryStore:
    _lock: RLock = field(default_factory=RLock)

    _users: Dict[int, dict] = field(default_factory=dict)
    _users_by_username: Dict[str, int] = field(default_factory=dict)

    _projects: Dict[int, dict] = field(default_factory=dict)

    _tasks: Dict[int, dict] = field(default_factory=dict)
    _task_assignments: Dict[int, Set[int]] = field(default_factory=dict)  # task_id -> {user_id}

    _user_seq: int = 0
    _project_seq: int = 0
    _task_seq: int = 0

    # -------- Users --------
    def create_user(self, *, username: str, password_hash: str, role: str, department: str) -> dict:
        with self._lock:
            if username in self._users_by_username:
                raise ValueError("user already exists")
            self._user_seq += 1
            user_id = self._user_seq
            user = {
                "id": user_id,
                "username": username,
                "password": password_hash,
                "role": role,
                "department": department,
            }
            self._users[user_id] = user
            self._users_by_username[username] = user_id
            return dict(user)

    def get_user(self, user_id: int) -> Optional[dict]:
        with self._lock:
            user = self._users.get(user_id)
            return dict(user) if user else None

    def get_user_by_username(self, username: str) -> Optional[dict]:
        with self._lock:
            uid = self._users_by_username.get(username)
            if not uid:
                return None
            return dict(self._users[uid])

    def count_users(self) -> int:
        with self._lock:
            return len(self._users)

    def update_user_password(self, user_id: int, password_hash: str) -> dict:
        with self._lock:
            user = self._users.get(user_id)
            if not user:
                raise KeyError("user not found")
            user["password"] = password_hash
            return dict(user)

    def delete_user(self, user_id: int) -> dict:
        with self._lock:
            user = self._users.get(user_id)
            if not user:
                raise KeyError("user not found")
            # remove username index
            self._users_by_username.pop(user["username"], None)
            # remove user record
            self._users.pop(user_id, None)
            # remove from assignments
            for assignees in self._task_assignments.values():
                assignees.discard(user_id)
            return dict(user)

    # -------- Projects --------
    def create_project(self, *, name: str, description: str, department: str) -> dict:
        with self._lock:
            self._project_seq += 1
            pid = self._project_seq
            project = {
                "id": pid,
                "name": name,
                "description": description,
                "department": department,
            }
            self._projects[pid] = project
            return dict(project)

    def get_project(self, project_id: int) -> Optional[dict]:
        with self._lock:
            p = self._projects.get(project_id)
            return dict(p) if p else None

    def list_projects(self, *, department: str) -> List[dict]:
        with self._lock:
            return [dict(p) for p in self._projects.values() if p.get("department") == department]

    def update_project(self, project_id: int, *, name: Optional[str], description: Optional[str], department: str) -> dict:
        with self._lock:
            p = self._projects.get(project_id)
            if not p or p.get("department") != department:
                raise KeyError("project not found")
            if name:
                p["name"] = name
            if description:
                p["description"] = description
            return dict(p)

    def delete_project(self, project_id: int, *, department: str) -> dict:
        with self._lock:
            p = self._projects.get(project_id)
            if not p or p.get("department") != department:
                raise KeyError("project not found")
            self._projects.pop(project_id, None)
            # detach tasks from this project
            for t in self._tasks.values():
                if t.get("project_id") == project_id:
                    t["project_id"] = None
            return dict(p)

    # -------- Tasks --------
    def create_task(
        self,
        *,
        title: str,
        description: Optional[str],
        priority: Optional[str],
        due_date: Optional[str],
        status: Optional[str],
        project_id: Optional[int],
        comments: Optional[str],
    ) -> dict:
        with self._lock:
            self._task_seq += 1
            tid = self._task_seq
            task = {
                "id": tid,
                "title": title,
                "description": description,
                "priority": priority or "medium",
                "due_date": due_date,
                "status": status or "pending",
                "project_id": project_id,
                "comments": comments,
                "timestamp": _utcnow_iso(),
            }
            self._tasks[tid] = task
            self._task_assignments.setdefault(tid, set())
            return dict(task)

    def get_task(self, task_id: int) -> Optional[dict]:
        with self._lock:
            t = self._tasks.get(task_id)
            return dict(t) if t else None

    def update_task(self, task_id: int, updates: dict) -> dict:
        with self._lock:
            t = self._tasks.get(task_id)
            if not t:
                raise KeyError("task not found")
            for k in [
                "title",
                "description",
                "priority",
                "due_date",
                "status",
                "project_id",
                "comments",
            ]:
                if k in updates and updates[k] is not None:
                    t[k] = updates[k]
            return dict(t)

    def delete_task(self, task_id: int) -> dict:
        with self._lock:
            t = self._tasks.get(task_id)
            if not t:
                raise KeyError("task not found")
            self._tasks.pop(task_id, None)
            self._task_assignments.pop(task_id, None)
            return dict(t)

    def set_task_assignees(self, task_id: int, user_ids: List[int]) -> None:
        with self._lock:
            if task_id not in self._tasks:
                raise KeyError("task not found")
            self._task_assignments[task_id] = set(int(uid) for uid in user_ids)

    def add_task_assignee(self, task_id: int, user_id: int) -> None:
        with self._lock:
            if task_id not in self._tasks:
                raise KeyError("task not found")
            self._task_assignments.setdefault(task_id, set()).add(int(user_id))

    def get_task_assignees(self, task_id: int) -> List[int]:
        with self._lock:
            return sorted(self._task_assignments.get(task_id, set()))

    def tasks_for_user(self, user_id: int) -> List[dict]:
        with self._lock:
            out: List[dict] = []
            for tid, assignees in self._task_assignments.items():
                if user_id in assignees and tid in self._tasks:
                    out.append(dict(self._tasks[tid]))
            return out

    def tasks_for_department(self, department: str) -> List[dict]:
        """Tasks assigned to any user in a department."""
        with self._lock:
            dept_users = {u["id"] for u in self._users.values() if u.get("department") == department}
            out: List[dict] = []
            for tid, assignees in self._task_assignments.items():
                if assignees.intersection(dept_users) and tid in self._tasks:
                    out.append(dict(self._tasks[tid]))
            return out

    def filter_tasks(
        self,
        *,
        role: str,
        requester_user_id: int,
        requester_department: str,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        due_date: Optional[str] = None,
        assigned_employee: Optional[int] = None,
    ) -> List[dict]:
        with self._lock:
            # Base set
            if role == "employee":
                tasks = self.tasks_for_user(requester_user_id)
            elif role == "manager":
                tasks = self.tasks_for_department(requester_department)
            else:
                # admin sees everything; but if assigned_employee filter is provided, only tasks for that user
                if assigned_employee is not None:
                    tasks = self.tasks_for_user(int(assigned_employee))
                else:
                    tasks = [dict(t) for t in self._tasks.values()]

            def matches(t: dict) -> bool:
                if status and t.get("status") != status:
                    return False
                if priority and t.get("priority") != priority:
                    return False
                if due_date and t.get("due_date") != due_date:
                    return False
                return True

            return [t for t in tasks if matches(t)]


store = MemoryStore()
