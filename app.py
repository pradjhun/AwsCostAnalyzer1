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
        # Apply format_currency to handle both string and numeric amounts
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
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📈 Trend Analysis", "🥧 Service Breakdown", "📊 Monthly Comparison", "💡 Insights", "🔍 Individual Service Analysis", "📅 Custom Date Range"])

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

with tab5:
    st.subheader("Individual Service Deep Dive")
    
    if st.session_state.service_costs:
        # Service selection dropdown
        services = [service['Service'] for service in st.session_state.service_costs]
        selected_service = st.selectbox(
            "Select AWS Service for Detailed Analysis:",
            services,
            help="Choose a service to see detailed cost breakdown and AI recommendations"
        )
        
        if selected_service:
            col_service1, col_service2 = st.columns([2, 1])
            
            with col_service2:
                # Action buttons
                if st.button("🔍 Analyze Service", type="primary"):
                    with st.spinner(f"Analyzing {selected_service} costs in detail..."):
                        try:
                            cost_service = AWSCostService()
                            start_date, end_date = get_date_range(6)
                            
                            # Get detailed service analysis
                            detailed_data = cost_service.get_service_detailed_costs(
                                selected_service, start_date, end_date
                            )
                            
                            # Store in session state
                            st.session_state.detailed_service_data = detailed_data
                            st.success("✅ Service analysis completed!")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Error analyzing service: {str(e)}")
                
                if st.button("🤖 Get AI Recommendations"):
                    if 'detailed_service_data' in st.session_state and st.session_state.detailed_service_data:
                        with st.spinner("Generating AI-powered cost optimization recommendations..."):
                            try:
                                cost_service = AWSCostService()
                                recommendations = cost_service.generate_ai_recommendations(
                                    st.session_state.detailed_service_data,
                                    st.session_state.service_costs
                                )
                                
                                st.session_state.ai_recommendations = recommendations
                                st.success("✅ AI recommendations generated!")
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"❌ Error generating recommendations: {str(e)}")
                    else:
                        st.warning("Please analyze the service first to get recommendations")
            
            with col_service1:
                # Service overview metrics
                selected_service_data = next(
                    (s for s in st.session_state.service_costs if s['Service'] == selected_service), 
                    None
                )
                
                if selected_service_data:
                    service_cost = float(selected_service_data['Amount'].replace('$', '').replace(',', ''))
                    total_aws_cost = sum([
                        float(s['Amount'].replace('$', '').replace(',', '')) 
                        for s in st.session_state.service_costs
                    ])
                    percentage = (service_cost / total_aws_cost) * 100
                    
                    col_metric1, col_metric2, col_metric3 = st.columns(3)
                    with col_metric1:
                        st.metric("Service Cost (6 months)", selected_service_data['Amount'])
                    with col_metric2:
                        st.metric("% of Total AWS Spend", f"{percentage:.1f}%")
                    with col_metric3:
                        st.metric("Average Monthly", f"${service_cost/6:,.2f}")
            
            # Display detailed analysis if available
            if 'detailed_service_data' in st.session_state and st.session_state.detailed_service_data:
                detailed_data = st.session_state.detailed_service_data
                
                st.markdown("---")
                st.subheader("📋 Usage Type Breakdown")
                
                # Usage breakdown table and chart
                if detailed_data['usage_breakdown']:
                    df_usage = pd.DataFrame(detailed_data['usage_breakdown'])
                    
                    # Add interactive filters for drill-down analysis
                    st.write("**Usage Type Breakdown - Interactive Analysis:**")
                    
                    col_filter1, col_filter2, col_filter3 = st.columns([2, 2, 1])
                    
                    with col_filter1:
                        # Month selection
                        available_months = sorted(list(set([item['Month'] for item in detailed_data['usage_breakdown']])))
                        selected_month = st.selectbox(
                            "Select Month for Detailed Analysis:",
                            available_months,
                            key="month_selector"
                        )
                    
                    with col_filter2:
                        # Usage type selection based on selected month
                        month_data = [item for item in detailed_data['usage_breakdown'] if item['Month'] == selected_month]
                        usage_types = sorted(list(set([item['Usage_Type'] for item in month_data])))
                        selected_usage_type = st.selectbox(
                            "Select Usage Type:",
                            usage_types,
                            key="usage_type_selector"
                        )
                    
                    with col_filter3:
                        # Drill-down button
                        if st.button("🔍 Get Details", key="drill_down_btn"):
                            with st.spinner(f"Analyzing {selected_usage_type} for {selected_month}..."):
                                try:
                                    cost_service = AWSCostService()
                                    start_date, end_date = get_date_range(6)
                                    
                                    # Convert month format for API call
                                    month_parts = selected_month.split(' ')
                                    month_num = {
                                        'January': '01', 'February': '02', 'March': '03', 
                                        'April': '04', 'May': '05', 'June': '06',
                                        'July': '07', 'August': '08', 'September': '09', 
                                        'October': '10', 'November': '11', 'December': '12'
                                    }[month_parts[0]]
                                    year = month_parts[1]
                                    month_format = f"{year}-{month_num}"
                                    
                                    # Get detailed usage type breakdown
                                    usage_details = cost_service.get_usage_type_details(
                                        selected_service, selected_usage_type, month_format, start_date, end_date
                                    )
                                    
                                    st.session_state.usage_type_details = usage_details
                                    st.success("✅ Detailed analysis completed!")
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"❌ Error getting details: {str(e)}")
                        
                        # Enhanced drill-down button for resource identification
                        if st.button("🏷️ Get Resource Names", key="enhanced_drill_down_btn"):
                            with st.spinner(f"Fetching resource names and details for {selected_usage_type} in {selected_month}..."):
                                try:
                                    cost_service = AWSCostService()
                                    start_date, end_date = get_date_range(6)
                                    
                                    # Convert month format for API call
                                    month_parts = selected_month.split(' ')
                                    month_num = {
                                        'January': '01', 'February': '02', 'March': '03', 
                                        'April': '04', 'May': '05', 'June': '06',
                                        'July': '07', 'August': '08', 'September': '09', 
                                        'October': '10', 'November': '11', 'December': '12'
                                    }[month_parts[0]]
                                    year = month_parts[1]
                                    month_format = f"{year}-{month_num}"
                                    
                                    # Get enhanced usage type breakdown with resource details
                                    enhanced_details = cost_service.get_enhanced_usage_type_details(
                                        selected_service, selected_usage_type, month_format, start_date, end_date
                                    )
                                    
                                    st.session_state.enhanced_usage_details = enhanced_details
                                    st.success("✅ Resource identification completed!")
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"❌ Error fetching resource details: {str(e)}")
                    
                    # Display main usage breakdown table
                    st.write("**Usage Type Summary:**")
                    display_df = df_usage.drop('Cost_Numeric', axis=1)
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                    
                    # Usage type pie chart
                    if len(df_usage) > 1:
                        fig_usage = px.pie(
                            df_usage.head(10), 
                            values='Cost_Numeric', 
                            names='Usage_Type',
                            title=f"Cost Distribution by Usage Type - {selected_service}"
                        )
                        fig_usage.update_traces(
                            hovertemplate='<b>%{label}</b><br>Cost: $%{value:,.2f}<br>Percentage: %{percent}<extra></extra>'
                        )
                        st.plotly_chart(fig_usage, use_container_width=True)
                
                # Resource breakdown if available
                if detailed_data['resource_breakdown']:
                    st.subheader("🏗️ Resource-Level Cost Analysis")
                    
                    df_resources = pd.DataFrame(detailed_data['resource_breakdown'])
                    st.write("**Top Cost Resources:**")
                    display_resources = df_resources.drop('Cost_Numeric', axis=1)
                    st.dataframe(display_resources, use_container_width=True, hide_index=True)
                    
                    # Resource cost bar chart
                    if len(df_resources) > 1:
                        fig_resources = px.bar(
                            df_resources.head(10),
                            x='Cost_Numeric',
                            y='Resource_ID',
                            orientation='h',
                            title=f"Top Resources by Cost - {selected_service}",
                            labels={'Cost_Numeric': 'Cost (USD)', 'Resource_ID': 'Resource ID'}
                        )
                        fig_resources.update_traces(
                            hovertemplate='<b>%{y}</b><br>Cost: $%{x:,.2f}<extra></extra>'
                        )
                        st.plotly_chart(fig_resources, use_container_width=True)
                
                # Monthly trend for the service
                if detailed_data['monthly_data']:
                    st.subheader("📈 Monthly Cost Trend")
                    
                    monthly_df = pd.DataFrame([
                        {'Month': month, 'Cost': cost} 
                        for month, cost in detailed_data['monthly_data'].items()
                    ])
                    
                    fig_monthly = px.line(
                        monthly_df,
                        x='Month',
                        y='Cost',
                        title=f"Monthly Cost Trend - {selected_service}",
                        markers=True
                    )
                    fig_monthly.update_traces(
                        hovertemplate='<b>%{x}</b><br>Cost: $%{y:,.2f}<extra></extra>'
                    )
                    st.plotly_chart(fig_monthly, use_container_width=True)
                
                # Display detailed usage type analysis if available
                if 'usage_type_details' in st.session_state and st.session_state.usage_type_details:
                    usage_details = st.session_state.usage_type_details
                    
                    st.markdown("---")
                    st.subheader(f"🔬 Detailed Analysis: {usage_details['usage_type']} ({usage_details['month']})")
                    
                    # Summary metrics for the specific usage type and month
                    col_detail1, col_detail2, col_detail3 = st.columns(3)
                    
                    with col_detail1:
                        st.metric("Total Cost", f"${usage_details['total_cost']:,.2f}")
                    with col_detail2:
                        st.metric("Total Usage", f"{usage_details['total_usage']:,.2f}")
                    with col_detail3:
                        avg_daily = usage_details['total_cost'] / len(usage_details['daily_breakdown']) if usage_details['daily_breakdown'] else 0
                        st.metric("Avg Daily Cost", f"${avg_daily:,.2f}")
                    
                    # Daily trend chart
                    if usage_details['daily_breakdown']:
                        st.write("**Daily Cost Trend:**")
                        df_daily = pd.DataFrame(usage_details['daily_breakdown'])
                        
                        fig_daily = px.line(
                            df_daily,
                            x='Date',
                            y='Cost_Numeric',
                            title=f"Daily Cost Trend - {usage_details['usage_type']} ({usage_details['month']})",
                            markers=True
                        )
                        fig_daily.update_traces(
                            hovertemplate='<b>%{x}</b><br>Cost: $%{y:,.2f}<extra></extra>'
                        )
                        st.plotly_chart(fig_daily, use_container_width=True)
                        
                        # Daily breakdown table
                        st.write("**Daily Breakdown:**")
                        display_daily = df_daily.drop(['Cost_Numeric', 'Usage_Numeric'], axis=1)
                        st.dataframe(display_daily, use_container_width=True, hide_index=True)
                    
                    # Operation breakdown
                    if usage_details['operation_breakdown']:
                        st.write("**Operations Breakdown:**")
                        df_operations = pd.DataFrame(usage_details['operation_breakdown'])
                        
                        # Operations table
                        display_operations = df_operations.drop(['Cost_Numeric', 'Usage_Numeric'], axis=1)
                        st.dataframe(display_operations, use_container_width=True, hide_index=True)
                        
                        # Operations pie chart
                        if len(df_operations) > 1:
                            fig_operations = px.pie(
                                df_operations,
                                values='Cost_Numeric',
                                names='Operation',
                                title=f"Cost by Operation - {usage_details['usage_type']}"
                            )
                            fig_operations.update_traces(
                                hovertemplate='<b>%{label}</b><br>Cost: $%{value:,.2f}<br>Percentage: %{percent}<extra></extra>'
                            )
                            st.plotly_chart(fig_operations, use_container_width=True)
                    
                    # Region breakdown
                    if usage_details['region_breakdown']:
                        st.write("**Regional Breakdown:**")
                        df_regions = pd.DataFrame(usage_details['region_breakdown'])
                        
                        # Regions table
                        display_regions = df_regions.drop('Cost_Numeric', axis=1)
                        st.dataframe(display_regions, use_container_width=True, hide_index=True)
                        
                        # Regions bar chart
                        if len(df_regions) > 1:
                            fig_regions = px.bar(
                                df_regions,
                                x='Cost_Numeric',
                                y='Region',
                                orientation='h',
                                title=f"Cost by Region - {usage_details['usage_type']}",
                                labels={'Cost_Numeric': 'Cost (USD)', 'Region': 'AWS Region'}
                            )
                            fig_regions.update_traces(
                                hovertemplate='<b>%{y}</b><br>Cost: $%{x:,.2f}<extra></extra>'
                            )
                            st.plotly_chart(fig_regions, use_container_width=True)
                    
                    # Clear detailed analysis button
                    if st.button("🗑️ Clear Detailed Analysis"):
                        if 'usage_type_details' in st.session_state:
                            del st.session_state.usage_type_details
                        st.rerun()
                
                # Display enhanced resource identification if available
                if 'enhanced_usage_details' in st.session_state and st.session_state.enhanced_usage_details:
                    enhanced_data = st.session_state.enhanced_usage_details
                    
                    st.markdown("---")
                    st.subheader(f"🏷️ Resource Identification: {enhanced_data['usage_type']} ({enhanced_data['month']})")
                    
                    # Cost attribution summary
                    if 'cost_attribution' in enhanced_data:
                        attribution = enhanced_data['cost_attribution']
                        col_attr1, col_attr2, col_attr3 = st.columns(3)
                        
                        with col_attr1:
                            st.metric("Total Cost", f"${attribution['total_cost']:,.2f}")
                        with col_attr2:
                            st.metric("Identified Resources", f"${attribution['identified_cost']:,.2f}")
                        with col_attr3:
                            st.metric("Attribution %", f"{attribution['attribution_percentage']:.1f}%")
                    
                    # Enhanced resource breakdown with names and details
                    if enhanced_data.get('enhanced_resources'):
                        st.write("**Resource Details with Names & Tags:**")
                        
                        # Create enhanced resource dataframe
                        df_enhanced = pd.DataFrame(enhanced_data['enhanced_resources'])
                        
                        # Display columns with resource identification
                        display_columns = ['Resource_Name', 'Resource_ID', 'Resource_Type', 'Resource_State', 
                                         'Region', 'Cost', 'Owner', 'Environment', 'Project']
                        
                        # Filter columns that exist in the dataframe
                        available_columns = [col for col in display_columns if col in df_enhanced.columns]
                        display_enhanced = df_enhanced[available_columns]
                        
                        st.dataframe(display_enhanced, use_container_width=True, hide_index=True)
                        
                        # Resource cost visualization by name
                        if len(df_enhanced) > 1:
                            fig_resource_names = px.bar(
                                df_enhanced.head(15),
                                x='Cost_Numeric',
                                y='Resource_Name',
                                orientation='h',
                                title=f"Top Resources by Cost - {enhanced_data['usage_type']}",
                                labels={'Cost_Numeric': 'Cost (USD)', 'Resource_Name': 'Resource Name'},
                                hover_data=['Resource_Type', 'Owner', 'Environment']
                            )
                            fig_resource_names.update_traces(
                                hovertemplate='<b>%{y}</b><br>Cost: $%{x:,.2f}<br>Type: %{customdata[0]}<br>Owner: %{customdata[1]}<br>Environment: %{customdata[2]}<extra></extra>'
                            )
                            st.plotly_chart(fig_resource_names, use_container_width=True)
                    
                    # Cost breakdown by owner, environment, and project
                    tabs_breakdown = st.tabs(["👤 By Owner", "🌍 By Environment", "📁 By Project"])
                    
                    with tabs_breakdown[0]:
                        if enhanced_data.get('cost_by_owner'):
                            st.write("**Cost Attribution by Owner:**")
                            df_owners = pd.DataFrame(enhanced_data['cost_by_owner'])
                            st.dataframe(df_owners, use_container_width=True, hide_index=True)
                            
                            if len(df_owners) > 1:
                                fig_owners = px.pie(
                                    df_owners,
                                    values='Cost',
                                    names='Owner',
                                    title="Cost Distribution by Owner"
                                )
                                st.plotly_chart(fig_owners, use_container_width=True)
                    
                    with tabs_breakdown[1]:
                        if enhanced_data.get('cost_by_environment'):
                            st.write("**Cost Attribution by Environment:**")
                            df_env = pd.DataFrame(enhanced_data['cost_by_environment'])
                            st.dataframe(df_env, use_container_width=True, hide_index=True)
                            
                            if len(df_env) > 1:
                                fig_env = px.pie(
                                    df_env,
                                    values='Cost',
                                    names='Environment',
                                    title="Cost Distribution by Environment"
                                )
                                st.plotly_chart(fig_env, use_container_width=True)
                    
                    with tabs_breakdown[2]:
                        if enhanced_data.get('cost_by_project'):
                            st.write("**Cost Attribution by Project:**")
                            df_projects = pd.DataFrame(enhanced_data['cost_by_project'])
                            st.dataframe(df_projects, use_container_width=True, hide_index=True)
                            
                            if len(df_projects) > 1:
                                fig_projects = px.pie(
                                    df_projects,
                                    values='Cost',
                                    names='Project',
                                    title="Cost Distribution by Project"
                                )
                                st.plotly_chart(fig_projects, use_container_width=True)
                    
                    # Individual resource details expander
                    with st.expander("🔍 Individual Resource Tags & Details"):
                        if enhanced_data.get('enhanced_resources'):
                            for i, resource in enumerate(enhanced_data['enhanced_resources'][:10]):  # Show top 10
                                with st.container():
                                    col_res1, col_res2 = st.columns([2, 1])
                                    
                                    with col_res1:
                                        st.write(f"**{resource['Resource_Name']}** ({resource['Resource_ID']})")
                                        st.write(f"Type: {resource['Resource_Type']} | State: {resource['Resource_State']} | Region: {resource['Region']}")
                                        
                                        if resource.get('Tags'):
                                            tags_str = ", ".join([f"{k}: {v}" for k, v in resource['Tags'].items()])
                                            st.write(f"Tags: {tags_str}")
                                        else:
                                            st.write("Tags: No tags found")
                                    
                                    with col_res2:
                                        st.metric("Cost", resource['Cost'])
                                        st.metric("Usage", resource['Usage_Quantity'])
                                    
                                    st.markdown("---")
                    
                    # Clear enhanced analysis button
                    if st.button("🗑️ Clear Resource Analysis"):
                        if 'enhanced_usage_details' in st.session_state:
                            del st.session_state.enhanced_usage_details
                        st.rerun()
            
            # Display AI recommendations if available
            if 'ai_recommendations' in st.session_state and st.session_state.ai_recommendations:
                st.markdown("---")
                st.subheader("🤖 AI-Powered Cost Optimization Recommendations")
                
                # Display recommendations in an expandable container
                with st.expander("💡 View Detailed Recommendations", expanded=True):
                    st.markdown(st.session_state.ai_recommendations)
                
                # Clear recommendations button
                if st.button("🗑️ Clear Recommendations"):
                    if 'ai_recommendations' in st.session_state:
                        del st.session_state.ai_recommendations
                    st.rerun()
    else:
        st.info("Please refresh cost data first to enable service analysis")

with tab6:
    st.subheader("Custom Date Range Analysis")
    
    # Date range selector
    col_date1, col_date2, col_date3 = st.columns([2, 2, 1])
    
    with col_date1:
        start_date_input = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=180),  # Default to 6 months ago
            max_value=datetime.now().date(),
            help="Select the start date for cost analysis"
        )
    
    with col_date2:
        end_date_input = st.date_input(
            "End Date",
            value=datetime.now().date(),
            max_value=datetime.now().date(),
            help="Select the end date for cost analysis"
        )
    
    with col_date3:
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.button("🔍 Analyze Custom Range", type="primary"):
            # Validate date range
            if start_date_input >= end_date_input:
                st.error("Start date must be before end date")
            elif (end_date_input - start_date_input).days > 365:
                st.error("Date range cannot exceed 365 days")
            elif start_date_input > datetime.now().date():
                st.error("Start date cannot be in the future")
            else:
                with st.spinner("Fetching cost data for custom date range..."):
                    try:
                        cost_service = AWSCostService()
                        
                        # Convert dates to datetime objects
                        custom_start = datetime.combine(start_date_input, datetime.min.time())
                        custom_end = datetime.combine(end_date_input, datetime.min.time())
                        
                        # Get monthly costs for custom range
                        custom_monthly_costs = cost_service.get_monthly_costs(custom_start, custom_end)
                        
                        # Get service breakdown for custom range
                        custom_service_costs = cost_service.get_costs_by_service(custom_start, custom_end)
                        
                        # Get daily costs for custom range (if range is <= 31 days)
                        custom_daily_costs = []
                        if (end_date_input - start_date_input).days <= 31:
                            custom_daily_costs = cost_service.get_daily_costs(custom_start, custom_end)
                        
                        # Store in session state
                        st.session_state.custom_monthly_costs = custom_monthly_costs
                        st.session_state.custom_service_costs = custom_service_costs
                        st.session_state.custom_daily_costs = custom_daily_costs
                        st.session_state.custom_date_range = {
                            'start': start_date_input,
                            'end': end_date_input,
                            'days': (end_date_input - start_date_input).days
                        }
                        
                        st.success(f"✅ Analysis completed for {start_date_input} to {end_date_input}")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error fetching custom date range data: {str(e)}")
    
    # Display custom range analysis results
    if 'custom_monthly_costs' in st.session_state and st.session_state.custom_monthly_costs:
        custom_range = st.session_state.custom_date_range
        
        st.markdown("---")
        st.subheader(f"📊 Analysis Results: {custom_range['start']} to {custom_range['end']} ({custom_range['days']} days)")
        
        # Summary metrics for custom range
        custom_monthly = st.session_state.custom_monthly_costs
        custom_services = st.session_state.custom_service_costs
        
        total_custom_cost = sum([float(item['Amount'].replace('$', '').replace(',', '')) for item in custom_monthly])
        avg_monthly_custom = total_custom_cost / len(custom_monthly) if custom_monthly else 0
        
        col_custom1, col_custom2, col_custom3, col_custom4 = st.columns(4)
        
        with col_custom1:
            st.metric("Total Cost", f"${total_custom_cost:,.2f}")
        with col_custom2:
            st.metric("Average Monthly", f"${avg_monthly_custom:,.2f}")
        with col_custom3:
            st.metric("Number of Months", len(custom_monthly))
        with col_custom4:
            st.metric("Number of Services", len(custom_services))
        
        # Custom range charts in tabs
        custom_tabs = st.tabs(["📈 Monthly Trend", "🥧 Service Breakdown", "📊 Daily Analysis", "📋 Data Tables"])
        
        with custom_tabs[0]:
            # Monthly trend chart for custom range
            if custom_monthly:
                df_custom_monthly = pd.DataFrame(custom_monthly)
                df_custom_monthly['Amount_Numeric'] = df_custom_monthly['Amount'].str.replace('$', '').str.replace(',', '').astype(float)
                
                fig_custom_monthly = px.line(
                    df_custom_monthly,
                    x='Month',
                    y='Amount_Numeric',
                    title=f"Monthly Cost Trend ({custom_range['start']} to {custom_range['end']})",
                    markers=True
                )
                fig_custom_monthly.update_traces(
                    hovertemplate='<b>%{x}</b><br>Cost: $%{y:,.2f}<extra></extra>'
                )
                st.plotly_chart(fig_custom_monthly, use_container_width=True)
        
        with custom_tabs[1]:
            # Service breakdown for custom range
            if custom_services:
                df_custom_services = pd.DataFrame(custom_services)
                df_custom_services['Amount_Numeric'] = df_custom_services['Amount'].str.replace('$', '').str.replace(',', '').astype(float)
                
                # Filter services with cost > $1
                df_custom_services_filtered = df_custom_services[df_custom_services['Amount_Numeric'] >= 1.0]
                
                fig_custom_services = px.pie(
                    df_custom_services_filtered,
                    values='Amount_Numeric',
                    names='Service',
                    title=f"Service Cost Distribution ({custom_range['start']} to {custom_range['end']})"
                )
                fig_custom_services.update_traces(
                    hovertemplate='<b>%{label}</b><br>Cost: $%{value:,.2f}<br>Percentage: %{percent}<extra></extra>'
                )
                st.plotly_chart(fig_custom_services, use_container_width=True)
                
                # Top services table
                st.write("**Top Services by Cost:**")
                top_custom_services = df_custom_services.head(10).drop('Amount_Numeric', axis=1)
                st.dataframe(top_custom_services, use_container_width=True, hide_index=True)
        
        with custom_tabs[2]:
            # Daily analysis (only if range <= 31 days)
            if st.session_state.custom_daily_costs and custom_range['days'] <= 31:
                df_custom_daily = pd.DataFrame(st.session_state.custom_daily_costs)
                df_custom_daily['Amount_Numeric'] = df_custom_daily['Amount'].str.replace('$', '').str.replace(',', '').astype(float)
                
                fig_custom_daily = px.line(
                    df_custom_daily,
                    x='Date',
                    y='Amount_Numeric',
                    title=f"Daily Cost Trend ({custom_range['start']} to {custom_range['end']})",
                    markers=True
                )
                fig_custom_daily.update_traces(
                    hovertemplate='<b>%{x}</b><br>Cost: $%{y:,.2f}<extra></extra>'
                )
                st.plotly_chart(fig_custom_daily, use_container_width=True)
                
                # Daily stats
                daily_costs = df_custom_daily['Amount_Numeric']
                col_daily1, col_daily2, col_daily3, col_daily4 = st.columns(4)
                
                with col_daily1:
                    st.metric("Avg Daily Cost", f"${daily_costs.mean():,.2f}")
                with col_daily2:
                    st.metric("Highest Day", f"${daily_costs.max():,.2f}")
                with col_daily3:
                    st.metric("Lowest Day", f"${daily_costs.min():,.2f}")
                with col_daily4:
                    st.metric("Daily Variance", f"${daily_costs.std():,.2f}")
                
            elif custom_range['days'] > 31:
                st.info("Daily analysis is only available for date ranges of 31 days or less")
            else:
                st.info("No daily cost data available for this range")
        
        with custom_tabs[3]:
            # Data tables for custom range
            col_table1, col_table2 = st.columns(2)
            
            with col_table1:
                st.write("**Monthly Costs:**")
                df_monthly_display = pd.DataFrame(custom_monthly)
                st.dataframe(df_monthly_display, use_container_width=True, hide_index=True)
            
            with col_table2:
                st.write("**Service Costs:**")
                df_services_display = pd.DataFrame(custom_services).head(15)  # Top 15 services
                st.dataframe(df_services_display, use_container_width=True, hide_index=True)
        
        # Export options for custom range
        st.markdown("---")
        st.subheader("📥 Export Custom Range Data")
        
        col_export_custom1, col_export_custom2 = st.columns(2)
        
        with col_export_custom1:
            if st.button("📊 Export Custom Monthly Data", key="export_custom_monthly"):
                csv_data = export_to_csv(custom_monthly, f"custom_monthly_costs_{custom_range['start']}_to_{custom_range['end']}")
                st.download_button(
                    label="Download Custom Monthly CSV",
                    data=csv_data,
                    file_name=f"custom_monthly_costs_{custom_range['start']}_to_{custom_range['end']}.csv",
                    mime="text/csv"
                )
        
        with col_export_custom2:
            if st.button("🛠️ Export Custom Service Data", key="export_custom_services"):
                csv_data = export_to_csv(custom_services, f"custom_service_costs_{custom_range['start']}_to_{custom_range['end']}")
                st.download_button(
                    label="Download Custom Service CSV",
                    data=csv_data,
                    file_name=f"custom_service_costs_{custom_range['start']}_to_{custom_range['end']}.csv",
                    mime="text/csv"
                )
        
        # Clear custom analysis
        if st.button("🗑️ Clear Custom Analysis"):
            for key in ['custom_monthly_costs', 'custom_service_costs', 'custom_daily_costs', 'custom_date_range']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

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
