#!/usr/bin/env python3
"""
Streamlit Analytics Dashboard for Sonora AI Dubbing System.

Real-time monitoring dashboard showing:
- System performance metrics
- Request analytics
- Cache performance
- Audio processing statistics
- Error tracking
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime, timedelta
import json

# Configure Streamlit page
st.set_page_config(
    page_title="Sonora Analytics Dashboard",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"
METRICS_ENDPOINT = f"{API_BASE_URL}/api/metrics"
ANALYTICS_ENDPOINT = f"{API_BASE_URL}/api/analytics"

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .error-card {
        background-color: #ffe6e6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff4444;
    }
    .success-card {
        background-color: #e6ffe6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #44ff44;
    }
    .warning-card {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=5)  # Cache for 5 seconds
def fetch_metrics():
    """Fetch metrics from the API with error handling."""
    try:
        response = requests.get(METRICS_ENDPOINT, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to connect to API: {e}")
        return None


@st.cache_data(ttl=10)  # Cache for 10 seconds
def fetch_analytics():
    """Fetch comprehensive analytics from the API."""
    try:
        response = requests.get(ANALYTICS_ENDPOINT, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Analytics API Error: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to connect to Analytics API: {e}")
        return None


def format_uptime(uptime_seconds):
    """Format uptime in a human-readable way."""
    if uptime_seconds < 60:
        return f"{uptime_seconds:.1f}s"
    elif uptime_seconds < 3600:
        return f"{uptime_seconds/60:.1f}m"
    else:
        return f"{uptime_seconds/3600:.1f}h"


def create_system_metrics_chart(metrics):
    """Create system metrics visualization."""
    if not metrics or 'system' not in metrics:
        return None
    
    system = metrics['system']
    
    # Create subplot with secondary y-axis
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('CPU Usage', 'Memory Usage', 'Memory (MB)', 'Disk Usage'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # CPU Usage
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=system.get('cpu_percent', 0),
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "CPU %"},
            gauge={'axis': {'range': [None, 100]},
                   'bar': {'color': "darkblue"},
                   'steps': [{'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 80], 'color': "yellow"},
                            {'range': [80, 100], 'color': "red"}],
                   'threshold': {'line': {'color': "red", 'width': 4},
                               'thickness': 0.75, 'value': 90}}
        ),
        row=1, col=1
    )
    
    # Memory Percentage
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=system.get('memory_percent', 0),
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Memory %"},
            gauge={'axis': {'range': [None, 100]},
                   'bar': {'color': "darkgreen"},
                   'steps': [{'range': [0, 60], 'color': "lightgray"},
                            {'range': [60, 80], 'color': "yellow"},
                            {'range': [80, 100], 'color': "red"}],
                   'threshold': {'line': {'color': "red", 'width': 4},
                               'thickness': 0.75, 'value': 90}}
        ),
        row=1, col=2
    )
    
    # Memory in MB
    fig.add_trace(
        go.Bar(
            x=['Memory Used'],
            y=[system.get('memory_mb', 0)],
            name='Memory (MB)',
            marker_color='lightblue'
        ),
        row=2, col=1
    )
    
    # Disk Usage
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=system.get('disk_percent', 0),
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Disk %"},
            gauge={'axis': {'range': [None, 100]},
                   'bar': {'color': "darkorange"},
                   'steps': [{'range': [0, 70], 'color': "lightgray"},
                            {'range': [70, 85], 'color': "yellow"},
                            {'range': [85, 100], 'color': "red"}],
                   'threshold': {'line': {'color': "red", 'width': 4},
                               'thickness': 0.75, 'value': 90}}
        ),
        row=2, col=2
    )
    
    fig.update_layout(height=600, showlegend=False, title_text="System Performance Metrics")
    return fig


def create_latency_chart(metrics):
    """Create latency visualization."""
    if not metrics or 'latency' not in metrics:
        return None
    
    latency = metrics['latency']
    
    # Create latency metrics
    fig = go.Figure()
    
    # Add latency bars
    fig.add_trace(go.Bar(
        x=['Average', 'Min', 'Max', 'P95', 'P99'],
        y=[latency.get('avg_latency_sec', 0),
           latency.get('min_latency_sec', 0),
           latency.get('max_latency_sec', 0),
           latency.get('p95_latency_sec', 0),
           latency.get('p99_latency_sec', 0)],
        marker_color=['lightblue', 'lightgreen', 'orange', 'red', 'darkred'],
        text=[f"{v:.3f}s" for v in [latency.get('avg_latency_sec', 0),
                                   latency.get('min_latency_sec', 0),
                                   latency.get('max_latency_sec', 0),
                                   latency.get('p95_latency_sec', 0),
                                   latency.get('p99_latency_sec', 0)]],
        textposition='auto'
    ))
    
    fig.update_layout(
        title="Request Latency Statistics",
        xaxis_title="Latency Type",
        yaxis_title="Latency (seconds)",
        height=400
    )
    
    return fig


def create_requests_chart(metrics):
    """Create request statistics visualization."""
    if not metrics or 'endpoints' not in metrics:
        return None
    
    endpoints = metrics['endpoints']
    if not endpoints:
        return None
    
    # Prepare data for visualization
    endpoint_names = list(endpoints.keys())
    request_counts = [endpoints[ep].get('requests', 0) for ep in endpoint_names]
    avg_latencies = [endpoints[ep].get('avg_latency', 0) for ep in endpoint_names]
    
    # Create subplot
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Request Counts by Endpoint', 'Average Latency by Endpoint'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Request counts
    fig.add_trace(
        go.Bar(
            x=endpoint_names,
            y=request_counts,
            name='Requests',
            marker_color='lightblue',
            text=request_counts,
            textposition='auto'
        ),
        row=1, col=1
    )
    
    # Average latencies
    fig.add_trace(
        go.Bar(
            x=endpoint_names,
            y=avg_latencies,
            name='Avg Latency (s)',
            marker_color='lightcoral',
            text=[f"{v:.3f}s" for v in avg_latencies],
            textposition='auto'
        ),
        row=1, col=2
    )
    
    fig.update_layout(height=400, showlegend=False, title_text="Endpoint Performance")
    return fig


def create_audio_stats_chart(metrics):
    """Create audio processing statistics visualization."""
    if not metrics or 'audio' not in metrics:
        return None
    
    audio = metrics['audio']
    
    fig = go.Figure()
    
    # Audio processing metrics
    metrics_data = {
        'Average Duration': audio.get('avg_audio_duration_sec', 0),
        'Total Processed': audio.get('total_audio_processed_sec', 0),
        'Files Processed': audio.get('audio_files_processed', 0)
    }
    
    fig.add_trace(go.Bar(
        x=list(metrics_data.keys()),
        y=list(metrics_data.values()),
        marker_color=['lightblue', 'lightgreen', 'lightcoral'],
        text=[f"{v:.1f}s" if 'Duration' in k or 'Processed' in k else str(v) for k, v in metrics_data.items()],
        textposition='auto'
    ))
    
    fig.update_layout(
        title="Audio Processing Statistics",
        xaxis_title="Metric",
        yaxis_title="Value",
        height=400
    )
    
    return fig


def create_cache_stats_chart(metrics):
    """Create cache performance visualization."""
    if not metrics or 'cache' not in metrics:
        return None
    
    cache = metrics['cache']
    
    # Cache hit/miss pie chart
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Cache Hit/Miss Ratio', 'Cache Performance'),
        specs=[[{"type": "pie"}, {"type": "bar"}]]
    )
    
    # Pie chart for hit/miss ratio
    hits = cache.get('cache_hits', 0)
    misses = cache.get('cache_misses', 0)
    
    if hits + misses > 0:
        fig.add_trace(
            go.Pie(
                labels=['Cache Hits', 'Cache Misses'],
                values=[hits, misses],
                hole=0.3,
                marker_colors=['lightgreen', 'lightcoral']
            ),
            row=1, col=1
        )
    
    # Bar chart for cache metrics
    cache_metrics = {
        'Hit Rate %': cache.get('cache_hit_rate_percent', 0),
        'Total Requests': cache.get('total_cache_requests', 0)
    }
    
    fig.add_trace(
        go.Bar(
            x=list(cache_metrics.keys()),
            y=list(cache_metrics.values()),
            marker_color=['lightblue', 'lightgreen'],
            text=[f"{v:.1f}%" if 'Rate' in k else str(v) for k, v in cache_metrics.items()],
            textposition='auto'
        ),
        row=1, col=2
    )
    
    fig.update_layout(height=400, showlegend=False, title_text="Cache Performance")
    return fig


def main():
    """Main dashboard application."""
    st.title("🎬 Sonora AI Dubbing Analytics Dashboard")
    st.markdown("Real-time performance monitoring for the Sonora AI Dubbing System")
    
    # Sidebar controls
    st.sidebar.header("Dashboard Controls")
    
    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("Auto-refresh (5s)", value=True)
    refresh_interval = 5 if auto_refresh else 0
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Now"):
        st.cache_data.clear()
        st.rerun()
    
    # API status check
    st.sidebar.header("API Status")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            st.sidebar.success("✅ API Online")
        else:
            st.sidebar.error("❌ API Error")
    except:
        st.sidebar.error("❌ API Offline")
    
    # Fetch data
    metrics = fetch_metrics()
    analytics = fetch_analytics()
    
    if not metrics:
        st.error("Unable to fetch metrics from the API. Please ensure the Sonora server is running.")
        return
    
    # Header metrics
    st.header("📊 System Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Uptime",
            value=format_uptime(metrics.get('uptime_seconds', 0)),
            help="Server uptime"
        )
    
    with col2:
        st.metric(
            label="Total Requests",
            value=metrics.get('total_requests', 0),
            help="Total API requests processed"
        )
    
    with col3:
        st.metric(
            label="Error Rate",
            value=f"{metrics.get('total_errors', 0)}",
            help="Total errors encountered"
        )
    
    with col4:
        cpu_percent = metrics.get('system', {}).get('cpu_percent', 0)
        st.metric(
            label="CPU Usage",
            value=f"{cpu_percent:.1f}%",
            help="Current CPU utilization"
        )
    
    # System Performance Section
    st.header("🖥️ System Performance")
    system_chart = create_system_metrics_chart(metrics)
    if system_chart:
        st.plotly_chart(system_chart, use_container_width=True)
    
    # Request Analytics Section
    st.header("📈 Request Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        latency_chart = create_latency_chart(metrics)
        if latency_chart:
            st.plotly_chart(latency_chart, use_container_width=True)
    
    with col2:
        requests_chart = create_requests_chart(metrics)
        if requests_chart:
            st.plotly_chart(requests_chart, use_container_width=True)
    
    # Audio Processing Section
    st.header("🎵 Audio Processing")
    audio_chart = create_audio_stats_chart(metrics)
    if audio_chart:
        st.plotly_chart(audio_chart, use_container_width=True)
    
    # Cache Performance Section
    st.header("💾 Cache Performance")
    cache_chart = create_cache_stats_chart(metrics)
    if cache_chart:
        st.plotly_chart(cache_chart, use_container_width=True)
    
    # Error Breakdown Section
    if metrics.get('error_breakdown'):
        st.header("⚠️ Error Breakdown")
        error_data = metrics['error_breakdown']
        
        if error_data:
            error_df = pd.DataFrame(list(error_data.items()), columns=['Error Type', 'Count'])
            fig = px.pie(error_df, values='Count', names='Error Type', title="Error Distribution")
            st.plotly_chart(fig, use_container_width=True)
    
    # Raw Data Section (Collapsible)
    with st.expander("🔍 Raw Metrics Data"):
        st.json(metrics)
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()


if __name__ == "__main__":
    main()









