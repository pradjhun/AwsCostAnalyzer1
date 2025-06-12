# Deployment Guide

This document provides step-by-step deployment instructions for the AWS Cost Calculator & FinOps Tool across different platforms.

## Quick Start

1. Ensure AWS credentials are configured
2. Install dependencies: `streamlit boto3 plotly pandas numpy`
3. Run: `streamlit run app.py --server.port 5000`
4. Access: `http://localhost:5000`

## Platform-Specific Deployments

### Replit Deployment

#### Step 1: Project Setup
1. Create new Replit project
2. Upload all project files (`app.py`, `aws_cost_service.py`, `utils.py`, `.streamlit/config.toml`)
3. Ensure Python 3.11+ is selected as runtime

#### Step 2: Dependencies
Install packages using Replit package manager:
- streamlit
- boto3
- plotly
- pandas
- numpy

#### Step 3: Environment Configuration
Add to Replit Secrets:
```
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-east-1
```

#### Step 4: Run Configuration
Set run command:
```bash
streamlit run app.py --server.port 5000
```

#### Step 5: Deploy
Click "Deploy" in Replit to make publicly accessible

### AWS ECS Fargate Deployment

#### Step 1: Container Setup
Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY pyproject.toml .
RUN pip install streamlit boto3 plotly pandas numpy

# Copy application code
COPY . .

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/_stcore/health || exit 1

# Run application
CMD ["streamlit", "run", "app.py", "--server.port", "5000", "--server.address", "0.0.0.0"]
```

#### Step 2: ECR Setup
```bash
# Create ECR repository
aws ecr create-repository --repository-name aws-cost-calculator

# Get login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -t aws-cost-calculator .
docker tag aws-cost-calculator:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/aws-cost-calculator:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/aws-cost-calculator:latest
```

#### Step 3: IAM Role
Create task execution role with permissions:
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

#### Step 4: ECS Task Definition
```json
{
  "family": "aws-cost-calculator",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/cost-calculator-task-role",
  "containerDefinitions": [
    {
      "name": "cost-calculator",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/aws-cost-calculator:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "AWS_DEFAULT_REGION",
          "value": "us-east-1"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/aws-cost-calculator",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Step 5: Load Balancer & Service
Create Application Load Balancer and ECS service with auto-scaling

### Heroku Deployment

#### Step 1: Heroku Setup
```bash
# Install Heroku CLI
# Login to Heroku
heroku login

# Create app
heroku create aws-cost-calculator-app
```

#### Step 2: Configuration Files
Create `runtime.txt`:
```
python-3.11.0
```

Create `Procfile`:
```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

#### Step 3: Environment Variables
```bash
heroku config:set AWS_ACCESS_KEY_ID=your_key
heroku config:set AWS_SECRET_ACCESS_KEY=your_secret
heroku config:set AWS_DEFAULT_REGION=us-east-1
```

#### Step 4: Deploy
```bash
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

### Google Cloud Run Deployment

#### Step 1: Build Container
```bash
# Build for Cloud Run
gcloud builds submit --tag gcr.io/PROJECT-ID/aws-cost-calculator

# Or use Cloud Build
gcloud run deploy aws-cost-calculator \
    --image gcr.io/PROJECT-ID/aws-cost-calculator \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 5000 \
    --memory 2Gi \
    --cpu 1 \
    --set-env-vars AWS_DEFAULT_REGION=us-east-1
```

#### Step 2: Set Environment Variables
```bash
gcloud run services update aws-cost-calculator \
    --set-env-vars AWS_ACCESS_KEY_ID=your_key,AWS_SECRET_ACCESS_KEY=your_secret
```

### Azure Container Instances

#### Step 1: Create Resource Group
```bash
az group create --name aws-cost-calculator-rg --location eastus
```

#### Step 2: Deploy Container
```bash
az container create \
    --resource-group aws-cost-calculator-rg \
    --name aws-cost-calculator \
    --image your-registry/aws-cost-calculator:latest \
    --dns-name-label aws-cost-calc \
    --ports 5000 \
    --environment-variables AWS_DEFAULT_REGION=us-east-1 \
    --secure-environment-variables AWS_ACCESS_KEY_ID=your_key AWS_SECRET_ACCESS_KEY=your_secret \
    --cpu 1 \
    --memory 2
```

## Production Considerations

### Performance Optimization

1. **Caching Strategy**
   - Implement Redis for session caching
   - Cache AWS API responses for 5-10 minutes
   - Use Streamlit session state efficiently

2. **Resource Limits**
   - Set appropriate CPU/memory limits
   - Configure auto-scaling based on usage
   - Monitor API rate limits

3. **Monitoring**
   - Set up CloudWatch/Application Insights
   - Monitor AWS API usage and costs
   - Track application performance metrics

### Security Hardening

1. **Network Security**
   - Use private subnets for containers
   - Configure security groups/firewall rules
   - Implement WAF for public endpoints

2. **Access Control**
   - Use IAM roles instead of access keys when possible
   - Implement authentication for production use
   - Rotate credentials regularly

3. **Data Protection**
   - Enable HTTPS/TLS termination
   - Use secrets management services
   - Audit access logs regularly

### High Availability

1. **Multi-Region Deployment**
   - Deploy in multiple AWS regions
   - Use Route 53 for health checks and failover
   - Replicate configuration across regions

2. **Load Balancing**
   - Use Application Load Balancer
   - Configure health checks
   - Set up auto-scaling groups

3. **Backup Strategy**
   - Regular configuration backups
   - Document disaster recovery procedures
   - Test failover scenarios

## Environment-Specific Configurations

### Development
```toml
[server]
port = 5000
headless = false
runOnSave = true

[logger]
level = "debug"
```

### Staging
```toml
[server]
port = 5000
headless = true
maxUploadSize = 50

[browser]
gatherUsageStats = false
```

### Production
```toml
[server]
port = 5000
headless = true
maxUploadSize = 200
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
```

## Troubleshooting Deployment Issues

### Common Problems

1. **Port Binding Issues**
   - Ensure port 5000 is available
   - Check firewall rules
   - Verify container port mapping

2. **AWS Credential Issues**
   - Validate IAM permissions
   - Check credential format
   - Test with AWS CLI first

3. **Memory Issues**
   - Increase container memory (minimum 2GB)
   - Monitor memory usage
   - Optimize data processing

4. **SSL/TLS Issues**
   - Configure proper certificates
   - Check load balancer settings
   - Verify domain configuration

### Health Checks

Implement health check endpoint:
```python
@app.route('/health')
def health_check():
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}
```

### Logging Configuration

Set up structured logging:
```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module
        })

logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler()],
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Scaling Considerations

### Horizontal Scaling
- Use container orchestration (ECS, Kubernetes)
- Implement session affinity if needed
- Consider stateless design

### Vertical Scaling
- Monitor resource usage
- Adjust CPU/memory based on demand
- Use burst capacity for peak loads

### Cost Optimization
- Use spot instances where appropriate
- Implement auto-scaling policies
- Monitor and optimize AWS API usage costs

This deployment guide ensures successful deployment across multiple platforms while maintaining security, performance, and reliability standards.