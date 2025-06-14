"""
文章資料庫管理模組 (Article Management Module)

此模組提供了一個基於 PyQt5 的圖形化介面，用於管理 SQLite 資料庫中的文章資料。
主要功能包括文章的新增、編輯、刪除和查詢。

主要功能：
    - 連接 SQLite 資料庫
    - 載入並顯示文章資料表
    - 支援新增、編輯和刪除文章
    - 提供資料驗證和錯誤處理
    - 支援資料變更追蹤和儲存

類別：
    DatabaseViewer: 主視窗類別，提供文章管理的圖形化介面

使用方式：
    1. 在 .env 檔案中設定以下環境變數：
       - DB_PATH: 資料庫檔案路徑 (預設: data/users.db)
       - TBL_ARTICLE: 文章資料表名稱 (預設: article)
    2. 執行此腳本以啟動應用程式

範例：
    $ python ops_article.py

依賴套件：
    - PyQt5 >= 5.15.0
    - python-dotenv

注意事項：
    - 確保執行環境已安裝所有必要的依賴套件
    - 確保資料庫目錄具有寫入權限
    - 建議在修改前先備份資料庫
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
    資料庫檢視器視窗類別
    """
    def __init__(self, database_path, table_name):
        """
        初始化資料庫檢視器
        
        參數:
            database_path (str): SQLite 資料庫檔案路徑
            table_name (str): 要顯示的資料表名稱
        """
        super().__init__()
        self.setWindowTitle("SQLite 資料庫檢視器")
        self.setGeometry(100, 100, 1000, 600)
        
        # 儲存資料庫連線資訊
        self.database_path = database_path
        self.table_name = table_name
        
        # 建立中央部件和佈局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 建立按鈕區域
        button_layout = QHBoxLayout()
        
        # 新增儲存按鈕
        self.save_button = QPushButton("儲存變更")
        self.save_button.clicked.connect(self.save_changes)
        self.save_button.setEnabled(False)
        
        # 新增記錄按鈕
        self.add_button = QPushButton("新增記錄")
        self.add_button.clicked.connect(self.insert_record)
        
        # 新增重新整理按鈕
        refresh_button = QPushButton("重新整理")
        refresh_button.clicked.connect(self.refresh_data)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(refresh_button)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        # 初始化資料庫連接
        if not self._init_database(database_path, table_name):
            return
        
        # 建立表格視圖
        self.tableView = QTableView()
        self.tableView.setEditTriggers(QTableView.DoubleClicked | QTableView.EditKeyPressed)
        self.tableView.setSelectionBehavior(QTableView.SelectRows)
        main_layout.addWidget(self.tableView)
        
        # 設定模型
        self.model.select()
        
        # 連接到資料變更信號
        self.model.dataChanged.connect(self.on_data_changed)
        
        # 設定表格屬性
        self.tableView.setModel(self.model)
        self.tableView.resizeColumnsToContents()
    
    def on_data_changed(self, top_left, bottom_right, roles=None):
        """
        當資料變更時啟用儲存按鈕並更新 updated_at 欄位
        """
        # 檢查是否是 updated_at 欄位的變更，避免無限遞迴
        if top_left.column() == self.model.fieldIndex('updated_at'):
            return
            
        # 啟用儲存按鈕
        self.save_button.setEnabled(True)
        
        # 獲取當前時間
        current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        
        # 更新 updated_at 欄位，並阻止觸發 dataChanged 信號
        self.model.blockSignals(True)  # 暫時阻斷信號
        index = self.model.index(top_left.row(), self.model.fieldIndex('updated_at'))
        self.model.setData(index, current_time)
        self.model.blockSignals(False)  # 恢復信號發送
    
    def insert_record(self):
        """
        新增一筆記錄
        """
        print("\n=== 開始新增記錄 ===")
    
        try:
            # 獲取當前行數
            current_row = self.model.rowCount()
            print(f"在位置 {current_row} 插入新行...")
        
            # 插入新行
            if not self.model.insertRow(current_row):
                raise Exception("插入新行失敗: " + self.model.lastError().text())
        
            # 設置預設值
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
            # 設置預設值
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
        
            # 設置所有欄位的值
            for i, (field, value) in enumerate(defaults.items(), start=1):
                index = self.model.index(current_row, i)
                if not self.model.setData(index, value):
                    print(f"警告: 無法設置 {field} 的值: {self.model.lastError().text()}")
        
            # 滾動到新行並開始編輯
            self.tableView.scrollToBottom()
            self.tableView.setCurrentIndex(self.model.index(current_row, 1))  # 選擇標題欄位
            self.tableView.edit(self.model.index(current_row, 1))
        
            # 啟用保存按鈕
            self.save_button.setEnabled(True)
        
            print(f"成功新增記錄，目前共 {self.model.rowCount()} 筆記錄")
        
        except Exception as e:
            error_msg = f"新增記錄時發生錯誤：{str(e)}"
            print(error_msg)
            QMessageBox.critical(self, "錯誤", error_msg)
            self.model.revertAll()

    def save_changes(self):
        """
        將變更儲存到資料庫
        """
        print("\n=== 開始儲存變更 ===")
        print(f"模型是否有未儲存變更: {self.model.isDirty()}")
    
        if not self.model.isDirty():
            print("沒有需要儲存的變更")
            return
        
        # 顯示當前記錄數
        current_row_count = self.model.rowCount()
        print(f"儲存前記錄數: {current_row_count}")
    
        # 開始交易
        print("開始資料庫交易...")
        if not self.db.transaction():
            error_msg = f"無法開始交易: {self.db.lastError().text()}"
            print(error_msg)
            QMessageBox.critical(self, "資料庫錯誤", error_msg)
            return
        
        try:
            # 提交變更到資料庫
            print("提交變更到資料庫...")
            if not self.model.submitAll():
                error_msg = f"提交變更失敗: {self.model.lastError().text()}"
                print(error_msg)
                raise Exception(error_msg)
            
            # 確認變更已提交
            print("確認提交交易...")
            if not self.db.commit():
                error_msg = f"提交交易失敗: {self.db.lastError().text()}"
                print(error_msg)
                raise Exception(error_msg)
            
            print("交易已成功提交")
        
            # 重新載入資料以確保同步
            print("重新載入資料...")
            if not self.model.select():
                error_msg = f"重新載入資料失敗: {self.model.lastError().text()}"
                print(error_msg)
                raise Exception(error_msg)
            
            # 顯示儲存後的記錄數
            new_row_count = self.model.rowCount()
            print(f"儲存後記錄數: {new_row_count}")
        
            if new_row_count > current_row_count:
                print(f"成功新增 {new_row_count - current_row_count} 筆記錄")
        
            # 顯示成功訊息
            QMessageBox.information(self, "成功", "資料已成功儲存！")
            self.save_button.setEnabled(False)
        
            # 驗證資料是否真的寫入資料庫
            self._verify_data_persistence()
        
        except Exception as e:
            # 發生錯誤時回滾交易
            print(f"發生錯誤，執行回滾: {str(e)}")
            if self.db.isOpen():
                if not self.db.rollback():
                    print(f"回滾失敗: {self.db.lastError().text()}")
            
            # 還原模型狀態
            try:
                self.model.revertAll()
                if not self.model.select():
                    print(f"重新載入模型失敗: {self.model.lastError().text()}")
            except Exception as e2:
                print(f"還原模型狀態時發生錯誤: {str(e2)}")
                
            # 顯示錯誤訊息
            QMessageBox.critical(self, "儲存錯誤", f"儲存資料時發生錯誤:\n{str(e)}")
            
            # 重新啟用按鈕以便重試
            self.save_button.setEnabled(True)

    def refresh_data(self):
        """
        重新載入資料
        """
        self.model.select()
        self.tableView.resizeColumnsToContents()
        self.save_button.setEnabled(False)
    
    def _verify_data_persistence(self):
        """
        驗證資料是否已正確寫入資料庫
        使用現有的資料庫連接進行驗證，避免創建新的連接
        """
        print("\n=== 開始驗證資料持久性 ===")
        
        # 取得當前資料庫檔案路徑
        db_path = self.db.databaseName()
        print(f"資料庫檔案: {os.path.abspath(db_path)}")
        print(f"檔案大小: {os.path.getsize(db_path) if os.path.exists(db_path) else '檔案不存在'} 位元組")
        
        try:
            # 使用主連接開始事務
            self.db.transaction()
            
            # 使用主連接執行查詢
            query = QSqlQuery(self.db)
            if not query.exec_("SELECT COUNT(*) as count FROM article"):
                print(f"查詢記錄數失敗: {query.lastError().text()}")
                self.db.rollback()
                return
                    
            if query.next():
                count = query.value(0)
                print(f"資料庫中的記錄數: {count}")
                
                # 比較模型中的記錄數
                model_count = self.model.rowCount()
                print(f"模型中的記錄數: {model_count}")
                
                if count != model_count:
                    print("警告: 模型與資料庫中的記錄數不一致！")
                    
                    # 清理現有查詢
                    query.finish()
                    
                    # 嘗試從資料庫讀取所有記錄
                    if query.exec_("SELECT id, title FROM article"):
                        print("\n資料庫中的記錄:") 
                        while query.next():
                            print(f"ID: {query.value(0)}, 標題: {query.value(1)}")
                    else:
                        print(f"讀取記錄失敗: {query.lastError().text()}")
                else:
                    print("驗證通過: 模型與資料庫中的記錄數一致")
            
            # 提交事務
            self.db.commit()
            
        except Exception as e:
            print(f"驗證過程中發生錯誤: {str(e)}")
            if self.db.isOpen():
                self.db.rollback()
        finally:
            # 確保查詢物件被正確清理
            if 'query' in locals() and query is not None:
                query.finish()
    
    def _init_database(self, database_path, table_name):
        """
        初始化資料庫連接
        
        參數:
            database_path (str): 資料庫檔案路徑
            table_name (str): 資料表名稱
            
        回傳:
            bool: 資料庫初始化是否成功
        """
        # 顯示資料庫檔案路徑
        print(f"資料庫路徑: {os.path.abspath(database_path)}")
        
        # 設定 SQLite 資料庫
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName(database_path)
        
        # 確保資料庫目錄存在
        db_dir = os.path.dirname(os.path.abspath(database_path))
        print(f"資料庫目錄: {db_dir}")
        
        if db_dir and not os.path.exists(db_dir):
            print(f"建立目錄: {db_dir}")
            os.makedirs(db_dir, exist_ok=True)
        
        print(f"嘗試開啟資料庫...")
        if not self.db.open():
            error_msg = f"無法開啟資料庫：{self.db.lastError().text()}"
            print(error_msg)
            QMessageBox.critical(self, "資料庫錯誤", error_msg)
            return False
            
        print("資料庫開啟成功")
        
        # 檢查資料表是否存在，如果不存在則建立
        print(f"檢查資料表: {table_name}")
        print(f"現有資料表: {self.db.tables()}")
        
        if table_name not in self.db.tables():
            print(f"建立資料表: {table_name}")
            query = QSqlQuery(self.db)
            if not query.exec_("""
                CREATE TABLE IF NOT EXISTS article (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT,
                    category TEXT,
                    author TEXT,
                    source TEXT,
                    src_url TEXT,
                    image_url TEXT,
                    l10n TEXT DEFAULT '繁中',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """):
                error = f"建立資料表失敗: {query.lastError().text()}"
                print(error)
                QMessageBox.critical(self, "資料表錯誤", error)
                return False
            print("資料表建立/確認完成")
        
        # 初始化模型 - 使用 OnManualSubmit 策略
        print("初始化模型...")
        self.model = QSqlTableModel(self, self.db)
        self.model.setTable(table_name)
        self.model.setEditStrategy(QSqlTableModel.OnManualSubmit)  # 改為手動提交
        
        # 設定欄位標題
        headers = [
            (0, "ID"),
            (1, "標題"),
            (2, "內容"),
            (3, "分類"),
            (4, "作者"),
            (5, "來源"),
            (6, "來源網址"),
            (7, "圖片網址"),
            (8, "語系"),
            (9, "建立時間"),
            (10, "更新時間")
        ]
        
        for col, header in headers:
            self.model.setHeaderData(col, Qt.Horizontal, header)
        
        # 載入資料
        print("載入資料...")
        if not self.model.select():
            error = f"無法載入資料表：{self.model.lastError().text()}"
            print(error)
            QMessageBox.critical(self, "錯誤", error)
            return False
            
        print(f"載入完成，共 {self.model.rowCount()} 筆記錄")
        return True


def main():
    """
    主函數，程式進入點
    """

    # 建立應用程式實例
    app = QApplication(sys.argv)
    
    # 建立並顯示主視窗
    window = DatabaseViewer(dbm.dbn, dbm.article_tbl)
    window.show()
    
    # 進入應用程式主循環
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
