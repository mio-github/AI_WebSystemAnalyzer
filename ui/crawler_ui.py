#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web自動解析システム - クローラー実行画面コンポーネント
"""

import os
import sys
import time
import yaml
import threading
import streamlit as st
from datetime import datetime

# 内部モジュールのインポート
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crawler.login import LoginManager
from crawler.crawler import WebCrawler
from analyzer.html_parser import HTMLParser
from analyzer.llm_analyzer import LLMAnalyzer
from analyzer.doc_generator import DocumentGenerator
from data_extractor.data_finder import DataFinder
from data_extractor.downloader import DataDownloader
from utils.logger import setup_logger


def render_crawler_page():
    """クローラー実行画面の描画"""
    st.markdown('<h1 class="main-header">クローラー実行</h1>', unsafe_allow_html=True)
    
    # 実行状態の初期化
    if 'crawler_running' not in st.session_state:
        st.session_state.crawler_running = False
    
    if 'crawler_complete' not in st.session_state:
        st.session_state.crawler_complete = False
    
    if 'crawler_log' not in st.session_state:
        st.session_state.crawler_log = []
    
    if 'crawler_progress' not in st.session_state:
        st.session_state.crawler_progress = 0
    
    if 'crawler_thread' not in st.session_state:
        st.session_state.crawler_thread = None
    
    # 実行オプション
    st.markdown('<h2 class="sub-header">実行オプション</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.checkbox(
            "ログイン実行",
            value=True,
            key="run_login",
            help="ターゲットシステムにログインするかどうか",
            disabled=st.session_state.crawler_running
        )
    
    with col2:
        st.checkbox(
            "クローリング実行",
            value=True,
            key="run_crawling",
            help="Web画面のクローリングを実行するかどうか",
            disabled=st.session_state.crawler_running
        )
    
    with col3:
        st.checkbox(
            "解析とドキュメント生成",
            value=True,
            key="run_analysis",
            help="HTMLの解析とドキュメント生成を実行するかどうか",
            disabled=st.session_state.crawler_running
        )
    
    # 詳細オプション
    with st.expander("詳細オプション", expanded=False):
        st.checkbox(
            "データ抽出実行",
            value=False,
            key="run_data_extraction",
            help="データソースの検出と抽出を実行するかどうか",
            disabled=st.session_state.crawler_running
        )
        
        # 動的にクローリング深度を設定可能に
        max_depth = st.session_state.config.get('crawler', {}).get('max_depth', 3)
        st.slider(
            "クロール深度",
            min_value=1,
            max_value=10,
            value=max_depth,
            key="run_max_depth",
            help="このセッションで使用するクロール深度",
            disabled=st.session_state.crawler_running
        )
        
        # ヘッドレスモードの一時的な切り替え
        headless = st.session_state.config.get('crawler', {}).get('headless', True)
        st.checkbox(
            "ヘッドレスモード",
            value=headless,
            key="run_headless",
            help="ブラウザを表示せずに実行するかどうか",
            disabled=st.session_state.crawler_running
        )
    
    # 実行ボタン
    col1, col2 = st.columns(2)
    with col1:
        if not st.session_state.crawler_running:
            start_button = st.button(
                "実行開始",
                key="start_crawler",
                type="primary",
                use_container_width=True,
                disabled=st.session_state.crawler_running
            )
            
            if start_button:
                st.session_state.crawler_running = True
                st.session_state.crawler_complete = False
                st.session_state.crawler_log = []
                st.session_state.crawler_progress = 0
                
                # 新しいスレッドで実行
                thread = threading.Thread(target=run_crawler_process)
                thread.daemon = True
                thread.start()
                st.session_state.crawler_thread = thread
                
                # ページを更新
                st.experimental_rerun()
    
    with col2:
        if st.session_state.crawler_running:
            stop_button = st.button(
                "中止",
                key="stop_crawler",
                type="secondary",
                use_container_width=True
            )
            
            if stop_button:
                st.session_state.crawler_log.append("ユーザーによりクローリングが中止されました。")
                st.session_state.crawler_running = False
                st.session_state.crawler_complete = False
                # スレッドは停止できないため、フラグで処理中断を知らせる
    
    # 実行状態と進捗状況
    if st.session_state.crawler_running or st.session_state.crawler_complete:
        # プログレスバー
        st.progress(st.session_state.crawler_progress)
        
        # ログ表示
        st.markdown('<h2 class="sub-header">実行ログ</h2>', unsafe_allow_html=True)
        log_container = st.container(height=300)
        with log_container:
            for log in st.session_state.crawler_log:
                st.text(log)
        
        # 自動更新
        if st.session_state.crawler_running:
            # 2秒ごとに更新
            time.sleep(2)
            st.experimental_rerun()
        
        # 完了後のメッセージ
        if st.session_state.crawler_complete:
            output_dir = st.session_state.get('crawler_output_dir', "")
            if output_dir:
                st.success(f"クローリングとドキュメント生成が完了しました。結果は {output_dir} に保存されています。")
                
                # ドキュメント閲覧ページへのリンク
                if st.button("ドキュメント閲覧ページへ", use_container_width=True):
                    st.session_state.current_page = "viewer"
                    st.experimental_rerun()


def add_log(message):
    """
    ログメッセージを追加
    
    Args:
        message (str): ログメッセージ
    """
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_entry = f"[{timestamp}] {message}"
    st.session_state.crawler_log.append(log_entry)


def run_crawler_process():
    """クローリングプロセスを実行"""
    try:
        # 設定の取得
        config = st.session_state.config
        
        # 一時的なオプションで設定を上書き
        config['crawler']['max_depth'] = st.session_state.run_max_depth
        config['crawler']['headless'] = st.session_state.run_headless
        
        # データ抽出オプションの設定
        if 'data_extraction' not in config:
            config['data_extraction'] = {}
        config['data_extraction']['enabled'] = st.session_state.run_data_extraction
        
        # ディレクトリ作成
        base_dir = config['storage']['base_dir']
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(base_dir, timestamp)
        
        dirs = {
            'base': output_dir,
            'html': os.path.join(output_dir, config['storage']['html_dir']),
            'screenshots': os.path.join(output_dir, config['storage']['screenshots_dir']),
            'docs': os.path.join(output_dir, config['storage']['docs_dir']),
            'data': os.path.join(output_dir, config['storage']['data_dir']),
        }
        
        # ディレクトリ作成
        for dir_path in dirs.values():
            os.makedirs(dir_path, exist_ok=True)
        
        add_log(f"出力ディレクトリを作成しました: {output_dir}")
        st.session_state.crawler_output_dir = output_dir
        st.session_state.crawler_progress = 0.1
        
        browser = None
        pages = None
        parsed_data = None
        
        try:
            # ステップ1: ログイン
            if st.session_state.run_login:
                add_log("ログイン処理を開始します...")
                login_manager = LoginManager(config)
                browser = login_manager.login()
                add_log("ログインに成功しました")
                st.session_state.crawler_progress = 0.2
            
            # ステップ2: クローリング
            if st.session_state.run_crawling and browser:
                add_log("クローリングを開始します...")
                crawler = WebCrawler(browser, config, dirs)
                pages = crawler.crawl()
                add_log(f"クローリングが完了しました。合計{len(pages)}ページを取得しました")
                st.session_state.crawler_progress = 0.5
            
            # ステップ3: HTML解析
            if st.session_state.run_analysis and pages:
                add_log("HTML解析を開始します...")
                html_parser = HTMLParser(dirs)
                parsed_data = html_parser.parse_all()
                add_log("HTML解析が完了しました")
                st.session_state.crawler_progress = 0.6
                
                # ステップ4: LLM解析
                add_log("LLM解析を開始します...")
                llm_analyzer = LLMAnalyzer(config, parsed_data)
                analysis_results = llm_analyzer.analyze()
                add_log("LLM解析が完了しました")
                st.session_state.crawler_progress = 0.8
                
                # ステップ5: ドキュメント生成
                add_log("ドキュメント生成を開始します...")
                doc_generator = DocumentGenerator(dirs, analysis_results)
                doc_generator.generate_all()
                add_log("ドキュメント生成が完了しました")
                st.session_state.crawler_progress = 0.9
            
            # ステップ6: データ抽出（オプション）
            if st.session_state.run_data_extraction and browser and parsed_data:
                add_log("データ抽出を開始します...")
                data_finder = DataFinder(parsed_data, config)
                data_targets = data_finder.find_data_sources()
                
                downloader = DataDownloader(browser, dirs, config)
                downloader.download_all(data_targets)
                add_log("データ抽出が完了しました")
            
            add_log(f"すべての処理が完了しました。結果は {output_dir} に保存されています")
            st.session_state.crawler_progress = 1.0
            
        finally:
            # ブラウザを閉じる
            if browser:
                browser.quit()
                add_log("ブラウザを終了しました")
        
        # 出力ディレクトリの更新（閲覧用）
        if 'available_output_dirs' not in st.session_state:
            st.session_state.available_output_dirs = []
        
        if timestamp not in st.session_state.available_output_dirs:
            st.session_state.available_output_dirs.insert(0, timestamp)
        
        st.session_state.selected_output_dir = timestamp
        
    except Exception as e:
        add_log(f"エラーが発生しました: {str(e)}")
        st.session_state.crawler_progress = 0.0
    
    finally:
        # 完了フラグを設定
        st.session_state.crawler_running = False
        st.session_state.crawler_complete = True 