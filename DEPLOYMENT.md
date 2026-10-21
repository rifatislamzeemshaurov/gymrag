# GymRAG — Deployment Guide

Everything needed to run GymRAG on AWS: one command to deploy, one to attach a domain, one to tear down. For what the product does, see the [README](README.md).

---

## 1. Overview

```
Browser ──HTTPS──► CloudFront ──┬── /            ──► S3 (static Next.js frontend)
  (custom domain optional)      └── /chat /upload ──► ALB ──► ECS Fargate (FastAPI agent)
                                                                 ├──► Qdrant  (supplement catalog)
                                                                 ├──► OpenAI  (chat + embeddings)
                                                                 └──► S3      (conversation memory)
```

The frontend and API share one CloudFront domain. The load balancer accepts traffic **only** from CloudFront.

---

## 2. One-time prerequisites

| Tool | Check it's installed |
|---|---|
| AWS CLI v2 | `aws --version` and `aws sts get-caller-identity` |
| Terraform ≥ 1.0 | `terraform -version` |
| Docker (running) | `docker info` |
| Node.js 20+ and npm | `node -v` |
| Python 3.12 + uv (for ingestion) | `uv --version` |

**AWS permissions.** The deploying identity needs to create and manage S3, ECR, ECS, Elastic Load Balancing, EC2 security groups, IAM roles, CloudWatch Logs and CloudFront. For a custom domain it also needs Route 53 and ACM. An administrator account is simplest for a first deploy.

**Region notes.** Everything is deployed to `AWS_REGION` (default `ap-south-1`), except the custom-domain certificate, which CloudFront requires in `us-east-1` (Terraform handles this automatically). The stack uses the region's **default VPC**. If you deleted it, recreate it with `aws ec2 create-default-vpc`.

**Vector database.** Create a free cluster at [cloud.qdrant.io](https://cloud.qdrant.io), copy its URL and API key, and load the catalog into it once (section 3).

---

## 3. Configure before deploying

**Secrets file.** From the project root:

```bash
cp .env.example .env
```

Fill in at least `OPENAI_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY` and `API_KEY_UI` (any long random string, for example `openssl rand -hex 24`). Leave the AWS keys empty to use your `aws configure` profile. `.env` is gitignored and never leaves your machine; the deploy script passes its values to Terraform as environment variables.

**Customer data.** The catalog is the PDFs in `data/`. Load them into Qdrant once, and again whenever they change:

```bash
cd backend && uv sync && cd ../ingestion
uv run --project ../backend --with jupyterlab jupyter lab rag_pipeline.ipynb   # run all cells
```

The notebook prints `Ingestion complete: 100/100 documents` for the sample catalog. See [`ingestion/ingest.md`](ingestion/ingest.md) to use your own PDFs.

---

## 4. Deploy: one command

```bash
./scripts/deploy.sh dev                      # macOS / Linux / Git Bash
```
```powershell
.\scripts\deploy.ps1 -Environment dev        # Windows PowerShell
```

Use `dev`, `test` or `prod`. Each is a separate Terraform workspace with its own resources.

**What the script does**

1. Loads `.env`, verifies the AWS credentials (and `AWS_ACCOUNT_ID` if set) and checks that Docker is running.
2. Selects or creates the Terraform workspace for the environment.
3. Creates the ECR repository, then builds the API image and pushes it with a timestamp tag.
4. Applies the full Terraform stack. A new ECS task definition that points at the new image rolls the service forward.
5. Waits until the new container passes the load balancer health checks.
6. Builds the frontend against the app's public URL, uploads it to S3 and invalidates the CloudFront cache.
7. Prints the URLs.

**How long.** The first deploy takes several minutes; CloudFront distribution creation is the slow part. Later deploys are faster.

**Output.** The script ends with a summary like:

```
Deployment complete!
App URL        : https://<distribution-id>.cloudfront.net
Custom domain  : https://gym.example.com          (only when a domain is attached)
ECS cluster    : gymrag-dev-cluster
ECS service    : gymrag-dev-api
Image deployed : <account>.dkr.ecr.<region>.amazonaws.com/gymrag-dev-api:<timestamp>
```

**Resources created** (`<env>` = dev / test / prod, `<account>` = your AWS account ID)

| Resource | Name |
|---|---|
| S3 bucket: frontend | `gymrag-<env>-frontend-<account>` |
| S3 bucket: conversation memory (private) | `gymrag-<env>-memory-<account>` |
| ECR repository | `gymrag-<env>-api` |
| ECS cluster | `gymrag-<env>-cluster` |
| ECS service and task definition | `gymrag-<env>-api` |
| CloudWatch log group | `/ecs/gymrag-<env>-api` |
| Application Load Balancer | `gymrag-<env>-alb` |
| Target group | `gymrag-<env>-api-tg` |
| Security groups | `gymrag-<env>-alb-sg`, `gymrag-<env>-ecs-sg` |
| IAM roles | `gymrag-<env>-ecs-execution-role`, `gymrag-<env>-ecs-task-role` |
| IAM inline policy (S3 memory access only) | `gymrag-<env>-ecs-task-s3-memory` |
| CloudFront distribution | tagged `Project=gymrag`, `Environment=<env>` |
| CloudFront function (custom domain only) | `gymrag-<env>-host-guard` |
| ACM certificate + Route 53 records (custom domain only) | for your domain |

---

## 5. Destroy: one command

```bash
./scripts/destroy.sh dev
```
```powershell
.\scripts\destroy.ps1 -Environment dev
```

The script empties both S3 buckets, then runs `terraform destroy` for that environment: the ECS service, load balancer, CloudFront distribution, ECR repository (including images), IAM roles, log group and any domain records and certificate it created. Your Route 53 hosted zone, your Qdrant cluster and your `.env` are never touched.

To also remove the empty Terraform workspace afterwards:

```bash
cd terraform
terraform workspace select default
terraform workspace delete dev
```

---

## 6. Custom domain: one command

```bash
./scripts/deploy.sh prod gym.example.com
```
```powershell
.\scripts\deploy.ps1 -Environment prod -Domain gym.example.com
```

- **Subdomain** (`gym.example.com`) or **apex** (`example.com`): both work. The script finds the public Route 53 hosted zone that owns the name, using the most specific zone if you have several.

**What happens automatically**

| Step | Done by |
|---|---|
| Find the hosted zone, split it into zone + subdomain | deploy script |
| Save `USE_CUSTOM_DOMAIN`, `DOMAIN_NAME`, `APP_SUBDOMAIN` to `.env` | deploy script |
| Request a free TLS certificate in `us-east-1` | Terraform (ACM) |
| Create the DNS validation records and wait for issuance | Terraform (Route 53 + ACM) |
| Attach the domain and certificate to CloudFront | Terraform |
| Create `A` and `AAAA` alias records to CloudFront | Terraform (Route 53) |
| 301-redirect the raw `*.cloudfront.net` address to your domain | Terraform (CloudFront Function) |
| Build the frontend against the custom domain | deploy script |

**Redeploys keep the domain.** It's saved in `.env`, so a plain `./scripts/deploy.sh prod` keeps serving on it.

**Detach it:**

```bash
./scripts/deploy.sh prod none
```

**A domain can only be attached to one environment at a time.** Use different names per environment (for example `gym.example.com` for prod and `gym-dev.example.com` for dev), and remember that `.env` holds the most recent choice.

**Domain bought elsewhere** (GoDaddy, Namecheap, Cloudflare Registrar…). One-time setup:

1. In Route 53, choose **Create hosted zone** and enter your domain (for example `example.com`) as a public zone.
2. Copy the four `NS` name servers it shows.
3. At your registrar, replace the domain's name servers with those four.
4. Wait for DNS to propagate (usually under an hour, up to 48 hours). `nslookup -type=NS example.com` should show the AWS servers.

> ⚠️ **Move your existing records first.** Changing name servers moves *all* DNS for the domain to Route 53. Recreate your existing records, especially **MX** (email), **TXT/SPF/DKIM** and any website records, in the new hosted zone *before* switching. Otherwise email and other services on the domain stop working.

**Cost.** The certificate is free. A Route 53 hosted zone is about $0.50 per month, plus a few cents for DNS queries.

---

## 7. Configuration reference

| Variable | Default | Where it is set |
|---|---|---|
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | empty (use the AWS CLI profile) | `.env` |
| `AWS_REGION` | `ap-south-1` | `.env` |
| `AWS_ACCOUNT_ID` | empty (no check) | `.env` |
| `PROJECT_NAME` | `gymrag` | `.env` → resource prefix |
| `USE_CUSTOM_DOMAIN` | `false` | `.env`, or set by `deploy … <domain>` |
| `DOMAIN_NAME` | `example.com` | `.env`, or set by `deploy … <domain>` |
| `APP_SUBDOMAIN` | `gym` (empty = apex) | `.env`, or set by `deploy … <domain>` |
| `CONTAINER_CPU` | `512` (0.5 vCPU) | `.env` → `TF_VAR_container_cpu` |
| `CONTAINER_MEMORY` | `1024` MiB | `.env` → `TF_VAR_container_memory` |
| `DESIRED_COUNT` | `1` | `.env` → `TF_VAR_desired_count` |
| `OPENAI_API_KEY` | (required) | `.env` → `TF_VAR_openai_api_key` |
| `OPENAI_MODEL` | `gpt-4o-mini` | `.env` → `TF_VAR_openai_model` |
| `QDRANT_URL` / `QDRANT_API_KEY` | (required) | `.env` → `TF_VAR_qdrant_url` / `TF_VAR_qdrant_api_key` |
| `API_KEY_UI` | (required) | `.env` → `TF_VAR_api_key` and the frontend build |
| `CORS_ORIGINS` | `http://localhost:3000` | `.env` (local only; set by Terraform in AWS) |
| `USE_S3` / `S3_BUCKET` | `false` / empty | `.env` (local only; set by Terraform in AWS) |
| `MEMORY_DIR` | `../memory` | `.env` (local only) |
| `NEXT_PUBLIC_API_URL` / `NEXT_PUBLIC_API_KEY` | `http://localhost:8000` | `frontend/.env.development` (local); generated on deploy |

---

## 8. Troubleshooting

**`.env not found - copy .env.example to .env and fill in the values.`**
Run the script from the project folder after creating `.env` (section 3).

**`Docker doesn't seem to be running.`**
Start Docker Desktop (or `dockerd`), wait until it's ready, and re-run.

**`AWS credentials were rejected`**
The keys in `.env` (or your CLI profile) are wrong or expired. Test with `aws sts get-caller-identity`.

**`AWS account mismatch: credentials belong to … but .env sets AWS_ACCOUNT_ID=…`**
You're signed in to a different account than intended. Switch profiles, or fix `AWS_ACCOUNT_ID`.

**`OPENAI_API_KEY in .env looks unset or a placeholder.`** / **`QDRANT_URL / QDRANT_API_KEY not set`** / **`API_KEY_UI not set`**
Fill in the named value in `.env`.

**`No public Route 53 hosted zone found for <domain>`**
Create the hosted zone first and point your registrar at it (section 6).

**`CNAMEAlreadyExists` during apply**
That hostname is already attached to another CloudFront distribution, often another environment. Use a different subdomain, or detach it there with `deploy … none`.

**Apply waits a long time at `aws_acm_certificate_validation`**
The domain's name servers don't point to Route 53 yet. Check with `nslookup -type=NS <domain>` and finish section 6.

**`ECS service did not reach a stable state`**
The container failed to start or failed health checks. Check the logs:
`aws logs tail /ecs/gymrag-<env>-api --since 30m`

**The app loads, but every answer is "The advisor is temporarily unavailable…"**
The API can't reach the catalog or OpenAI. Check the same logs. The most common causes are a wrong `QDRANT_URL` or key, or a collection that was never ingested into that cluster (run the notebook against it).

**Windows: `running scripts is disabled on this system`**
Allow scripts for the current session only: `Set-ExecutionPolicy -Scope Process Bypass`, then run the script again.

**macOS / Linux: `Permission denied` on a script**
`chmod +x scripts/*.sh`

**`Error: Workspace '<env>' does not exist` on destroy**
Nothing was deployed to that environment, so there's nothing to destroy.

---

## 9. Cost notes

Approximate on-demand prices in `ap-south-1` for one environment with light traffic. Check the AWS pricing pages for your region.

| Resource | Approx. monthly cost |
|---|---|
| ECS Fargate (0.5 vCPU, 1 GB, always on) | ~$19 |
| Application Load Balancer | ~$18 + usage |
| CloudFront, S3, ECR, CloudWatch Logs | < $2 at low traffic |
| Route 53 hosted zone (custom domain only) | $0.50 |
| ACM certificate | free |
| Qdrant Cloud | free tier is enough for the sample catalog |
| OpenAI (`gpt-4o-mini` + embeddings) | pay per use; a fraction of a cent per chat |
| **Total per environment** | **about $40 per month + OpenAI usage** |

**Biggest saving:** destroy `dev` and `test` when you're not using them (`./scripts/destroy.sh dev`). The load balancer and Fargate task cost the same whether or not anyone is chatting, and redeploying takes one command.
