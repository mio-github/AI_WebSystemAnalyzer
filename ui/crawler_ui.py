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
import queue
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

# スレッド間通信用のキュー
log_queue = queue.Queue()
progress_queue = queue.Queue()
status_queue = queue.Queue()


def process_thread_data():
    """スレッドからのデータを処理"""
    # ログキューの処理
    while not log_queue.empty():
        try:
            log_message = log_queue.get_nowait()
            if 'crawler_log' not in st.session_state:
                st.session_state.crawler_log = []
            st.session_state.crawler_log.append(log_message)
        except queue.Empty:
            break
    
    # 進捗キューの処理
    while not progress_queue.empty():
        try:
            progress = progress_queue.get_nowait()
            st.session_state.crawler_progress = progress
        except queue.Empty:
            break
    
    # ステータスキューの処理
    while not status_queue.empty():
        try:
            status = status_queue.get_nowait()
            if 'completed' in status:
                st.session_state.crawler_complete = status['completed']
            if 'running' in status:
                st.session_state.crawler_running = status['running']
            if 'output_dir' in status:
                st.session_state.crawler_output_dir = status['output_dir']
            if 'current_step' in status:
                st.session_state.current_step = status['current_step']
        except queue.Empty:
            break


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
    
    if 'config' not in st.session_state:
        st.session_state.config = {}
    
    # スレッドからのデータを処理
    process_thread_data()
    
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
                st.rerun()
    
    with col2:
        if st.session_state.crawler_running:
            stop_button = st.button(
                "中止",
                key="stop_crawler",
                type="secondary",
                use_container_width=True
            )
            
            if stop_button:
                log_queue.put("ユーザーによりクローリングが中止されました。")
                status_queue.put({'running': False, 'completed': False})
                # スレッドは停止できないため、フラグで処理中断を知らせる
    
    # 実行状態と進捗状況
    if st.session_state.crawler_running or st.session_state.crawler_complete:
        # プログレスバー
        progress_value = st.session_state.crawler_progress
        st.progress(progress_value)
        
        # 進捗パーセンテージと現在のステップ表示
        if 'current_step' not in st.session_state:
            st.session_state.current_step = ""
        
        progress_col1, progress_col2 = st.columns([1, 3])
        with progress_col1:
            st.markdown(f"**進捗率:** {int(progress_value * 100)}%")
        with progress_col2:
            st.markdown(f"**現在の処理:** {st.session_state.current_step}")
        
        # ログ表示
        st.markdown('<h2 class="sub-header">実行ログ</h2>', unsafe_allow_html=True)
        log_container = st.container()
        with log_container:
            for log in st.session_state.crawler_log:
                st.text(log)
        
        # 自動更新
        if st.session_state.crawler_running:
            # 2秒ごとに更新
            time.sleep(2)
            st.rerun()
        
        # 完了後のメッセージ
        if st.session_state.crawler_complete:
            output_dir = st.session_state.get('crawler_output_dir', "")
            if output_dir:
                st.success(f"クローリングとドキュメント生成が完了しました。結果は {output_dir} に保存されています。")
                
                # ドキュメント閲覧ページへのリンク
                if st.button("ドキュメント閲覧ページへ", use_container_width=True):
                    st.session_state.current_page = "viewer"
                    st.rerun()


def add_log(message):
    """
    ログメッセージをキューに追加（スレッドセーフ）
    
    Args:
        message (str): ログメッセージ
    """
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_entry = f"[{timestamp}] {message}"
    log_queue.put(log_entry)
    
    # コンソールにも出力
    print(f"LOG: {log_entry}")


def update_progress(value, step_description=""):
    """
    進捗状況をキューに追加（スレッドセーフ）
    
    Args:
        value (float): 進捗値（0～1）
        step_description (str): 現在のステップの説明
    """
    progress_queue.put(value)
    
    # 現在のステップ情報も更新
    if step_description:
        status_queue.put({'current_step': step_description})
        print(f"PROGRESS: {int(value * 100)}% - {step_description}")


def update_status(**kwargs):
    """
    ステータス情報をキューに追加（スレッドセーフ）
    
    Args:
        **kwargs: キーと値のペア
    """
    status_queue.put(kwargs)


def run_crawler_process():
    """クローリングプロセスを実行"""
    try:
        # 設定の取得
        config = {}
        if hasattr(st.session_state, 'config'):
            config = st.session_state.config
        
        # 一時的なオプションで設定を上書き
        if 'crawler' not in config:
            config['crawler'] = {}
        
        if hasattr(st.session_state, 'run_max_depth'):
            config['crawler']['max_depth'] = st.session_state.run_max_depth
        
        if hasattr(st.session_state, 'run_headless'):
            config['crawler']['headless'] = st.session_state.run_headless
        
        # データ抽出オプションの設定
        if 'data_extraction' not in config:
            config['data_extraction'] = {}
        
        if hasattr(st.session_state, 'run_data_extraction'):
            config['data_extraction']['enabled'] = st.session_state.run_data_extraction
        
        # ディレクトリ作成
        if 'storage' not in config:
            config['storage'] = {'base_dir': 'output', 'html_dir': 'html', 'screenshots_dir': 'screenshots', 'docs_dir': 'docs', 'data_dir': 'data'}
        
        base_dir = config['storage']['base_dir']
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(base_dir, timestamp)
        
        dirs = {
            'base': output_dir,
            'html': os.path.join(output_dir, config['storage'].get('html_dir', 'html')),
            'screenshots': os.path.join(output_dir, config['storage'].get('screenshots_dir', 'screenshots')),
            'docs': os.path.join(output_dir, config['storage'].get('docs_dir', 'docs')),
            'data': os.path.join(output_dir, config['storage'].get('data_dir', 'data')),
        }
        
        # ディレクトリ作成
        for dir_path in dirs.values():
            os.makedirs(dir_path, exist_ok=True)
        
        add_log(f"出力ディレクトリを作成しました: {output_dir}")
        add_log(f"HTML保存先: {dirs['html']}")
        add_log(f"スクリーンショット保存先: {dirs['screenshots']}")
        add_log(f"ドキュメント保存先: {dirs['docs']}")
        add_log(f"データ保存先: {dirs['data']}")
        update_status(output_dir=output_dir)
        update_progress(0.1, "環境準備完了")
        
        browser = None
        pages = None
        parsed_data = None
        
        try:
            # ステップ1: ログイン
            if hasattr(st.session_state, 'run_login') and st.session_state.run_login:
                add_log("ログイン処理を開始します...")
                login_manager = LoginManager(config)
                update_progress(0.15, "ブラウザ起動中...")
                browser = login_manager.login()
                add_log("ログインに成功しました")
                add_log(f"ログインURL: {browser.current_url}")
                add_log(f"ページタイトル: {browser.title}")
                update_progress(0.2, "ログイン完了")
            
            # ステップ2: クローリング
            if hasattr(st.session_state, 'run_crawling') and st.session_state.run_crawling and browser:
                add_log("クローリングを開始します...")
                # WebCrawlerにファイル保存の詳細を表示するコールバックを追加
                
                def crawler_callback(event, data):
                    """クローラーからのイベントを処理"""
                    if event == 'page_visit':
                        url = data.get('url', '')
                        title = data.get('title', '')
                        add_log(f"ページ訪問: {title} ({url})")
                    elif event == 'screenshot':
                        path = data.get('path', '')
                        url = data.get('url', '')
                        add_log(f"スクリーンショット保存: {path}")
                        # ファイル存在確認
                        if os.path.exists(path):
                            file_size = os.path.getsize(path)
                            add_log(f"  - ファイルサイズ: {file_size} bytes")
                        else:
                            add_log(f"  - ⚠️ ファイルが見つかりません")
                    elif event == 'html_save':
                        path = data.get('path', '')
                        url = data.get('url', '')
                        add_log(f"HTML保存: {path}")
                        # ファイル存在確認
                        if os.path.exists(path):
                            file_size = os.path.getsize(path)
                            add_log(f"  - ファイルサイズ: {file_size} bytes")
                        else:
                            add_log(f"  - ⚠️ ファイルが見つかりません")
                    elif event == 'link_found':
                        url = data.get('url', '')
                        text = data.get('text', '')
                        add_log(f"リンク検出: {text} ({url})")
                
                crawler = WebCrawler(browser, config, dirs)
                # クローラーに進捗コールバックを設定
                crawler.set_callback = crawler_callback
                update_progress(0.25, "クローリング準備中...")
                
                # クローリングの直前に空の出力フォルダをチェック
                add_log("出力ディレクトリの初期状態を確認:")
                for dir_name, dir_path in dirs.items():
                    files = os.listdir(dir_path) if os.path.exists(dir_path) else []
                    add_log(f"  - {dir_name}: {len(files)}ファイル")
                
                pages = crawler.crawl()
                
                # クローリング後の出力フォルダをチェック
                add_log("クローリング後の出力ディレクトリを確認:")
                for dir_name, dir_path in dirs.items():
                    files = os.listdir(dir_path) if os.path.exists(dir_path) else []
                    add_log(f"  - {dir_name}: {len(files)}ファイル")
                    if dir_name in ['html', 'screenshots'] and len(files) > 0:
                        # サンプルとして最大5つのファイルを表示
                        file_samples = files[:5]
                        add_log(f"    サンプルファイル: {', '.join(file_samples)}")
                
                add_log(f"クローリングが完了しました。合計{len(pages)}ページを取得しました")
                update_progress(0.5, f"クローリング完了（{len(pages)}ページ）")
            
            # ステップ3: HTML解析
            if hasattr(st.session_state, 'run_analysis') and st.session_state.run_analysis and pages:
                add_log("HTML解析を開始します...")
                html_parser = HTMLParser(dirs)
                update_progress(0.55, "HTML解析中...")
                
                # 解析対象ファイルの確認
                html_files = os.listdir(dirs['html']) if os.path.exists(dirs['html']) else []
                add_log(f"HTML解析対象: {len(html_files)}ファイル")
                if html_files:
                    add_log(f"解析対象のサンプル: {', '.join(html_files[:5])}")
                
                parsed_data = html_parser.parse_all()
                
                # 解析結果の確認
                if parsed_data:
                    add_log(f"HTML解析結果: {len(parsed_data)}ページの構造データ")
                    # サンプルとして最初のページの概要を表示
                    if len(parsed_data) > 0:
                        first_page = parsed_data[0]
                        page_url = first_page.get('url', '')
                        page_title = first_page.get('title', '')
                        elements = first_page.get('elements', {})
                        links = len(elements.get('links', []))
                        forms = len(elements.get('forms', []))
                        tables = len(elements.get('tables', []))
                        add_log(f"  サンプルページ: {page_title} ({page_url})")
                        add_log(f"    - リンク: {links}個, フォーム: {forms}個, テーブル: {tables}個")
                
                add_log("HTML解析が完了しました")
                update_progress(0.6, "HTML解析完了")
                
                # ステップ4: LLM解析
                add_log("LLM解析を開始します...")
                llm_analyzer = LLMAnalyzer(config, parsed_data)
                update_progress(0.65, "LLM解析中...")
                analysis_results = llm_analyzer.analyze()
                add_log("LLM解析が完了しました")
                update_progress(0.8, "LLM解析完了")
                
                # ステップ5: ドキュメント生成
                add_log("ドキュメント生成を開始します...")
                doc_generator = DocumentGenerator(dirs, analysis_results)
                update_progress(0.85, "ドキュメント生成中...")
                doc_generator.generate_all()
                
                # 生成されたドキュメントの確認
                docs_files = os.listdir(dirs['docs']) if os.path.exists(dirs['docs']) else []
                add_log(f"生成されたドキュメント: {len(docs_files)}ファイル")
                if docs_files:
                    add_log(f"ドキュメントサンプル: {', '.join(docs_files[:5])}")
                
                add_log("ドキュメント生成が完了しました")
                update_progress(0.9, "ドキュメント生成完了")
            
            # ステップ6: データ抽出（オプション）
            if hasattr(st.session_state, 'run_data_extraction') and st.session_state.run_data_extraction and browser and parsed_data:
                add_log("データ抽出を開始します...")
                update_progress(0.92, "データソース検出中...")
                data_finder = DataFinder(parsed_data, config)
                data_targets = data_finder.find_data_sources()
                
                update_progress(0.95, "データダウンロード中...")
                downloader = DataDownloader(browser, dirs, config)
                downloader.download_all(data_targets)
                add_log("データ抽出が完了しました")
                update_progress(0.98, "データ抽出完了")
            
            # 最終出力確認
            add_log("最終的な出力ファイル確認:")
            total_files = 0
            for dir_name, dir_path in dirs.items():
                files = os.listdir(dir_path) if os.path.exists(dir_path) else []
                add_log(f"  - {dir_name}ディレクトリ: {len(files)}ファイル")
                total_files += len(files)
            add_log(f"合計ファイル数: {total_files}ファイル")
            
            add_log(f"すべての処理が完了しました。結果は {output_dir} に保存されています")
            update_progress(1.0, "処理完了")
            
        finally:
            # ブラウザを閉じる
            if browser:
                browser.quit()
                add_log("ブラウザを終了しました")
        
        # 出力ディレクトリの更新（閲覧用）
        update_status(completed=True, running=False)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        add_log(f"エラーが発生しました: {str(e)}")
        add_log(f"エラー詳細: {error_details}")
        update_progress(0.0, "エラー発生")
        update_status(completed=False, running=False)
    
    finally:
        # 完了フラグを設定
        update_status(completed=True, running=False) 