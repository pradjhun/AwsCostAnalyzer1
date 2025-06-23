import boto3
import os
import numpy as np
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AWSCostService:
    """Service class for interacting with AWS Cost Explorer API"""
    
    def __init__(self):
        """Initialize AWS Cost Explorer client"""
        try:
            # Get AWS credentials from environment variables
            aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
            aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
            aws_region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
            
            if not aws_access_key_id or not aws_secret_access_key:
                raise ValueError("AWS credentials not found in environment variables")
            
            # Initialize boto3 session and Cost Explorer client
            session = boto3.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=aws_region
            )
            
            self.cost_explorer = session.client('ce', region_name='us-east-1')  # Cost Explorer is only available in us-east-1
            self.bedrock = session.client('bedrock-runtime', region_name=aws_region)
            self.ec2 = session.client('ec2', region_name=aws_region)
            self.rds = session.client('rds', region_name=aws_region)
            self.s3 = session.client('s3', region_name=aws_region)
            self.lambda_client = session.client('lambda', region_name=aws_region)
            self.resource_groups = session.client('resourcegroupstaggingapi', region_name=aws_region)
            self.ses_client = session.client('ses', region_name=aws_region)  # For budget notifications
            logger.info("AWS Cost Explorer, Bedrock, and resource clients initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AWS Cost Explorer client: {str(e)}")
            raise
    
    def get_monthly_costs(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Get monthly cost data for the specified date range
        
        Args:
            start_date: Start date for cost data
            end_date: End date for cost data
            
        Returns:
            List of dictionaries containing monthly cost data
        """
        try:
            logger.info(f"Fetching monthly costs from {start_date.date()} to {end_date.date()}")
            
            response = self.cost_explorer.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ]
            )
            
            monthly_costs = []
            
            # Process the response to extract monthly totals
            for result in response['ResultsByTime']:
                start_period = datetime.strptime(result['TimePeriod']['Start'], '%Y-%m-%d')
                month_name = start_period.strftime('%B %Y')
                
                # Calculate total cost for the month
                total_cost = 0.0
                for group in result['Groups']:
                    amount = float(group['Metrics']['BlendedCost']['Amount'])
                    total_cost += amount
                
                monthly_costs.append({
                    'Month': month_name,
                    'Amount': f"${total_cost:,.2f}",
                    'Period': result['TimePeriod']['Start']
                })
            
            # Sort by period to ensure chronological order
            monthly_costs.sort(key=lambda x: x['Period'])
            
            logger.info(f"Successfully retrieved {len(monthly_costs)} months of cost data")
            return monthly_costs
            
        except Exception as e:
            logger.error(f"Error fetching monthly costs: {str(e)}")
            raise Exception(f"Failed to fetch monthly cost data: {str(e)}")
    
    def get_costs_by_service(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Get cost breakdown by AWS service for the specified date range
        
        Args:
            start_date: Start date for cost data
            end_date: End date for cost data
            
        Returns:
            List of dictionaries containing service cost data
        """
        try:
            logger.info(f"Fetching service costs from {start_date.date()} to {end_date.date()}")
            
            response = self.cost_explorer.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ]
            )
            
            service_costs = {}
            
            # Aggregate costs by service across all months
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    service_name = group['Keys'][0] if group['Keys'] else 'Unknown Service'
                    amount = float(group['Metrics']['BlendedCost']['Amount'])
                    
                    if service_name in service_costs:
                        service_costs[service_name] += amount
                    else:
                        service_costs[service_name] = amount
            
            # Convert to list of dictionaries and sort by cost (descending)
            service_list = []
            for service, cost in service_costs.items():
                if cost > 0:  # Only include services with actual costs
                    service_list.append({
                        'Service': service,
                        'Amount': f"${cost:,.2f}"
                    })
            
            # Sort by cost amount (descending)
            service_list.sort(key=lambda x: float(x['Amount'].replace('$', '').replace(',', '')), reverse=True)
            
            logger.info(f"Successfully retrieved cost data for {len(service_list)} services")
            return service_list
            
        except Exception as e:
            logger.error(f"Error fetching service costs: {str(e)}")
            raise Exception(f"Failed to fetch service cost data: {str(e)}")
    
    def get_daily_costs(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Get daily cost data for the specified date range
        
        Args:
            start_date: Start date for cost data
            end_date: End date for cost data
            
        Returns:
            List of dictionaries containing daily cost data
        """
        try:
            logger.info(f"Fetching daily costs from {start_date.date()} to {end_date.date()}")
            
            response = self.cost_explorer.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['BlendedCost']
            )
            
            daily_costs = []
            
            for result in response['ResultsByTime']:
                date = result['TimePeriod']['Start']
                total_cost = float(result['Total']['BlendedCost']['Amount'])
                
                daily_costs.append({
                    'Date': date,
                    'Amount': f"${total_cost:,.2f}"
                })
            
            logger.info(f"Successfully retrieved {len(daily_costs)} days of cost data")
            return daily_costs
            
        except Exception as e:
            logger.error(f"Error fetching daily costs: {str(e)}")
            raise Exception(f"Failed to fetch daily cost data: {str(e)}")
    
    def get_cost_forecast(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get cost forecast for the specified date range
        
        Args:
            start_date: Start date for forecast
            end_date: End date for forecast
            
        Returns:
            Dictionary containing forecast data
        """
        try:
            logger.info(f"Fetching cost forecast from {start_date.date()} to {end_date.date()}")
            
            response = self.cost_explorer.get_cost_forecast(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Metric='BLENDED_COST',
                Granularity='MONTHLY'
            )
            
            total_forecast = float(response['Total']['Amount'])
            
            forecast_data = {
                'Total': f"${total_forecast:,.2f}",
                'Period': f"{start_date.strftime('%B %Y')} - {end_date.strftime('%B %Y')}",
                'MeanValue': f"${float(response['Total']['Amount']):,.2f}"
            }
            
            logger.info("Successfully retrieved cost forecast")
            return forecast_data
            
        except Exception as e:
            logger.error(f"Error fetching cost forecast: {str(e)}")
            raise Exception(f"Failed to fetch cost forecast: {str(e)}")
    
    def get_service_detailed_costs(self, service_name: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get detailed cost breakdown for a specific AWS service with resource-level granularity
        
        Args:
            service_name: Name of the AWS service
            start_date: Start date for cost data
            end_date: End date for cost data
            
        Returns:
            Dictionary containing detailed service cost breakdown
        """
        try:
            logger.info(f"Fetching detailed costs for {service_name} from {start_date.date()} to {end_date.date()}")
            
            # Get cost breakdown by usage type for the service
            response = self.cost_explorer.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost', 'UsageQuantity'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'USAGE_TYPE'
                    }
                ],
                Filter={
                    'Dimensions': {
                        'Key': 'SERVICE',
                        'Values': [service_name]
                    }
                }
            )
            
            usage_breakdown = []
            monthly_data = {}
            
            # Process response to get usage type breakdown
            for result in response['ResultsByTime']:
                month = datetime.strptime(result['TimePeriod']['Start'], '%Y-%m-%d').strftime('%B %Y')
                
                for group in result['Groups']:
                    usage_type = group['Keys'][0] if group['Keys'] else 'Unknown Usage Type'
                    cost = float(group['Metrics']['BlendedCost']['Amount'])
                    usage = float(group['Metrics']['UsageQuantity']['Amount'])
                    
                    if cost > 0:
                        usage_breakdown.append({
                            'Month': month,
                            'Usage_Type': usage_type,
                            'Cost': f"${cost:,.2f}",
                            'Usage_Quantity': f"{usage:,.2f}",
                            'Cost_Numeric': cost
                        })
                        
                        if month not in monthly_data:
                            monthly_data[month] = 0
                        monthly_data[month] += cost
            
            # Get instance-level breakdown using valid dimensions
            resource_breakdown = []
            try:
                # Try to get breakdown by instance type (works for EC2, RDS, etc.)
                instance_response = self.cost_explorer.get_cost_and_usage(
                    TimePeriod={
                        'Start': start_date.strftime('%Y-%m-%d'),
                        'End': end_date.strftime('%Y-%m-%d')
                    },
                    Granularity='MONTHLY',
                    Metrics=['BlendedCost'],
                    GroupBy=[
                        {
                            'Type': 'DIMENSION',
                            'Key': 'INSTANCE_TYPE'
                        }
                    ],
                    Filter={
                        'Dimensions': {
                            'Key': 'SERVICE',
                            'Values': [service_name]
                        }
                    }
                )
                
                for result in instance_response['ResultsByTime']:
                    for group in result['Groups']:
                        instance_type = group['Keys'][0] if group['Keys'] else 'Unknown Type'
                        cost = float(group['Metrics']['BlendedCost']['Amount'])
                        
                        if cost > 0 and instance_type not in ['NoInstanceType', '']:
                            resource_breakdown.append({
                                'Resource_Type': instance_type,
                                'Cost': f"${cost:,.2f}",
                                'Cost_Numeric': cost,
                                'Category': 'Instance Type'
                            })
                
            except Exception as e:
                logger.debug(f"Instance type grouping not available for {service_name}: {str(e)}")
            
            # Try to get breakdown by availability zone
            try:
                az_response = self.cost_explorer.get_cost_and_usage(
                    TimePeriod={
                        'Start': start_date.strftime('%Y-%m-%d'),
                        'End': end_date.strftime('%Y-%m-%d')
                    },
                    Granularity='MONTHLY',
                    Metrics=['BlendedCost'],
                    GroupBy=[
                        {
                            'Type': 'DIMENSION',
                            'Key': 'AZ'
                        }
                    ],
                    Filter={
                        'Dimensions': {
                            'Key': 'SERVICE',
                            'Values': [service_name]
                        }
                    }
                )
                
                for result in az_response['ResultsByTime']:
                    for group in result['Groups']:
                        az = group['Keys'][0] if group['Keys'] else 'Unknown AZ'
                        cost = float(group['Metrics']['BlendedCost']['Amount'])
                        
                        if cost > 0 and az not in ['NoAZ', '']:
                            resource_breakdown.append({
                                'Resource_Type': az,
                                'Cost': f"${cost:,.2f}",
                                'Cost_Numeric': cost,
                                'Category': 'Availability Zone'
                            })
                
            except Exception as e:
                logger.debug(f"AZ grouping not available for {service_name}: {str(e)}")
            
            # Try to get breakdown by platform (for EC2)
            try:
                platform_response = self.cost_explorer.get_cost_and_usage(
                    TimePeriod={
                        'Start': start_date.strftime('%Y-%m-%d'),
                        'End': end_date.strftime('%Y-%m-%d')
                    },
                    Granularity='MONTHLY',
                    Metrics=['BlendedCost'],
                    GroupBy=[
                        {
                            'Type': 'DIMENSION',
                            'Key': 'PLATFORM'
                        }
                    ],
                    Filter={
                        'Dimensions': {
                            'Key': 'SERVICE',
                            'Values': [service_name]
                        }
                    }
                )
                
                for result in platform_response['ResultsByTime']:
                    for group in result['Groups']:
                        platform = group['Keys'][0] if group['Keys'] else 'Unknown Platform'
                        cost = float(group['Metrics']['BlendedCost']['Amount'])
                        
                        if cost > 0 and platform not in ['NoPlatform', '']:
                            resource_breakdown.append({
                                'Resource_Type': platform,
                                'Cost': f"${cost:,.2f}",
                                'Cost_Numeric': cost,
                                'Category': 'Platform'
                            })
                
            except Exception as e:
                logger.debug(f"Platform grouping not available for {service_name}: {str(e)}")
            
            # Sort by cost (descending)
            resource_breakdown.sort(key=lambda x: x['Cost_Numeric'], reverse=True)
            
            if not resource_breakdown:
                logger.warning(f"Could not fetch detailed resource data for {service_name} using available dimensions")
            
            # Sort usage breakdown by cost
            usage_breakdown.sort(key=lambda x: x['Cost_Numeric'], reverse=True)
            
            # Calculate total cost for the service
            total_cost = sum([item['Cost_Numeric'] for item in usage_breakdown])
            
            return {
                'service_name': service_name,
                'total_cost': total_cost,
                'usage_breakdown': usage_breakdown,
                'resource_breakdown': resource_breakdown[:20],  # Top 20 resources
                'monthly_data': monthly_data
            }
            
        except Exception as e:
            logger.error(f"Error fetching detailed costs for {service_name}: {str(e)}")
            raise Exception(f"Failed to fetch detailed cost data for {service_name}: {str(e)}")
    
    def generate_ai_recommendations(self, service_data: Dict[str, Any], all_services_data: List[Dict[str, Any]]) -> str:
        """
        Generate AI-powered cost optimization recommendations using AWS Bedrock
        
        Args:
            service_data: Detailed cost data for the specific service
            all_services_data: Cost data for all services for context
            
        Returns:
            AI-generated recommendations as string
        """
        try:
            import json
            
            # Prepare context for the AI
            context = {
                "service_name": service_data['service_name'],
                "total_cost": service_data['total_cost'],
                "usage_breakdown": service_data['usage_breakdown'][:10],  # Top 10 usage types
                "resource_breakdown": service_data['resource_breakdown'][:10],  # Top 10 resources
                "monthly_trends": service_data['monthly_data'],
                "total_aws_spend": sum([float(s['Amount'].replace('$', '').replace(',', '')) for s in all_services_data])
            }
            
            prompt = f"""
            You are an AWS FinOps expert analyzing cost data. Based on the following AWS service cost breakdown, provide specific, actionable cost optimization recommendations.

            Service Analysis:
            - Service: {context['service_name']}
            - Total Cost (6 months): ${context['total_cost']:,.2f}
            - Percentage of total AWS spend: {(context['total_cost'] / context['total_aws_spend'] * 100):.1f}%

            Usage Breakdown (Top cost drivers):
            {json.dumps(context['usage_breakdown'], indent=2)}

            Resource Breakdown (if available):
            {json.dumps(context['resource_breakdown'], indent=2)}

            Monthly Trends:
            {json.dumps(context['monthly_trends'], indent=2)}

            Please provide:
            1. **Immediate Cost Optimization Opportunities** (3-5 specific actions)
            2. **Resource Right-Sizing Recommendations** (if applicable)
            3. **Architecture Optimization Suggestions**
            4. **Potential Monthly Savings Estimate**
            5. **Implementation Priority** (High/Medium/Low for each recommendation)

            Keep recommendations practical, specific to the usage patterns shown, and include estimated savings percentages where possible.
            """
            
            # Call AWS Bedrock Claude model
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
            
            response = self.bedrock.invoke_model(
                modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                contentType="application/json",
                accept="application/json",
                body=body
            )
            
            response_body = json.loads(response['body'].read())
            recommendations = response_body['content'][0]['text']
            
            logger.info(f"Successfully generated AI recommendations for {service_data['service_name']}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating AI recommendations: {str(e)}")
            return f"Unable to generate AI recommendations at this time. Error: {str(e)}\n\nPlease ensure you have access to AWS Bedrock Claude models in your region."
    
    def get_usage_type_details(self, service_name: str, usage_type: str, month: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get detailed breakdown for a specific usage type within a service for a specific month
        
        Args:
            service_name: Name of the AWS service
            usage_type: Specific usage type to analyze
            month: Month to analyze (format: "YYYY-MM")
            start_date: Start date for cost data
            end_date: End date for cost data
            
        Returns:
            Dictionary containing detailed usage type breakdown
        """
        try:
            logger.info(f"Fetching detailed breakdown for {service_name} - {usage_type} in {month}")
            
            # Parse month to get specific date range
            month_start = datetime.strptime(month, '%Y-%m')
            if month_start.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1, day=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1, day=1)
            
            # Get detailed breakdown with multiple dimensions
            response = self.cost_explorer.get_cost_and_usage(
                TimePeriod={
                    'Start': month_start.strftime('%Y-%m-%d'),
                    'End': month_end.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['BlendedCost', 'UsageQuantity'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'OPERATION'
                    }
                ],
                Filter={
                    'And': [
                        {
                            'Dimensions': {
                                'Key': 'SERVICE',
                                'Values': [service_name]
                            }
                        },
                        {
                            'Dimensions': {
                                'Key': 'USAGE_TYPE',
                                'Values': [usage_type]
                            }
                        }
                    ]
                }
            )
            
            daily_breakdown = []
            operation_breakdown = {}
            total_cost = 0
            total_usage = 0
            
            # Process daily data
            for result in response['ResultsByTime']:
                date = result['TimePeriod']['Start']
                daily_cost = 0
                daily_usage = 0
                
                for group in result['Groups']:
                    operation = group['Keys'][0] if group['Keys'] else 'Unknown Operation'
                    cost = float(group['Metrics']['BlendedCost']['Amount'])
                    usage = float(group['Metrics']['UsageQuantity']['Amount'])
                    
                    daily_cost += cost
                    daily_usage += usage
                    
                    if operation not in operation_breakdown:
                        operation_breakdown[operation] = {'cost': 0, 'usage': 0}
                    operation_breakdown[operation]['cost'] += cost
                    operation_breakdown[operation]['usage'] += usage
                
                if daily_cost > 0:
                    daily_breakdown.append({
                        'Date': date,
                        'Cost': f"${daily_cost:,.2f}",
                        'Usage_Quantity': f"{daily_usage:,.2f}",
                        'Cost_Numeric': daily_cost,
                        'Usage_Numeric': daily_usage
                    })
                
                total_cost += daily_cost
                total_usage += daily_usage
            
            # Convert operation breakdown to list
            operations = []
            for operation, data in operation_breakdown.items():
                if data['cost'] > 0:
                    operations.append({
                        'Operation': operation,
                        'Cost': f"${data['cost']:,.2f}",
                        'Usage_Quantity': f"{data['usage']:,.2f}",
                        'Cost_Numeric': data['cost'],
                        'Usage_Numeric': data['usage']
                    })
            
            # Sort by cost (descending)
            operations.sort(key=lambda x: x['Cost_Numeric'], reverse=True)
            daily_breakdown.sort(key=lambda x: x['Date'])
            
            # Get region breakdown if available
            try:
                region_response = self.cost_explorer.get_cost_and_usage(
                    TimePeriod={
                        'Start': month_start.strftime('%Y-%m-%d'),
                        'End': month_end.strftime('%Y-%m-%d')
                    },
                    Granularity='MONTHLY',
                    Metrics=['BlendedCost'],
                    GroupBy=[
                        {
                            'Type': 'DIMENSION',
                            'Key': 'REGION'
                        }
                    ],
                    Filter={
                        'And': [
                            {
                                'Dimensions': {
                                    'Key': 'SERVICE',
                                    'Values': [service_name]
                                }
                            },
                            {
                                'Dimensions': {
                                    'Key': 'USAGE_TYPE',
                                    'Values': [usage_type]
                                }
                            }
                        ]
                    }
                )
                
                regions = []
                for result in region_response['ResultsByTime']:
                    for group in result['Groups']:
                        region = group['Keys'][0] if group['Keys'] else 'Unknown Region'
                        cost = float(group['Metrics']['BlendedCost']['Amount'])
                        
                        if cost > 0:
                            regions.append({
                                'Region': region,
                                'Cost': f"${cost:,.2f}",
                                'Cost_Numeric': cost
                            })
                
                regions.sort(key=lambda x: x['Cost_Numeric'], reverse=True)
                
            except Exception as e:
                logger.warning(f"Could not fetch region data: {str(e)}")
                regions = []
            
            return {
                'service_name': service_name,
                'usage_type': usage_type,
                'month': month,
                'total_cost': total_cost,
                'total_usage': total_usage,
                'daily_breakdown': daily_breakdown,
                'operation_breakdown': operations,
                'region_breakdown': regions
            }
            
        except Exception as e:
            logger.error(f"Error fetching usage type details: {str(e)}")
            raise Exception(f"Failed to fetch usage type details: {str(e)}")
    
    def get_actual_resource_names(self, service_name: str, usage_type: str, month: str) -> List[Dict[str, Any]]:
        """
        Get actual resource names and identifiers for specific services
        
        Args:
            service_name: AWS service name
            usage_type: Usage type to analyze
            month: Month to analyze
            
        Returns:
            List of dictionaries containing actual resource information
        """
        resources = []
        
        try:
            # Amazon Q Business - get indices and applications
            if 'Amazon Q' in service_name:
                try:
                    # Initialize Q Business client with correct region
                    regions_to_try = ['us-east-1', 'us-west-2', 'eu-west-1']
                    qbusiness = None
                    
                    for region in regions_to_try:
                        try:
                            qbusiness = boto3.client('qbusiness', region_name=region)
                            # Test the connection
                            applications = qbusiness.list_applications()
                            break
                        except Exception as e:
                            logger.debug(f"Q Business not available in {region}: {str(e)}")
                            continue
                    
                    if qbusiness:
                        # List applications
                        applications = qbusiness.list_applications()
                        for app in applications.get('applications', []):
                            app_id = app.get('applicationId')
                            app_name = app.get('displayName', app_id)
                            
                            # Get indices for this application
                            try:
                                indices = qbusiness.list_indices(applicationId=app_id)
                                for index in indices.get('indices', []):
                                    index_id = index.get('indexId')
                                    index_name = index.get('displayName', index_id)
                                    resources.append({
                                        'resource_name': index_name,
                                        'resource_id': index_id,
                                        'application': app_name,
                                        'application_id': app_id,
                                        'status': index.get('status', 'Unknown')
                                    })
                            except Exception as e:
                                logger.debug(f"Could not list indices for app {app_id}: {str(e)}")
                    else:
                        logger.warning("Q Business service not available in any tested region")
                            
                except Exception as e:
                    logger.warning(f"Could not access Q Business resources: {str(e)}")
            
            # EC2 instances
            elif 'EC2' in service_name or 'Elastic Compute' in service_name:
                try:
                    response = self.ec2.describe_instances()
                    for reservation in response['Reservations']:
                        for instance in reservation['Instances']:
                            instance_id = instance['InstanceId']
                            name_tag = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), f"EC2-{instance_id}")
                            resources.append({
                                'resource_name': name_tag,
                                'resource_id': instance_id,
                                'instance_type': instance.get('InstanceType', 'Unknown'),
                                'state': instance.get('State', {}).get('Name', 'Unknown'),
                                'az': instance.get('Placement', {}).get('AvailabilityZone', 'Unknown')
                            })
                except Exception as e:
                    logger.warning(f"Could not list EC2 instances: {str(e)}")
            
            # RDS instances
            elif 'RDS' in service_name or 'Relational Database' in service_name:
                try:
                    response = self.rds.describe_db_instances()
                    for db in response['DBInstances']:
                        db_id = db['DBInstanceIdentifier']
                        db_name = db.get('DBName') or db_id
                        resources.append({
                            'resource_name': db_name,
                            'resource_id': db_id,
                            'instance_class': db.get('DBInstanceClass', 'Unknown'),
                            'state': db.get('DBInstanceStatus', 'Unknown'),
                            'engine': db.get('Engine', 'Unknown')
                        })
                except Exception as e:
                    logger.warning(f"Could not list RDS instances: {str(e)}")
            
            # S3 buckets
            elif 'S3' in service_name or 'Simple Storage' in service_name:
                try:
                    response = self.s3.list_buckets()
                    for bucket in response['Buckets']:
                        bucket_name = bucket['Name']
                        resources.append({
                            'resource_name': bucket_name,
                            'resource_id': bucket_name,
                            'creation_date': bucket.get('CreationDate', 'Unknown')
                        })
                except Exception as e:
                    logger.warning(f"Could not list S3 buckets: {str(e)}")
            
            # Lambda functions
            elif 'Lambda' in service_name:
                try:
                    response = self.lambda_client.list_functions()
                    for function in response['Functions']:
                        function_name = function['FunctionName']
                        resources.append({
                            'resource_name': function_name,
                            'resource_id': function_name,
                            'runtime': function.get('Runtime', 'Unknown'),
                            'state': function.get('State', 'Unknown')
                        })
                except Exception as e:
                    logger.warning(f"Could not list Lambda functions: {str(e)}")
            
            # Use Resource Groups Tagging API as fallback
            else:
                try:
                    # Try to get resources using the resource groups API
                    response = self.resource_groups.get_resources(
                        ResourcesPerPage=100,
                        ResourceTypeFilters=[service_name] if service_name else []
                    )
                    
                    for resource in response.get('ResourceTagMappingList', []):
                        arn = resource.get('ResourceARN', '')
                        resource_id = arn.split('/')[-1] if '/' in arn else arn.split(':')[-1]
                        name_tag = next((tag['Value'] for tag in resource.get('Tags', []) if tag['Key'] == 'Name'), resource_id)
                        
                        resources.append({
                            'resource_name': name_tag,
                            'resource_id': resource_id,
                            'resource_type': arn.split(':')[2] if ':' in arn else 'Unknown',
                            'arn': arn
                        })
                        
                except Exception as e:
                    logger.warning(f"Could not use Resource Groups API for {service_name}: {str(e)}")
            
            logger.info(f"Found {len(resources)} resources for {service_name}")
            return resources
            
        except Exception as e:
            logger.error(f"Error getting resource names for {service_name}: {str(e)}")
            return []

    def get_resource_level_cost_breakdown(self, service_name: str, usage_type: str, month: str, 
                                        month_start: datetime, month_end: datetime) -> Dict[str, Any]:
        """
        Get detailed resource-level cost breakdown combining actual resources with cost data
        
        Args:
            service_name: AWS service name
            usage_type: Usage type to analyze
            month: Month string (YYYY-MM)
            month_start: Start of month datetime
            month_end: End of month datetime
            
        Returns:
            Dictionary containing detailed resource cost breakdown
        """
        try:
            logger.info(f"Generating resource-level cost breakdown for {service_name} - {usage_type}")
            
            breakdown = {
                'service_name': service_name,
                'usage_type': usage_type,
                'month': month,
                'resource_costs': [],
                'daily_breakdown': [],
                'hourly_patterns': [],
                'cost_trends': {},
                'optimization_opportunities': []
            }
            
            # Get actual resources for this service
            actual_resources = self.get_actual_resource_names(service_name, usage_type, month)
            
            # Get daily cost breakdown for the month
            daily_response = self.cost_explorer.get_cost_and_usage(
                TimePeriod={
                    'Start': month_start.strftime('%Y-%m-%d'),
                    'End': month_end.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['BlendedCost', 'UsageQuantity'],
                Filter={
                    'And': [
                        {
                            'Dimensions': {
                                'Key': 'SERVICE',
                                'Values': [service_name]
                            }
                        },
                        {
                            'Dimensions': {
                                'Key': 'USAGE_TYPE',
                                'Values': [usage_type]
                            }
                        }
                    ]
                }
            )
            
            # Process daily costs
            daily_costs = []
            for result in daily_response['ResultsByTime']:
                date = result['TimePeriod']['Start']
                cost = float(result['Total']['BlendedCost']['Amount'])
                usage = float(result['Total']['UsageQuantity']['Amount'])
                
                daily_costs.append({
                    'date': date,
                    'cost': cost,
                    'usage': usage,
                    'cost_formatted': f"${cost:,.2f}",
                    'usage_formatted': f"{usage:,.2f}"
                })
            
            breakdown['daily_breakdown'] = daily_costs
            
            # Analyze cost trends
            if daily_costs:
                costs_only = [d['cost'] for d in daily_costs]
                breakdown['cost_trends'] = {
                    'avg_daily_cost': sum(costs_only) / len(costs_only),
                    'max_daily_cost': max(costs_only),
                    'min_daily_cost': min(costs_only),
                    'total_cost': sum(costs_only),
                    'cost_variance': np.var(costs_only) if len(costs_only) > 1 else 0,
                    'trend_direction': 'increasing' if costs_only[-1] > costs_only[0] else 'decreasing'
                }
            
            # Match actual resources with cost data using multiple dimensions
            resource_cost_mapping = []
            
            if actual_resources:
                for resource in actual_resources:
                    resource_name = resource.get('resource_name', 'Unknown')
                    resource_id = resource.get('resource_id', 'Unknown')
                    
                    # Try to get cost data for this specific resource using different approaches
                    estimated_cost = 0
                    cost_confidence = 'Low'
                    
                    # For Amazon Q, try to correlate with application-level costs
                    if 'Amazon Q' in service_name:
                        app_name = resource.get('application', '')
                        # Estimate cost based on total usage divided by number of resources
                        if breakdown['cost_trends'].get('total_cost', 0) > 0:
                            estimated_cost = breakdown['cost_trends']['total_cost'] / len(actual_resources)
                            cost_confidence = 'Estimated'
                    
                    # For EC2, try to get instance-specific costs
                    elif 'EC2' in service_name and resource.get('instance_type'):
                        try:
                            instance_cost_response = self.cost_explorer.get_cost_and_usage(
                                TimePeriod={
                                    'Start': month_start.strftime('%Y-%m-%d'),
                                    'End': month_end.strftime('%Y-%m-%d')
                                },
                                Granularity='MONTHLY',
                                Metrics=['BlendedCost'],
                                GroupBy=[
                                    {
                                        'Type': 'DIMENSION',
                                        'Key': 'INSTANCE_TYPE'
                                    }
                                ],
                                Filter={
                                    'And': [
                                        {
                                            'Dimensions': {
                                                'Key': 'SERVICE',
                                                'Values': [service_name]
                                            }
                                        },
                                        {
                                            'Dimensions': {
                                                'Key': 'USAGE_TYPE',
                                                'Values': [usage_type]
                                            }
                                        }
                                    ]
                                }
                            )
                            
                            # Find matching instance type
                            for result in instance_cost_response['ResultsByTime']:
                                for group in result['Groups']:
                                    if group['Keys'][0] == resource.get('instance_type'):
                                        estimated_cost = float(group['Metrics']['BlendedCost']['Amount'])
                                        cost_confidence = 'High'
                                        break
                        except Exception as e:
                            logger.debug(f"Could not get instance-specific cost: {str(e)}")
                    
                    # Calculate cost per day for this resource
                    daily_cost = estimated_cost / len(daily_costs) if daily_costs else 0
                    
                    resource_cost_mapping.append({
                        'resource_name': resource_name,
                        'resource_id': resource_id,
                        'estimated_monthly_cost': estimated_cost,
                        'estimated_daily_cost': daily_cost,
                        'cost_confidence': cost_confidence,
                        'cost_formatted': f"${estimated_cost:,.2f}",
                        'daily_cost_formatted': f"${daily_cost:,.2f}",
                        'resource_details': resource,
                        'utilization_score': self._calculate_utilization_score(resource, daily_costs),
                        'optimization_potential': self._identify_optimization_opportunities(resource, estimated_cost, daily_costs)
                    })
            
            # Sort by estimated cost
            resource_cost_mapping.sort(key=lambda x: x['estimated_monthly_cost'], reverse=True)
            breakdown['resource_costs'] = resource_cost_mapping
            
            # Generate optimization recommendations
            breakdown['optimization_opportunities'] = self._generate_resource_optimization_recommendations(
                resource_cost_mapping, breakdown['cost_trends']
            )
            
            logger.info(f"Generated cost breakdown for {len(resource_cost_mapping)} resources")
            return breakdown
            
        except Exception as e:
            logger.error(f"Error generating resource-level cost breakdown: {str(e)}")
            return {
                'service_name': service_name,
                'usage_type': usage_type,
                'month': month,
                'resource_costs': [],
                'daily_breakdown': [],
                'cost_trends': {},
                'optimization_opportunities': [],
                'error': str(e)
            }

    def _calculate_utilization_score(self, resource: Dict[str, Any], daily_costs: List[Dict[str, Any]]) -> float:
        """Calculate utilization score for a resource based on cost patterns"""
        try:
            if not daily_costs:
                return 0.0
            
            # Simple utilization based on cost consistency
            costs = [d['cost'] for d in daily_costs if d['cost'] > 0]
            if not costs:
                return 0.0
            
            # Higher variance = lower utilization score
            avg_cost = sum(costs) / len(costs)
            variance = sum((c - avg_cost) ** 2 for c in costs) / len(costs)
            utilization = max(0, 100 - (variance / avg_cost * 100)) if avg_cost > 0 else 0
            
            return min(100, max(0, utilization))
        except:
            return 50.0  # Default moderate score

    def _identify_optimization_opportunities(self, resource: Dict[str, Any], 
                                           estimated_cost: float, daily_costs: List[Dict[str, Any]]) -> List[str]:
        """Identify optimization opportunities for a resource"""
        opportunities = []
        
        try:
            if estimated_cost > 100:  # High cost resources
                opportunities.append("High-cost resource - review necessity")
            
            if daily_costs:
                costs = [d['cost'] for d in daily_costs if d['cost'] > 0]
                if costs:
                    zero_cost_days = len([d for d in daily_costs if d['cost'] == 0])
                    if zero_cost_days > len(daily_costs) * 0.3:  # 30% zero usage
                        opportunities.append("Low utilization - consider rightsizing")
                    
                    # Check for weekend patterns (if we have enough data)
                    if len(costs) >= 7:
                        weekend_avg = sum(costs[-2:]) / 2  # Last 2 days approximation
                        weekday_avg = sum(costs[:-2]) / max(1, len(costs) - 2)
                        if weekend_avg < weekday_avg * 0.5:
                            opportunities.append("Weekend idle time - consider scheduling")
            
            # Service-specific recommendations
            service_type = resource.get('resource_type', '').lower()
            if 'ec2' in service_type or 'instance' in service_type:
                opportunities.append("Consider Reserved Instances for steady workloads")
            elif 's3' in service_type:
                opportunities.append("Review storage class optimization")
            elif 'lambda' in service_type:
                opportunities.append("Optimize memory allocation and timeout settings")
            
        except Exception as e:
            logger.debug(f"Error identifying optimization opportunities: {str(e)}")
        
        return opportunities[:3]  # Return top 3 opportunities

    def _generate_resource_optimization_recommendations(self, resource_costs: List[Dict[str, Any]], 
                                                      cost_trends: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate comprehensive optimization recommendations"""
        recommendations = []
        
        try:
            if not resource_costs:
                return recommendations
            
            total_cost = cost_trends.get('total_cost', 0)
            
            # High cost resource recommendations
            high_cost_resources = [r for r in resource_costs if r['estimated_monthly_cost'] > total_cost * 0.2]
            if high_cost_resources:
                recommendations.append({
                    'type': 'High Cost Resources',
                    'description': f"Found {len(high_cost_resources)} resources consuming >20% of total cost",
                    'action': 'Review and optimize these high-impact resources first',
                    'potential_savings': sum([r['estimated_monthly_cost'] * 0.1 for r in high_cost_resources]),
                    'resources': [r['resource_name'] for r in high_cost_resources[:5]]
                })
            
            # Low utilization recommendations
            low_util_resources = [r for r in resource_costs if r['utilization_score'] < 30]
            if low_util_resources:
                recommendations.append({
                    'type': 'Low Utilization',
                    'description': f"Found {len(low_util_resources)} underutilized resources",
                    'action': 'Consider rightsizing, scheduling, or terminating unused resources',
                    'potential_savings': sum([r['estimated_monthly_cost'] * 0.3 for r in low_util_resources]),
                    'resources': [r['resource_name'] for r in low_util_resources[:5]]
                })
            
            # Cost trend recommendations
            if cost_trends.get('trend_direction') == 'increasing':
                recommendations.append({
                    'type': 'Cost Trend Alert',
                    'description': 'Costs are trending upward this month',
                    'action': 'Investigate recent changes and implement cost controls',
                    'potential_savings': cost_trends.get('avg_daily_cost', 0) * 5,  # 5 days of average cost
                    'resources': []
                })
            
        except Exception as e:
            logger.debug(f"Error generating optimization recommendations: {str(e)}")
        
        return recommendations

    def validate_email(self, email: str) -> bool:
        """Validate email address format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def verify_ses_email(self, email: str) -> Dict[str, Any]:
        """Verify email address with SES"""
        try:
            response = self.ses_client.get_identity_verification_attributes(
                Identities=[email]
            )
            
            verification_status = response.get('VerificationAttributes', {}).get(email, {}).get('VerificationStatus', 'NotStarted')
            
            return {
                'email': email,
                'verified': verification_status == 'Success',
                'status': verification_status,
                'pending_verification': verification_status == 'Pending'
            }
        except Exception as e:
            logger.warning(f"Could not check SES verification status for {email}: {str(e)}")
            return {
                'email': email,
                'verified': False,
                'status': 'Unknown',
                'pending_verification': False,
                'error': str(e)
            }

    def send_verification_email(self, email: str) -> Dict[str, Any]:
        """Send verification email through SES"""
        try:
            self.ses_client.verify_email_identity(EmailAddress=email)
            
            return {
                'success': True,
                'message': f'Verification email sent to {email}. Please check your inbox and click the verification link.',
                'email': email
            }
        except Exception as e:
            logger.error(f"Failed to send verification email to {email}: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to send verification email: {str(e)}',
                'email': email,
                'error': str(e)
            }

    def check_budget_threshold(self, budget_amount: float, current_month_cost: float, email: str) -> Dict[str, Any]:
        """Check if current costs exceed budget threshold"""
        try:
            threshold_percentage = (current_month_cost / budget_amount) * 100 if budget_amount > 0 else 0
            
            budget_status = {
                'budget_amount': budget_amount,
                'current_cost': current_month_cost,
                'remaining_budget': budget_amount - current_month_cost,
                'threshold_percentage': threshold_percentage,
                'email': email,
                'exceeded': current_month_cost > budget_amount,
                'warning_80': threshold_percentage >= 80,
                'warning_90': threshold_percentage >= 90,
                'timestamp': datetime.now().isoformat()
            }
            
            # Determine notification level
            if budget_status['exceeded']:
                budget_status['alert_level'] = 'critical'
                budget_status['message'] = f"Budget exceeded! Current cost ${current_month_cost:,.2f} exceeds budget ${budget_amount:,.2f}"
            elif budget_status['warning_90']:
                budget_status['alert_level'] = 'high'
                budget_status['message'] = f"Budget warning: 90% threshold reached. Current cost ${current_month_cost:,.2f}"
            elif budget_status['warning_80']:
                budget_status['alert_level'] = 'medium'
                budget_status['message'] = f"Budget alert: 80% threshold reached. Current cost ${current_month_cost:,.2f}"
            else:
                budget_status['alert_level'] = 'normal'
                budget_status['message'] = f"Budget on track. Current cost ${current_month_cost:,.2f} of ${budget_amount:,.2f}"
            
            return budget_status
            
        except Exception as e:
            logger.error(f"Error checking budget threshold: {str(e)}")
            return {
                'error': str(e),
                'budget_amount': budget_amount,
                'current_cost': current_month_cost,
                'email': email
            }

    def send_budget_notification(self, budget_status: Dict[str, Any]) -> Dict[str, Any]:
        """Send budget notification email"""
        try:
            email = budget_status['email']
            alert_level = budget_status.get('alert_level', 'normal')
            
            # Skip sending if no alert needed
            if alert_level == 'normal':
                return {
                    'sent': False,
                    'reason': 'No alert threshold reached',
                    'email': email
                }
            
            # Check if email is verified
            verification_status = self.verify_ses_email(email)
            if not verification_status['verified']:
                return {
                    'sent': False,
                    'reason': 'Email not verified with SES',
                    'email': email,
                    'verification_status': verification_status
                }
            
            # Prepare email content
            subject = self._get_notification_subject(alert_level, budget_status)
            body_text, body_html = self._get_notification_body(budget_status)
            
            # Send email
            response = self.ses_client.send_email(
                Source=email,  # Must be verified email
                Destination={'ToAddresses': [email]},
                Message={
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': {
                        'Text': {'Data': body_text, 'Charset': 'UTF-8'},
                        'Html': {'Data': body_html, 'Charset': 'UTF-8'}
                    }
                }
            )
            
            logger.info(f"Budget notification sent to {email} - Alert Level: {alert_level}")
            
            return {
                'sent': True,
                'message_id': response['MessageId'],
                'email': email,
                'alert_level': alert_level,
                'subject': subject
            }
            
        except Exception as e:
            logger.error(f"Failed to send budget notification: {str(e)}")
            return {
                'sent': False,
                'error': str(e),
                'email': budget_status.get('email', 'Unknown')
            }

    def _get_notification_subject(self, alert_level: str, budget_status: Dict[str, Any]) -> str:
        """Generate email subject based on alert level"""
        current_cost = budget_status['current_cost']
        budget_amount = budget_status['budget_amount']
        
        subjects = {
            'critical': f'AWS Budget EXCEEDED - ${current_cost:,.2f} of ${budget_amount:,.2f}',
            'high': f'AWS Budget Alert - 90% Threshold Reached',
            'medium': f'AWS Budget Warning - 80% Threshold Reached'
        }
        
        return subjects.get(alert_level, 'AWS Budget Notification')

    def _get_notification_body(self, budget_status: Dict[str, Any]) -> tuple:
        """Generate email body content (text and HTML)"""
        
        # Extract data
        budget_amount = budget_status['budget_amount']
        current_cost = budget_status['current_cost']
        remaining_budget = budget_status['remaining_budget']
        threshold_percentage = budget_status['threshold_percentage']
        alert_level = budget_status['alert_level']
        timestamp = budget_status['timestamp']
        
        # Text version
        text_body = f"""
AWS Budget Notification

Alert Level: {alert_level.upper()}
Budget Amount: ${budget_amount:,.2f}
Current Cost: ${current_cost:,.2f}
Remaining Budget: ${remaining_budget:,.2f}
Usage Percentage: {threshold_percentage:.1f}%

{budget_status['message']}

Generated at: {timestamp}

This is an automated notification from AWS Cost Calculator & FinOps Tool.
"""
        
        # HTML version
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #f4f4f4; padding: 20px; text-align: center; }}
        .alert-critical {{ background-color: #d32f2f; color: white; }}
        .alert-high {{ background-color: #f57c00; color: white; }}
        .alert-medium {{ background-color: #fbc02d; color: black; }}
        .content {{ padding: 20px; }}
        .metrics {{ background-color: #f9f9f9; padding: 15px; margin: 15px 0; }}
        .metric {{ margin: 10px 0; }}
        .footer {{ font-size: 12px; color: #666; text-align: center; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header alert-{alert_level}">
            <h2>AWS Budget Notification</h2>
            <p><strong>{budget_status['message']}</strong></p>
        </div>
        
        <div class="content">
            <div class="metrics">
                <div class="metric"><strong>Budget Amount:</strong> ${budget_amount:,.2f}</div>
                <div class="metric"><strong>Current Cost:</strong> ${current_cost:,.2f}</div>
                <div class="metric"><strong>Remaining Budget:</strong> ${remaining_budget:,.2f}</div>
                <div class="metric"><strong>Usage Percentage:</strong> {threshold_percentage:.1f}%</div>
            </div>
            
            <h3>Recommendations:</h3>
            <ul>
                <li>Review your AWS resource usage and optimize where possible</li>
                <li>Check for unused or idle resources</li>
                <li>Consider implementing cost controls and alerts</li>
                <li>Use the AWS Cost Calculator tool for detailed analysis</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>Generated at: {timestamp}</p>
            <p>This is an automated notification from AWS Cost Calculator & FinOps Tool.</p>
        </div>
    </div>
</body>
</html>
"""
        
        return text_body.strip(), html_body.strip()

    def get_current_month_cost(self) -> float:
        """Get current month's cost for budget comparison"""
        try:
            # Get current month dates
            now = datetime.now()
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Get costs for current month
            response = self.cost_explorer.get_cost_and_usage(
                TimePeriod={
                    'Start': start_of_month.strftime('%Y-%m-%d'),
                    'End': now.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost']
            )
            
            total_cost = 0
            for result in response['ResultsByTime']:
                cost = float(result['Total']['BlendedCost']['Amount'])
                total_cost += cost
            
            return total_cost
            
        except Exception as e:
            logger.error(f"Error getting current month cost: {str(e)}")
            return 0.0
    
    def get_enhanced_usage_type_details(self, service_name: str, usage_type: str, month: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get enhanced detailed breakdown with resource identification for a specific usage type
        
        Args:
            service_name: Name of the AWS service
            usage_type: Specific usage type to analyze
            month: Month to analyze (format: "YYYY-MM")
            start_date: Start date for cost data
            end_date: End date for cost data
            
        Returns:
            Dictionary containing enhanced usage type breakdown with resource details
        """
        try:
            logger.info(f"Fetching enhanced breakdown for {service_name} - {usage_type} in {month}")
            
            # Get the basic usage type details first
            basic_details = self.get_usage_type_details(service_name, usage_type, month, start_date, end_date)
            
            # Get actual resource names for this service
            actual_resources = self.get_actual_resource_names(service_name, usage_type, month)
            
            # Parse month to get specific date range
            month_start = datetime.strptime(month, '%Y-%m')
            if month_start.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1, day=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1, day=1)
            
            # Get enhanced resource breakdown using valid dimensions
            enhanced_resources = []
            
            # Try multiple valid dimensions to get resource-level insights
            dimensions_to_try = [
                ('INSTANCE_TYPE', 'Instance Type'),
                ('AZ', 'Availability Zone'), 
                ('PLATFORM', 'Platform'),
                ('OPERATION', 'Operation'),
                ('REGION', 'Region')
            ]
            
            for dimension_key, dimension_name in dimensions_to_try:
                try:
                    resource_response = self.cost_explorer.get_cost_and_usage(
                        TimePeriod={
                            'Start': month_start.strftime('%Y-%m-%d'),
                            'End': month_end.strftime('%Y-%m-%d')
                        },
                        Granularity='MONTHLY',
                        Metrics=['BlendedCost', 'UsageQuantity'],
                        GroupBy=[
                            {
                                'Type': 'DIMENSION',
                                'Key': dimension_key
                            }
                        ],
                        Filter={
                            'And': [
                                {
                                    'Dimensions': {
                                        'Key': 'SERVICE',
                                        'Values': [service_name]
                                    }
                                },
                                {
                                    'Dimensions': {
                                        'Key': 'USAGE_TYPE',
                                        'Values': [usage_type]
                                    }
                                }
                            ]
                        }
                    )
                    
                    for result in resource_response['ResultsByTime']:
                        for group in result['Groups']:
                            resource_value = group['Keys'][0] if group['Keys'] else f'Unknown {dimension_name}'
                            cost = float(group['Metrics']['BlendedCost']['Amount'])
                            usage = float(group['Metrics']['UsageQuantity']['Amount'])
                            
                            if cost > 0 and resource_value not in [f'No{dimension_key}', '']:
                                # Create a descriptive resource entry
                                enhanced_resources.append({
                                    'Resource_ID': f"{dimension_name}: {resource_value}",
                                    'Resource_Name': resource_value,
                                    'Resource_Type': dimension_name,
                                    'Resource_State': 'Active',
                                    'Region': resource_value if dimension_name == 'Region' else 'Multiple',
                                    'Cost': f"${cost:,.2f}",
                                    'Usage_Quantity': f"{usage:,.2f}",
                                    'Cost_Numeric': cost,
                                    'Usage_Numeric': usage,
                                    'Tags': {},
                                    'Owner': 'Unknown',
                                    'Environment': 'Unknown',
                                    'Project': 'Unknown',
                                    'Category': dimension_name
                                })
                    
                except Exception as e:
                    logger.debug(f"Could not fetch {dimension_name} data: {str(e)}")
                    continue
            
            # Try to get actual resource information using linked account dimension
            try:
                account_response = self.cost_explorer.get_cost_and_usage(
                    TimePeriod={
                        'Start': month_start.strftime('%Y-%m-%d'),
                        'End': month_end.strftime('%Y-%m-%d')
                    },
                    Granularity='MONTHLY',
                    Metrics=['BlendedCost', 'UsageQuantity'],
                    GroupBy=[
                        {
                            'Type': 'DIMENSION',
                            'Key': 'LINKED_ACCOUNT'
                        }
                    ],
                    Filter={
                        'And': [
                            {
                                'Dimensions': {
                                    'Key': 'SERVICE',
                                    'Values': [service_name]
                                }
                            },
                            {
                                'Dimensions': {
                                    'Key': 'USAGE_TYPE',
                                    'Values': [usage_type]
                                }
                            }
                        ]
                    }
                )
                
                for result in account_response['ResultsByTime']:
                    for group in result['Groups']:
                        account_id = group['Keys'][0] if group['Keys'] else 'Unknown Account'
                        cost = float(group['Metrics']['BlendedCost']['Amount'])
                        usage = float(group['Metrics']['UsageQuantity']['Amount'])
                        
                        if cost > 0:
                            enhanced_resources.append({
                                'Resource_ID': f"Account: {account_id}",
                                'Resource_Name': f"AWS Account {account_id}",
                                'Resource_Type': 'AWS Account',
                                'Resource_State': 'Active',
                                'Region': 'Multiple',
                                'Cost': f"${cost:,.2f}",
                                'Usage_Quantity': f"{usage:,.2f}",
                                'Cost_Numeric': cost,
                                'Usage_Numeric': usage,
                                'Tags': {},
                                'Owner': 'Unknown',
                                'Environment': 'Unknown',
                                'Project': 'Unknown',
                                'Category': 'Account'
                            })
                            
            except Exception as e:
                logger.debug(f"Could not fetch linked account data: {str(e)}")
            
            # Sort by cost (descending) and remove duplicates
            enhanced_resources.sort(key=lambda x: x['Cost_Numeric'], reverse=True)
            
            # Remove duplicate entries based on resource name and cost
            seen = set()
            unique_resources = []
            for resource in enhanced_resources:
                key = (resource['Resource_Name'], resource['Cost_Numeric'])
                if key not in seen:
                    seen.add(key)
                    unique_resources.append(resource)
            
            basic_details['enhanced_resources'] = unique_resources[:50]  # Top 50 unique resources
            basic_details['actual_resources'] = actual_resources  # Add actual resource names
            
            # Get detailed resource-level cost breakdown
            resource_cost_breakdown = self.get_resource_level_cost_breakdown(
                service_name, usage_type, month, month_start, month_end
            )
            basic_details['resource_cost_breakdown'] = resource_cost_breakdown
            
            if not enhanced_resources:
                logger.warning(f"Could not fetch enhanced resource data using available dimensions")
            
            # Add cost attribution analysis
            if basic_details['enhanced_resources']:
                total_identified_cost = sum([r['Cost_Numeric'] for r in basic_details['enhanced_resources']])
                basic_details['cost_attribution'] = {
                    'total_cost': basic_details['total_cost'],
                    'identified_cost': total_identified_cost,
                    'unidentified_cost': basic_details['total_cost'] - total_identified_cost,
                    'attribution_percentage': (total_identified_cost / basic_details['total_cost']) * 100 if basic_details['total_cost'] > 0 else 0
                }
                
                # Group by common attributes
                by_owner = {}
                by_environment = {}
                by_project = {}
                
                for resource in basic_details['enhanced_resources']:
                    owner = resource['Owner']
                    env = resource['Environment']
                    project = resource['Project']
                    cost = resource['Cost_Numeric']
                    
                    by_owner[owner] = by_owner.get(owner, 0) + cost
                    by_environment[env] = by_environment.get(env, 0) + cost
                    by_project[project] = by_project.get(project, 0) + cost
                
                basic_details['cost_by_owner'] = sorted(
                    [{'Owner': k, 'Cost': v, 'Cost_Formatted': f"${v:,.2f}"} for k, v in by_owner.items()],
                    key=lambda x: x['Cost'], reverse=True
                )
                basic_details['cost_by_environment'] = sorted(
                    [{'Environment': k, 'Cost': v, 'Cost_Formatted': f"${v:,.2f}"} for k, v in by_environment.items()],
                    key=lambda x: x['Cost'], reverse=True
                )
                basic_details['cost_by_project'] = sorted(
                    [{'Project': k, 'Cost': v, 'Cost_Formatted': f"${v:,.2f}"} for k, v in by_project.items()],
                    key=lambda x: x['Cost'], reverse=True
                )
            
            return basic_details
            
        except Exception as e:
            logger.error(f"Error fetching enhanced usage type details: {str(e)}")
            raise Exception(f"Failed to fetch enhanced usage type details: {str(e)}")
