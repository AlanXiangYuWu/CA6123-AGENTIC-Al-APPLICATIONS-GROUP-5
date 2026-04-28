# Docker and Containerization Basics

**Category**: devops
**Source**: Docker official docs
**Use Case**: Coder Agent uses this when generating deployment configs.

---

## 1. Overview

**Docker** is a platform for building and running containerized applications. It was released in 2013 by **Solomon Hykes** and **Docker Inc.** and quickly became the de facto standard for application packaging across modern software development. Docker did not invent containers—Linux had containerization primitives (namespaces, cgroups) for years before Docker arrived—but it produced the developer experience that made containers practical: a simple way to define an application's runtime environment as code, build it into a portable image, and run it identically on any machine that supports Docker.

The central value proposition of Docker is **runtime portability**. A containerized application carries its own dependencies, configuration, and runtime requirements. The same container that runs on a developer's laptop runs identically in CI, staging, and production. The class of bugs caused by "works on my machine" mismatches—different Python versions, different system libraries, missing packages—largely disappears. This portability is also the foundation of every modern orchestration system: Kubernetes, ECS, Cloud Run, and Nomad all schedule containers, not raw processes.

This document covers the difference between containers and virtual machines, Docker's core concepts, the structure of a Dockerfile, multi-stage builds for smaller production images, Docker Compose for multi-container application development, a complete Dockerfile for a FastAPI backend, and the best practices and pitfalls that distinguish production-quality Docker usage from naive usage.

---

## 2. Container vs Virtual Machine

Containers and virtual machines (VMs) both isolate workloads, but they do so at fundamentally different layers of the stack.

A **virtual machine** virtualizes the hardware. Each VM runs a complete operating system—kernel, system libraries, and all—on top of a hypervisor that emulates physical hardware. VMs are strongly isolated from each other and from the host, but they are heavy: each VM image is gigabytes, boot times are tens of seconds to minutes, and running many VMs on a single host consumes substantial memory because each duplicates an entire OS.

A **container** virtualizes the operating system. Containers share the host's kernel and isolate only the userspace—filesystem, processes, network, and so on—using kernel features like namespaces and control groups (cgroups). The container image contains only the application and its dependencies, not a full OS. Container images are typically tens to hundreds of megabytes, containers start in milliseconds to seconds, and a single host can comfortably run hundreds of containers because they share the underlying kernel.

The trade-off: containers are lighter and faster but provide weaker isolation than VMs. For trusted application code, this trade-off favors containers strongly. For running untrusted code (multi-tenant code execution, isolating malicious workloads), VMs or specialized container-on-VM solutions (Firecracker, Kata Containers, gVisor) provide stronger guarantees.

For modern application deployment—web services, APIs, background workers, batch jobs—containers are the dominant choice, and VMs serve as the underlying substrate that hosts container clusters rather than as the primary unit of deployment.

---

## 3. Core Concepts

Five concepts cover most Docker usage.

**Image.** A read-only template that contains everything needed to run an application: code, runtime, system libraries, environment variables, and configuration. An image is a recipe; it does not run by itself. Images are built from Dockerfiles and stored in registries.

**Container.** A running instance of an image. Containers can be started, stopped, paused, and destroyed, and many containers can run from the same image. Each container has its own writable filesystem layer on top of the read-only image, its own process tree, and its own network namespace.

**Dockerfile.** A text file with instructions for building an image. Each instruction (FROM, COPY, RUN, etc.) creates a new layer in the resulting image. Dockerfiles are checked into source control alongside the application code; the image is reproducible from the Dockerfile.

**Registry.** A service that stores and distributes images. **Docker Hub** is the public default; private registries include **GitHub Container Registry (GHCR)**, **AWS Elastic Container Registry (ECR)**, **Google Artifact Registry**, and self-hosted options like Harbor. Registries support image versioning through tags (`my-app:1.4.2`, `my-app:latest`).

**Volume.** Persistent storage that outlives the container. Containers themselves are ephemeral—any data written inside a container's filesystem is lost when the container is removed. Volumes attach to specific paths inside the container and persist data across container restarts and replacements. Databases, file uploads, and any other stateful data must use volumes.

A few additional concepts worth knowing: **networks** (Docker creates virtual networks that connect containers), **labels** (metadata attached to images and containers for orchestration), and **build context** (the set of files Docker has access to during a build, defined by the directory passed to `docker build`).

---

## 4. Dockerfile Anatomy

A Dockerfile is a sequence of instructions. Each instruction adds a layer to the resulting image. A simple example for a FastAPI Python application:

```dockerfile
# Use an official Python base image with a specific version
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy dependency manifest first, so dependency installation
# can be cached separately from application code changes
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Document which port the application listens on
EXPOSE 8000

# Specify the default command when the container starts
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Key instructions:

- **`FROM`**: the base image. Always pin to a specific version (`python:3.11-slim`, not `python:latest`) so that builds are reproducible.
- **`WORKDIR`**: sets the working directory for subsequent instructions and for the running container.
- **`COPY`**: copies files from the build context into the image.
- **`RUN`**: executes a command during the build (typically installing packages).
- **`EXPOSE`**: documents which port the application listens on. It does not actually publish the port; that happens at runtime.
- **`CMD`**: the command that runs when the container starts. Use the JSON-array form (`["cmd", "arg1", "arg2"]`) rather than the shell form to avoid shell-related signal-handling issues.
- **`ENTRYPOINT`** (not shown): an alternative to `CMD` that produces a container with a fixed entry point and configurable arguments.

**Layer caching is central to fast builds.** Docker caches each instruction's result; if nothing the instruction depends on has changed, Docker reuses the cached layer. The convention is to order the Dockerfile from **least-frequently-changed to most-frequently-changed**: copy `requirements.txt` and install dependencies before copying the application code, so that changes to application code do not invalidate the dependency-installation layer.

---

## 5. Multi-stage Builds

Production images often need to be much smaller than build images. Build images contain compilers, dev tools, and intermediate artifacts; production images need only the runtime and the compiled application. **Multi-stage builds** solve this by defining multiple `FROM` stages in a single Dockerfile, with the final image copying only the necessary artifacts from earlier stages.

A simplified Node.js example:

```dockerfile
# Stage 1: build the application
FROM node:20 AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: production image with only the build output and runtime deps
FROM node:20-slim
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY package.json .
EXPOSE 3000
USER node
CMD ["node", "dist/server.js"]
```

The final image contains only the production-runtime files; the full Node.js dev environment, source code, build tools, and intermediate files are discarded with the builder stage. Image sizes typically shrink by 50–80% with multi-stage builds.

The pattern applies to any language with a build step (Go, Rust, TypeScript, Java) and to any language where production images can omit dev tooling (most of them).

---

## 6. Docker Compose for Multi-container Apps

Modern applications rarely consist of a single container. A typical web application has at least an application container, a database container, and often a cache (Redis), a message broker, or other services. Running each container manually with `docker run` is tedious and error-prone. **Docker Compose** solves this by defining the entire application stack in a single YAML file and managing it as a unit.

A `docker-compose.yml` for a Python+PostgreSQL application:

```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://app_user:app_pass@db:5432/codecub
      REDIS_URL: redis://cache:6379/0
    depends_on:
      - db
      - cache
    volumes:
      - ./app:/app

  db:
    image: postgres:16
    environment:
      POSTGRES_DB: codecub
      POSTGRES_USER: app_user
      POSTGRES_PASSWORD: app_pass
    volumes:
      - db_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  cache:
    image: redis:7-alpine
    volumes:
      - cache_data:/data

volumes:
  db_data:
  cache_data:
```

A single command starts the whole stack:

```bash
docker-compose up
```

Compose handles networking automatically: the `app` container can reach the database at the hostname `db` and Redis at `cache`, because Compose creates a default network and registers each service by name. Volumes (`db_data`, `cache_data`) persist data across `docker-compose down` and `docker-compose up` cycles.

Compose is excellent for **local development** and **integration testing**. For production, container orchestration platforms (Kubernetes, ECS, Cloud Run) replace Compose with their own service-definition formats. The mental model carries over: services, images, environment variables, networking, and volumes are common across all of these systems.

---

## 7. Example: Dockerfile for Educational Coding App for Kids

A complete, production-ready Dockerfile for the **CodeCub** FastAPI backend, including multi-stage build, non-root user, and the disciplines covered above:

```dockerfile
# syntax=docker/dockerfile:1

###############################################################
# Stage 1: builder — install dependencies into a virtual env
###############################################################
FROM python:3.11-slim AS builder

# Prevent Python from buffering stdout/stderr (better logs)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build-time system dependencies
RUN apt-get update \
    && apt-get install --no-install-recommends -y build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Create a virtual environment for clean copy into the final stage
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies first (cached unless requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

###############################################################
# Stage 2: runtime — minimal final image
###############################################################
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Install runtime-only system dependencies (libpq for PostgreSQL connections)
RUN apt-get update \
    && apt-get install --no-install-recommends -y libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Create a non-root user to run the application
RUN groupadd --system app && useradd --system --gid app --home /app app

WORKDIR /app

# Copy application source (after dependencies, so dep layers are cached)
COPY --chown=app:app . .

# Drop root privileges
USER app

# Document the listening port (informational; runtime publishes the port)
EXPOSE 8000

# Healthcheck for orchestrators
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

# Start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Notable disciplines applied:

- **Multi-stage build.** Build-time dependencies (`build-essential`, `libpq-dev`) are confined to the builder stage; the runtime image carries only `libpq5`. Image size is reduced substantially.
- **Pinned base image.** `python:3.11-slim` rather than `python:latest`. The `slim` variant is smaller than the default and adequate for most Python applications.
- **Layer ordering.** Dependencies install before application code copies, so application changes do not invalidate the dependency layer.
- **Non-root user.** The final `USER app` directive drops root privileges. Containers running as root are a security concern; the discipline is to drop privileges in every production image.
- **Healthcheck.** Orchestrators use the healthcheck to detect failed instances and restart them. The check assumes the application exposes a `/health` endpoint that returns 200 when healthy.
- **No secrets in the image.** Database URLs, API keys, and other secrets are passed as environment variables at runtime, not baked into the image.

A companion `.dockerignore` file prevents unwanted files from being copied into the build context:

```
__pycache__
*.pyc
*.pyo
.git
.venv
venv
node_modules
*.egg-info
.pytest_cache
.env
.env.*
.coverage
*.log
```

Without `.dockerignore`, the entire repository (including `.git`, `node_modules`, and local `.env` files) gets copied into the build context, slowing builds and risking secret leakage into images.

---

## 8. Best Practices and Pitfalls

**Best practices:**

- **Use specific base image versions, not `latest`.** `python:3.11-slim` is reproducible; `python:latest` changes underneath you and can break builds without warning.
- **Add a `.dockerignore`.** Prevents unwanted files from polluting the build context. The single most-forgotten file in Docker projects.
- **Use multi-stage builds for languages with a build step.** Production images should not contain compilers or dev tooling.
- **Order Dockerfile instructions from least- to most-frequently-changed.** Maximizes layer-cache hit rates during development.
- **Don't run as root.** Add a `USER` directive in production images. Many orchestration platforms now require this for compliance.
- **Don't bake secrets into images.** Use environment variables, secret-management services, or runtime injection. Secrets in image layers persist forever, even if removed in later layers.
- **Pin dependency versions.** A `requirements.txt` with `fastapi>=0.100` produces non-reproducible builds. Pin exact versions or use a lock file.
- **Set `PYTHONUNBUFFERED=1` (Python) and equivalent for other languages.** Buffered stdout causes log loss when containers terminate.
- **Add a healthcheck.** Orchestrators rely on it; without one, dead instances stay in the load-balancer pool.

**Common pitfalls:**

- **Bloated images.** Forgetting `--no-install-recommends`, leaving build tools in the final stage, copying unnecessary files. Aim for the smallest production image consistent with the application's needs.
- **Secrets in image layers.** Even if the secret is removed in a later layer, it remains in the previous layer and is visible to anyone who pulls the image.
- **Mutable `latest` tag in production.** A deployment that pulls `my-app:latest` does not know which version it ran; rollback becomes guesswork. Always tag with immutable identifiers (commit SHAs or semantic versions).
- **Ignoring `.dockerignore`.** Leaks `node_modules`, `.git`, local databases, and `.env` files into the image; bloats the build context; risks secret exposure.
- **Running development workloads in containers identical to production.** Development typically benefits from hot reload, volume-mounted source, and verbose logging that production does not. Compose overrides or separate development Dockerfiles are appropriate.
- **Forgetting volume permissions.** When running as a non-root user, volumes mounted from the host may have permissions that the in-container user cannot write. Plan for this in production deployments.
- **Treating containers as VMs.** Long-running shell sessions inside containers, manual changes to running containers, persistent data inside container filesystems—all anti-patterns. Containers are designed to be ephemeral and reproducible from images.
- **Ignoring image vulnerability scanning.** Base images and dependencies accumulate CVEs over time. Scan images periodically (Trivy, Grype, Snyk) and refresh base images on a regular cadence.

---

## 9. References

- Docker — Get Started: https://docs.docker.com/get-started/
- Docker — What is a Container: https://www.docker.com/resources/what-container/