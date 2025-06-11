import boto3
import os
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
            logger.info("AWS Cost Explorer and Bedrock clients initialized successfully")
            
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
            
            # Get resource-level breakdown if available
            try:
                resource_response = self.cost_explorer.get_cost_and_usage(
                    TimePeriod={
                        'Start': start_date.strftime('%Y-%m-%d'),
                        'End': end_date.strftime('%Y-%m-%d')
                    },
                    Granularity='MONTHLY',
                    Metrics=['BlendedCost'],
                    GroupBy=[
                        {
                            'Type': 'DIMENSION',
                            'Key': 'RESOURCE_ID'
                        }
                    ],
                    Filter={
                        'Dimensions': {
                            'Key': 'SERVICE',
                            'Values': [service_name]
                        }
                    }
                )
                
                resource_breakdown = []
                for result in resource_response['ResultsByTime']:
                    for group in result['Groups']:
                        resource_id = group['Keys'][0] if group['Keys'] else 'Unknown Resource'
                        cost = float(group['Metrics']['BlendedCost']['Amount'])
                        
                        if cost > 0 and resource_id != 'NoResourceId':
                            resource_breakdown.append({
                                'Resource_ID': resource_id,
                                'Cost': f"${cost:,.2f}",
                                'Cost_Numeric': cost
                            })
                
                # Sort by cost (descending)
                resource_breakdown.sort(key=lambda x: x['Cost_Numeric'], reverse=True)
                
            except Exception as e:
                logger.warning(f"Could not fetch resource-level data for {service_name}: {str(e)}")
                resource_breakdown = []
            
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
