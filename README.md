# task_project

Flask app (now using **in-memory** storage; no database required).

## Docker Compose

```sh
docker compose up --build
```

## Jenkins Pipeline

This repo includes a `Jenkinsfile` that builds the Docker image and runs the container on port 5000.

Notes:
- Your Jenkins agent must have Docker installed and permission to run Docker (often by adding the `jenkins` user to the `docker` group).
- The pipeline removes any previous container named `task-project-app` to avoid port conflicts.
- Since storage is in-memory, data resets whenever the container restarts.
# task_project
