#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web自動解析システム - データ抽出画面コンポーネント
"""

import os
import sys
import json
import time
import threading
import pandas as pd
import streamlit as st
from datetime import datetime

# 内部モジュールのインポート
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crawler.login import LoginManager
from data_extractor.data_finder import DataFinder
from data_extractor.downloader import DataDownloader


def render_data_extractor_page():
    """データ抽出画面の描画"""
    st.markdown('<h1 class="main-header">データ抽出</h1>', unsafe_allow_html=True)
    
    # 利用可能な出力ディレクトリがない場合
    if not st.session_state.available_output_dirs:
        st.warning("クローリング結果が見つかりません。先にクローラーを実行してください。")
        if st.button("クローラー実行画面へ", use_container_width=True):
            st.session_state.current_page = "crawler"
            st.experimental_rerun()
        return
    
    # 実行状態の初期化
    if 'extraction_running' not in st.session_state:
        st.session_state.extraction_running = False
    
    if 'extraction_complete' not in st.session_state:
        st.session_state.extraction_complete = False
    
    if 'extraction_log' not in st.session_state:
        st.session_state.extraction_log = []
    
    if 'extraction_progress' not in st.session_state:
        st.session_state.extraction_progress = 0
    
    if 'data_sources' not in st.session_state:
        st.session_state.data_sources = None
    
    if 'selected_sources' not in st.session_state:
        st.session_state.selected_sources = []
    
    # 選択されたディレクトリのパスを取得
    selected_dir = st.session_state.selected_output_dir
    base_dir = st.session_state.config.get('storage', {}).get('base_dir', './output')
    output_dir = os.path.join(base_dir, selected_dir)
    structure_file = os.path.join(output_dir, 'structure_data.json')
    data_dir = os.path.join(output_dir, st.session_state.config.get('storage', {}).get('data_dir', 'extracted_data'))
    
    # タブの作成
    tabs = st.tabs(["データソース検出", "ダウンロード済みデータ"])
    
    with tabs[0]:  # データソース検出
        render_data_source_detection(structure_file, output_dir, data_dir)
    
    with tabs[1]:  # ダウンロード済みデータ
        render_downloaded_data(data_dir)


def render_data_source_detection(structure_file, output_dir, data_dir):
    """データソース検出の表示"""
    st.markdown('<h2 class="sub-header">データソース検出</h2>', unsafe_allow_html=True)
    
    # データソースを検出または表示
    if st.session_state.data_sources is None:
        # 構造データファイルが存在するか確認
        if os.path.exists(structure_file):
            st.info("データソースを検出中...")
            
            # データソース検出
            st.session_state.data_sources = detect_data_sources(structure_file)
            
            if not st.session_state.data_sources:
                st.warning("データソースが検出されませんでした")
            else:
                st.success(f"{len(st.session_state.data_sources)}個のデータソースが見つかりました")
                # ページをリロード
                st.experimental_rerun()
        else:
            st.error("構造データファイルが見つかりません")
            return
    
    # データソースが見つかっている場合、表示
    if st.session_state.data_sources:
        # データソースのフィルタリングオプション
        filter_options = ["すべて", "リンク", "テーブル", "フォーム", "API"]
        selected_filter = st.selectbox("フィルタ", filter_options)
        
        # データソースのDF表示用にフィルタリング
        filtered_sources = st.session_state.data_sources
        if selected_filter != "すべて":
            source_type_map = {"リンク": "link", "テーブル": "table", "フォーム": "form", "API": "api"}
            filtered_sources = [s for s in st.session_state.data_sources 
                                if s.get('type') == source_type_map.get(selected_filter, "")]
        
        # データソースをDataFrameとして表示
        if filtered_sources:
            # 表示用のDataFrameを作成
            df_data = []
            for i, source in enumerate(filtered_sources):
                source_type = source.get('type', '')
                type_display = {
                    'link': 'リンク', 
                    'table': 'テーブル', 
                    'form': 'フォーム',
                    'api': 'API'
                }.get(source_type, source_type)
                
                url = source.get('url', '')
                text = source.get('text', '')
                title = source.get('title', '')
                page_url = source.get('page_url', '')
                file_type = source.get('file_type', '')
                
                # リンクテキストがない場合はURLを表示
                display_text = text if text else (title if title else url)
                if len(display_text) > 50:
                    display_text = display_text[:47] + "..."
                
                df_data.append({
                    'ID': i + 1,
                    'タイプ': type_display,
                    '説明': display_text,
                    'ファイル形式': file_type.upper() if file_type else '',
                    'ソースページ': os.path.basename(page_url) if page_url else '',
                    '選択': i in st.session_state.selected_sources
                })
            
            df = pd.DataFrame(df_data)
            
            # DataFrameをインタラクティブに表示
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                column_config={
                    "選択": st.column_config.CheckboxColumn(
                        "選択",
                        help="ダウンロードするデータソースを選択",
                        default=False,
                    )
                },
                disabled=["ID", "タイプ", "説明", "ファイル形式", "ソースページ"],
                hide_index=True,
            )
            
            # 選択された行を更新
            selected_rows = edited_df[edited_df['選択'] == True]['ID'].tolist()
            st.session_state.selected_sources = [idx - 1 for idx in selected_rows]
            
            # 詳細表示
            if st.session_state.selected_sources:
                st.markdown('<h3 class="sub-header">選択されたデータソースの詳細</h3>', unsafe_allow_html=True)
                
                for idx in st.session_state.selected_sources:
                    if idx < len(st.session_state.data_sources):
                        source = st.session_state.data_sources[idx]
                        with st.expander(f"データソース #{idx + 1}", expanded=True):
                            st.json(source)
        else:
            st.info(f"'{selected_filter}' タイプのデータソースが見つかりません")
        
        # データダウンロードボタン
        col1, col2 = st.columns(2)
        
        with col1:
            if not st.session_state.extraction_running and st.session_state.selected_sources:
                start_button = st.button(
                    "選択したデータをダウンロード",
                    key="start_extraction",
                    type="primary",
                    use_container_width=True,
                    disabled=st.session_state.extraction_running or not st.session_state.selected_sources
                )
                
                if start_button:
                    st.session_state.extraction_running = True
                    st.session_state.extraction_complete = False
                    st.session_state.extraction_log = []
                    st.session_state.extraction_progress = 0
                    
                    # 新しいスレッドで実行
                    thread = threading.Thread(
                        target=run_extraction_process, 
                        args=(output_dir, data_dir)
                    )
                    thread.daemon = True
                    thread.start()
                    
                    # ページを更新
                    st.experimental_rerun()
        
        with col2:
            if st.session_state.extraction_running:
                stop_button = st.button(
                    "中止",
                    key="stop_extraction",
                    type="secondary",
                    use_container_width=True
                )
                
                if stop_button:
                    st.session_state.extraction_log.append("ユーザーによりデータ抽出が中止されました。")
                    st.session_state.extraction_running = False
                    st.session_state.extraction_complete = False
        
        # 実行状態と進捗状況
        if st.session_state.extraction_running or st.session_state.extraction_complete:
            # プログレスバー
            st.progress(st.session_state.extraction_progress)
            
            # ログ表示
            st.markdown('<h3 class="sub-header">実行ログ</h3>', unsafe_allow_html=True)
            log_container = st.container(height=200)
            with log_container:
                for log in st.session_state.extraction_log:
                    st.text(log)
            
            # 自動更新
            if st.session_state.extraction_running:
                # 2秒ごとに更新
                time.sleep(2)
                st.experimental_rerun()
            
            # 完了後のメッセージ
            if st.session_state.extraction_complete:
                st.success("データダウンロードが完了しました")
                
                # タブ切り替えボタン
                if st.button("ダウンロード済みデータを表示", use_container_width=True):
                    # タブを切り替え
                    st.experimental_set_query_params(active_tab="ダウンロード済みデータ")
                    st.experimental_rerun()


def render_downloaded_data(data_dir):
    """ダウンロード済みデータの表示"""
    st.markdown('<h2 class="sub-header">ダウンロード済みデータ</h2>', unsafe_allow_html=True)
    
    if not os.path.exists(data_dir):
        st.warning("データディレクトリが見つかりません")
        return
    
    # 全ファイルを検索（サブディレクトリも含む）
    all_files = []
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if not file.startswith('.'):  # 隠しファイルを除外
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, data_dir)
                
                # ファイルサイズを取得
                file_size = os.path.getsize(file_path)
                size_str = format_size(file_size)
                
                # 更新日時を取得
                mtime = os.path.getmtime(file_path)
                date_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                
                all_files.append({
                    'ファイル名': file,
                    'パス': rel_path,
                    'サイズ': size_str,
                    '更新日時': date_str,
                    '絶対パス': file_path
                })
    
    if not all_files:
        st.info("ダウンロードされたデータがありません")
        return
    
    # データをDataFrameとして表示
    df = pd.DataFrame(all_files)
    
    # 表示用のDataFrame
    display_df = df[['ファイル名', 'パス', 'サイズ', '更新日時']]
    
    # DataFrameを表示
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # ファイルのプレビュー
    st.markdown('<h3 class="sub-header">ファイルプレビュー</h3>', unsafe_allow_html=True)
    
    # ファイル選択
    selected_file = st.selectbox(
        "プレビューするファイルを選択",
        df['パス'].tolist()
    )
    
    if selected_file:
        # 選択されたファイルの絶対パスを取得
        selected_row = df[df['パス'] == selected_file].iloc[0]
        file_path = selected_row['絶対パス']
        
        # ファイル拡張子を取得
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # ファイルタイプに応じて表示
        if ext in ['.csv', '.tsv']:
            try:
                # CSVファイルをDataFrameとして読み込み
                data = pd.read_csv(file_path)
                st.dataframe(data, use_container_width=True)
                
                # データ統計
                with st.expander("データ統計"):
                    st.write(data.describe())
            except Exception as e:
                st.error(f"ファイルの読み込みに失敗しました: {e}")
        
        elif ext in ['.xls', '.xlsx']:
            try:
                # Excelファイルを読み込み
                data = pd.read_excel(file_path)
                st.dataframe(data, use_container_width=True)
                
                # データ統計
                with st.expander("データ統計"):
                    st.write(data.describe())
            except Exception as e:
                st.error(f"ファイルの読み込みに失敗しました: {e}")
        
        elif ext in ['.json']:
            try:
                # JSONファイルを読み込み
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                st.json(data)
            except Exception as e:
                st.error(f"ファイルの読み込みに失敗しました: {e}")
        
        elif ext in ['.txt', '.md', '.log']:
            try:
                # テキストファイルを読み込み
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                st.text_area("ファイル内容", content, height=300)
            except Exception as e:
                st.error(f"ファイルの読み込みに失敗しました: {e}")
        
        elif ext in ['.png', '.jpg', '.jpeg', '.gif']:
            # 画像ファイルを表示
            st.image(file_path)
        
        else:
            st.info(f"このファイル形式 ({ext}) のプレビューはサポートされていません")
        
        # ダウンロードボタン
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        st.download_button(
            label="ファイルをダウンロード",
            data=file_content,
            file_name=os.path.basename(file_path),
            mime="application/octet-stream"
        )


def detect_data_sources(structure_file):
    """
    構造データからデータソースを検出
    
    Args:
        structure_file (str): 構造データファイルのパス
        
    Returns:
        list: 検出されたデータソースのリスト
    """
    try:
        # 構造データを読み込む
        with open(structure_file, 'r', encoding='utf-8') as f:
            structure_data = json.load(f)
        
        # データソースを検出
        data_sources = []
        
        for page in structure_data:
            page_url = page.get('url', '')
            elements = page.get('elements', {})
            
            # リンクからデータソースを検出
            for link in elements.get('links', []):
                url = link.get('url', '')
                text = link.get('text', '')
                title = link.get('title', '')
                
                # ファイル拡張子をチェック
                file_extensions = ['.csv', '.xlsx', '.xls', '.pdf', '.zip', '.json', '.xml']
                is_file_link = any(url.endswith(ext) for ext in file_extensions)
                
                # データダウンロード関連のキーワードをチェック
                keywords = ['download', 'export', 'csv', 'excel', 'pdf', 'report', 'data',
                            'ダウンロード', 'エクスポート', 'レポート', 'データ']
                
                is_data_link = False
                if text or title:
                    is_data_link = any(keyword.lower() in text.lower() or keyword.lower() in title.lower() 
                                     for keyword in keywords)
                
                if is_file_link or is_data_link:
                    # ファイルタイプを取得
                    file_type = get_file_type(url)
                    
                    # データソースを追加
                    data_sources.append({
                        'type': 'link',
                        'url': url,
                        'text': text,
                        'title': title,
                        'page_url': page_url,
                        'file_type': file_type
                    })
            
            # テーブルからデータソースを検出
            for i, table in enumerate(elements.get('tables', []), 1):
                headers = table.get('headers', [])
                rows = table.get('rows', [])
                
                # テーブルが十分なデータを持っているか確認
                if headers and len(headers) > 1 and rows and len(rows) > 1:
                    data_sources.append({
                        'type': 'table',
                        'page_url': page_url,
                        'table_index': i,
                        'headers': headers,
                        'row_count': len(rows),
                        'scrape_target': True
                    })
            
            # フォームからデータソースを検出
            for form in elements.get('forms', []):
                form_action = form.get('action', '')
                form_method = form.get('method', '').upper()
                fields = form.get('fields', [])
                
                # エクスポート関連のフィールドを検出
                keywords = ['export', 'download', 'csv', 'excel', 'report',
                            'エクスポート', 'ダウンロード', 'レポート']
                
                for field in fields:
                    field_name = field.get('name', '').lower()
                    field_value = field.get('value', '').lower()
                    field_id = field.get('id', '').lower()
                    
                    is_export_field = any(keyword in field_name or keyword in field_value or keyword in field_id 
                                         for keyword in keywords)
                    
                    if is_export_field:
                        data_sources.append({
                            'type': 'form',
                            'url': form_action,
                            'method': form_method,
                            'fields': fields,
                            'page_url': page_url,
                            'export_field': field_name
                        })
                        break
            
            # API呼び出しの検出
            api_patterns = ['/api/', '/rest/', '/data/', '/export/', '/json', '/xml']
            for link in elements.get('links', []):
                url = link.get('url', '')
                
                is_api = any(pattern in url for pattern in api_patterns)
                
                if is_api:
                    data_sources.append({
                        'type': 'api',
                        'url': url,
                        'page_url': page_url
                    })
        
        # 重複を削除
        unique_sources = []
        unique_urls = set()
        
        for source in data_sources:
            url = source.get('url', '')
            if source['type'] == 'table':
                # テーブルの場合はページURLとテーブルインデックスで一意に識別
                identifier = f"{source['page_url']}#{source['table_index']}"
            else:
                identifier = url
                
            if identifier and identifier not in unique_urls:
                unique_urls.add(identifier)
                unique_sources.append(source)
        
        return unique_sources
        
    except Exception as e:
        st.error(f"データソース検出中にエラーが発生しました: {e}")
        return []


def get_file_type(url):
    """URLからファイルタイプを判定"""
    extension_map = {
        '.csv': 'csv',
        '.tsv': 'csv',
        '.xlsx': 'excel',
        '.xls': 'excel',
        '.pdf': 'pdf',
        '.zip': 'archive',
        '.json': 'json',
        '.xml': 'xml',
        '.doc': 'document',
        '.docx': 'document',
        '.ppt': 'presentation',
        '.pptx': 'presentation'
    }
    
    # URLの末尾から拡張子を検出
    for ext, file_type in extension_map.items():
        if url.endswith(ext):
            return file_type
    
    # 拡張子がない場合はURLのパターンから推測
    if 'csv' in url:
        return 'csv'
    elif 'excel' in url or 'xlsx' in url or 'xls' in url:
        return 'excel'
    elif 'pdf' in url:
        return 'pdf'
    elif 'json' in url:
        return 'json'
    elif 'xml' in url:
        return 'xml'
    
    # 不明な場合
    return 'unknown'


def format_size(size_bytes):
    """バイト数を人間が読みやすい形式にフォーマット"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        size_kb = size_bytes / 1024
        return f"{size_kb:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        size_mb = size_bytes / (1024 * 1024)
        return f"{size_mb:.1f} MB"
    else:
        size_gb = size_bytes / (1024 * 1024 * 1024)
        return f"{size_gb:.1f} GB"


def add_log(message):
    """ログメッセージを追加"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_entry = f"[{timestamp}] {message}"
    st.session_state.extraction_log.append(log_entry)


def run_extraction_process(output_dir, data_dir):
    """データ抽出プロセスを実行"""
    try:
        # 設定の取得
        config = st.session_state.config
        
        # 選択されたデータソースのみ抽出
        selected_sources = []
        for idx in st.session_state.selected_sources:
            if idx < len(st.session_state.data_sources):
                selected_sources.append(st.session_state.data_sources[idx])
        
        if not selected_sources:
            add_log("選択されたデータソースがありません")
            return
        
        add_log(f"{len(selected_sources)}個のデータソースをダウンロードします")
        st.session_state.extraction_progress = 0.1
        
        # ディレクトリ存在確認
        os.makedirs(data_dir, exist_ok=True)
        
        # ブラウザセットアップ
        add_log("ブラウザを起動しています...")
        login_manager = LoginManager(config)
        browser = login_manager.login()
        add_log("ログインに成功しました")
        st.session_state.extraction_progress = 0.2
        
        try:
            # ダウンローダーの作成
            downloader = DataDownloader(browser, {'data': data_dir, 'base': output_dir}, config)
            
            # 各データソースをダウンロード
            total_sources = len(selected_sources)
            for i, source in enumerate(selected_sources):
                if not st.session_state.extraction_running:
                    add_log("ユーザーによりデータ抽出が中止されました")
                    break
                
                source_type = source.get('type', '')
                source_url = source.get('url', '')
                source_text = source.get('text', '') or source.get('title', '') or source_url
                
                # 進捗を更新
                progress = 0.2 + (0.8 * (i / total_sources))
                st.session_state.extraction_progress = progress
                
                # ソースタイプに応じたダウンロード
                add_log(f"データソース #{i+1} をダウンロード中: {source_text[:50]}...")
                
                if source_type == 'link':
                    result = downloader._download_link(source)
                elif source_type == 'table':
                    result = downloader._scrape_table(source)
                elif source_type == 'form':
                    result = downloader._download_form(source)
                elif source_type == 'api':
                    result = downloader._download_api(source)
                else:
                    add_log(f"不明なソースタイプ: {source_type}")
                    continue
                
                if result:
                    add_log(f"データソース #{i+1} のダウンロードが完了しました")
                else:
                    add_log(f"データソース #{i+1} のダウンロードに失敗しました")
            
            add_log(f"データ抽出が完了しました。結果は {data_dir} に保存されています")
            st.session_state.extraction_progress = 1.0
            
        finally:
            # ブラウザを閉じる
            if browser:
                browser.quit()
                add_log("ブラウザを終了しました")
        
    except Exception as e:
        add_log(f"データ抽出中にエラーが発生しました: {str(e)}")
        st.session_state.extraction_progress = 0.0
    
    finally:
        # 完了フラグを設定
        st.session_state.extraction_running = False
        st.session_state.extraction_complete = True 