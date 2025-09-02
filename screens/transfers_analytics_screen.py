import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

def get_transfers_data():
    """Get data from the transfers table"""
    try:
        conn = sqlite3.connect('db_unity.db')
        query = """
        SELECT 
            created_at,
            amount,
            developer_fee,
            developer_fee_percent,
            currency,
            state,
            source_currency,
            destination_currency
        FROM transfers_new
        WHERE amount IS NOT NULL AND amount > 0
        ORDER BY created_at
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Convert created_at to datetime with explicit format to avoid warnings
        df['created_at'] = pd.to_datetime(df['created_at'], format='%Y-%m-%dT%H:%M:%S.%fZ', errors='coerce')
        df['date'] = df['created_at'].dt.date
        df['weekday'] = df['created_at'].dt.weekday  # 0=Monday, 6=Sunday
        
        # Convert amount and developer_fee to numeric, handling any non-numeric values
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        df['developer_fee'] = pd.to_numeric(df['developer_fee'], errors='coerce')
        df['developer_fee_percent'] = pd.to_numeric(df['developer_fee_percent'], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

def show_transfers_analytics_screen():
    """Screen for analyzing transfers data"""
    st.markdown("## 📊 Análisis de Transferencias - Últimos 30 Días")
    
    # Load data
    df = get_transfers_data()
    
    if df.empty:
        st.warning("No se encontraron datos de transferencias.")
        return
    
    # Debug: Show data info
    st.info(f"Data loaded: {len(df)} rows, {len(df.columns)} columns")
    st.info(f"Amount column dtype: {df['amount'].dtype}, Sample values: {df['amount'].head(3).tolist()}")
    st.info(f"Developer fee column dtype: {df['developer_fee'].dtype}, Sample values: {df['developer_fee'].head(3).tolist()}")
    
    # Filter out weekends for statistics too
    weekday_df = df[df['weekday'] < 5]
    
    # Display basic statistics (weekdays only)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_amount = weekday_df['amount'].sum()
        if pd.isna(total_amount):
            st.metric("Total Amount (Weekdays)", "N/A")
        else:
            st.metric("Total Amount (Weekdays)", f"${total_amount:,.2f}")
    
    with col2:
        total_fees = weekday_df['developer_fee'].sum()
        if pd.isna(total_fees):
            st.metric("Total Developer Fees (Weekdays)", "N/A")
        else:
            st.metric("Total Developer Fees (Weekdays)", f"${total_fees:,.2f}")
    
    with col3:
        avg_fee_percent = weekday_df['developer_fee_percent'].mean()
        if pd.isna(avg_fee_percent):
            st.metric("Avg Fee % (Weekdays)", "N/A")
        else:
            st.metric("Avg Fee % (Weekdays)", f"{avg_fee_percent:.2f}%")
    
    with col4:
        total_transactions = len(weekday_df)
        st.metric("Total Transactions (Weekdays)", total_transactions)
    
    st.markdown("---")
    
    # Date range filter
    st.markdown("### 📅 Filtros de Fecha")
    col1, col2 = st.columns(2)
    
    with col1:
        min_date = weekday_df['date'].min()
        max_date = weekday_df['date'].max()
        start_date = st.date_input(
            "Fecha de inicio",
            value=min_date,
            min_value=min_date,
            max_value=max_date
        )
    
    with col2:
        end_date = st.date_input(
            "Fecha de fin",
            value=max_date,
            min_value=min_date,
            max_value=max_date
        )
    
    # Add weekend filter option
    st.markdown("**Nota:** Los datos mostrados excluyen automáticamente los fines de semana (sábados y domingos).")
    
    # Filter data by date range and exclude weekends (Saturday=5, Sunday=6)
    filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date) & (df['weekday'] < 5)]
    
    if filtered_df.empty:
        st.warning("No hay datos para el rango de fechas seleccionado.")
        return
    
    # Daily aggregation
    daily_stats = filtered_df.groupby('date').agg({
        'amount': ['sum', 'count'],
        'developer_fee': 'sum',
        'developer_fee_percent': 'mean'
    }).reset_index()
    
    daily_stats.columns = ['date', 'total_amount', 'transaction_count', 'total_fees', 'avg_fee_percent']
    
    # Charts
    st.markdown("### 📈 Evolución Diaria")
    
    # Amount evolution chart
    fig_amount = px.bar(
        daily_stats, 
        x='date', 
        y='total_amount',
        title='Evolución Diaria del Monto Total',
        labels={'total_amount': 'Monto Total ($)', 'date': 'Fecha'}
    )
    fig_amount.update_layout(
        height=400,
        xaxis=dict(
            type='category',
            tickmode='array',
            tickvals=daily_stats['date'].tolist(),
            ticktext=[d.strftime('%Y-%m-%d') for d in daily_stats['date']]
        )
    )
    st.plotly_chart(fig_amount, use_container_width=True)
    
    # Developer fees evolution chart
    fig_fees = px.bar(
        daily_stats, 
        x='date', 
        y='total_fees',
        title='Evolución Diaria de Developer Fees',
        labels={'total_fees': 'Developer Fees ($)', 'date': 'Fecha'}
    )
    fig_fees.update_layout(
        height=400,
        xaxis=dict(
            type='category',
            tickmode='array',
            tickvals=daily_stats['date'].tolist(),
            ticktext=[d.strftime('%Y-%m-%d') for d in daily_stats['date']]
        )
    )
    st.plotly_chart(fig_fees, use_container_width=True)
    
    # Combined chart
    fig_combined = go.Figure()
    
    fig_combined.add_trace(go.Bar(
        x=daily_stats['date'],
        y=daily_stats['total_amount'],
        name='Monto Total',
        yaxis='y'
    ))
    
    fig_combined.add_trace(go.Bar(
        x=daily_stats['date'],
        y=daily_stats['total_fees'],
        name='Developer Fees',
        yaxis='y2'
    ))
    
    fig_combined.update_layout(
        title='Evolución Diaria: Monto vs Developer Fees',
        height=500,
        yaxis=dict(title='Monto Total ($)', side='left'),
        yaxis2=dict(title='Developer Fees ($)', side='right', overlaying='y'),
        hovermode='x unified',
        barmode='group',
        xaxis=dict(
            type='category',
            tickmode='array',
            tickvals=daily_stats['date'].tolist(),
            ticktext=[d.strftime('%Y-%m-%d') for d in daily_stats['date']]
        )
    )
    
    st.plotly_chart(fig_combined, use_container_width=True)
    
    # Transaction count chart
    fig_count = px.bar(
        daily_stats,
        x='date',
        y='transaction_count',
        title='Número de Transacciones por Día',
        labels={'transaction_count': 'Número de Transacciones', 'date': 'Fecha'}
    )
    fig_count.update_layout(
        height=400,
        xaxis=dict(
            type='category',
            tickmode='array',
            tickvals=daily_stats['date'].tolist(),
            ticktext=[d.strftime('%Y-%m-%d') for d in daily_stats['date']]
        )
    )
    st.plotly_chart(fig_count, use_container_width=True)
    
    # Detailed data table
    st.markdown("### 📋 Datos Detallados")
    
    # Add currency filter
    currencies = ['Todos'] + list(filtered_df['currency'].unique())
    selected_currency = st.selectbox("Filtrar por Moneda", currencies)
    
    # Show weekday information
    st.markdown(f"**Datos mostrados:** {len(filtered_df)} transacciones de lunes a viernes")
    
    if selected_currency != 'Todos':
        filtered_df = filtered_df[filtered_df['currency'] == selected_currency]
    
    # Display table with key columns
    display_df = filtered_df[['created_at', 'amount', 'developer_fee', 'developer_fee_percent', 'currency', 'state']].copy()
    display_df['created_at'] = display_df['created_at'].dt.strftime('%Y-%m-%d %H:%M:%S')
    display_df.columns = ['Fecha', 'Monto', 'Developer Fee', 'Fee %', 'Moneda', 'Estado']
    
    st.dataframe(display_df, use_container_width=True)
    
    # Summary statistics
    st.markdown("### 📊 Estadísticas Resumen")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Estadísticas por Moneda:**")
        currency_stats = filtered_df.groupby('currency').agg({
            'amount': ['sum', 'mean', 'count'],
            'developer_fee': 'sum'
        }).round(2)
        currency_stats.columns = ['Total Amount', 'Avg Amount', 'Count', 'Total Fees']
        st.dataframe(currency_stats)
    
    with col2:
        st.markdown("**Estadísticas por Estado:**")
        state_stats = filtered_df.groupby('state').agg({
            'amount': ['sum', 'count'],
            'developer_fee': 'sum'
        }).round(2)
        state_stats.columns = ['Total Amount', 'Count', 'Total Fees']
        st.dataframe(state_stats)
