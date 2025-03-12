#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ロギング機能を提供するユーティリティモジュール
"""

import os
import logging
from logging.handlers import RotatingFileHandler


def setup_logger(level="INFO", log_file="auto_analyze.log"):
    """
    ロガーの設定を行う
    
    Args:
        level (str): ログレベル (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file (str): ログファイルのパス
        
    Returns:
        logging.Logger: 設定済みのロガーインスタンス
    """
    # ログレベルのマッピング
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    # 文字列からログレベルに変換
    log_level = level_map.get(level.upper(), logging.INFO)
    
    # ルートロガーの取得と設定
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # すでにハンドラが設定されている場合はクリア
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # コンソールハンドラの設定
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # ファイルハンドラの設定
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_format = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    return logger 