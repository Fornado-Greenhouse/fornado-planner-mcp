# Azure-Native Deployment Plan

## Overview

This plan deploys the Microsoft Planner MCP Server entirely within the Azure ecosystem, providing seamless integration with Azure AD OAuth and Microsoft Graph API while using Azure-native security and monitoring tools.

**Why Azure-Native:**
- ✅ Single cloud vendor (Microsoft/Azure for everything)
- ✅ Better integration with Azure AD and Graph API (same Azure regions, lower latency)
- ✅ Native security tools (Defender for Cloud, Sentinel, Policy)
- ✅ Unified monitoring (Application Insights + Azure Monitor)
- ✅ Simplified compliance (all data stays in Microsoft cloud)
- ✅ Easier billing and cost management (single invoice)
- ✅ Built-in Azure AD integration

**Complete Azure Architecture:**
```
┌──────────────────────────────────────────────────────────────────┐
│                      Azure Subscription                           │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Azure AD (Identity)                                       │  │
│  │  - OAuth 2.0 Authorization Server                          │  │
│  │  - User Authentication                                     │  │
│  │  - Token Issuance                                          │  │
│  └─────────────────────────┬──────────────────────────────────┘  │
│                            ↓                                      │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Azure Front Door (CDN + SSL)                              │  │
│  │  - Global load balancing                                   │  │
│  │  - SSL/TLS termination                                     │  │
│  │  - DDoS protection                                         │  │
│  │  - WAF (Web Application Firewall)                          │  │
│  └─────────────────────────┬──────────────────────────────────┘  │
│                            ↓                                      │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Azure Container Instances (ACI) or App Service            │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  FastMCP Server Container                            │  │  │
│  │  │  - Azure OAuth Provider                              │  │  │
│  │  │  - MCP Tools & Resources                             │  │  │
│  │  │  - Graph API Client                                  │  │  │
│  │  │  - Application Insights SDK                          │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  └─────────────────────────┬──────────────────────────────────┘  │
│                            │                                      │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Security & Secrets                                        │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  Azure Key Vault                                     │  │  │
│  │  │  - Azure AD credentials                              │  │  │
│  │  │  - OAuth signing keys                                │  │  │
│  │  │  - Encryption keys                                   │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  Microsoft Defender for Cloud                        │  │  │
│  │  │  - Runtime threat detection                          │  │  │
│  │  │  - Vulnerability scanning                            │  │  │
│  │  │  - Security recommendations                          │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                            │                                      │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Monitoring & Observability                               │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  Application Insights                                │  │  │
│  │  │  - APM & distributed tracing                         │  │  │
│  │  │  - Performance monitoring                            │  │  │
│  │  │  - Custom metrics                                    │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  Azure Monitor                                       │  │  │
│  │  │  - Log Analytics                                     │  │  │
│  │  │  - Metrics & alerts                                  │  │  │
│  │  │  - Dashboards                                        │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                            ↓                                      │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Microsoft Graph API                                       │  │
│  │  - Microsoft Planner                                       │  │
│  │  - Microsoft 365 Services                                  │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Deployment Options Comparison

| Feature | Azure Container Instances | Azure App Service | Azure Container Apps |
|---------|---------------------------|-------------------|----------------------|
| **Pricing** | Pay per second | Monthly plan | Pay per use |
| **Scaling** | Manual | Auto-scale | Auto-scale (serverless) |
| **SSL** | Via Front Door | Built-in | Built-in |
| **Deployment** | Simple | Very simple | Simple |
| **Cost (estimate)** | ~$30/month | ~$50/month | ~$20-40/month |
| **Complexity** | Low | Very low | Low |
| **Best for** | Cost-conscious | Simplicity | Modern, scalable |

**Recommendation:** Start with **Azure Container Apps** (best balance of features and cost)

---

## Phase 1: Azure Resource Setup

### Step 1.1: Prerequisites

- Azure subscription
- Azure CLI installed: `az --version`
- Docker installed (for local testing)
- Your Azure AD credentials from the transformation plan

### Step 1.2: Login and Set Subscription

```bash
# Login to Azure
az login

# List subscriptions
az account list --output table

# Set active subscription
az account set --subscription "Your Subscription Name"

# Verify
az account show
```

### Step 1.3: Create Resource Group

```bash
# Set variables
RESOURCE_GROUP="rg-planner-mcp-prod"
LOCATION="eastus"  # Choose region close to your users
APP_NAME="planner-mcp"

# Create resource group
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# Tag for organization
az group update \
  --name $RESOURCE_GROUP \
  --tags Environment=Production Application=PlannerMCP
```

---

## Phase 2: Azure Key Vault Setup

### Step 2.1: Create Key Vault

```bash
# Key Vault name must be globally unique
KEYVAULT_NAME="${APP_NAME}-kv-$(openssl rand -hex 4)"

az keyvault create \
  --name $KEYVAULT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --enable-rbac-authorization false \
  --enabled-for-deployment true \
  --enabled-for-template-deployment true

# Get Key Vault URL
KEYVAULT_URL=$(az keyvault show \
  --name $KEYVAULT_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.vaultUri \
  --output tsv)

echo "Key Vault URL: $KEYVAULT_URL"
```

### Step 2.2: Store Secrets

```bash
# Azure AD OAuth credentials
az keyvault secret set \
  --vault-name $KEYVAULT_NAME \
  --name "AZURE-TENANT-ID" \
  --value "your-tenant-id"

az keyvault secret set \
  --vault-name $KEYVAULT_NAME \
  --name "AZURE-CLIENT-ID" \
  --value "your-client-id"

az keyvault secret set \
  --vault-name $KEYVAULT_NAME \
  --name "AZURE-CLIENT-SECRET" \
  --value "your-client-secret"

# Generate and store OAuth keys
az keyvault secret set \
  --vault-name $KEYVAULT_NAME \
  --name "JWT-SIGNING-KEY" \
  --value "$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"

az keyvault secret set \
  --vault-name $KEYVAULT_NAME \
  --name "STORAGE-ENCRYPTION-KEY" \
  --value "$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"

# Verify secrets
az keyvault secret list --vault-name $KEYVAULT_NAME --output table
```

### Step 2.3: Create Managed Identity

```bash
# Create user-assigned managed identity
IDENTITY_NAME="${APP_NAME}-identity"

az identity create \
  --name $IDENTITY_NAME \
  --resource-group $RESOURCE_GROUP

# Get identity details
IDENTITY_ID=$(az identity show \
  --name $IDENTITY_NAME \
  --resource-group $RESOURCE_GROUP \
  --query id \
  --output tsv)

IDENTITY_PRINCIPAL_ID=$(az identity show \
  --name $IDENTITY_NAME \
  --resource-group $RESOURCE_GROUP \
  --query principalId \
  --output tsv)

echo "Identity ID: $IDENTITY_ID"
echo "Principal ID: $IDENTITY_PRINCIPAL_ID"
```

### Step 2.4: Grant Key Vault Access

```bash
# Grant managed identity access to Key Vault secrets
az keyvault set-policy \
  --name $KEYVAULT_NAME \
  --object-id $IDENTITY_PRINCIPAL_ID \
  --secret-permissions get list

# Verify access policy
az keyvault show \
  --name $KEYVAULT_NAME \
  --query properties.accessPolicies
```

---

## Phase 3: Application Insights Setup

### Step 3.1: Create Application Insights

```bash
# Create Log Analytics workspace first
WORKSPACE_NAME="${APP_NAME}-logs"

az monitor log-analytics workspace create \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $WORKSPACE_NAME \
  --location $LOCATION

# Get workspace ID
WORKSPACE_ID=$(az monitor log-analytics workspace show \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $WORKSPACE_NAME \
  --query id \
  --output tsv)

# Create Application Insights
APPINSIGHTS_NAME="${APP_NAME}-insights"

az monitor app-insights component create \
  --app $APPINSIGHTS_NAME \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP \
  --workspace $WORKSPACE_ID

# Get instrumentation key and connection string
APPINSIGHTS_KEY=$(az monitor app-insights component show \
  --app $APPINSIGHTS_NAME \
  --resource-group $RESOURCE_GROUP \
  --query instrumentationKey \
  --output tsv)

APPINSIGHTS_CONNECTION=$(az monitor app-insights component show \
  --app $APPINSIGHTS_NAME \
  --resource-group $RESOURCE_GROUP \
  --query connectionString \
  --output tsv)

echo "Application Insights Key: $APPINSIGHTS_KEY"
echo "Connection String: $APPINSIGHTS_CONNECTION"
```

### Step 3.2: Store Application Insights in Key Vault

```bash
az keyvault secret set \
  --vault-name $KEYVAULT_NAME \
  --name "APPINSIGHTS-INSTRUMENTATION-KEY" \
  --value "$APPINSIGHTS_KEY"

az keyvault secret set \
  --vault-name $KEYVAULT_NAME \
  --name "APPINSIGHTS-CONNECTION-STRING" \
  --value "$APPINSIGHTS_CONNECTION"
```

---

## Phase 4: Container Registry Setup

### Step 4.1: Create Azure Container Registry

```bash
# ACR name must be globally unique (alphanumeric only)
ACR_NAME="${APP_NAME}acr$(openssl rand -hex 4)"

az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --admin-enabled true

# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show \
  --name $ACR_NAME \
  --resource-group $RESOURCE_GROUP \
  --query loginServer \
  --output tsv)

echo "ACR Login Server: $ACR_LOGIN_SERVER"
```

### Step 4.2: Login to ACR

```bash
# Login to ACR
az acr login --name $ACR_NAME

# Or get credentials for Docker
ACR_USERNAME=$(az acr credential show \
  --name $ACR_NAME \
  --query username \
  --output tsv)

ACR_PASSWORD=$(az acr credential show \
  --name $ACR_NAME \
  --query passwords[0].value \
  --output tsv)

# Docker login
echo $ACR_PASSWORD | docker login $ACR_LOGIN_SERVER \
  --username $ACR_USERNAME \
  --password-stdin
```

---

## Phase 5: Containerize Application

### Step 5.1: Create Dockerfile

**File:** `Dockerfile`

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY cli/ ./cli/
COPY scripts/ ./scripts/

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Environment variables (overridden at runtime)
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health').read()"

# Run application
CMD ["python", "src/server.py"]
```

### Step 5.2: Create .dockerignore

**File:** `.dockerignore`

```
.git
.gitignore
.env
.env.*
*.md
README.md
TRANSFORMATION_PLAN.md
BLUEROCK_INTEGRATION_PLAN.md
AZURE_NATIVE_DEPLOYMENT.md
__pycache__
*.pyc
*.pyo
*.pyd
.pytest_cache
.token_cache.json
venv/
.venv/
tests/
.vscode/
.idea/
*.log
```

### Step 5.3: Update server.py for Azure

Add health endpoint and Azure integration:

**File:** `src/server.py` (additions)

```python
# Add at the top
import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from opencensus.ext.azure.log_exporter import AzureLogHandler
from applicationinsights import TelemetryClient

# Add helper to load secrets from Key Vault
def load_secrets_from_keyvault():
    """Load secrets from Azure Key Vault using managed identity."""
    keyvault_url = os.getenv("AZURE_KEYVAULT_URL")
    if not keyvault_url:
        logger.warning("AZURE_KEYVAULT_URL not set, using environment variables")
        return

    try:
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=keyvault_url, credential=credential)

        # Load secrets
        os.environ["AZURE_TENANT_ID"] = client.get_secret("AZURE-TENANT-ID").value
        os.environ["AZURE_CLIENT_ID"] = client.get_secret("AZURE-CLIENT-ID").value
        os.environ["AZURE_CLIENT_SECRET"] = client.get_secret("AZURE-CLIENT-SECRET").value
        os.environ["JWT_SIGNING_KEY"] = client.get_secret("JWT-SIGNING-KEY").value
        os.environ["STORAGE_ENCRYPTION_KEY"] = client.get_secret("STORAGE-ENCRYPTION-KEY").value

        logger.info("secrets_loaded_from_keyvault")
    except Exception as e:
        logger.error("failed_to_load_secrets", error=str(e))
        raise

# Add Application Insights logging
def configure_azure_logging():
    """Configure logging to Azure Application Insights."""
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if connection_string:
        # Add Azure handler to structlog
        import logging
        azure_handler = AzureLogHandler(connection_string=connection_string)
        logging.getLogger().addHandler(azure_handler)
        logger.info("azure_logging_configured")

# Call at startup
load_secrets_from_keyvault()
configure_azure_logging()

# Add health endpoint
@mcp.tool()
async def health() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.mcp_server_version,
        "timestamp": datetime.utcnow().isoformat()
    }
```

### Step 5.4: Build and Push Container

```bash
# Navigate to repository root
cd /path/to/fornado-planner-mcp

# Build container
docker build -t ${ACR_LOGIN_SERVER}/planner-mcp:latest .

# Test locally (optional)
docker run -p 8080:8080 \
  -e AZURE_TENANT_ID="your-tenant-id" \
  -e AZURE_CLIENT_ID="your-client-id" \
  -e AZURE_CLIENT_SECRET="your-secret" \
  -e AZURE_BASE_URL="http://localhost:8080" \
  -e AZURE_REQUIRED_SCOPES='["planner.access"]' \
  ${ACR_LOGIN_SERVER}/planner-mcp:latest

# Push to ACR
docker push ${ACR_LOGIN_SERVER}/planner-mcp:latest

# Verify
az acr repository list --name $ACR_NAME --output table
```

---

## Phase 6: Deploy to Azure Container Apps

### Step 6.1: Create Container Apps Environment

```bash
# Install Container Apps extension
az extension add --name containerapp --upgrade

# Create environment
ENVIRONMENT_NAME="${APP_NAME}-env"

az containerapp env create \
  --name $ENVIRONMENT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --logs-workspace-id $WORKSPACE_ID

# Verify
az containerapp env show \
  --name $ENVIRONMENT_NAME \
  --resource-group $RESOURCE_GROUP
```

### Step 6.2: Deploy Container App

```bash
# Create container app
CONTAINERAPP_NAME="${APP_NAME}"

az containerapp create \
  --name $CONTAINERAPP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $ENVIRONMENT_NAME \
  --image ${ACR_LOGIN_SERVER}/planner-mcp:latest \
  --target-port 8080 \
  --ingress external \
  --registry-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --user-assigned $IDENTITY_ID \
  --cpu 1.0 \
  --memory 2Gi \
  --min-replicas 1 \
  --max-replicas 3 \
  --env-vars \
    AZURE_KEYVAULT_URL=$KEYVAULT_URL \
    APPLICATIONINSIGHTS_CONNECTION_STRING=secretref:appinsights-connection \
    AZURE_BASE_URL="https://${CONTAINERAPP_NAME}.azurecontainerapps.io" \
    AZURE_REQUIRED_SCOPES='["planner.access"]' \
    MCP_SERVER_PORT=8080 \
    LOG_LEVEL=INFO

# Add secrets
az containerapp secret set \
  --name $CONTAINERAPP_NAME \
  --resource-group $RESOURCE_GROUP \
  --secrets appinsights-connection=$APPINSIGHTS_CONNECTION

# Get app URL
APP_URL=$(az containerapp show \
  --name $CONTAINERAPP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn \
  --output tsv)

echo "Application URL: https://${APP_URL}"
```

### Step 6.3: Configure Auto-Scaling

```bash
# Scale based on HTTP requests
az containerapp update \
  --name $CONTAINERAPP_NAME \
  --resource-group $RESOURCE_GROUP \
  --scale-rule-name http-scaling \
  --scale-rule-type http \
  --scale-rule-http-concurrency 50

# Scale based on CPU
az containerapp update \
  --name $CONTAINERAPP_NAME \
  --resource-group $RESOURCE_GROUP \
  --scale-rule-name cpu-scaling \
  --scale-rule-type cpu \
  --scale-rule-metadata type=Utilization value=70
```

---

## Phase 7: Custom Domain and SSL

### Step 7.1: Add Custom Domain (Optional)

```bash
# If you have a custom domain: planner-mcp.yourdomain.com

# Add domain to Container App
az containerapp hostname add \
  --hostname planner-mcp.yourdomain.com \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINERAPP_NAME

# Get TXT validation record
az containerapp hostname list \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINERAPP_NAME

# Add TXT record in your DNS:
# Name: asuid.planner-mcp
# Value: <validation-code-from-above>

# Bind certificate (auto-managed)
az containerapp hostname bind \
  --hostname planner-mcp.yourdomain.com \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINERAPP_NAME \
  --environment $ENVIRONMENT_NAME \
  --validation-method HTTP
```

**Update Azure AD redirect URI:**
```
https://planner-mcp.yourdomain.com/auth/callback
```

Or use the default:
```
https://${CONTAINERAPP_NAME}.azurecontainerapps.io/auth/callback
```

---

## Phase 8: Azure Monitor and Alerts

### Step 8.1: Create Dashboards

**In Azure Portal:**
1. Go to **Azure Monitor** → **Dashboards** → **New dashboard**
2. Name: "Planner MCP Production"
3. Add tiles:
   - **Application Insights**: Request rate, response time, failures
   - **Container App**: CPU, memory, replica count
   - **Log Analytics**: Recent errors, security events

### Step 8.2: Configure Alerts

```bash
# Create action group for notifications
ACTION_GROUP_NAME="planner-mcp-alerts"

az monitor action-group create \
  --name $ACTION_GROUP_NAME \
  --resource-group $RESOURCE_GROUP \
  --short-name "PlannerMCP" \
  --email-receiver \
    name="Admin" \
    email-address="your-email@example.com"

# Alert on high error rate
az monitor metrics alert create \
  --name "PlannerMCP-HighErrorRate" \
  --resource-group $RESOURCE_GROUP \
  --scopes $(az containerapp show \
    --name $CONTAINERAPP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query id --output tsv) \
  --condition "avg requests/failed > 5" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action $ACTION_GROUP_NAME \
  --description "Alert when error rate exceeds 5 failures per minute"

# Alert on high CPU
az monitor metrics alert create \
  --name "PlannerMCP-HighCPU" \
  --resource-group $RESOURCE_GROUP \
  --scopes $(az containerapp show \
    --name $CONTAINERAPP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query id --output tsv) \
  --condition "avg UsageNanoCores > 800000000" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action $ACTION_GROUP_NAME \
  --description "Alert when CPU usage exceeds 80%"
```

### Step 8.3: Query Logs

```kusto
// Recent errors
ContainerAppConsoleLogs_CL
| where Log_s contains "ERROR"
| project TimeGenerated, Log_s
| order by TimeGenerated desc
| take 50

// OAuth authentication events
ContainerAppConsoleLogs_CL
| where Log_s contains "oauth" or Log_s contains "authentication"
| project TimeGenerated, Log_s
| order by TimeGenerated desc

// Performance metrics
requests
| where timestamp > ago(1h)
| summarize
    RequestCount = count(),
    AvgDuration = avg(duration),
    P95Duration = percentile(duration, 95)
  by bin(timestamp, 5m)
| render timechart

// Graph API calls
dependencies
| where target contains "graph.microsoft.com"
| summarize
    CallCount = count(),
    SuccessRate = countif(success == true) * 100.0 / count()
  by name
| order by CallCount desc
```

---

## Phase 9: Microsoft Defender for Cloud

### Step 9.1: Enable Defender

```bash
# Enable Defender for Container Apps
az security pricing create \
  --name ContainerApps \
  --tier Standard

# Enable Defender for Container Registry
az security pricing create \
  --name ContainerRegistry \
  --tier Standard

# Enable Defender for Key Vault
az security pricing create \
  --name KeyVaults \
  --tier Standard
```

### Step 9.2: Configure Security Policies

```bash
# Assign Azure Policy for security baseline
az policy assignment create \
  --name "PlannerMCP-SecurityBaseline" \
  --scope "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP" \
  --policy-set-definition "/providers/Microsoft.Authorization/policySetDefinitions/1f3afdf9-d0c9-4c3d-847f-89da613e70a8" \
  --display-name "Azure Security Benchmark for Planner MCP"

# Enable vulnerability scanning for container images
az acr update \
  --name $ACR_NAME \
  --resource-group $RESOURCE_GROUP \
  --defender-enabled true
```

### Step 9.3: View Security Recommendations

**In Azure Portal:**
1. Go to **Microsoft Defender for Cloud**
2. Navigate to **Recommendations**
3. Filter by resource group: `rg-planner-mcp-prod`
4. Review and remediate recommendations

Common recommendations:
- Enable diagnostic logging
- Restrict network access
- Use managed identities
- Enable encryption at rest

---

## Phase 10: CI/CD with GitHub Actions

### Step 10.1: Create Service Principal

```bash
# Create service principal for GitHub Actions
SP_NAME="${APP_NAME}-github-sp"

az ad sp create-for-rbac \
  --name $SP_NAME \
  --role contributor \
  --scopes /subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP \
  --sdk-auth

# Save the JSON output as GitHub secret: AZURE_CREDENTIALS
```

### Step 10.2: GitHub Actions Workflow

**File:** `.github/workflows/deploy-azure.yml`

```yaml
name: Deploy to Azure Container Apps

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:

env:
  RESOURCE_GROUP: rg-planner-mcp-prod
  CONTAINER_APP_NAME: planner-mcp
  ACR_NAME: plannermcpacr<unique-suffix>

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Login to Azure
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Login to ACR
        run: |
          az acr login --name ${{ env.ACR_NAME }}

      - name: Build and push container
        run: |
          IMAGE_TAG=${{ github.sha }}
          docker build -t ${{ env.ACR_NAME }}.azurecr.io/planner-mcp:$IMAGE_TAG .
          docker push ${{ env.ACR_NAME }}.azurecr.io/planner-mcp:$IMAGE_TAG

          # Also tag as latest
          docker tag ${{ env.ACR_NAME }}.azurecr.io/planner-mcp:$IMAGE_TAG \
            ${{ env.ACR_NAME }}.azurecr.io/planner-mcp:latest
          docker push ${{ env.ACR_NAME }}.azurecr.io/planner-mcp:latest

      - name: Deploy to Container Apps
        run: |
          az containerapp update \
            --name ${{ env.CONTAINER_APP_NAME }} \
            --resource-group ${{ env.RESOURCE_GROUP }} \
            --image ${{ env.ACR_NAME }}.azurecr.io/planner-mcp:${{ github.sha }}

      - name: Run smoke tests
        run: |
          APP_URL=$(az containerapp show \
            --name ${{ env.CONTAINER_APP_NAME }} \
            --resource-group ${{ env.RESOURCE_GROUP }} \
            --query properties.configuration.ingress.fqdn \
            --output tsv)

          # Health check
          curl -f https://${APP_URL}/health || exit 1

          # OAuth metadata check
          curl -f https://${APP_URL}/.well-known/oauth-authorization-server || exit 1

      - name: Logout from Azure
        run: az logout
```

---

## Cost Optimization

### Monthly Cost Estimate (Azure-Native)

| Resource | Specification | Monthly Cost (USD) |
|----------|---------------|-------------------|
| Container Apps | 1 vCPU, 2 GB RAM, always-on | ~$30 |
| Container Registry | Basic tier | ~$5 |
| Key Vault | Secrets storage | ~$1 |
| Application Insights | 5 GB data ingestion | ~$10 |
| Log Analytics | 5 GB data retention | ~$5 |
| Defender for Cloud | Standard tier (optional) | ~$15 |
| **Total (without Defender)** | | **~$51** |
| **Total (with Defender)** | | **~$66** |

**Free Tier Considerations:**
- Container Apps: First 180,000 vCPU-seconds free per month
- Application Insights: First 5 GB free
- Log Analytics: First 5 GB free
- Actual costs may be lower for low-traffic applications

### Cost Reduction Strategies

```bash
# 1. Use consumption-only pricing (scale to zero when idle)
az containerapp update \
  --name $CONTAINERAPP_NAME \
  --resource-group $RESOURCE_GROUP \
  --min-replicas 0 \
  --max-replicas 3

# 2. Reduce log retention
az monitor log-analytics workspace update \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $WORKSPACE_NAME \
  --retention-time 30  # days

# 3. Use Basic tier for dev/test
# (Create separate resource group for dev with Basic SKUs)

# 4. Set budget alerts
az consumption budget create \
  --amount 100 \
  --budget-name "planner-mcp-monthly" \
  --category cost \
  --time-grain monthly \
  --time-period start-date=$(date +%Y-%m-01) \
  --notifications \
    actual_threshold=80 \
    contact_emails="your-email@example.com" \
    contact_roles="Owner"
```

---

## Security Hardening

### Step 11.1: Enable Private Endpoints (Production)

```bash
# Create VNet
VNET_NAME="${APP_NAME}-vnet"

az network vnet create \
  --resource-group $RESOURCE_GROUP \
  --name $VNET_NAME \
  --address-prefix 10.0.0.0/16 \
  --subnet-name default \
  --subnet-prefix 10.0.1.0/24

# Create private endpoint for Key Vault
az network private-endpoint create \
  --name "${KEYVAULT_NAME}-pe" \
  --resource-group $RESOURCE_GROUP \
  --vnet-name $VNET_NAME \
  --subnet default \
  --private-connection-resource-id $(az keyvault show \
    --name $KEYVAULT_NAME \
    --query id --output tsv) \
  --group-id vault \
  --connection-name "${KEYVAULT_NAME}-connection"

# Disable public access to Key Vault
az keyvault update \
  --name $KEYVAULT_NAME \
  --resource-group $RESOURCE_GROUP \
  --public-network-access Disabled
```

### Step 11.2: Configure Network Policies

```bash
# Restrict Container App ingress
az containerapp ingress access-restriction set \
  --name $CONTAINERAPP_NAME \
  --resource-group $RESOURCE_GROUP \
  --rule-name "allow-azure-ad" \
  --ip-address "login.microsoftonline.com" \
  --action Allow

# Enable CORS for specific origins only
az containerapp ingress cors enable \
  --name $CONTAINERAPP_NAME \
  --resource-group $RESOURCE_GROUP \
  --allowed-origins "https://claude.ai" "https://yourdomain.com" \
  --allowed-methods GET POST PUT DELETE \
  --allowed-headers "*" \
  --max-age 3600
```

---

## Disaster Recovery

### Step 12.1: Backup Strategy

```bash
# Enable soft delete for Key Vault (enabled by default)
az keyvault update \
  --name $KEYVAULT_NAME \
  --resource-group $RESOURCE_GROUP \
  --enable-soft-delete true \
  --retention-days 90

# Enable purge protection (cannot be disabled once enabled)
az keyvault update \
  --name $KEYVAULT_NAME \
  --resource-group $RESOURCE_GROUP \
  --enable-purge-protection true

# Backup container images (ACR geo-replication)
az acr replication create \
  --registry $ACR_NAME \
  --location westus2
```

### Step 12.2: Multi-Region Deployment (Optional)

For high availability, deploy to multiple regions:

```bash
# Secondary region
SECONDARY_LOCATION="westus2"
SECONDARY_ENV="${APP_NAME}-env-west"

# Create environment in secondary region
az containerapp env create \
  --name $SECONDARY_ENV \
  --resource-group $RESOURCE_GROUP \
  --location $SECONDARY_LOCATION \
  --logs-workspace-id $WORKSPACE_ID

# Deploy container app in secondary region
az containerapp create \
  --name "${CONTAINERAPP_NAME}-west" \
  --resource-group $RESOURCE_GROUP \
  --environment $SECONDARY_ENV \
  --image ${ACR_LOGIN_SERVER}/planner-mcp:latest \
  # ... (same config as primary)

# Use Azure Front Door for global load balancing
# (See Azure Front Door documentation)
```

---

## Testing and Validation

### Step 13.1: Test OAuth Flow

```bash
# Get app URL
APP_URL=$(az containerapp show \
  --name $CONTAINERAPP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn \
  --output tsv)

# Test OAuth metadata endpoint
curl https://${APP_URL}/.well-known/oauth-authorization-server | jq

# Test health endpoint
curl https://${APP_URL}/health | jq

# Test with Python client
python3 << EOF
from fastmcp import Client
import asyncio

async def test():
    async with Client('https://${APP_URL}/mcp', auth='oauth') as client:
        result = await client.call_tool('get_user_info')
        print(result)

asyncio.run(test())
EOF
```

### Step 13.2: Load Testing

```bash
# Install Azure Load Testing
az extension add --name load

# Create load test
az load test create \
  --name "planner-mcp-load-test" \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Run test (requires JMX file)
az load test run \
  --test-id "planner-mcp-load-test" \
  --load-test-config-file load-test.yaml \
  --resource-group $RESOURCE_GROUP
```

---

## Monitoring Queries

### Application Insights Queries

```kusto
// Request performance by operation
requests
| where timestamp > ago(24h)
| summarize
    Count = count(),
    AvgDuration = avg(duration),
    P50 = percentile(duration, 50),
    P95 = percentile(duration, 95),
    P99 = percentile(duration, 99)
  by operation_Name
| order by Count desc

// Failed requests
requests
| where timestamp > ago(1h) and success == false
| project timestamp, operation_Name, resultCode, duration, url
| order by timestamp desc

// Dependency calls to Microsoft Graph
dependencies
| where timestamp > ago(24h)
| where target contains "graph.microsoft.com"
| summarize
    TotalCalls = count(),
    SuccessRate = round(countif(success == true) * 100.0 / count(), 2),
    AvgDuration = round(avg(duration), 2)
  by name
| order by TotalCalls desc

// Custom events (MCP tool calls)
customEvents
| where timestamp > ago(24h)
| where name == "mcp_tool_call"
| summarize Count = count() by tostring(customDimensions.tool_name)
| order by Count desc

// Exceptions
exceptions
| where timestamp > ago(24h)
| summarize Count = count() by type, outerMessage
| order by Count desc
```

---

## Summary

### Azure-Native Stack

| Layer | Azure Service | Purpose |
|-------|---------------|---------|
| **Identity** | Azure AD | OAuth authentication |
| **Compute** | Container Apps | Run FastMCP server |
| **Secrets** | Key Vault | Store credentials |
| **Registry** | Container Registry | Store container images |
| **Monitoring** | Application Insights | APM and telemetry |
| **Logs** | Log Analytics | Centralized logging |
| **Security** | Defender for Cloud | Runtime protection |
| **Networking** | VNet + Private Endpoints | Network isolation |
| **CI/CD** | GitHub Actions | Automated deployment |

### Benefits Over Hybrid Approach

| Feature | Azure-Native | AWS Hybrid (BlueRock) |
|---------|-------------|----------------------|
| **Complexity** | ✅ Low (single cloud) | ⚠️ Medium (cross-cloud) |
| **Integration** | ✅ Native with Azure AD/Graph | ⚠️ Cross-cloud networking |
| **Monitoring** | ✅ Unified (App Insights) | ⚠️ Split (CloudWatch + Azure) |
| **Cost** | ✅ ~$51/month | ⚠️ ~$35 + data transfer |
| **Security** | ✅ Azure Defender | ✅ BlueRock MCP-specific |
| **Management** | ✅ Single portal | ⚠️ Two portals |
| **Compliance** | ✅ All data in Azure | ⚠️ Split across clouds |

### Deployment Checklist

- [x] Create Azure resources (Key Vault, ACR, App Insights)
- [x] Store secrets in Key Vault
- [x] Build and push container image
- [x] Deploy to Container Apps
- [x] Configure custom domain and SSL
- [x] Set up monitoring and alerts
- [x] Enable Defender for Cloud
- [x] Configure CI/CD pipeline
- [ ] **Update Azure AD redirect URI to production URL**
- [ ] Test OAuth flow end-to-end
- [ ] Run load tests
- [ ] Document runbook
- [ ] Train team on Azure operations

---

## Next Steps

1. **Review this plan** and approve deployment approach
2. **Run Phase 1-5** to set up Azure infrastructure and build container
3. **Deploy to Azure** using Phase 6
4. **Configure monitoring** (Phase 7-8)
5. **Enable security** features (Phase 9)
6. **Set up CI/CD** (Phase 10)
7. **Test thoroughly** (Phase 13)
8. **Go live** and monitor

**Estimated Setup Time:** 3-4 hours
**Monthly Cost:** ~$51 (without Defender) to ~$66 (with Defender)
**Maintenance:** ~1-2 hours/month

This Azure-native approach provides a **production-ready, fully managed, secure deployment** that's perfectly aligned with your Microsoft/Azure technology stack.
