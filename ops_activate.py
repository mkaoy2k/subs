#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
訂閱管理模組 (Subscription Management Module)

此腳本用於管理使用者的訂閱狀態，可以新增或更新使用者的訂閱資訊。

使用方法:
python ops_activate.py user@example.com "premium"
"""

import sys
import os
import logging
from dotenv import load_dotenv
import glogTime
import db_sqlite as dbm


def setup_logging():
    """
    設定日誌記錄
    
    Returns:
        logging.Logger: 配置好的日誌記錄器
    """
    log = logging.getLogger(__name__)
    log.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    log.addHandler(handler)
    return log

def update_subscription(email, subscription_msg, l10n):
    """
    更新使用者的訂閱狀態
    
    Args:
        email (str): 使用者的電子郵件
        subscription_msg (str): 訂閱狀態訊息
        
    Returns:
        bool: 更新成功返回 True，否則返回 False
    """
    user = dbm.get_user(email)
    
    if user is not None:
        try:
            dbm.update_user(email, {
                'subscription': subscription_msg,
                'l10n': l10n})
            return True
        except Exception as err:
            log.error(f"更新使用者訂閱狀態時發生錯誤: {err}")
            return False
    else:
        if dbm.validate_email(email):
            try:
                dbm.insert_user(email, subscription_msg, l10n)
                return True
            except Exception as err:
                log.error(f"新增使用者時發生錯誤: {err}")
                return False
        else:
            log.error(f"無效的電子郵件格式: {email}")
            return False

@glogTime.func_timer_decorator
def main():
    """
    主函數，處理命令列參數並執行相應操作
    
    預期參數:
        sys.argv[1]: 使用者的電子郵件
        sys.argv[2]: 訂閱狀態訊息
    """
    load_dotenv(".env")
    
    global log
    log = setup_logging()
    log.setLevel(getattr(logging, os.getenv("LOGGING", "INFO").upper(), logging.INFO))
    
    if len(sys.argv) != 3:
        log.error(f"參數錯誤，需要 2 個參數（電子郵件和訂閱訊息），但收到 {len(sys.argv)-1} 個")
        sys.exit(1)
        
    email = sys.argv[1].strip()
    subscription_msg = sys.argv[2].strip().upper()
    
    l10n = os.getenv("L10N", "TW").strip()
    if update_subscription(email, subscription_msg, l10n):
        print("Done")
    else:
        print("Failed")

if __name__ == "__main__":
    main()