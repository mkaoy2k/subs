"""
Article Table Batch Management Module

This module provides a PyQt5-based graphical interface for managing article data in an SQLite database.
Key features include creating, editing, deleting, and querying articles.

Main Features:
    - Connect to SQLite database
    - Load and display article table
    - Support for adding, editing, and deleting articles
    - Data validation and error handling
    - Track and save data changes

Classes:
    DatabaseViewer: Main window class providing the graphical interface for article management

Usage:
    1. Set the following environment variables in the .env file:
       - DB_PATH: Database file path (default: data/users.db)
       - TBL_ARTICLE: Article table name (default: article)
    2. Execute this script to start the application

Example:
    $ python ops_article.py

Dependencies:
    - PyQt5 >= 5.15.0
    - python-dotenv

Notes:
    - Ensure all required dependencies are installed in the execution environment
    - Ensure the database directory has write permissions
    - It is recommended to back up the database before making changes
"""

import os
import sys
import datetime
from pathlib import Path
from dotenv import load_dotenv
import db_utils as dbm

from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QVBoxLayout, QWidget, QMessageBox, QPushButton, QHBoxLayout
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QFont


class DatabaseViewer(QMainWindow):
    """
    Database Viewer Window Class
    
    This class provides a graphical interface for viewing and managing database tables.
    It allows users to view, add, edit, and delete records in the specified table.
    """
    def __init__(self, database_path, table_name):
        """
        Initialize the database viewer
        
        Args:
            database_path (str): Path to the SQLite database file
            table_name (str): Name of the table to display
        """
        super().__init__()
        self.setWindowTitle("SQLite Database Viewer")
        self.setGeometry(100, 100, 1000, 600)
        
        # Store database connection information
        self.database_path = database_path
        self.table_name = table_name
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create button area
        button_layout = QHBoxLayout()
        
        # Add save button
        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self.save_changes)
        self.save_button.setEnabled(False)
        
        # Add record button
        self.add_button = QPushButton("Add Record")
        self.add_button.clicked.connect(self.insert_record)
        
        # Add refresh button
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_data)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(refresh_button)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        # Initialize database connection
        if not self._init_database(database_path, table_name):
            return
        
        # Create table view
        self.tableView = QTableView()
        self.tableView.setEditTriggers(QTableView.DoubleClicked | QTableView.EditKeyPressed)
        self.tableView.setSelectionBehavior(QTableView.SelectRows)
        main_layout.addWidget(self.tableView)
        
        # Set model
        self.model.select()
        
        # Connect to data changed signal
        self.model.dataChanged.connect(self.on_data_changed)
        
        # Set table properties
        self.tableView.setModel(self.model)
        self.tableView.resizeColumnsToContents()
    
    def on_data_changed(self, top_left, bottom_right, roles=None):
        """
        Enable save button and update the updated_at field when data is changed
        
        Args:
            top_left: The top-left index of the changed data
            bottom_right: The bottom-right index of the changed data
            roles: The item roles that were changed
        """
        # Check if it's an updated_at field change to avoid infinite recursion
        if top_left.column() == self.model.fieldIndex('updated_at'):
            return
            
        # Enable save button
        self.save_button.setEnabled(True)
        
        # Get current time
        current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        
        # Update updated_at field and prevent triggering dataChanged signal
        self.model.blockSignals(True)  # Temporarily block signals
        index = self.model.index(top_left.row(), self.model.fieldIndex('updated_at'))
        self.model.setData(index, current_time)
        self.model.blockSignals(False)  # Restore signal emission
    
    def insert_record(self):
        """
        Insert a new record into the table
        
        This method adds a new row to the model with default values and prepares it for editing.
        It also updates the UI to show the new record and enables the save button.
        """
        print("\n=== Starting to add a new record ===")
    
        try:
            # Get the current row count
            current_row = self.model.rowCount()
            print(f"Inserting new row at position {current_row}...")
        
            # Insert a new row
            if not self.model.insertRow(current_row):
                raise Exception("Failed to insert new row: " + self.model.lastError().text())
        
            # Get current timestamp
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
            # Set default values for the new record
            defaults = {
                "title": "New Article",
                "content": "",
                "category": "News",
                "author": "",
                "source": "",
                "src_url": "",
                "image_url": "",
                "l10n": "US",
                "created_at": now,
                "updated_at": now
            }
        
            # Set values for all fields
            for i, (field, value) in enumerate(defaults.items(), start=1):
                index = self.model.index(current_row, i)
                if not self.model.setData(index, value):
                    print(f"Warning: Failed to set value for {field}: {self.model.lastError().text()}")
        
            # Scroll to the new row and start editing
            self.tableView.scrollToBottom()
            self.tableView.setCurrentIndex(self.model.index(current_row, 1))  # Select the title field
            self.tableView.edit(self.model.index(current_row, 1))
        
            # Enable the save button
            self.save_button.setEnabled(True)
        
            print(f"Successfully added new record. Total records: {self.model.rowCount()}")
        
        except Exception as e:
            error_msg = f"Error occurred while adding record: {str(e)}"
            print(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
            self.model.revertAll()

    def save_changes(self):
        """
        Save changes to the database
        
        This method commits all pending changes in the model to the database.
        It handles transaction management and provides user feedback on success or failure.
        """
        print("\n=== Starting to save changes ===")
        print(f"Are there unsaved changes in the model: {self.model.isDirty()}")
    
        if not self.model.isDirty():
            print("No changes to save")
            return
        
        # Display current record count
        current_row_count = self.model.rowCount()
        print(f"Record count before save: {current_row_count}")
    
        # Begin transaction
        print("Starting database transaction...")
        if not self.db.transaction():
            error_msg = f"Failed to start transaction: {self.db.lastError().text()}"
            print(error_msg)
            QMessageBox.critical(self, "Database Error", error_msg)
            return
        
        try:
            # Submit changes to the database
            print("Submitting changes to database...")
            if not self.model.submitAll():
                error_msg = f"Failed to submit changes: {self.model.lastError().text()}"
                print(error_msg)
                raise Exception(error_msg)
            
            # Confirm the transaction was committed
            print("Committing transaction...")
            if not self.db.commit():
                error_msg = f"Failed to commit transaction: {self.db.lastError().text()}"
                print(error_msg)
                raise Exception(error_msg)
            
            # Reload the model to ensure data consistency
            print("Reloading model...")
            self.model.select()
            
            # Disable save button
            self.save_button.setEnabled(False)
            # Verify data was actually written to the database
            self._verify_data_persistence()
        
        except Exception as e:
            # Rollback transaction on error
            print(f"Error occurred, performing rollback: {str(e)}")
            if self.db.isOpen():
                if not self.db.rollback():
                    print(f"Rollback failed: {self.db.lastError().text()}")
            
            # Restore model state
            try:
                self.model.revertAll()
                if not self.model.select():
                    print(f"Failed to reload model: {self.model.lastError().text()}")
            except Exception as e2:
                print(f"Error occurred while restoring model state: {str(e2)}")
                
            # Show error message
            QMessageBox.critical(self, "Save Error", f"An error occurred while saving data:\n{str(e)}")
            
            # Re-enable button for retry
            self.save_button.setEnabled(True)

    def refresh_data(self):
        """
        Reload data from the database into the model
        
        This method refreshes the data in the model by selecting all records
        from the database and adjusting the table view columns to fit the content.
        It also disables the save button as no changes are pending after refresh.
        """
        self.model.select()
        self.tableView.resizeColumnsToContents()
        self.save_button.setEnabled(False)
    
    def _verify_data_persistence(self):
        """
        Verify that data has been correctly written to the database
        
        This method uses the existing database connection to verify data persistence
        without creating a new connection. It compares the record count in the database
        with the record count in the model to ensure data integrity.
        """
        print("\n=== Starting data persistence verification ===")
        
        # Get current database file path
        db_path = self.db.databaseName()
        print(f"Database file: {os.path.abspath(db_path)}")
        print(f"File size: {os.path.getsize(db_path) if os.path.exists(db_path) else 'File does not exist'} bytes")
        
        try:
            # Start transaction using main connection
            self.db.transaction()
            
            # Execute query using main connection
            query = QSqlQuery(self.db)
            if not query.exec_("SELECT COUNT(*) as count FROM article"):
                print(f"Failed to query record count: {query.lastError().text()}")
                self.db.rollback()
                return
                    
            if query.next():
                count = query.value(0)
                print(f"Record count in database: {count}")
                
                # Compare with model's record count
                model_count = self.model.rowCount()
                print(f"Record count in model: {model_count}")
                
                if count != model_count:
                    print(f"Warning: Database record count ({count}) does not match model record count ({model_count})")
                else:
                    print("Record count verification passed")
            
            # Commit transaction
            self.db.commit()
            
        except Exception as e:
            print(f"Error occurred during verification: {str(e)}")
            if self.db.isOpen():
                self.db.rollback()
        finally:
            # Ensure query object is properly cleaned up
            if 'query' in locals() and query is not None:
                query.finish()
    
    def _init_database(self, database_path, table_name):
        """
        Initialize database connection
        
        Args:
            database_path (str): Path to the database file
            table_name (str): Name of the table to use
            
        Returns:
            bool: True if database initialization was successful, False otherwise
        """
        # Display database file path
        print(f"Database path: {os.path.abspath(database_path)}")
        
        # Set up SQLite database
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName(database_path)
        
        # Ensure database directory exists
        db_dir = os.path.dirname(database_path)
        print(f"Database directory: {db_dir}")
        if db_dir and not os.path.exists(db_dir):
            print(f"Creating directory: {db_dir}")
            os.makedirs(db_dir, exist_ok=True)
            
        print(f"Attempting to open database...")
        if not self.db.open():
            error_msg = f"Failed to open database: {self.db.lastError().text()}"
            print(error_msg)
            QMessageBox.critical(self, "Database Error", error_msg)
            return False
            
        print("Database opened successfully")
        
        # Check if table exists, create if it doesn't
        print(f"Checking table: {table_name}")
        print(f"Existing tables: {self.db.tables()}")
        
        if table_name not in self.db.tables():
            print(f"Creating table: {table_name}")
            query = QSqlQuery(self.db)
            if not query.exec_(
                f"""
                CREATE TABLE {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT,
                    category TEXT,
                    author TEXT,
                    source TEXT,
                    src_url TEXT,
                    image_url TEXT,
                    l10n TEXT DEFAULT 'en',
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            ):
                error = f"Failed to create table: {query.lastError().text()}"
                print(error)
                QMessageBox.critical(self, "Table Error", error)
                return False
            print("Table creation/verification complete")
        
        # Initialize model - using OnManualSubmit strategy
        print("Initializing model...")
        self.model = QSqlTableModel(self, self.db)
        self.model.setTable(table_name)
        self.model.setEditStrategy(QSqlTableModel.OnManualSubmit)  # Changed to manual submit
        
        # Set column headers
        self.model.setHeaderData(0, Qt.Horizontal, "ID")
        column_headers = [
            (1, "Title"),
            (2, "Content"),
            (3, "Category"),
            (4, "Author"),
            (5, "Source"),
            (6, "Source URL"),
            (7, "Image URL"),
            (8, "Language"),
            (9, "Created At"),
            (10, "Updated At")
        ]
        for col, header in column_headers:
            self.model.setHeaderData(col, Qt.Horizontal, header)
        
        # Load data
        print("Loading data...")
        if not self.model.select():
            error = f"Failed to load table: {self.model.lastError().text()}"
            print(error)
            QMessageBox.critical(self, "Error", error)
            return False
            
        print(f"Loading complete, total {self.model.rowCount()} records")
        return True

def show_window(dbp=None, tbl=None):
    """
    Main function - entry point of the application
    
    Args:
        dbp (str, optional): Path to the database. If None, will use default from db_utils.
        tbl (str, optional): Table name. If None, will use default from db_utils.
    """
    # Create application object
    app = QApplication(sys.argv)
    
    # If no arguments provided, use defaults from db_utils
    if dbp is None or tbl is None:
        import db_utils as dbm
        dbp = dbp or dbm.dbn
        tbl = tbl or dbm.db_tables['article']
    
    # Create and show main window
    window = DatabaseViewer(dbp, tbl)
    window.show()
    
    # Enter application main event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    import argparse
    
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Article Batch Editor')
    parser.add_argument('--db', type=str, help='Path to the database file')
    parser.add_argument('--table', type=str, help='Name of the table to edit')
    
    # Parse command line arguments
    args = parser.parse_args()
    
    # Show the window with provided or default arguments
    show_window(args.db, args.table)
