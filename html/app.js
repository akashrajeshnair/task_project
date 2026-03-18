const API_BASE_URL = 'http://localhost:5000';
let authToken = localStorage.getItem('authToken') || '';

// Utility: safe query helper
function $id(id) {
    return document.getElementById(id);
}

function setText(id, text) {
    const el = $id(id);
    if (el) el.textContent = text;
}

// Display token if element exists
if ($id('token-display')) {
    setText('token-display', authToken || 'Not logged in');
}

// Helper function to display response
function displayResponse(data) {
    const out = $id('response-output');
    if (out) out.textContent = JSON.stringify(data, null, 2);
}

// Helper function to make API calls
async function apiCall(endpoint, method = 'GET', body = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        }
    };

    if (authToken) {
        options.headers['Authorization'] = `Bearer ${authToken}`;
    }

    if (body) {
        options.body = JSON.stringify(body);
    }

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        const data = await response.json();
        displayResponse(data);
        return data;
    } catch (error) {
        displayResponse({ error: error.message });
    }
}

// Only attach handlers if elements exist on the page
if ($id('register-form')) {
    $id('register-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {
            username: $id('reg-username').value,
            email: $id('reg-email').value,
            password: $id('reg-password').value,
            role: $id('reg-role').value,
            department: $id('reg-department').value
        };
        await apiCall('/auth/register', 'POST', data);
    });
}

if ($id('login-form')) {
    $id('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {
            username: $id('login-username').value,
            password: $id('login-password').value
        };
        const response = await apiCall('/auth/login', 'POST', data);
        if (response && response.token) {
            authToken = response.token;
            localStorage.setItem('authToken', authToken);
            if ($id('token-display')) setText('token-display', authToken);
        }
    });
}

if ($id('logout-btn')) {
    $id('logout-btn').addEventListener('click', () => {
        authToken = '';
        localStorage.removeItem('authToken');
        if ($id('token-display')) setText('token-display', 'Not logged in');
        displayResponse({ message: 'Logged out successfully' });
    });
}

// Projects
if ($id('create-project-form')) {
    $id('create-project-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {
            name: $id('project-name').value,
            description: $id('project-description').value
        };
        await apiCall('/project/create', 'POST', data);
    });
}

if ($id('list-projects-btn')) {
    $id('list-projects-btn').addEventListener('click', async () => {
        const data = await apiCall('/project/list', 'GET');
        if (data && data.projects && $id('projects-list')) {
            const projectsHtml = data.projects.map(p =>
                `<p><strong>ID:</strong> ${p.id} | <strong>Name:</strong> ${p.name} | <strong>Description:</strong> ${p.description}</p>`
            ).join('');
            $id('projects-list').innerHTML = projectsHtml;
        }
    });
}

if ($id('get-project-tasks-btn')) {
    $id('get-project-tasks-btn').addEventListener('click', async () => {
        const projectId = $id('project-id-tasks').value;
        const data = await apiCall(`/project/${projectId}/tasks`, 'GET');
        if (data && data.tasks && $id('project-tasks-list')) {
            const tasksHtml = data.tasks.map(t =>
                `<p><strong>ID:</strong> ${t.id} | <strong>Title:</strong> ${t.title} | <strong>Status:</strong> ${t.status} | <strong>Due:</strong> ${t.due_date}</p>`
            ).join('');
            $id('project-tasks-list').innerHTML = tasksHtml;
        }
    });
}

if ($id('update-project-form')) {
    $id('update-project-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const projectId = $id('update-project-id').value;
        const data = {};
        const name = $id('update-project-name').value;
        const description = $id('update-project-description').value;
        if (name) data.name = name;
        if (description) data.description = description;
        await apiCall(`/project/${projectId}`, 'PUT', data);
    });
}

if ($id('delete-project-btn')) {
    $id('delete-project-btn').addEventListener('click', async () => {
        const projectId = $id('delete-project-id').value;
        await apiCall(`/project/${projectId}/delete`, 'DELETE');
    });
}

// Tasks
if ($id('create-task-form')) {
    $id('create-task-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const assignedEmployees = $id('task-assigned-employees').value;
        const data = {
            title: $id('task-title').value,
            description: $id('task-description').value,
            priority: $id('task-priority').value,
            due_date: $id('task-due-date').value,
            status: $id('task-status').value,
            assigned_employees: assignedEmployees ? assignedEmployees.split(',').map(id => parseInt(id.trim())) : [],
            project_id: parseInt($id('task-project-id').value) || null,
            comments: $id('task-comments').value
        };
        await apiCall('/task/create-task', 'POST', data);
    });
}

if ($id('list-tasks-btn')) {
    $id('list-tasks-btn').addEventListener('click', async () => {
        const data = await apiCall('/task/list-tasks', 'GET');
        if (data && Array.isArray(data) && $id('tasks-list')) {
            const tasksHtml = data.map(t =>
                `<p><strong>ID:</strong> ${t.id} | <strong>Title:</strong> ${t.title} | <strong>Status:</strong> ${t.status} | <strong>Priority:</strong> ${t.priority}</p>`
            ).join('');
            $id('tasks-list').innerHTML = tasksHtml;
        }
    });
}

if ($id('view-task-btn')) {
    $id('view-task-btn').addEventListener('click', async () => {
        const taskId = $id('view-task-id').value;
        const data = await apiCall(`/task/view-task/${taskId}`, 'GET');
        if (data && $id('task-details')) {
            const detailsHtml = `
                <p><strong>ID:</strong> ${data.id}</p>
                <p><strong>Title:</strong> ${data.title}</p>
                <p><strong>Description:</strong> ${data.description}</p>
                <p><strong>Status:</strong> ${data.status}</p>
                <p><strong>Priority:</strong> ${data.priority}</p>
                <p><strong>Due Date:</strong> ${data.due_date}</p>
                <p><strong>Comments:</strong> ${data.comments}</p>
            `;
            $id('task-details').innerHTML = detailsHtml;
        }
    });
}

if ($id('filter-tasks-form')) {
    $id('filter-tasks-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {};
        const status = $id('filter-status').value;
        const priority = $id('filter-priority').value;
        const dueDate = $id('filter-due-date').value;
        const assignedEmployee = $id('filter-assigned-employee').value;

        if (status) data.status = status;
        if (priority) data.priority = priority;
        if (dueDate) data.due_date = dueDate;
        if (assignedEmployee) data.assigned_employee = parseInt(assignedEmployee);

        const result = await apiCall('/task/filter-tasks', 'POST', data);
        if (result && Array.isArray(result) && $id('filtered-tasks-list')) {
            const tasksHtml = result.map(t =>
                `<p><strong>ID:</strong> ${t.id} | <strong>Title:</strong> ${t.title} | <strong>Status:</strong> ${t.status} | <strong>Priority:</strong> ${t.priority}</p>`
            ).join('');
            $id('filtered-tasks-list').innerHTML = tasksHtml;
        }
    });
}

if ($id('update-task-form')) {
    $id('update-task-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const taskId = $id('update-task-id').value;
        const data = {};

        const title = $id('update-task-title').value;
        const description = $id('update-task-description').value;
        const priority = $id('update-task-priority').value;
        const dueDate = $id('update-task-due-date').value;
        const status = $id('update-task-status').value;
        const assignedEmployees = $id('update-task-assigned-employees').value;
        const comments = $id('update-task-comments').value;

        if (title) data.title = title;
        if (description) data.description = description;
        if (priority) data.priority = priority;
        if (dueDate) data.due_date = dueDate;
        if (status) data.status = status;
        if (assignedEmployees) data.assigned_employees = assignedEmployees.split(',').map(id => parseInt(id.trim()));
        if (comments) data.comments = comments;

        await apiCall(`/task/update-task/${taskId}`, 'PUT', data);
    });
}

if ($id('delete-task-btn')) {
    $id('delete-task-btn').addEventListener('click', async () => {
        const taskId = $id('delete-task-id').value;
        await apiCall(`/task/delete-task/${taskId}`, 'DELETE');
    });
}
