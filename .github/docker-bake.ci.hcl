# CI-only overlay for `docker buildx bake -f docker-compose.yml -f this`.
# Adds a GitHub Actions layer cache to the targets compose already defines, so
# the build stays a real `docker compose` build and the dev path is untouched.
target "backend" {
  cache-from = ["type=gha,scope=backend"]
  cache-to   = ["type=gha,scope=backend,mode=max"]
}

target "agent" {
  cache-from = ["type=gha,scope=agent"]
  cache-to   = ["type=gha,scope=agent,mode=max"]
}

target "frontend" {
  cache-from = ["type=gha,scope=frontend"]
  cache-to   = ["type=gha,scope=frontend,mode=max"]
}
