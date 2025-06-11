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
            logger.info("AWS Cost Explorer client initialized successfully")
            
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
