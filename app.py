#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web自動解析システム - GUIアプリケーション
"""

import os
import sys
import yaml
import time
import logging
import streamlit as st
from datetime import datetime
from pathlib import Path

# 内部モジュールのインポート
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.logger import setup_logger
from ui.setup import render_setup_page
from ui.crawler_ui import render_crawler_page
from ui.viewer import render_viewer_page
from ui.data_extractor_ui import render_data_extractor_page

# スタイル設定
st.set_page_config(
    page_title="Web自動解析システム",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSSスタイル
def load_css():
    css = """
    <style>
        .main-header {
            font-size: 2rem;
            color: #1E88E5;
            text-align: center;
            margin-bottom: 1rem;
        }
        .sub-header {
            font-size: 1.5rem;
            color: #0D47A1;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
        }
        .info-box {
            background-color: #E3F2FD;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        .success-box {
            background-color: #E8F5E9;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        .warning-box {
            background-color: #FFF8E1;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        .error-box {
            background-color: #FFEBEE;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
        }
        .stTabs [data-baseweb="tab"] {
            font-size: 1rem;
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def load_config(config_path="config.yaml"):
    """設定ファイルを読み込む"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        st.error(f"設定ファイルの読み込みに失敗しました: {e}")
        return {}

def initialize_session_state():
    """セッション状態の初期化"""
    if 'config' not in st.session_state:
        st.session_state.config = load_config()
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "setup"
    
    if 'crawler_results' not in st.session_state:
        st.session_state.crawler_results = None
    
    if 'available_output_dirs' not in st.session_state:
        st.session_state.available_output_dirs = []
        
    if 'selected_output_dir' not in st.session_state:
        st.session_state.selected_output_dir = None

def detect_output_directories():
    """出力ディレクトリを検出"""
    try:
        base_dir = st.session_state.config.get('storage', {}).get('base_dir', './output')
        if os.path.exists(base_dir):
            dirs = [d for d in os.listdir(base_dir) 
                   if os.path.isdir(os.path.join(base_dir, d)) and 
                   os.path.exists(os.path.join(base_dir, d, 'documents'))]
            
            # 新しいものから順にソート
            dirs.sort(reverse=True)
            
            st.session_state.available_output_dirs = dirs
            
            # 選択されていない場合は最新のディレクトリを選択
            if not st.session_state.selected_output_dir and dirs:
                st.session_state.selected_output_dir = dirs[0]
    except Exception as e:
        st.error(f"出力ディレクトリの検出中にエラーが発生しました: {e}")

def render_sidebar():
    """サイドバーの描画"""
    with st.sidebar:
        st.image("https://raw.githubusercontent.com/mio-github/AI_WebSystemAnalyzer/main/ui/assets/logo.png", 
                 width=100, use_column_width=False)
        st.title("Web自動解析システム")
        
        # ナビゲーションメニュー
        selected = st.radio(
            "ナビゲーション",
            ["設定", "クローラー実行", "ドキュメント閲覧", "データ抽出"],
            format_func=lambda x: {
                "設定": "💼 設定", 
                "クローラー実行": "🔍 クローラー実行", 
                "ドキュメント閲覧": "📄 ドキュメント閲覧", 
                "データ抽出": "💾 データ抽出"
            }[x],
        )
        
        # ページの切り替え
        if selected == "設定":
            st.session_state.current_page = "setup"
        elif selected == "クローラー実行":
            st.session_state.current_page = "crawler"
        elif selected == "ドキュメント閲覧":
            st.session_state.current_page = "viewer"
        elif selected == "データ抽出":
            st.session_state.current_page = "data_extractor"
        
        # 設定を保存ボタン
        if st.session_state.current_page == "setup":
            if st.button("設定を保存", use_container_width=True):
                try:
                    with open("config.yaml", "w", encoding="utf-8") as f:
                        yaml.dump(st.session_state.config, f, default_flow_style=False, allow_unicode=True)
                    st.success("設定を保存しました")
                except Exception as e:
                    st.error(f"設定の保存に失敗しました: {e}")
        
        # 出力ディレクトリ選択（ドキュメント閲覧ページのみ）
        if st.session_state.current_page in ["viewer", "data_extractor"]:
            if st.session_state.available_output_dirs:
                st.selectbox(
                    "出力ディレクトリ",
                    st.session_state.available_output_dirs,
                    index=st.session_state.available_output_dirs.index(st.session_state.selected_output_dir) 
                          if st.session_state.selected_output_dir in st.session_state.available_output_dirs else 0,
                    key="selected_output_dir"
                )
            else:
                st.info("利用可能な出力ディレクトリがありません")
        
        # バージョン情報
        st.markdown("---")
        st.caption("バージョン 0.1.0008")
        st.caption("© 2025 Mio System Co.,Ltd.")

def main():
    """メイン実行関数"""
    # セッション状態の初期化
    initialize_session_state()
    
    # CSSスタイルの読み込み
    load_css()
    
    # 出力ディレクトリの検出
    detect_output_directories()
    
    # サイドバーの描画
    render_sidebar()
    
    # 現在のページを描画
    if st.session_state.current_page == "setup":
        render_setup_page()
    elif st.session_state.current_page == "crawler":
        render_crawler_page()
    elif st.session_state.current_page == "viewer":
        render_viewer_page()
    elif st.session_state.current_page == "data_extractor":
        render_data_extractor_page()

if __name__ == "__main__":
    main() 