#!/usr/bin/env python3
"""
Advanced Strategy Evolution UI

Comprehensive Streamlit interface for tracking optimal day trading strategy evolution.
Features rich visualizations, detailed analysis, and interactive exploration.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import pickle
from datetime import datetime
import json
import numpy as np
from collections import defaultdict
import re
from streamlit import session_state as state

# Page config with advanced settings
st.set_page_config(
    page_title="🧪 Advanced Strategy Evolution Lab", 
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
.metric-container {
    background-color: #f0f2f6;
    padding: 10px;
    border-radius: 10px;
    border-left: 5px solid #4CAF50;
}
.stAlert > div {
    padding: 10px;
}
.strategy-card {
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 15px;
    margin: 10px 0;
    background-color: #fafafa;
}
</style>
""", unsafe_allow_html=True)

def calculate_complexity_score(params):
    """Calculate a simple complexity score based on parameter count and types"""
    if not params:
        return 0
    score = len(params) * 10
    for k, v in params.items():
        if isinstance(v, (list, dict)):
            score += 20
        elif isinstance(v, str) and len(v) > 50:
            score += 15
    return min(score, 100)

def get_performance_grade(score):
    """Assign performance grade based on score"""
    if score >= 2.0:
        return "🏆 Excellent"
    elif score >= 1.5:
        return "🥈 Great"
    elif score >= 1.0:
        return "🥉 Good"
    elif score >= 0.5:
        return "📈 Fair"
    else:
        return "❌ Poor"

def load_strategy_logs(log_dir_path):
    """Load comprehensive strategy evolution logs from directory"""
    log_dir = Path(log_dir_path)
    
    # Initialize data structures
    evolution_data = []
    code_data = defaultdict(dict)  # Store strategy code by round
    feedback_data = defaultdict(list)  # Store feedback by round
    hypothesis_data = {}  # Store hypotheses
    
    # Load evolving code messages (our strategy data)
    evolving_code_dir = log_dir / "evolving code" / "1"
    
    if evolving_code_dir.exists():
        for pkl_file in evolving_code_dir.glob("*.pkl"):
            try:
                with open(pkl_file, 'rb') as f:
                    data_list = pickle.load(f)
                    if data_list and len(data_list) > 0:
                        data = data_list[0]  # First item in list
                        round_num = getattr(data, 'round', 0)
                        
                        evolution_data.append({
                            'round': round_num,
                            'strategy_name': getattr(data, 'strategy_name', 'Unknown'),
                            'strategy_type': getattr(data, 'strategy_type', 'Unknown'),
                            'parameters': getattr(data, 'parameters', {}),
                            'metrics': getattr(data, 'metrics', {}),
                            'status': getattr(data, 'status', 'unknown'),
                            'timestamp': getattr(data, 'timestamp', ''),
                            'task_name': getattr(data, 'target_task', type('obj', (), {'name': 'Unknown'})).name,
                            'execution_time': getattr(data, 'execution_time', 0),
                            'code_size': len(str(getattr(data, 'parameters', {}))),
                            'complexity_score': calculate_complexity_score(getattr(data, 'parameters', {}))
                        })
                        
                        # Store strategy code if available
                        if hasattr(data, 'strategy_code'):
                            code_data[round_num] = getattr(data, 'strategy_code', '')
                            
            except Exception as e:
                st.sidebar.warning(f"Error reading {pkl_file.name}: {e}")
    
    # Sort by round number
    evolution_data.sort(key=lambda x: x['round'])
    return evolution_data, code_data, feedback_data, hypothesis_data

def get_available_log_dirs():
    """Get list of available log directories"""
    log_base = Path("/workspace/RD-Agent/log")
    if not log_base.exists():
        return []
    
    log_dirs = []
    for d in log_base.iterdir():
        if d.is_dir() and d.name.startswith("2025-"):
            # Check if it has our strategy evolution structure
            if (d / "evolving code").exists() or (d / "scenario").exists():
                log_dirs.append(d.name)
    
    return sorted(log_dirs, reverse=True)

# Enhanced Main UI with rich header
st.markdown("""
<div style="text-align: center; padding: 20px 0;">
<h1>🧪 Advanced Strategy Evolution Lab</h1>
<p style="font-size: 18px; color: #666;">Comprehensive Analysis & Visualization of Algorithmic Trading Strategy Evolution</p>
</div>
""", unsafe_allow_html=True)

# Sidebar for log selection
st.sidebar.header("🔧 Control Panel")
available_logs = get_available_log_dirs()

if not available_logs:
    st.error("❌ No strategy evolution logs found!")
    st.info("💡 Run the optimal day trading scenario first to generate logs.")
    st.stop()

selected_log = st.sidebar.selectbox(
    "📊 Choose Evolution Run:",
    available_logs,
    help="Select a strategy evolution run to analyze"
)

if selected_log:
    log_path = f"/workspace/RD-Agent/log/{selected_log}"
    evolution_data, code_data, feedback_data, hypothesis_data = load_strategy_logs(log_path)
    
    if not evolution_data:
        st.warning("⚠️ No strategy evolution data found in selected log.")
        st.stop()
    
    # Initialize session state for advanced features
    if 'selected_round' not in st.session_state:
        st.session_state.selected_round = 0
    if 'comparison_rounds' not in st.session_state:
        st.session_state.comparison_rounds = []

    # Add navigation tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "📈 Performance", "🧪 Evolution", "💻 Code Analysis", "🔍 Deep Dive"])

    # Tab 1: Overview with enhanced metrics
    with tab1:
        st.header("🎯 Evolution Overview Dashboard")
        
        # Enhanced metrics row 1
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_rounds = len(evolution_data)
            st.metric("Total Rounds", total_rounds)
        
        with col2:
            successful_rounds = len([d for d in evolution_data if d['status'] == 'success'])
            success_rate = (successful_rounds / total_rounds * 100) if total_rounds > 0 else 0
            st.metric("Success Rate", f"{success_rate:.1f}%", f"{successful_rounds}/{total_rounds}")
        
        with col3:
            if evolution_data:
                best_sharpe = max([d['metrics'].get('sharpe_ratio', -float('inf')) for d in evolution_data if d['status'] == 'success'], default=-float('inf'))
                st.metric("Best Sharpe", f"{best_sharpe:.2f}" if best_sharpe != -float('inf') else "N/A")
        
        with col4:
            if evolution_data:
                avg_complexity = np.mean([d['complexity_score'] for d in evolution_data])
                st.metric("Avg Complexity", f"{avg_complexity:.1f}")
        
        with col5:
            strategy_types = set([d['strategy_type'] for d in evolution_data])
            st.metric("Strategy Types", len(strategy_types))
        
        # Enhanced metrics row 2
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if evolution_data:
                total_trades = sum([d['metrics'].get('total_trades', 0) for d in evolution_data if d['status'] == 'success'])
                st.metric("Total Trades", f"{total_trades:,}")
        
        with col2:
            if evolution_data:
                avg_return = np.mean([d['metrics'].get('total_return', 0) * 100 for d in evolution_data if d['status'] == 'success'])
                st.metric("Avg Return", f"{avg_return:.1f}%")
        
        with col3:
            if evolution_data:
                best_win_rate = max([d['metrics'].get('win_rate', 0) * 100 for d in evolution_data if d['status'] == 'success'], default=0)
                st.metric("Best Win Rate", f"{best_win_rate:.1f}%")
        
        with col4:
            if evolution_data:
                min_drawdown = min([abs(d['metrics'].get('max_drawdown', 0)) * 100 for d in evolution_data if d['status'] == 'success'], default=0)
                st.metric("Min Drawdown", f"{min_drawdown:.1f}%")
        
        with col5:
            if evolution_data:
                improvement_rounds = sum(1 for i in range(1, len(evolution_data)) 
                                       if evolution_data[i]['metrics'].get('sharpe_ratio', -999) > evolution_data[i-1]['metrics'].get('sharpe_ratio', -999))
                st.metric("Improvement Rounds", improvement_rounds)
        
        # Evolution timeline
        st.subheader("📈 Evolution Timeline")
        if evolution_data:
            timeline_data = []
            for d in evolution_data:
                timeline_data.append({
                    'Round': d['round'],
                    'Status': '✅ Success' if d['status'] == 'success' else '❌ Failed',
                    'Sharpe': d['metrics'].get('sharpe_ratio', 0),
                    'Return': d['metrics'].get('total_return', 0) * 100,
                    'Strategy': d['strategy_name'],
                    'Type': d['strategy_type'],
                    'Complexity': d['complexity_score']
                })
            
            timeline_df = pd.DataFrame(timeline_data)
            
            # Interactive timeline chart
            fig = px.scatter(timeline_df, x='Round', y='Sharpe', 
                           color='Status', size='Complexity',
                           hover_data=['Return', 'Strategy', 'Type'],
                           title='Strategy Evolution Timeline')
            fig.add_hline(y=1.0, line_dash="dash", line_color="green", 
                         annotation_text="Target Sharpe > 1.0")
            fig.add_hline(y=0.0, line_dash="dot", line_color="red", 
                         annotation_text="Break-even")
            st.plotly_chart(fig, use_container_width=True)

    # Tab 2: Enhanced Performance Analysis  
    with tab2:
        st.header("📈 Performance Deep Dive")
        
        if evolution_data:
            df = pd.DataFrame(evolution_data)
            
            # Extract comprehensive metrics
            metrics_data = []
            for idx, row in df.iterrows():
                if row['status'] == 'success' and row['metrics']:
                    metrics_data.append({
                        'Round': row['round'],
                        'Strategy': row['strategy_name'],
                        'Type': row['strategy_type'],
                        'Sharpe Ratio': row['metrics'].get('sharpe_ratio', 0),
                        'Sortino Ratio': row['metrics'].get('sortino_ratio', 0),
                        'Total Return': row['metrics'].get('total_return', 0) * 100,
                        'Max Drawdown': abs(row['metrics'].get('max_drawdown', 0)) * 100,
                        'Win Rate': row['metrics'].get('win_rate', 0) * 100,
                        'Total Trades': row['metrics'].get('total_trades', 0),
                        'Avg Trade Return': row['metrics'].get('avg_trade_return', 0) * 100,
                        'Volatility': row['metrics'].get('volatility', 0) * 100,
                        'Parameters': str(row['parameters']),
                        'Complexity': row['complexity_score']
                    })
            
            if metrics_data:
                metrics_df = pd.DataFrame(metrics_data)
                
                # Performance metrics selection
                col1, col2 = st.columns([1, 3])
                with col1:
                    metric_options = ['Sharpe Ratio', 'Sortino Ratio', 'Total Return', 'Win Rate', 'Max Drawdown']
                    selected_metric = st.selectbox('Select Primary Metric:', metric_options)
                    show_all_rounds = st.checkbox('Include Failed Rounds', value=False)
                
                # Multi-panel performance dashboard
                fig = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=(f'{selected_metric} Evolution', 'Risk-Return Profile', 
                                  'Performance Distribution', 'Strategy Types'),
                    specs=[[{"colspan": 2}, None], [{}, {}]]
                )
                
                # Evolution line chart
                fig.add_trace(
                    go.Scatter(x=metrics_df['Round'], y=metrics_df[selected_metric],
                             mode='lines+markers', name=selected_metric,
                             line=dict(width=3), marker=dict(size=10)),
                    row=1, col=1
                )
                
                # Add target lines based on metric
                if selected_metric == 'Sharpe Ratio':
                    fig.add_hline(y=1.0, line_dash="dash", line_color="green", row=1, col=1)
                    fig.add_hline(y=2.0, line_dash="dash", line_color="blue", row=1, col=1)
                elif selected_metric == 'Total Return':
                    fig.add_hline(y=0.0, line_dash="dash", line_color="red", row=1, col=1)
                
                # Risk-Return scatter
                fig.add_trace(
                    go.Scatter(x=metrics_df['Total Return'], y=metrics_df['Sharpe Ratio'],
                             mode='markers', name='Strategies',
                             marker=dict(size=metrics_df['Win Rate']/3, 
                                       color=metrics_df['Round'], 
                                       colorscale='viridis',
                                       showscale=True),
                             text=metrics_df['Strategy'],
                             hovertemplate='<b>%{text}</b><br>Return: %{x:.1f}%<br>Sharpe: %{y:.2f}<extra></extra>'),
                    row=2, col=1
                )
                
                # Performance distribution
                fig.add_trace(
                    go.Histogram(x=metrics_df[selected_metric], nbinsx=8, 
                               name=f'{selected_metric} Distribution'),
                    row=2, col=2
                )
                
                fig.update_layout(height=800, showlegend=True, 
                                title_text="📊 Comprehensive Performance Analysis")
                st.plotly_chart(fig, use_container_width=True)
                
                # Performance leaderboard
                st.subheader("🏆 Performance Leaderboard")
                
                # Sort by selected metric
                sorted_df = metrics_df.sort_values(selected_metric, ascending=False)
                sorted_df['Rank'] = range(1, len(sorted_df) + 1)
                sorted_df['Grade'] = sorted_df[selected_metric].apply(get_performance_grade)
                
                # Display top performers
                display_cols = ['Rank', 'Round', 'Strategy', 'Type', selected_metric, 
                              'Grade', 'Total Trades', 'Win Rate']
                st.dataframe(sorted_df[display_cols], use_container_width=True)
                
        else:
            st.info("No performance data available")

    # Tab 3: Evolution Analysis
    with tab3:
        st.header("🧪 Evolution Pattern Analysis")
        
        if evolution_data and len(evolution_data) > 1:
            # Evolution statistics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader("📈 Improvement Tracking")
                improvements = 0
                deteriorations = 0
                
                for i in range(1, len(evolution_data)):
                    current_sharpe = evolution_data[i]['metrics'].get('sharpe_ratio', -999)
                    prev_sharpe = evolution_data[i-1]['metrics'].get('sharpe_ratio', -999)
                    
                    if current_sharpe > prev_sharpe:
                        improvements += 1
                    elif current_sharpe < prev_sharpe:
                        deteriorations += 1
                
                st.metric("Improvements", improvements, f"{improvements/(len(evolution_data)-1)*100:.1f}%")
                st.metric("Deteriorations", deteriorations, f"{deteriorations/(len(evolution_data)-1)*100:.1f}%")
            
            with col2:
                st.subheader("🎯 Strategy Diversity")
                strategy_changes = len(set(d['strategy_type'] for d in evolution_data))
                param_complexity = np.mean([d['complexity_score'] for d in evolution_data])
                
                st.metric("Strategy Variants", strategy_changes)
                st.metric("Avg Complexity", f"{param_complexity:.1f}")
            
            with col3:
                st.subheader("⏱️ Evolution Efficiency")
                total_time = sum(d.get('execution_time', 0) for d in evolution_data)
                best_round = max(evolution_data, key=lambda x: x['metrics'].get('sharpe_ratio', -999))['round']
                
                st.metric("Total Runtime", f"{total_time:.1f}s" if total_time > 0 else "N/A")
                st.metric("Best at Round", best_round)
            
            # Evolution heatmap
            st.subheader("🔥 Performance Heatmap")
            
            # Create heatmap data
            heatmap_data = []
            round_labels = []
            for d in evolution_data:
                if d['status'] == 'success':
                    heatmap_data.append([
                        d['metrics'].get('sharpe_ratio', 0),
                        d['metrics'].get('total_return', 0) * 100,
                        d['metrics'].get('win_rate', 0) * 100,
                        abs(d['metrics'].get('max_drawdown', 0)) * 100
                    ])
                    round_labels.append(f"Round {d['round']}")
            
            if heatmap_data:
                heatmap_df = pd.DataFrame(heatmap_data, 
                                        columns=['Sharpe Ratio', 'Total Return (%)', 'Win Rate (%)', 'Max Drawdown (%)'])
                heatmap_df.index = round_labels
                
                fig = px.imshow(heatmap_df.T, 
                              title="Strategy Performance Heatmap",
                              color_continuous_scale="RdYlGn",
                              aspect="auto")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Insufficient data for evolution analysis (need at least 2 rounds)")

    # Tab 4: Code Analysis
    with tab4:
        st.header("💻 Strategy Code Analysis")
        
        if code_data:
            st.subheader("📁 Strategy Code by Round")
            
            # Round selector for code viewing
            available_rounds = sorted(code_data.keys())
            if available_rounds:
                selected_code_round = st.selectbox("Select Round for Code View:", available_rounds)
                
                if selected_code_round in code_data:
                    st.code(code_data[selected_code_round], language='python')
                else:
                    st.info("No code available for this round")
            else:
                st.info("No strategy code found in logs")
        else:
            st.info("No strategy code available")
        
        # Code complexity analysis
        if evolution_data:
            st.subheader("📊 Code Complexity Evolution")
            
            complexity_data = [(d['round'], d['complexity_score'], d['metrics'].get('sharpe_ratio', 0)) 
                             for d in evolution_data if d['status'] == 'success']
            
            if complexity_data:
                complexity_df = pd.DataFrame(complexity_data, columns=['Round', 'Complexity', 'Sharpe'])
                
                fig = px.scatter(complexity_df, x='Complexity', y='Sharpe', 
                               title='📈 Complexity vs Performance',
                               hover_data=['Round'])
                fig.add_hline(y=1.0, line_dash="dash", line_color="green")
                st.plotly_chart(fig, use_container_width=True)

    # Tab 5: Deep Dive Analysis
    with tab5:
        st.header("🔬 Deep Dive Analysis")
        
        if evolution_data:
            # Strategy comparison
            st.subheader("⚖️ Strategy Comparison")
            
            comparison_rounds = st.multiselect(
                "Select rounds to compare:",
                options=[d['round'] for d in evolution_data if d['status'] == 'success'],
                default=[d['round'] for d in evolution_data if d['status'] == 'success'][:min(3, len(evolution_data))]
            )
            
            if len(comparison_rounds) >= 2:
                comparison_data = [d for d in evolution_data if d['round'] in comparison_rounds]
                
                # Radar chart for comparison
                fig = go.Figure()
                
                for data in comparison_data:
                    metrics = data['metrics']
                    values = [
                        metrics.get('sharpe_ratio', 0),
                        metrics.get('total_return', 0) * 100,
                        metrics.get('win_rate', 0) * 100,
                        100 - abs(metrics.get('max_drawdown', 0)) * 100  # Invert drawdown
                    ]
                    
                    fig.add_trace(go.Scatterpolar(
                        r=values + [values[0]],  # Close the polygon
                        theta=['Sharpe Ratio', 'Total Return (%)', 'Win Rate (%)', 'Low Drawdown'] + ['Sharpe Ratio'],
                        fill='toself',
                        name=f'Round {data["round"]} - {data["strategy_name"]}'
                    ))
                
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, max(5, 2)]
                        )
                    ),
                    showlegend=True,
                    title="🕸️ Strategy Performance Comparison"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Detailed strategy analysis
            st.subheader("📋 Detailed Strategy Analysis")
            
            # Create enhanced detailed table
            if evolution_data:
                table_data = []
                for d in evolution_data:
                    if d['status'] == 'success':
                        metrics = d['metrics']
                        table_data.append({
                            'Round': d['round'],
                            'Strategy': d['strategy_name'],
                            'Type': d['strategy_type'], 
                            'Parameters': ', '.join([f"{k}={v}" for k, v in d['parameters'].items()])[:100],
                            'Sharpe': f"{metrics.get('sharpe_ratio', 0):.3f}",
                            'Sortino': f"{metrics.get('sortino_ratio', 0):.3f}",
                            'Return': f"{metrics.get('total_return', 0)*100:.2f}%",
                            'Drawdown': f"{abs(metrics.get('max_drawdown', 0))*100:.2f}%",
                            'Win Rate': f"{metrics.get('win_rate', 0)*100:.1f}%",
                            'Trades': metrics.get('total_trades', 0),
                            'Volatility': f"{metrics.get('volatility', 0)*100:.2f}%",
                            'Grade': get_performance_grade(metrics.get('sharpe_ratio', 0)),
                            'Complexity': d['complexity_score']
                        })
                
                if table_data:
                    table_df = pd.DataFrame(table_data)
                    st.dataframe(table_df, use_container_width=True)
                    
                    # Enhanced best strategy highlights
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        best_sharpe_idx = table_df['Sharpe'].astype(float).idxmax()
                        best_sharpe = table_df.iloc[best_sharpe_idx]
                        st.success(f"🏆 **Best Sharpe**: {best_sharpe['Strategy']} (Round {best_sharpe['Round']})\n"
                                  f"Sharpe: {best_sharpe['Sharpe']} | Return: {best_sharpe['Return']}")
                    
                    with col2:
                        best_return_idx = table_df['Return'].str.rstrip('%').astype(float).idxmax()
                        best_return = table_df.iloc[best_return_idx]
                        st.success(f"💰 **Best Return**: {best_return['Strategy']} (Round {best_return['Round']})\n"
                                  f"Return: {best_return['Return']} | Sharpe: {best_return['Sharpe']}")
                    
                    with col3:
                        best_winrate_idx = table_df['Win Rate'].str.rstrip('%').astype(float).idxmax()
                        best_winrate = table_df.iloc[best_winrate_idx]
                        st.success(f"🎯 **Best Win Rate**: {best_winrate['Strategy']} (Round {best_winrate['Round']})\n"
                                  f"Win Rate: {best_winrate['Win Rate']} | Trades: {best_winrate['Trades']}")
                else:
                    st.info("No successful strategy data to display")
            
            # Enhanced Data Export
            st.subheader("📁 Data Export & Raw Data")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if evolution_data:
                    # Export evolution data
                    evolution_csv = pd.DataFrame(evolution_data).to_csv(index=False)
                    st.download_button(
                        "📊 Download Evolution Data (CSV)",
                        evolution_csv,
                        f"strategy_evolution_{selected_log}.csv",
                        "text/csv",
                        key="evolution_csv"
                    )
            
            with col2:
                if 'metrics_data' in locals() and metrics_data:
                    # Export detailed metrics
                    metrics_csv = pd.DataFrame(metrics_data).to_csv(index=False)
                    st.download_button(
                        "📈 Download Metrics Data (CSV)", 
                        metrics_csv,
                        f"strategy_metrics_{selected_log}.csv",
                        "text/csv",
                        key="metrics_csv"
                    )
            
            # Raw data viewer
            with st.expander("🗂️ View Raw Data", expanded=False):
                data_view = st.selectbox("Select data to view:", 
                                       ["Evolution Data", "Code Data", "Feedback Data"])
                
                if data_view == "Evolution Data":
                    st.json(evolution_data)
                elif data_view == "Code Data" and code_data:
                    st.json(dict(code_data))
                elif data_view == "Feedback Data" and feedback_data:
                    st.json(dict(feedback_data))
                else:
                    st.info(f"No {data_view.lower()} available")

# Enhanced Footer with system info
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**🧪 Advanced Strategy Evolution Lab**")
    st.markdown("*Powered by RD-Agent & VectorBT*")
with col2:
    if 'evolution_data' in locals() and evolution_data:
        st.markdown("**📊 Data Summary**")
        st.markdown(f"Rounds: {len(evolution_data)} | Success: {len([d for d in evolution_data if d['status'] == 'success'])}")
with col3:
    st.markdown("**⏰ Last Updated**")
    st.markdown(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")