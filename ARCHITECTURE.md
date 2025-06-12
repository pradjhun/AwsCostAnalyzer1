# System Architecture

## Overview

The AWS Cost Calculator & FinOps Tool follows a modular architecture with clear separation between data layer, service layer, and presentation layer. The system integrates with multiple AWS APIs to provide comprehensive cost analysis and optimization insights.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                        │
├─────────────────────────────────────────────────────────────────┤
│  Streamlit Web Interface                                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │ Dashboard   │ │ Service     │ │ Resource    │ │ AI Insights ││
│  │ Overview    │ │ Analysis    │ │ Breakdown   │ │ & Reports   ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│  AWSCostService (aws_cost_service.py)                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │ Cost        │ │ Resource    │ │ AI          │ │ Data        ││
│  │ Analysis    │ │ Discovery   │ │ Integration │ │ Processing  ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
│                                                                 │
│  Utils (utils.py)                                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │ Data        │ │ Export      │ │ Validation  │ │ Formatting  ││
│  │ Transform   │ │ Functions   │ │ Logic       │ │ Utils       ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATA/API LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│  AWS Services Integration                                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │ Cost        │ │ Bedrock     │ │ Resource    │ │ Service     ││
│  │ Explorer    │ │ AI Models   │ │ Groups      │ │ APIs        ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
│                                                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │ EC2 API     │ │ RDS API     │ │ S3 API      │ │ Lambda API  ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
│                                                                 │
│  ┌─────────────┐ ┌─────────────┐                               │
│  │ Q Business  │ │ IAM/STS     │                               │
│  │ API         │ │ Auth        │                               │
│  └─────────────┘ └─────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### Presentation Layer

#### Streamlit Web Interface (app.py)
- **Purpose**: User interface and interaction management
- **Key Features**:
  - Interactive dashboard with cost visualizations
  - Date range selection and filtering
  - Service-specific analysis views
  - Resource identification displays
  - Export functionality
- **Dependencies**: streamlit, plotly, pandas
- **State Management**: Session-based caching for performance

### Service Layer

#### AWSCostService (aws_cost_service.py)
Main service orchestrator handling all AWS integrations:

**Core Methods**:
- `get_monthly_costs()`: Retrieve monthly cost aggregations
- `get_costs_by_service()`: Service-level cost breakdown
- `get_daily_costs()`: Daily granular cost analysis
- `get_service_detailed_costs()`: Detailed service analysis
- `get_actual_resource_names()`: Resource identification
- `get_resource_level_cost_breakdown()`: Granular resource analysis
- `generate_ai_recommendations()`: AI-powered insights

**Design Patterns**:
- Singleton pattern for AWS client management
- Factory pattern for service-specific resource discovery
- Strategy pattern for different cost analysis approaches

#### Utils Module (utils.py)
Support functions for data processing:

**Core Functions**:
- `format_currency()`: Consistent monetary formatting
- `get_date_range()`: Date calculation utilities
- `export_to_csv()`: Data export functionality
- `calculate_cost_trend()`: Trend analysis
- `validate_date_range()`: Input validation

### Data/API Layer

#### AWS Cost Explorer
- **Purpose**: Primary cost and usage data source
- **API Calls**:
  - GetCostAndUsage: Core cost retrieval
  - GetDimensionValues: Available dimensions
- **Granularity**: Daily, Monthly, Yearly
- **Metrics**: BlendedCost, UnblendedCost, UsageQuantity

#### AWS Bedrock
- **Purpose**: AI-powered analysis and recommendations
- **Model**: Claude 3.5 Sonnet (anthropic.claude-3-5-sonnet-20241022-v2:0)
- **Use Cases**:
  - Cost optimization recommendations
  - Usage pattern analysis
  - Service-specific insights

#### Resource APIs
Individual service APIs for resource identification:

**EC2 API**:
- DescribeInstances: Instance metadata
- Tags and naming information
- Instance types and states

**RDS API**:
- DescribeDBInstances: Database information
- Engine types and configurations
- Performance characteristics

**S3 API**:
- ListBuckets: Bucket enumeration
- Bucket metadata and policies

**Lambda API**:
- ListFunctions: Function inventory
- Runtime and configuration details

**Q Business API**:
- ListApplications: Q Business applications
- ListIndices: Enterprise indices
- Application configurations

## Data Flow Architecture

### Request Processing Flow

```
User Input → Streamlit → AWSCostService → AWS APIs → Data Processing → Visualization
    ↓           ↓            ↓              ↓           ↓              ↓
Date Range → Validation → Cost Queries → Raw Data → Aggregation → Charts/Tables
    ↓           ↓            ↓              ↓           ↓              ↓
Filters    → Parameters → API Calls   → Response  → Transformation → Display
```

### Cost Analysis Pipeline

1. **Data Acquisition**:
   - Parallel API calls to Cost Explorer
   - Service-specific resource enumeration
   - Data validation and error handling

2. **Data Processing**:
   - Cost aggregation by dimensions
   - Resource correlation and mapping
   - Trend calculation and analysis

3. **AI Enhancement**:
   - Context preparation for AI models
   - Bedrock API integration
   - Recommendation generation

4. **Visualization**:
   - Chart data preparation
   - Interactive component rendering
   - Export data formatting

### Resource Identification Pipeline

```
Service Selection → API Discovery → Resource Enumeration → Cost Correlation → Display
       ↓               ↓               ↓                    ↓               ↓
   Amazon Q    → Q Business API → List Applications → Cost Attribution → Index Names
   EC2         → EC2 API        → Describe Instances → Instance Costs   → Instance IDs
   RDS         → RDS API        → Describe DBs       → Database Costs   → DB Names
   S3          → S3 API         → List Buckets       → Storage Costs    → Bucket Names
   Lambda      → Lambda API     → List Functions     → Function Costs   → Function Names
```

## Security Architecture

### Authentication & Authorization

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Access   │    │   AWS STS       │    │   IAM Roles     │
│                 │    │                 │    │                 │
│ Environment     │───▶│ AssumeRole      │───▶│ Cost Explorer   │
│ Variables       │    │ Credentials     │    │ Service APIs    │
│ IAM Keys        │    │ Temporary       │    │ Bedrock Access  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Data Protection
- All API communications over HTTPS/TLS
- No persistent storage of sensitive data
- Session-based temporary caching only
- Input validation and sanitization

### Network Security
- AWS VPC endpoints for private API access
- Security groups and NACLs for container deployment
- Load balancer SSL termination
- WAF protection for public endpoints

## Scalability Architecture

### Horizontal Scaling

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load          │    │   Container     │    │   Auto Scaling  │
│   Balancer      │    │   Orchestration │    │   Groups        │
│                 │    │                 │    │                 │
│ Traffic         │───▶│ ECS/Kubernetes  │───▶│ Dynamic         │
│ Distribution    │    │ Pod Management  │    │ Scaling         │
│ Health Checks   │    │ Service Mesh    │    │ Metrics Based   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Performance Optimization
- Session state caching for API responses
- Parallel API call execution
- Lazy loading for large datasets
- Efficient data structures and algorithms

### Resource Management
- Memory-optimized data processing
- CPU-efficient visualization rendering
- Network bandwidth optimization
- Storage-minimal temporary caching

## Monitoring & Observability

### Application Metrics
- Request latency and throughput
- Error rates by API endpoint
- Resource utilization patterns
- User interaction analytics

### AWS API Metrics
- Cost Explorer API usage
- Service API call volumes
- Rate limit monitoring
- Error categorization

### Business Metrics
- Cost analysis accuracy
- Optimization recommendation effectiveness
- User engagement patterns
- Export usage statistics

## Integration Patterns

### API Integration Strategy
- Circuit breaker pattern for fault tolerance
- Exponential backoff for rate limiting
- Bulk request optimization
- Caching layer for frequently accessed data

### Error Handling Architecture
- Graceful degradation for partial failures
- User-friendly error messaging
- Detailed logging for debugging
- Fallback data sources where applicable

### Extension Points
- Plugin architecture for new AWS services
- Configurable analysis algorithms
- Custom visualization components
- External data source integration

This architecture ensures scalability, maintainability, and extensibility while providing robust cost analysis capabilities for AWS environments.