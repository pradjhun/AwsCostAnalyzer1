import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import io

def format_currency(amount) -> str:
    """
    Format a numeric amount as currency string
    
    Args:
        amount: Numeric amount to format (float or string)
        
    Returns:
        Formatted currency string
    """
    # If already a string (already formatted), return as is
    if isinstance(amount, str):
        return amount
    # If numeric, format it
    return f"${amount:,.2f}"

def get_date_range(months: int) -> Tuple[datetime, datetime]:
    """
    Get start and end dates for the specified number of months ago
    
    Args:
        months: Number of months to go back
        
    Returns:
        Tuple of (start_date, end_date)
    """
    end_date = datetime.now().replace(day=1)  # First day of current month
    
    # Calculate start date by going back the specified number of months
    start_date = end_date
    for _ in range(months):
        start_date = start_date.replace(day=1) - timedelta(days=1)
        start_date = start_date.replace(day=1)
    
    return start_date, end_date

def export_to_csv(data: List[Dict[str, Any]], data_type: str) -> str:
    """
    Convert data to CSV format for export
    
    Args:
        data: List of dictionaries containing the data
        data_type: Type of data being exported
        
    Returns:
        CSV string
    """
    if not data:
        return ""
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Add metadata
    csv_buffer = io.StringIO()
    csv_buffer.write(f"# AWS Cost Data Export - {data_type.title()}\n")
    csv_buffer.write(f"# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    csv_buffer.write(f"# Total records: {len(data)}\n")
    csv_buffer.write("\n")
    
    # Write the actual data
    df.to_csv(csv_buffer, index=False)
    
    return csv_buffer.getvalue()

def calculate_cost_trend(current_costs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate cost trends and statistics
    
    Args:
        current_costs: List of cost data dictionaries
        
    Returns:
        Dictionary containing trend analysis
    """
    if len(current_costs) < 2:
        return {
            'trend': 'insufficient_data',
            'change_percentage': 0,
            'average_cost': 0,
            'total_cost': 0
        }
    
    # Extract numeric values
    costs = []
    for cost_data in current_costs:
        amount_str = cost_data.get('Amount', '$0.00')
        amount = float(amount_str.replace('$', '').replace(',', ''))
        costs.append(amount)
    
    # Calculate statistics
    total_cost = sum(costs)
    average_cost = total_cost / len(costs)
    
    # Calculate trend (last month vs previous month)
    if len(costs) >= 2:
        current_month = costs[-1]
        previous_month = costs[-2]
        
        if previous_month > 0:
            change_percentage = ((current_month - previous_month) / previous_month) * 100
        else:
            change_percentage = 0
        
        if change_percentage > 5:
            trend = 'increasing'
        elif change_percentage < -5:
            trend = 'decreasing'
        else:
            trend = 'stable'
    else:
        change_percentage = 0
        trend = 'stable'
    
    return {
        'trend': trend,
        'change_percentage': change_percentage,
        'average_cost': average_cost,
        'total_cost': total_cost,
        'highest_cost': max(costs),
        'lowest_cost': min(costs)
    }

def filter_costs_by_threshold(service_costs: List[Dict[str, Any]], threshold: float = 1.0) -> List[Dict[str, Any]]:
    """
    Filter service costs by minimum threshold
    
    Args:
        service_costs: List of service cost dictionaries
        threshold: Minimum cost threshold to include
        
    Returns:
        Filtered list of service costs
    """
    filtered_costs = []
    
    for service in service_costs:
        amount_str = service.get('Amount', '$0.00')
        amount = float(amount_str.replace('$', '').replace(',', ''))
        
        if amount >= threshold:
            filtered_costs.append(service)
    
    return filtered_costs

def generate_cost_summary(monthly_costs: List[Dict[str, Any]], service_costs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a comprehensive cost summary
    
    Args:
        monthly_costs: List of monthly cost data
        service_costs: List of service cost data
        
    Returns:
        Dictionary containing cost summary
    """
    if not monthly_costs:
        return {
            'total_cost': 0,
            'average_monthly': 0,
            'months_analyzed': 0,
            'top_service': 'None',
            'service_count': 0
        }
    
    # Calculate monthly statistics
    monthly_amounts = []
    for month_data in monthly_costs:
        amount_str = month_data.get('Amount', '$0.00')
        amount = float(amount_str.replace('$', '').replace(',', ''))
        monthly_amounts.append(amount)
    
    total_cost = sum(monthly_amounts)
    average_monthly = total_cost / len(monthly_amounts) if monthly_amounts else 0
    
    # Find top service
    top_service = 'None'
    if service_costs:
        top_service = service_costs[0].get('Service', 'Unknown')
    
    return {
        'total_cost': total_cost,
        'average_monthly': average_monthly,
        'months_analyzed': len(monthly_costs),
        'top_service': top_service,
        'service_count': len(service_costs),
        'highest_monthly': max(monthly_amounts) if monthly_amounts else 0,
        'lowest_monthly': min(monthly_amounts) if monthly_amounts else 0
    }

def validate_date_range(start_date: datetime, end_date: datetime) -> bool:
    """
    Validate if the date range is reasonable for cost analysis
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        Boolean indicating if date range is valid
    """
    if start_date >= end_date:
        return False
    
    # Check if date range is not too large (more than 1 year)
    max_days = 365
    if (end_date - start_date).days > max_days:
        return False
    
    # Check if dates are not in the future
    if start_date > datetime.now() or end_date > datetime.now():
        return False
    
    return True

def parse_aws_service_name(service_name: str) -> str:
    """
    Parse and clean AWS service names for better display
    
    Args:
        service_name: Raw AWS service name
        
    Returns:
        Cleaned service name
    """
    # Common AWS service name mappings
    service_mappings = {
        'Amazon Elastic Compute Cloud - Compute': 'EC2 - Compute',
        'Amazon Simple Storage Service': 'S3',
        'Amazon Relational Database Service': 'RDS',
        'Amazon CloudFront': 'CloudFront',
        'AWS Lambda': 'Lambda',
        'Amazon Elastic Load Balancing': 'ELB',
        'Amazon Virtual Private Cloud': 'VPC',
        'Amazon CloudWatch': 'CloudWatch',
        'AWS Key Management Service': 'KMS',
        'Amazon Route 53': 'Route 53'
    }
    
    # Return mapped name if available, otherwise return original
    return service_mappings.get(service_name, service_name)
