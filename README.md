# AWS Cost Calculator & FinOps Tool

A comprehensive Streamlit-based AWS cost management and optimization platform that provides detailed cost analysis, resource identification, and AI-powered optimization recommendations.

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture & Data Flow](#architecture--data-flow)
4. [Prerequisites](#prerequisites)
5. [Installation & Setup](#installation--setup)
6. [Deployment](#deployment)
7. [Configuration](#configuration)
8. [Usage Guide](#usage-guide)
9. [API Integration](#api-integration)
10. [Security Considerations](#security-considerations)
11. [Troubleshooting](#troubleshooting)
12. [Contributing](#contributing)

## Overview

The AWS Cost Calculator & FinOps Tool is an enterprise-grade solution designed to provide comprehensive AWS cost visibility, analysis, and optimization. Built with Streamlit and integrated with AWS Cost Explorer API, AWS Bedrock, and multiple AWS service APIs, it delivers actionable insights for cloud financial management.

### Key Capabilities

- **Multi-dimensional Cost Analysis**: Analyze costs across services, time periods, and resources
- **Resource-Level Cost Attribution**: Identify specific resources consuming costs with actual names and IDs
- **AI-Powered Optimization**: Generate intelligent cost optimization recommendations using AWS Bedrock
- **Interactive Visualizations**: Dynamic charts and graphs for cost trend analysis
- **Real-time Data**: Direct integration with AWS APIs for up-to-date cost information
- **Flexible Time Ranges**: Analyze costs from 30 days to 12 months with custom date selection

## Features

### 1. Cost Overview Dashboard
- Monthly cost trends with interactive charts
- Service-level cost breakdown with pie charts and tables
- Quick access to preset time ranges (30 days, 90 days, 6 months, 12 months)
- Export capabilities for CSV data

### 2. Service Analysis
- Detailed cost breakdown by individual AWS services
- Usage type analysis with drill-down capabilities
- Monthly trend analysis for specific services
- Resource-level cost attribution

### 3. Resource Identification
- **Amazon Q Business**: Enterprise Index names, applications, and status
- **EC2 Instances**: Instance names, IDs, types, and availability zones
- **RDS Databases**: Database names, identifiers, classes, and engines
- **S3 Buckets**: Bucket names and creation dates
- **Lambda Functions**: Function names, runtime, and states

### 4. Advanced Analytics
- Daily cost pattern analysis
- Utilization scoring based on cost consistency
- Cost variance and trend direction analysis
- Optimization opportunity identification

### 5. AI-Powered Recommendations
- Service-specific optimization suggestions
- Cost reduction strategies
- Resource rightsizing recommendations
- Usage pattern analysis

## Architecture & Data Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │  AWS Cost       │    │  AWS Bedrock    │
│                 │    │  Explorer API   │    │  (AI Models)    │
│   - Dashboard   │◄───┤                 │    │                 │
│   - Charts      │    │  - Cost Data    │    │  - Claude 3.5   │
│   - Tables      │    │  - Usage Data   │    │  - Optimization │
│   - Analysis    │    │  - Dimensions   │    │  - Insights     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  AWSCostService │    │  Service APIs   │    │  Data Processing│
│                 │    │                 │    │                 │
│  - Cost queries │◄───┤  - EC2 API      │    │  - Aggregation  │
│  - Resource IDs │    │  - RDS API      │    │  - Analysis     │
│  - AI requests  │    │  - S3 API       │    │  - Visualization│
│  - Optimization │    │  - Lambda API   │    │  - Export       │
└─────────────────┘    │  - Q Business   │    └─────────────────┘
                       └─────────────────┘
```

### Data Flow Process

1. **User Input**: User selects date range and analysis parameters through Streamlit UI
2. **Cost Data Retrieval**: System queries AWS Cost Explorer API for cost and usage data
3. **Resource Identification**: Parallel API calls to service-specific APIs to fetch actual resource names
4. **Data Processing**: Cost data is aggregated, analyzed, and correlated with resource information
5. **AI Analysis**: AWS Bedrock processes cost patterns to generate optimization recommendations
6. **Visualization**: Data is rendered into interactive charts, tables, and insights
7. **Export**: Users can download processed data as CSV files

### Service Integration Points

- **AWS Cost Explorer**: Primary source for cost and usage data
- **AWS Bedrock**: AI-powered analysis and recommendations
- **EC2 API**: Instance identification and metadata
- **RDS API**: Database resource information
- **S3 API**: Bucket listing and details
- **Lambda API**: Function identification
- **Q Business API**: Enterprise Index and application data
- **Resource Groups Tagging API**: Fallback for resource identification

## Prerequisites

### AWS Requirements
- AWS Account with appropriate permissions
- AWS CLI configured or IAM roles with the following permissions:
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "ce:GetCostAndUsage",
          "ce:GetDimensionValues",
          "ce:GetUsageReport",
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

### Technical Requirements
- Python 3.11 or higher
- UV package manager (recommended) or pip
- 2GB+ RAM for data processing
- Network access to AWS APIs

### Environment Variables
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `AWS_DEFAULT_REGION`: Default AWS region (e.g., us-east-1)

## Installation & Setup

### Local Development

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd aws-cost-calculator
   ```

2. **Install dependencies**:
   ```bash
   # Using UV (recommended)
   uv add streamlit boto3 plotly pandas numpy

   # Or using pip
   pip install streamlit boto3 plotly pandas numpy
   ```

3. **Configure AWS credentials**:
   ```bash
   # Option 1: AWS CLI
   aws configure

   # Option 2: Environment variables
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_DEFAULT_REGION=us-east-1
   ```

4. **Create Streamlit configuration**:
   ```bash
   mkdir -p .streamlit
   cat > .streamlit/config.toml << EOF
   [server]
   headless = true
   address = "0.0.0.0"
   port = 5000
   EOF
   ```

5. **Run the application**:
   ```bash
   streamlit run app.py --server.port 5000
   ```

### Production Deployment

#### Replit Deployment

1. **Upload files** to your Replit environment
2. **Install dependencies** using the package manager
3. **Set environment variables** in Replit Secrets:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
4. **Configure the run command**:
   ```bash
   streamlit run app.py --server.port 5000
   ```
5. **Deploy** using Replit's deployment feature

#### Docker Deployment

1. **Create Dockerfile**:
   ```dockerfile
   FROM python:3.11-slim

   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt

   COPY . .
   EXPOSE 5000

   CMD ["streamlit", "run", "app.py", "--server.port", "5000", "--server.address", "0.0.0.0"]
   ```

2. **Build and run**:
   ```bash
   docker build -t aws-cost-calculator .
   docker run -p 5000:5000 -e AWS_ACCESS_KEY_ID=xxx -e AWS_SECRET_ACCESS_KEY=xxx aws-cost-calculator
   ```

#### AWS ECS/Fargate Deployment

1. **Push Docker image** to Amazon ECR
2. **Create ECS task definition** with appropriate IAM roles
3. **Configure load balancer** for public access
4. **Set auto-scaling policies** based on usage

## Configuration

### AWS Service Configuration

The application automatically detects available AWS services and regions. Key configuration points:

- **Default Region**: Set via `AWS_DEFAULT_REGION` environment variable
- **Cost Explorer Region**: Always uses `us-east-1` (AWS requirement)
- **Multi-region Support**: Application attempts multiple regions for service-specific APIs

### Application Settings

Configure via `.streamlit/config.toml`:

```toml
[server]
headless = true
address = "0.0.0.0"
port = 5000
maxUploadSize = 200

[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"

[browser]
gatherUsageStats = false
```

### Cost Analysis Settings

Default settings can be modified in `aws_cost_service.py`:

- **Date Range Limits**: Maximum 365 days for custom ranges
- **Resource Limits**: Top 50 resources displayed
- **API Timeout**: 30 seconds for AWS API calls
- **Cache Duration**: Session-based caching for performance

## Usage Guide

### 1. Initial Setup
- Access the application via the provided URL
- The dashboard loads with default 30-day cost data
- Sidebar provides quick preset options for different time ranges

### 2. Date Range Selection
- Use the date picker at the top to select custom date ranges
- Click "Analyze Date Range" to refresh all data
- Preset buttons (30 days, 90 days, etc.) provide quick access

### 3. Cost Overview Analysis
- **Monthly Costs Tab**: View aggregated monthly costs with trend charts
- **Service Breakdown Tab**: Analyze costs by individual AWS services
- **Daily Analysis Tab**: Examine daily cost patterns (for ranges ≤31 days)

### 4. Service-Level Analysis
- Select a service from the dropdown in the Service Analysis section
- View detailed usage types and monthly breakdowns
- Generate AI-powered optimization recommendations

### 5. Resource Identification
- Click "Get Resource Names" for detailed resource-level analysis
- View actual resource names, IDs, and cost attribution
- Examine utilization scores and optimization opportunities

### 6. Advanced Features
- **Export Data**: Download cost data as CSV files
- **AI Recommendations**: Generate service-specific optimization suggestions
- **Resource Cost Breakdown**: Detailed per-resource cost analysis with daily patterns

## API Integration

### AWS Cost Explorer Integration

```python
# Example cost query
response = cost_explorer.get_cost_and_usage(
    TimePeriod={
        'Start': '2024-01-01',
        'End': '2024-01-31'
    },
    Granularity='MONTHLY',
    Metrics=['BlendedCost'],
    GroupBy=[{
        'Type': 'DIMENSION',
        'Key': 'SERVICE'
    }]
)
```

### Resource API Integration

```python
# Example EC2 instance query
ec2 = boto3.client('ec2')
response = ec2.describe_instances()
for reservation in response['Reservations']:
    for instance in reservation['Instances']:
        instance_id = instance['InstanceId']
        name = get_tag_value(instance.get('Tags', []), 'Name')
```

### AI Integration with AWS Bedrock

```python
# Example AI recommendation request
bedrock = boto3.client('bedrock-runtime')
response = bedrock.invoke_model(
    modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
    body=json.dumps({
        'anthropic_version': 'bedrock-2023-05-31',
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 2000
    })
)
```

## Security Considerations

### AWS Permissions
- Use least-privilege IAM policies
- Regularly rotate access keys
- Consider using IAM roles instead of access keys for production

### Data Protection
- All AWS API communication uses HTTPS
- No sensitive data is stored locally
- Session-based data caching only

### Network Security
- Deploy behind a load balancer with SSL termination
- Use VPC endpoints for AWS API access when possible
- Implement IP whitelisting for production deployments

### Application Security
- Input validation on all user inputs
- Error handling prevents information disclosure
- Rate limiting on AWS API calls

## Troubleshooting

### Common Issues

1. **AWS Permission Errors**:
   ```
   Error: AccessDenied
   Solution: Verify IAM permissions and credentials
   ```

2. **Cost Explorer API Limits**:
   ```
   Error: Throttling
   Solution: Implement exponential backoff (already included)
   ```

3. **Resource API Timeouts**:
   ```
   Error: Timeout
   Solution: Check network connectivity and AWS service status
   ```

4. **Missing Cost Data**:
   ```
   Issue: No cost data for recent dates
   Solution: AWS Cost Explorer has 24-48 hour delay for latest data
   ```

### Debug Mode

Enable debug logging by setting:
```python
logging.basicConfig(level=logging.DEBUG)
```

### Performance Optimization

- Use session state for caching API responses
- Implement pagination for large datasets
- Optimize date ranges for faster queries
- Use parallel API calls where possible

## Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Install development dependencies
4. Make changes and test thoroughly
5. Submit a pull request

### Code Style
- Follow PEP 8 for Python code
- Use type hints for function parameters
- Add docstrings for all functions
- Implement proper error handling

### Testing
- Test with multiple AWS accounts
- Verify all service integrations
- Test edge cases and error conditions
- Validate cost calculations

## Support

For support and questions:
- Review this documentation
- Check AWS service status
- Verify IAM permissions
- Test with minimal date ranges first

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Note**: This tool provides cost estimates and analysis based on AWS Cost Explorer data. Always verify cost calculations with official AWS billing statements for financial decisions.