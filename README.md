# Smart URL Shortener with Click Analytics (AWS Serverless)

A beginner-friendly AWS project using AWS SAM, Lambda, API Gateway, DynamoDB and GitHub Actions.

## What it does

- Creates a short code for a valid HTTP/HTTPS URL.
- Redirects visitors from `/{code}` to the original URL.
- Counts each successful redirect in DynamoDB.
- Returns click analytics from `/stats/{code}`.
- Deploys separate AWS stacks for `dev`, `staging`, and `prod`.

## Project structure

```text
smart-url-shortener-aws/
├── .github/
│   └── workflows/
│       └── deploy.yml
├── backend/
│   ├── app.py
│   └── requirements.txt
├── frontend/
│   └── index.html
├── tests/
│   └── test_app.py
├── template.yaml
├── samconfig.toml
└── README.md
```

## 1. Requirements

Install:
- Git
- Python 3.12
- AWS CLI
- AWS SAM CLI
- VS Code

Configure AWS CLI locally with an IAM user/role that has permission to deploy CloudFormation, Lambda, API Gateway, DynamoDB and IAM resources:

```powershell
aws configure
aws sts get-caller-identity
sam --version
```

Never put AWS access keys in source code or commit them to Git.

## 2. Run tests locally

Open the project folder in VS Code, then in its terminal:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
pip install pytest
$env:PYTHONPATH="backend"
pytest -q
```

If PowerShell blocks activation, run:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

## 3. Deploy manually to AWS (first test)

From the project root:

```powershell
sam build --template-file template.yaml
sam deploy --guided
```

Use a stack name such as `smart-url-shortener-dev`, region `ap-south-1`, and allow SAM to create the required IAM role. The template has an `Environment` parameter; for repeatable deployment use:

```powershell
sam deploy --stack-name smart-url-shortener-dev --resolve-s3 --region ap-south-1 --capabilities CAPABILITY_IAM --no-confirm-changeset --parameter-overrides Environment=dev
```

After deployment, find the `ApiUrl` output:

```powershell
aws cloudformation describe-stacks --stack-name smart-url-shortener-dev --query "Stacks[0].Outputs" --output table
```

## 4. Connect the frontend

Open `frontend/index.html`. Replace:

```javascript
const API_BASE_URL = "PASTE_API_GATEWAY_URL_HERE".replace(/\/$/, "");
```

with the deployed `ApiUrl` value, including its trailing `/` or without it. Example format:

```javascript
const API_BASE_URL = "https://xxxxxxxxxx.execute-api.ap-south-1.amazonaws.com/Prod".replace(/\/$/, "");
```

Open `frontend/index.html` in a browser (or use VS Code Live Server). Create a URL, open the short link, then select **View analytics**. The short link opens the API Gateway redirect endpoint.

Note: the frontend is a simple static page for learning. It is not hosted by AWS in this starter project.

## 5. Configure GitHub Actions CI/CD

Create a GitHub repository and push this project. Create these branches:

- `dev` → deploys stack `smart-url-shortener-dev`
- `staging` → deploys stack `smart-url-shortener-staging`
- `main` → deploys stack `smart-url-shortener-prod`

In GitHub, open **Settings → Secrets and variables → Actions**.

Add repository secrets:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

Add repository variable:
- `AWS_REGION` = `ap-south-1`

Use an IAM identity dedicated to CI/CD with least-privilege permissions. For a real production setup, prefer GitHub OIDC role assumption over long-lived access keys.

The workflow runs tests on pushes and pull requests. It deploys only after tests pass and only for pushes/manual runs on the three deployment branches. Each branch gets its own CloudFormation stack and DynamoDB table.

## 6. Git commands

If this is a new GitHub repository:

```powershell
git init
git add .
git commit -m "Initial Smart URL Shortener project"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main

git checkout -b dev
git push -u origin dev

git checkout main
git checkout -b staging
git push -u origin staging
```

For later changes:

```powershell
git add .
git commit -m "Add URL shortener feature"
git push
```

## 7. API endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/shorten` | Create a short URL |
| GET | `/{code}` | Redirect to original URL and increment clicks |
| GET | `/stats/{code}` | Read click analytics |

Example request:

```json
{
  "url": "https://www.example.com/some/long/page"
}
```

## Important

- AWS resources may incur charges. DynamoDB uses on-demand billing; API Gateway, Lambda and other AWS services have usage-based pricing and free-tier eligibility varies.
- Delete test stacks when finished if you do not need them:
  `aws cloudformation delete-stack --stack-name smart-url-shortener-dev`
- Do not delete a stack containing data you want to keep.
- This is a learning project, not a production-hardened public URL service. Before production use, add rate limiting, abuse prevention, URL safety checks, custom domain/HTTPS configuration, monitoring and stronger access controls.
