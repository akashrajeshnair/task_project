from flask import Flask, send_from_directory
from flask_cors import CORS
from api.authentication import auth_bp
from api.tasks import task_bp
from api.projects import project_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(auth_bp)
app.register_blueprint(task_bp)
app.register_blueprint(project_bp)

@app.route('/')
def serve_index():
    return send_from_directory('html', 'index.html')

@app.route('/<path:path>')
def serve_static_files(path):
    return send_from_directory('html', path)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
