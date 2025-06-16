"""
Database Management Tool

This module provides database management features including:
- Table structure modifications
- Database maintenance
- Data migration
"""

import sqlite3
import os
import streamlit as st
from db_utils import get_db_connection, user_tbl, article_tbl

def add_column_if_not_exists(table_name, column_name, column_definition):
    """
    Add a column to the specified table if it doesn't exist
    
    Args:
        table_name (str): Name of the table
        column_name (str): Name of the column to add
        column_definition (str): Column definition (e.g., "TEXT NOT NULL DEFAULT 'US'")
        
    Returns:
        bool: Returns True if successfully added or column already exists, False otherwise
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if column already exists
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [column[1] for column in cursor.fetchall()]
            
            if column_name.lower() in [col.lower() for col in columns]:
                st.info(f"Column '{column_name}' already exists in table '{table_name}'")
                return True
                
            # Add new column
            alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
            cursor.execute(alter_sql)
            conn.commit()
            st.success(f"Successfully added column '{column_name}' to table '{table_name}'")
            return True
            
    except sqlite3.Error as e:
        st.error(f"Error adding column: {str(e)}")
        return False

def init_db_management():
    """Initialize database management page"""
    st.title("Database Management Tool")
    
    st.header("Table Structure Management")
    
    # Select table to manage
    table = st.selectbox(
        "Select Table",
        [user_tbl, article_tbl]
    )
    
    st.subheader(f"Managing Table: {table}")
    
    # Display current table structure
    if st.button("Show Table Structure"):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                
                if not columns:
                    st.warning(f"Table not found: {table}")
                else:
                    st.write("### Table Structure")
                    st.table([{"Column Name": col[1], "Data Type": col[2], "Allow NULL": "No" if col[3] else "Yes", 
                               "Default": col[4], "Primary Key": "Yes" if col[5] else "No"} for col in columns])
        except sqlite3.Error as e:
            st.error(f"Error reading table structure: {str(e)}")
    
    # Add column functionality
    st.subheader("Add Column")
    with st.form("add_column_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_column = st.text_input("New Column Name", key="new_column")
        with col2:
            column_type = st.selectbox(
                "Data Type",
                ["TEXT", "INTEGER", "REAL", "BLOB", "TIMESTAMP"],
                key="column_type"
            )
        
        default_value = st.text_input("Default Value (Optional)", key="default_value")
        not_null = st.checkbox("NOT NULL Constraint", key="not_null")
        
        if st.form_submit_button("Add Column"):
            if not new_column:
                st.warning("Please enter a column name")
            else:
                # Build column definition
                column_definition = column_type
                if not_null:
                    column_definition += " NOT NULL"
                if default_value:
                    if column_type in ["TEXT", "TIMESTAMP"]:
                        default_value = f"'{default_value}'"
                    column_definition += f" DEFAULT {default_value}"
                
                if add_column_if_not_exists(table, new_column, column_definition):
                    st.rerun()
    
    # Special handling: Add l10n column to user table
    if table == user_tbl:
        st.subheader("Quick Actions")
        if st.button("Add l10n Column (if not exists)"):
            if add_column_if_not_exists(user_tbl, "l10n", "TEXT NOT NULL DEFAULT 'US'"):
                st.rerun()

if __name__ == "__main__":
    init_db_management()
