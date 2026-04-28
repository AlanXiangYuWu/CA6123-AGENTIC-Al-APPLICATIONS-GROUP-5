# CI/CD Pipelines

**Category**: devops
**Source**: GitHub Actions docs, Martin Fowler
**Use Case**: Architect/Coder Agent generates pipeline configs in deployment guide.

---

## 1. Overview

A **CI/CD pipeline** automates the journey from a developer's commit to a running deployment. The pipeline runs every time someone pushes code: it builds the artifact, runs the test suite, performs static analysis and security scans, and—depending on the configuration—deploys to staging or production. The goal is to make the path from code to production fast, reliable, and consistent, so that developers ship many small changes per day rather than batching them into infrequent risky releases.

The discipline that produces working CI/CD is older than the tooling. **Continuous Integration** was popularized by **Martin Fowler** and **Kent Beck** in the early 2000s, articulating a practice that small teams at companies like ThoughtWorks and the broader Extreme Programming community had been using for years. The original idea was simple: developers should integrate their work into a shared mainline frequently—at least daily—and an automated build should verify that integration on every commit. The value proposition is that integration bugs are caught hours after they are introduced, while the developer's context is fresh, rather than weeks later during a "merge week."

Modern CI/CD platforms—GitHub Actions, GitLab CI, CircleCI, Jenkins, Buildkite—operationalize the practice. The principles are the same as in 2002; the tooling makes them effortless to apply. This document covers the distinction between CI, Continuous Delivery, and Continuous Deployment; the major platforms; the standard pipeline stages; best practices; a complete GitHub Actions workflow for an educational coding app; deployment strategies (blue-green, canary, rolling); and the common pitfalls.

---

## 2. CI vs CD vs CDeploy

Three terms are often used loosely; the distinctions matter.

**Continuous Integration (CI).** Developers merge their work into the main branch frequently—at least daily, often many times a day. An automated build runs on every merge, verifying that the integrated code compiles, passes tests, and meets quality gates. CI is fundamentally about **integration discipline**: keeping the main branch in a known-good state at all times, so that any commit could in principle be released.

**Continuous Delivery (CD).** Builds that pass CI are automatically deployed to a staging environment, and the deployment to production is a manual decision—a single button click, triggered by a release manager or product owner when the change is ready to go live. Continuous Delivery means the system is always in a deployable state; the gate to production is human, not technical.

**Continuous Deployment.** Builds that pass CI go to production automatically, with no human gate. Every commit that passes the pipeline reaches users. Continuous Deployment requires substantial confidence in the pipeline (tests must catch regressions reliably) and substantial confidence in feature flagging and rollback capabilities (mistakes will reach production quickly and must be containable).

The terminology overlap—both Continuous Delivery and Continuous Deployment are abbreviated "CD"—causes regular confusion. When someone says "CI/CD," they usually mean Continuous Delivery; teams that practice full Continuous Deployment usually say so explicitly. The choice between Continuous Delivery and Continuous Deployment is partly a function of risk tolerance and partly a function of pipeline maturity. Most early-stage products start with Continuous Delivery and graduate to Continuous Deployment as confidence in the pipeline grows.

---

## 3. Major Platforms

| Platform | Strengths | Trade-offs |
|---|---|---|
| **GitHub Actions** | Native integration with GitHub repositories; very generous free tier for public and private repos; YAML-based workflow definitions; large marketplace of pre-built actions; rapidly evolving feature set. | Vendor-tied to GitHub. Self-hosted runners are supported but operationally heavier than fully managed runs. |
| **GitLab CI** | Bundled into GitLab itself; tight integration with GitLab issues, merge requests, and registry; YAML-based pipelines; well-suited for self-hosted GitLab instances. | Less natural for projects hosted on GitHub. Smaller marketplace than GitHub Actions. |
| **CircleCI** | Fast and reliable hosted runners; popular in open-source; YAML configuration with strong caching primitives; orbs (reusable config packages). | Pricing has historically been less generous than GitHub Actions for private repos at scale. |
| **Jenkins** | Mature, self-hosted, vast plugin ecosystem; full control over runners and execution environment; widely deployed in enterprise. | Operationally heavy: self-hosted, requires patching and scaling. Configuration via plugins can drift over time. |
| **Buildkite** | Hybrid model: cloud-hosted orchestration plus self-hosted runners. Useful when builds need access to internal networks or specialized hardware (GPUs, large caches). | More setup than fully managed platforms; pricing model targets larger teams. |

The practical default for most modern projects hosted on GitHub is **GitHub Actions**, because of its tight repo integration and zero setup cost. Teams already on GitLab use GitLab CI for the same reason. Jenkins remains the right choice for environments with strict self-hosting requirements (regulated industries, on-premises infrastructure) or with deeply customized build environments. CircleCI and Buildkite serve specific niches well but rarely beat GitHub Actions for new projects without a specific reason.

---

## 4. Pipeline Stages

A typical pipeline runs through a recognizable sequence of stages, each gating the next.

**1. Trigger.** What starts the pipeline. Common triggers: push to a branch, opening or updating a pull request, scheduled runs (nightly builds), manual invocation, or events from external systems.

**2. Build.** Compile the source, install dependencies, package the application. For containerized applications, this stage typically builds a Docker image. The build stage produces the artifact that downstream stages test and deploy.

**3. Test.** Run the test suite. Modern pipelines often split this into multiple parallel jobs: unit tests (fast, run first), integration tests (slower, requires a database or other services), end-to-end tests (slowest, runs against a deployed environment).

**4. Lint and static analysis.** Code formatting (Black, Prettier), linting (Ruff, ESLint), type checking (mypy, TypeScript), and other quality gates. These checks are fast and should run in parallel with—or even before—heavier test stages.

**5. Security scan.** Vulnerability scanning of dependencies (Snyk, Dependabot, npm audit) and container images (Trivy, Grype). Security scans typically run in parallel with tests.

**6. Deploy.** Push the artifact to the target environment. For Continuous Delivery, this stage targets staging by default and requires manual approval to advance to production. For Continuous Deployment, the stage targets production directly.

**7. Smoke test.** Lightweight verification that the deployed system is alive and serving traffic correctly. Health-check endpoints, sample API calls, and basic UI smoke tests run here. A failed smoke test triggers automatic rollback.

A few additional stages appear in mature pipelines: artifact publishing (to a container registry, package registry, or CDN), database migration, performance testing, and post-deployment notifications.

---

## 5. Best Practices

**Fail fast.** Run the cheapest, most likely-to-fail checks first. Lint runs before unit tests; unit tests run before integration tests; integration tests run before deployment. A pipeline that runs the slow tests last gives developers fast feedback on the simple failures and reserves the long wait for the cases where everything else has already passed.

**Cache dependencies.** Re-downloading and re-installing dependencies on every build wastes time. Modern CI platforms support caching keyed on dependency-manifest hashes (`requirements.txt`, `package-lock.json`, `Cargo.lock`). A well-cached pipeline takes seconds to install dependencies that would otherwise take minutes.

**Parallelize independent jobs.** Lint, type-check, unit tests, and security scans typically have no dependencies on each other. Running them as parallel jobs reduces wall-clock time substantially. Sequential execution is appropriate only when one stage genuinely depends on another's output.

**Separate workflows for PR and main.** Pull-request pipelines often run lighter checks (unit tests, lint) for fast feedback. Main-branch pipelines run heavier checks (full integration tests, deployment to staging, smoke tests) because they represent code that will ship.

**Secrets management.** Never commit secrets to source control. Use the platform's secrets store (GitHub Actions Secrets, GitLab CI Variables, etc.). Access secrets only in jobs that need them, and prefer short-lived credentials (OIDC-issued cloud credentials, ephemeral tokens) over long-lived API keys where possible.

**Pin tool versions.** A workflow that uses `actions/checkout@v4` is more reproducible than one that uses `actions/checkout@main`. Same for language versions, image tags, and container actions. Floating versions break workflows unpredictably when upstream changes.

**Make pipelines fast.** A 30-minute pipeline is a productivity tax that compounds across every developer on the team. Aim for a sub-10-minute main-branch pipeline; aim for a sub-5-minute PR pipeline. Optimization targets: caching, parallelization, sharding tests across multiple workers, and trimming slow tests that are not contributing proportional value.

**Make pipelines reproducible locally.** Developers should be able to run the same checks on their own machines that the pipeline runs in CI. Pipelines that succeed in CI but fail locally (or vice versa) are a sign of environment drift; tools like containers, devcontainers, or `make` targets aligned between local and CI close the gap.

---

## 6. Example: GitHub Actions Workflow for Educational Coding App for Kids

A complete GitHub Actions workflow for **CodeCub**, the educational coding app, covering lint, test, Docker image build, and deployment to staging:

```yaml
name: CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: "3.11"
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  lint:
    name: Lint and type-check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: "pip"

      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-dev.txt

      - name: Ruff (lint)
        run: ruff check .

      - name: Black (format check)
        run: black --check .

      - name: Mypy (type check)
        run: mypy app

  test:
    name: Test
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
          POSTGRES_DB: codecub_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: "pip"

      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-dev.txt

      - name: Run tests
        env:
          DATABASE_URL: postgresql://test_user:test_pass@localhost:5432/codecub_test
        run: pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: actions/upload-artifact@v4
        with:
          name: coverage
          path: coverage.xml

  security-scan:
    name: Security scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Trivy filesystem scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: fs
          severity: HIGH,CRITICAL
          exit-code: "1"

  build-image:
    name: Build Docker image
    needs: [lint, test, security-scan]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:main
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy-staging:
    name: Deploy to staging
    needs: build-image
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_DEPLOY_ROLE_ARN }}
          aws-region: us-east-1

      - name: Deploy to ECS staging
        run: |
          aws ecs update-service \
            --cluster codecub-staging \
            --service codecub-api \
            --force-new-deployment

      - name: Wait for service to stabilize
        run: |
          aws ecs wait services-stable \
            --cluster codecub-staging \
            --services codecub-api

      - name: Smoke test
        run: |
          curl --fail --retry 5 --retry-delay 10 \
            https://api-staging.codecub.example/health
```

Notes on this workflow:

- **Triggers run on every push to main and every pull request to main**, ensuring both PR feedback and main-branch deployment are covered.
- **Lint, test, and security-scan jobs run in parallel**, providing fast feedback. Each takes roughly 2–3 minutes; running them sequentially would triple the wall-clock time.
- **The test job uses a real PostgreSQL service container**, not a mock. Integration tests that hit a real database catch a class of bugs that mock-only tests miss.
- **Build, deploy, and smoke-test jobs run only on main**, after lint/test/security-scan all pass. PRs do not deploy.
- **The build job uses GitHub's container registry (GHCR)**, with images tagged by both commit SHA (immutable, traceable) and `main` (convenient mutable pointer for the latest main build).
- **Deployment uses OIDC-issued AWS credentials** (`role-to-assume`) rather than static API keys—a security best practice that eliminates long-lived credentials.
- **Smoke test verifies the deployed service responds to its health-check endpoint** before the workflow declares success.

A separate workflow (not shown) would handle production deployment, gated by manual approval (for Continuous Delivery) or triggered automatically on git tag (for Continuous Deployment). The principles are identical; the trigger and target environment differ.

---

## 7. Deployment Strategies

How a new version reaches production matters as much as how it is built. Three deployment strategies dominate.

**Blue-green deployment.** Two identical production environments exist: "blue" (currently serving traffic) and "green" (the new version). The pipeline deploys the new version to green and runs verification against it. When verification passes, traffic is switched from blue to green—typically at the load balancer or DNS layer. If a problem appears, the switch is reversed. Blue-green is conceptually simple, provides instant rollback, and works well for stateless services. The trade-offs are double infrastructure cost during the deployment and the difficulty of handling stateful services that cannot easily be cloned.

**Canary deployment.** The new version is deployed alongside the old, and a small percentage of traffic (1%, then 5%, then 25%) is routed to it. Metrics are observed at each percentage; if they look healthy, the percentage increases. If they degrade, traffic shifts back to the old version. Canary provides continuous validation under real production load and limits the blast radius of bad releases. The trade-offs are operational complexity—routing infrastructure, dual-version monitoring, careful metric design—and the need for both versions to coexist for the duration of the rollout.

**Rolling update.** Instances are replaced incrementally. In a service with ten instances, the deployment might replace them two at a time, waiting for each batch to become healthy before proceeding. Rolling update is the default in Kubernetes and most container orchestrators. It avoids the double-infrastructure cost of blue-green but does not provide instant rollback (a rolled-back rolling update is itself another rolling update). It works well for routine deployments where the new version is expected to be safe.

The choice depends on risk profile: rolling for routine deployments, canary for higher-risk changes (new features touching billing, new performance-sensitive paths), blue-green for major version cuts where instant rollback is essential. Many teams use rolling as the default and canary or blue-green for specific high-stakes releases.

---

## 8. Common Pitfalls

- **Slow pipelines.** A pipeline that takes 45 minutes to run is a productivity tax that compounds across every developer. Profile it, parallelize, cache, and trim slow tests until it runs in under 10 minutes for main and under 5 for PRs.
- **Flaky tests.** Tests that pass and fail intermittently train developers to retry until green, which masks real failures. Treat flakiness as a bug; quarantine flaky tests until they are fixed, do not normalize re-running.
- **Pipelines that work in CI but fail locally (or vice versa).** Environment drift between developer machines and CI runners produces hard-to-reproduce failures. Use containers or devcontainers to align the environments.
- **Secrets leaked through logs.** Build scripts that print environment variables, debug logs that include API keys, or error messages that expose tokens are a recurring source of credential leaks. Audit pipelines for secret-printing patterns; use platform secret-masking features.
- **No rollback plan.** A deployment pipeline that deploys but does not roll back leaves operators scrambling at 2 AM. Every deployment should have a documented, tested rollback path.
- **Coupling pipelines to a specific platform without abstraction.** Pipelines written deeply against GitHub Actions–specific syntax become hard to migrate. Where possible, push complex logic into scripts (`make`, `nox`, `Taskfile`) that can run anywhere.
- **Skipping security scans because they are slow or noisy.** Vulnerability scans surface real risks; turning them off because they fail too often is the wrong fix. Tune severity thresholds and exception lists rather than disabling the scan.
- **Manual steps disguised as automation.** A pipeline that "deploys" by sending a Slack notification asking someone to push a button has not solved the deployment problem. Either automate it or be honest that it is manual.
- **Pipelines that run on every commit without filtering paths.** A documentation-only change should not trigger a 20-minute test run. Use path filters to skip irrelevant pipelines.
- **Ignoring pipeline maintenance.** Dependencies in workflow files (`actions/checkout@v3` in 2026) become outdated. Treat the pipeline as code with the same maintenance discipline as the application.

---

## 9. References

- GitHub Actions documentation: https://docs.github.com/en/actions
- Martin Fowler — Continuous Integration: https://martinfowler.com/articles/continuousIntegration.html