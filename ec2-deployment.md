# Amazon Linux EC2 Deployment Guide

## Prerequisites

### EC2 Instance Requirements
- **Instance Type**: t3.medium or larger (minimum 2GB RAM)
- **AMI**: Amazon Linux 2023 or Amazon Linux 2
- **Storage**: 20GB+ EBS volume
- **Security Group**: Allow inbound traffic on port 5000 (or 80/443 for production)

### IAM Configuration
Attach IAM role to EC2 instance with the following policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "ce:GetDimensionValues",
        "bedrock:InvokeModel",
        "ec2:DescribeInstances",
        "rds:DescribeDBInstances",
        "s3:ListBuckets",
        "lambda:ListFunctions",
        "qbusiness:ListApplications",
        "qbusiness:ListIndices",
        "resource-groups:GetResources"
      ],
      "Resource": "*"
    }
  ]
}
```

## Step-by-Step Deployment

### 1. Connect to EC2 Instance

```bash
ssh -i your-key.pem ec2-user@your-instance-ip
```

### 2. System Updates and Dependencies

```bash
# Update system packages
sudo yum update -y

# Install Python 3.11 (Amazon Linux 2023)
sudo yum install -y python3.11 python3.11-pip python3.11-dev

# For Amazon Linux 2, use:
# sudo amazon-linux-extras install python3.8
# sudo yum install -y python38 python38-pip python38-devel

# Install Git
sudo yum install -y git

# Install system dependencies for Python packages
sudo yum install -y gcc gcc-c++ make
sudo yum install -y libffi-devel openssl-devel
```

### 3. Create Application Directory

```bash
# Create application directory
sudo mkdir -p /opt/aws-cost-calculator
sudo chown ec2-user:ec2-user /opt/aws-cost-calculator
cd /opt/aws-cost-calculator
```

### 4. Upload Application Files

Option A - Upload files via SCP:
```bash
# From your local machine
scp -i your-key.pem app.py ec2-user@your-instance-ip:/opt/aws-cost-calculator/
scp -i your-key.pem aws_cost_service.py ec2-user@your-instance-ip:/opt/aws-cost-calculator/
scp -i your-key.pem utils.py ec2-user@your-instance-ip:/opt/aws-cost-calculator/
scp -r -i your-key.pem .streamlit/ ec2-user@your-instance-ip:/opt/aws-cost-calculator/
```

Option B - Clone from repository:
```bash
git clone your-repository-url .
```

### 5. Python Environment Setup

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install required packages
pip install streamlit==1.28.0
pip install boto3==1.34.0
pip install pandas==2.0.0
pip install plotly==5.17.0
pip install numpy==1.24.0
```

### 6. Configure Streamlit

Create or verify `.streamlit/config.toml`:
```bash
mkdir -p .streamlit
cat > .streamlit/config.toml << 'EOF'
[server]
headless = true
address = "0.0.0.0"
port = 5000
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false

[logger]
level = "info"
EOF
```

### 7. AWS Configuration

If not using IAM roles, configure AWS credentials:
```bash
# Option 1: AWS CLI (recommended)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
aws configure

# Option 2: Environment variables
echo 'export AWS_ACCESS_KEY_ID=your_access_key' >> ~/.bashrc
echo 'export AWS_SECRET_ACCESS_KEY=your_secret_key' >> ~/.bashrc
echo 'export AWS_DEFAULT_REGION=us-east-1' >> ~/.bashrc
source ~/.bashrc
```

### 8. Create Systemd Service (Production)

```bash
sudo tee /etc/systemd/system/aws-cost-calculator.service > /dev/null << 'EOF'
[Unit]
Description=AWS Cost Calculator & FinOps Tool
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/opt/aws-cost-calculator
Environment=PATH=/opt/aws-cost-calculator/venv/bin
ExecStart=/opt/aws-cost-calculator/venv/bin/streamlit run app.py --server.port 5000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable aws-cost-calculator
sudo systemctl start aws-cost-calculator
```

### 9. Configure Firewall

```bash
# Allow port 5000 (if firewall is enabled)
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload

# Or disable firewall (not recommended for production)
sudo systemctl stop firewalld
sudo systemctl disable firewalld
```

### 10. Test Deployment

```bash
# Check service status
sudo systemctl status aws-cost-calculator

# View logs
sudo journalctl -u aws-cost-calculator -f

# Test locally
curl http://localhost:5000

# Test externally (replace with your instance IP)
curl http://your-instance-ip:5000
```

## Production Enhancements

### 1. Reverse Proxy with Nginx

```bash
# Install Nginx
sudo yum install -y nginx

# Configure Nginx
sudo tee /etc/nginx/conf.d/aws-cost-calculator.conf > /dev/null << 'EOF'
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# Start Nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

### 2. SSL Certificate with Let's Encrypt

```bash
# Install Certbot
sudo yum install -y python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo systemctl enable certbot-renew.timer
```

### 3. Log Management

```bash
# Create log directory
sudo mkdir -p /var/log/aws-cost-calculator
sudo chown ec2-user:ec2-user /var/log/aws-cost-calculator

# Update systemd service for logging
sudo tee /etc/systemd/system/aws-cost-calculator.service > /dev/null << 'EOF'
[Unit]
Description=AWS Cost Calculator & FinOps Tool
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/opt/aws-cost-calculator
Environment=PATH=/opt/aws-cost-calculator/venv/bin
ExecStart=/opt/aws-cost-calculator/venv/bin/streamlit run app.py --server.port 5000
Restart=always
RestartSec=10
StandardOutput=append:/var/log/aws-cost-calculator/app.log
StandardError=append:/var/log/aws-cost-calculator/error.log

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl restart aws-cost-calculator
```

### 4. Monitoring Setup

```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
sudo rpm -U ./amazon-cloudwatch-agent.rpm

# Create CloudWatch config
sudo tee /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json > /dev/null << 'EOF'
{
    "metrics": {
        "namespace": "AWS/EC2/Custom",
        "metrics_collected": {
            "cpu": {
                "measurement": ["cpu_usage_idle", "cpu_usage_iowait"],
                "metrics_collection_interval": 60
            },
            "disk": {
                "measurement": ["used_percent"],
                "metrics_collection_interval": 60,
                "resources": ["*"]
            },
            "mem": {
                "measurement": ["mem_used_percent"],
                "metrics_collection_interval": 60
            }
        }
    },
    "logs": {
        "logs_collected": {
            "files": {
                "collect_list": [
                    {
                        "file_path": "/var/log/aws-cost-calculator/app.log",
                        "log_group_name": "/aws/ec2/aws-cost-calculator",
                        "log_stream_name": "app"
                    }
                ]
            }
        }
    }
}
EOF

# Start CloudWatch agent
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config -m ec2 -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json -s
```

## Security Hardening

### 1. Update Security Group
- Remove port 5000 from security group
- Allow only port 80/443 for Nginx
- Restrict SSH access to specific IPs

### 2. System Security
```bash
# Update packages regularly
sudo yum update -y

# Configure automatic security updates
sudo yum install -y yum-cron
sudo systemctl enable yum-cron
sudo systemctl start yum-cron
```

### 3. Application Security
```bash
# Set proper file permissions
sudo chown -R ec2-user:ec2-user /opt/aws-cost-calculator
sudo chmod -R 755 /opt/aws-cost-calculator
sudo chmod 600 /opt/aws-cost-calculator/.streamlit/config.toml
```

## Maintenance Scripts

Create maintenance script:
```bash
cat > /opt/aws-cost-calculator/maintenance.sh << 'EOF'
#!/bin/bash

# Backup configuration
sudo cp /opt/aws-cost-calculator/.streamlit/config.toml /opt/aws-cost-calculator/config.toml.backup

# Update packages
source /opt/aws-cost-calculator/venv/bin/activate
pip install --upgrade streamlit boto3 pandas plotly numpy

# Restart service
sudo systemctl restart aws-cost-calculator

# Check status
sudo systemctl status aws-cost-calculator
EOF

chmod +x /opt/aws-cost-calculator/maintenance.sh
```

## Troubleshooting

### Common Issues

1. **Permission denied errors**:
   ```bash
   sudo chown -R ec2-user:ec2-user /opt/aws-cost-calculator
   ```

2. **Port already in use**:
   ```bash
   sudo lsof -i :5000
   sudo systemctl stop aws-cost-calculator
   ```

3. **AWS credentials issues**:
   ```bash
   aws sts get-caller-identity
   ```

4. **Python package conflicts**:
   ```bash
   rm -rf venv
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### Health Check Script

```bash
cat > /opt/aws-cost-calculator/health-check.sh << 'EOF'
#!/bin/bash

# Check if service is running
if ! systemctl is-active --quiet aws-cost-calculator; then
    echo "Service is down, restarting..."
    sudo systemctl restart aws-cost-calculator
fi

# Check if application is responding
if ! curl -f http://localhost:5000/_stcore/health &>/dev/null; then
    echo "Application not responding, restarting..."
    sudo systemctl restart aws-cost-calculator
fi
EOF

chmod +x /opt/aws-cost-calculator/health-check.sh

# Add to crontab for automated health checks
echo "*/5 * * * * /opt/aws-cost-calculator/health-check.sh" | crontab -
```

This deployment guide provides a complete setup for running the AWS Cost Calculator on Amazon Linux EC2, including production-ready configurations with monitoring, logging, and security best practices.