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
    page_title="🧬 Advanced Strategy Evolution Lab", 
    page_icon="🧬",
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
    
    # Load additional logs (feedback, hypotheses)
    try:
        for log_file in log_dir.rglob("*.pkl"):
            if "feedback" in log_file.name:
                with open(log_file, 'rb') as f:
                    feedback_list = pickle.load(f)
                    if isinstance(feedback_list, list):
                        for fb in feedback_list:
                            round_match = re.search(r'round[_\s]*(\d+)', str(fb), re.IGNORECASE)
                            if round_match:
                                round_num = int(round_match.group(1))
                                feedback_data[round_num].append(str(fb))
    except Exception as e:
        pass  # Non-critical
    
    # Sort by round number
    evolution_data.sort(key=lambda x: x['round'])
    return evolution_data, code_data, feedback_data, hypothesis_data

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
<h1>🧬 Advanced Strategy Evolution Lab</h1>
<p style="font-size: 18px; color: #666;">Comprehensive Analysis & Visualization of Algorithmic Trading Strategy Evolution</p>
</div>
""", unsafe_allow_html=True)

# Add navigation tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "📈 Performance", "🧬 Evolution", "💾 Code Analysis", "🔍 Deep Dive"])

# Sidebar for log selection
st.sidebar.header("Select Evolution Run")
available_logs = get_available_log_dirs()

if not available_logs:
    st.error("No strategy evolution logs found!")
    st.info("Run the optimal day trading scenario first to generate logs.")
    st.stop()

selected_log = st.sidebar.selectbox(
    "Choose evolution run:",
    available_logs,
    help="Select a strategy evolution run to analyze"
)

if selected_log:
    log_path = f"/workspace/RD-Agent/log/{selected_log}"
    evolution_data, code_data, feedback_data, hypothesis_data = load_strategy_logs(log_path)
    
    if not evolution_data:
        st.warning("No strategy evolution data found in selected log.")
        st.stop()
    
    # Initialize session state for advanced features
    if 'selected_round' not in st.session_state:
        st.session_state.selected_round = 0
    if 'comparison_rounds' not in st.session_state:
        st.session_state.comparison_rounds = []
    
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
    
    # Evolution Progress Chart
    st.header("📊 Evolution Progress")
    
    if evolution_data:
        df = pd.DataFrame(evolution_data)
        
        # Extract metrics for plotting
        metrics_data = []
        for idx, row in df.iterrows():
            if row['status'] == 'success' and row['metrics']:
                metrics_data.append({
                    'Round': row['round'],
                    'Strategy': row['strategy_name'],
                    'Type': row['strategy_type'],
                    'Sharpe Ratio': row['metrics'].get('sharpe_ratio', 0),
                    'Total Return': row['metrics'].get('total_return', 0) * 100,  # Convert to percentage
                    'Max Drawdown': abs(row['metrics'].get('max_drawdown', 0)) * 100,  # Convert to percentage
                    'Win Rate': row['metrics'].get('win_rate', 0) * 100,  # Convert to percentage
                    'Total Trades': row['metrics'].get('total_trades', 0),
                    'Parameters': str(row['parameters'])
                })
        
        if metrics_data:
            metrics_df = pd.DataFrame(metrics_data)
            
            # Sharpe Ratio Evolution
            fig = px.line(metrics_df, x='Round', y='Sharpe Ratio', 
                         title='Sharpe Ratio Evolution', 
                         hover_data=['Strategy', 'Type', 'Parameters'])
            fig.add_hline(y=1.0, line_dash="dash", line_color="green", 
                         annotation_text="Target (Sharpe > 1.0)")
            st.plotly_chart(fig, use_container_width=True)
            
            # Multi-metric comparison
            col1, col2 = st.columns(2)
            
            with col1:
                fig2 = px.bar(metrics_df, x='Round', y='Total Return', 
                             title='Total Return by Round (%)', color='Type')
                st.plotly_chart(fig2, use_container_width=True)
            
            with col2:
                fig3 = px.scatter(metrics_df, x='Total Return', y='Sharpe Ratio', 
                                 size='Win Rate', color='Type', hover_name='Strategy',
                                 title='Risk-Return Profile')
                st.plotly_chart(fig3, use_container_width=True)
    
    # Strategy Details Table
    st.header("🔍 Strategy Details")
    
    if evolution_data:
        # Create detailed table
        table_data = []
        for d in evolution_data:
            if d['status'] == 'success':
                metrics = d['metrics']
                table_data.append({
                    'Round': d['round'],
                    'Strategy': d['strategy_name'],
                    'Type': d['strategy_type'], 
                    'Parameters': ', '.join([f"{k}={v}" for k, v in d['parameters'].items()]),
                    'Sharpe Ratio': f"{metrics.get('sharpe_ratio', 0):.2f}",
                    'Total Return': f"{metrics.get('total_return', 0)*100:.1f}%",
                    'Max Drawdown': f"{abs(metrics.get('max_drawdown', 0))*100:.1f}%",
                    'Win Rate': f"{metrics.get('win_rate', 0)*100:.1f}%",
                    'Total Trades': metrics.get('total_trades', 0),
                    'Status': '✅' if metrics.get('sharpe_ratio', -1) > 1.0 else '❌'
                })
        
        if table_data:
            table_df = pd.DataFrame(table_data)
            st.dataframe(table_df, use_container_width=True)
            
            # Best Strategy Highlight
            best_idx = table_df['Sharpe Ratio'].astype(float).idxmax()
            best_strategy = table_df.iloc[best_idx]
            
            st.success(f"🏆 **Best Strategy**: {best_strategy['Strategy']} "
                      f"(Round {best_strategy['Round']}) - "
                      f"Sharpe: {best_strategy['Sharpe Ratio']}, "
                      f"Return: {best_strategy['Total Return']}")
        else:
            st.info("No successful strategy data to display")
    
    # Raw Data Export
    with st.expander("📁 Raw Data Export"):
        if evolution_data:
            st.json(evolution_data)
            
            # Download button for CSV
            if metrics_data:
                csv = pd.DataFrame(metrics_data).to_csv(index=False)
                st.download_button(
                    "Download Evolution Data (CSV)",
                    csv,
                    f"strategy_evolution_{selected_log}.csv",
                    "text/csv"
                )

# Footer
st.markdown("---")
st.markdown("*Strategy Evolution Tracker - Built for RD-Agent Optimal Day Trading*")