import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from aws_cost_service import AWSCostService
from utils import format_currency, export_to_csv, get_date_range

# Page configuration
st.set_page_config(
    page_title="AWS Cost Calculator & FinOps Tool",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main title
st.title("💰 AWS Cost Calculator & FinOps Tool")
st.markdown("---")

# Initialize session state
if 'cost_data' not in st.session_state:
    st.session_state.cost_data = None
if 'service_costs' not in st.session_state:
    st.session_state.service_costs = None
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = None

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # AWS Credentials status
    st.subheader("AWS Credentials")
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID", "")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    aws_region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    
    if aws_access_key and aws_secret_key:
        st.success("✅ AWS credentials configured")
    else:
        st.error("❌ AWS credentials not found in environment variables")
        st.info("Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
    
    st.text(f"Region: {aws_region}")
    
    # Refresh data button
    st.subheader("Data Management")
    if st.button("🔄 Refresh Cost Data", type="primary"):
        with st.spinner("Fetching AWS cost data..."):
            try:
                cost_service = AWSCostService()
                start_date, end_date = get_date_range(6)
                
                # Get monthly costs
                st.session_state.cost_data = cost_service.get_monthly_costs(start_date, end_date)
                
                # Get service breakdown
                st.session_state.service_costs = cost_service.get_costs_by_service(start_date, end_date)
                
                st.session_state.last_refresh = datetime.now()
                st.success("✅ Data refreshed successfully!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error fetching cost data: {str(e)}")
    
    # Last refresh timestamp
    if st.session_state.last_refresh:
        st.text(f"Last refresh: {st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")

# Main content area
if st.session_state.cost_data is None:
    st.info("👆 Click 'Refresh Cost Data' in the sidebar to load AWS cost information")
    st.stop()

# Display cost data
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📊 Monthly Cost Overview")
    
    # Monthly costs table
    if st.session_state.cost_data:
        df_monthly = pd.DataFrame(st.session_state.cost_data)
        df_monthly['Amount'] = df_monthly['Amount'].apply(format_currency)
        
        # Display table with sorting
        st.subheader("💵 Last 6 Months Cost Summary")
        st.dataframe(
            df_monthly,
            use_container_width=True,
            hide_index=True
        )
        
        # Total cost calculation
        total_cost = sum([float(item['Amount'].replace('$', '').replace(',', '')) 
                         for item in st.session_state.cost_data])
        average_monthly = total_cost / len(st.session_state.cost_data)
        
        # Metrics
        col_metric1, col_metric2, col_metric3 = st.columns(3)
        with col_metric1:
            st.metric("Total Cost (6 months)", format_currency(total_cost))
        with col_metric2:
            st.metric("Average Monthly Cost", format_currency(average_monthly))
        with col_metric3:
            # Calculate trend (current vs previous month)
            if len(st.session_state.cost_data) >= 2:
                current_month = float(st.session_state.cost_data[-1]['Amount'].replace('$', '').replace(',', ''))
                previous_month = float(st.session_state.cost_data[-2]['Amount'].replace('$', '').replace(',', ''))
                trend = ((current_month - previous_month) / previous_month) * 100
                st.metric("Month-over-Month Change", f"{trend:+.1f}%")

with col2:
    st.header("📈 Quick Stats")
    
    if st.session_state.cost_data:
        # Find highest and lowest cost months
        costs_numeric = [(item['Month'], float(item['Amount'].replace('$', '').replace(',', ''))) 
                        for item in st.session_state.cost_data]
        
        highest_month = max(costs_numeric, key=lambda x: x[1])
        lowest_month = min(costs_numeric, key=lambda x: x[1])
        
        st.metric("Highest Cost Month", f"{highest_month[0]}", format_currency(highest_month[1]))
        st.metric("Lowest Cost Month", f"{lowest_month[0]}", format_currency(lowest_month[1]))
        
        # Cost variance
        costs_values = [x[1] for x in costs_numeric]
        variance = max(costs_values) - min(costs_values)
        st.metric("Cost Variance", format_currency(variance))

# Charts section
st.header("📊 Interactive Charts")

# Create tabs for different chart types
tab1, tab2, tab3, tab4 = st.tabs(["📈 Trend Analysis", "🥧 Service Breakdown", "📊 Monthly Comparison", "💡 Insights"])

with tab1:
    st.subheader("Monthly Cost Trend")
    if st.session_state.cost_data:
        # Prepare data for line chart
        df_chart = pd.DataFrame(st.session_state.cost_data)
        df_chart['Amount_Numeric'] = df_chart['Amount'].str.replace('$', '').str.replace(',', '').astype(float)
        
        # Line chart
        fig_line = px.line(
            df_chart, 
            x='Month', 
            y='Amount_Numeric',
            title="AWS Costs Over Last 6 Months",
            markers=True,
            line_shape='linear'
        )
        fig_line.update_layout(
            xaxis_title="Month",
            yaxis_title="Cost (USD)",
            hovermode='x unified'
        )
        fig_line.update_traces(
            hovertemplate='<b>%{x}</b><br>Cost: $%{y:,.2f}<extra></extra>'
        )
        st.plotly_chart(fig_line, use_container_width=True)

with tab2:
    st.subheader("Cost Breakdown by AWS Service")
    if st.session_state.service_costs:
        # Prepare service data for pie chart
        df_services = pd.DataFrame(st.session_state.service_costs)
        df_services['Amount_Numeric'] = df_services['Amount'].str.replace('$', '').str.replace(',', '').astype(float)
        
        # Filter out very small amounts for better visualization
        df_services_filtered = df_services[df_services['Amount_Numeric'] >= 1.0]
        
        # Pie chart for service breakdown
        fig_pie = px.pie(
            df_services_filtered, 
            values='Amount_Numeric', 
            names='Service',
            title="Cost Distribution by AWS Service (Last 6 Months)"
        )
        fig_pie.update_traces(
            hovertemplate='<b>%{label}</b><br>Cost: $%{value:,.2f}<br>Percentage: %{percent}<extra></extra>'
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
        # Service costs table
        st.subheader("Detailed Service Costs")
        df_services_display = df_services.copy()
        df_services_display = df_services_display.sort_values('Amount_Numeric', ascending=False)
        df_services_display = df_services_display.drop('Amount_Numeric', axis=1)
        
        st.dataframe(
            df_services_display,
            use_container_width=True,
            hide_index=True
        )

with tab3:
    st.subheader("Monthly Cost Comparison")
    if st.session_state.cost_data:
        df_chart = pd.DataFrame(st.session_state.cost_data)
        df_chart['Amount_Numeric'] = df_chart['Amount'].str.replace('$', '').str.replace(',', '').astype(float)
        
        # Bar chart for monthly comparison
        fig_bar = px.bar(
            df_chart, 
            x='Month', 
            y='Amount_Numeric',
            title="Monthly AWS Costs Comparison",
            color='Amount_Numeric',
            color_continuous_scale='Blues'
        )
        fig_bar.update_layout(
            xaxis_title="Month",
            yaxis_title="Cost (USD)",
            showlegend=False
        )
        fig_bar.update_traces(
            hovertemplate='<b>%{x}</b><br>Cost: $%{y:,.2f}<extra></extra>'
        )
        st.plotly_chart(fig_bar, use_container_width=True)

with tab4:
    st.subheader("Cost Analysis Insights")
    
    if st.session_state.cost_data and st.session_state.service_costs:
        col_insight1, col_insight2 = st.columns(2)
        
        with col_insight1:
            st.write("**Cost Trends:**")
            
            # Calculate month-over-month changes
            df_chart = pd.DataFrame(st.session_state.cost_data)
            df_chart['Amount_Numeric'] = df_chart['Amount'].str.replace('$', '').str.replace(',', '').astype(float)
            
            if len(df_chart) >= 2:
                changes = []
                for i in range(1, len(df_chart)):
                    current = df_chart.iloc[i]['Amount_Numeric']
                    previous = df_chart.iloc[i-1]['Amount_Numeric']
                    change = ((current - previous) / previous) * 100
                    changes.append(f"• {df_chart.iloc[i]['Month']}: {change:+.1f}%")
                
                for change in changes:
                    st.write(change)
        
        with col_insight2:
            st.write("**Top Cost Drivers:**")
            
            # Show top 5 services by cost
            df_services = pd.DataFrame(st.session_state.service_costs)
            df_services['Amount_Numeric'] = df_services['Amount'].str.replace('$', '').str.replace(',', '').astype(float)
            top_services = df_services.nlargest(5, 'Amount_Numeric')
            
            for _, service in top_services.iterrows():
                percentage = (service['Amount_Numeric'] / df_services['Amount_Numeric'].sum()) * 100
                st.write(f"• {service['Service']}: {service['Amount']} ({percentage:.1f}%)")

# Export functionality
st.header("📥 Export Options")
col_export1, col_export2 = st.columns(2)

with col_export1:
    if st.button("📊 Export Monthly Costs to CSV"):
        if st.session_state.cost_data:
            csv_data = export_to_csv(st.session_state.cost_data, "monthly_costs")
            st.download_button(
                label="Download Monthly Costs CSV",
                data=csv_data,
                file_name=f"aws_monthly_costs_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

with col_export2:
    if st.button("🛠️ Export Service Costs to CSV"):
        if st.session_state.service_costs:
            csv_data = export_to_csv(st.session_state.service_costs, "service_costs")
            st.download_button(
                label="Download Service Costs CSV",
                data=csv_data,
                file_name=f"aws_service_costs_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

# Footer
st.markdown("---")
st.markdown("*AWS Cost Calculator & FinOps Tool - Monitor and analyze your AWS spending*")
