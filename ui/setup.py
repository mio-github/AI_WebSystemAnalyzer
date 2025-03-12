#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web自動解析システム - 設定画面コンポーネント
"""

import os
import yaml
import streamlit as st


def render_setup_page():
    """設定画面の描画"""
    st.markdown('<h1 class="main-header">システム設定</h1>', unsafe_allow_html=True)
    
    # 設定タブの作成
    tabs = st.tabs(["ターゲットシステム", "クローラー設定", "ストレージ設定", "LLM設定", "ログ設定"])
    
    with tabs[0]:  # ターゲットシステム設定
        render_target_settings()
    
    with tabs[1]:  # クローラー設定
        render_crawler_settings()
    
    with tabs[2]:  # ストレージ設定
        render_storage_settings()
    
    with tabs[3]:  # LLM設定
        render_llm_settings()
    
    with tabs[4]:  # ログ設定
        render_log_settings()
    
    # 変更を反映ボタン
    st.button("変更を反映", use_container_width=True, 
              help="設定の変更をリアルタイムに反映します。永続的に保存するには、サイドバーの「設定を保存」ボタンを使用してください。")


def render_target_settings():
    """ターゲットシステム設定の描画"""
    st.markdown('<h2 class="sub-header">ターゲットシステム設定</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.text_input(
            "ベースURL",
            value=st.session_state.config.get('target', {}).get('base_url', ""),
            key="target_base_url",
            help="解析対象システムのベースURL",
            on_change=lambda: update_config('target.base_url', st.session_state.target_base_url)
        )
    
    with col2:
        st.text_input(
            "ログインURL",
            value=st.session_state.config.get('target', {}).get('login_url', ""),
            key="target_login_url",
            help="ログインページのURL",
            on_change=lambda: update_config('target.login_url', st.session_state.target_login_url)
        )
    
    st.markdown('<h3 class="sub-header">認証情報</h3>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.text_input(
            "ユーザー名",
            value=st.session_state.config.get('target', {}).get('credentials', {}).get('username', ""),
            key="target_username",
            help="ログイン用のユーザー名",
            on_change=lambda: update_config('target.credentials.username', st.session_state.target_username)
        )
    
    with col2:
        st.text_input(
            "パスワード",
            value=st.session_state.config.get('target', {}).get('credentials', {}).get('password', ""),
            key="target_password",
            type="password",
            help="ログイン用のパスワード",
            on_change=lambda: update_config('target.credentials.password', st.session_state.target_password)
        )


def render_crawler_settings():
    """クローラー設定の描画"""
    st.markdown('<h2 class="sub-header">クローラー設定</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.checkbox(
            "ヘッドレスモード",
            value=st.session_state.config.get('crawler', {}).get('headless', True),
            key="crawler_headless",
            help="ブラウザを表示せずに実行するかどうか",
            on_change=lambda: update_config('crawler.headless', st.session_state.crawler_headless)
        )
    
    with col2:
        st.checkbox(
            "スクリーンショット取得",
            value=st.session_state.config.get('crawler', {}).get('screenshot', True),
            key="crawler_screenshot",
            help="ページのスクリーンショットを取得するかどうか",
            on_change=lambda: update_config('crawler.screenshot', st.session_state.crawler_screenshot)
        )
    
    with col3:
        st.number_input(
            "同時実行数",
            min_value=1,
            max_value=10,
            value=st.session_state.config.get('crawler', {}).get('concurrency', 1),
            key="crawler_concurrency",
            help="クローリングの同時実行数（高い値はサーバーに負荷をかける可能性があります）",
            on_change=lambda: update_config('crawler.concurrency', st.session_state.crawler_concurrency)
        )
    
    col1, col2 = st.columns(2)
    with col1:
        st.number_input(
            "ページ読み込み待機時間（秒）",
            min_value=0.1,
            max_value=10.0,
            step=0.1,
            value=st.session_state.config.get('crawler', {}).get('delay', 1.5),
            key="crawler_delay",
            help="ページ読み込み後の待機時間（JavaScriptの実行などに必要）",
            on_change=lambda: update_config('crawler.delay', st.session_state.crawler_delay)
        )
    
    with col2:
        st.number_input(
            "クロール最大深度",
            min_value=1,
            max_value=10,
            value=st.session_state.config.get('crawler', {}).get('max_depth', 3),
            key="crawler_max_depth",
            help="リンクを辿る最大深度",
            on_change=lambda: update_config('crawler.max_depth', st.session_state.crawler_max_depth)
        )
    
    # 除外パターン
    st.text_area(
        "除外パターン (1行に1パターン)",
        value="\n".join(st.session_state.config.get('crawler', {}).get('exclude_patterns', [])),
        key="crawler_exclude_patterns",
        help="クロールから除外するURLパターン（正規表現）",
        on_change=lambda: update_config('crawler.exclude_patterns', 
                                       st.session_state.crawler_exclude_patterns.split('\n'))
    )


def render_storage_settings():
    """ストレージ設定の描画"""
    st.markdown('<h2 class="sub-header">ストレージ設定</h2>', unsafe_allow_html=True)
    
    st.text_input(
        "ベースディレクトリ",
        value=st.session_state.config.get('storage', {}).get('base_dir', "./output"),
        key="storage_base_dir",
        help="出力ファイルの保存先ベースディレクトリ",
        on_change=lambda: update_config('storage.base_dir', st.session_state.storage_base_dir)
    )
    
    col1, col2 = st.columns(2)
    with col1:
        st.text_input(
            "HTMLディレクトリ",
            value=st.session_state.config.get('storage', {}).get('html_dir', "html"),
            key="storage_html_dir",
            help="HTML保存用のサブディレクトリ名",
            on_change=lambda: update_config('storage.html_dir', st.session_state.storage_html_dir)
        )
        
        st.text_input(
            "スクリーンショットディレクトリ",
            value=st.session_state.config.get('storage', {}).get('screenshots_dir', "screenshots"),
            key="storage_screenshots_dir",
            help="スクリーンショット保存用のサブディレクトリ名",
            on_change=lambda: update_config('storage.screenshots_dir', st.session_state.storage_screenshots_dir)
        )
    
    with col2:
        st.text_input(
            "ドキュメントディレクトリ",
            value=st.session_state.config.get('storage', {}).get('docs_dir', "documents"),
            key="storage_docs_dir",
            help="生成されたドキュメント保存用のサブディレクトリ名",
            on_change=lambda: update_config('storage.docs_dir', st.session_state.storage_docs_dir)
        )
        
        st.text_input(
            "データディレクトリ",
            value=st.session_state.config.get('storage', {}).get('data_dir', "extracted_data"),
            key="storage_data_dir",
            help="抽出されたデータ保存用のサブディレクトリ名",
            on_change=lambda: update_config('storage.data_dir', st.session_state.storage_data_dir)
        )


def render_llm_settings():
    """LLM設定の描画"""
    st.markdown('<h2 class="sub-header">LLM設定</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox(
            "LLMプロバイダー",
            options=["openai", "anthropic", "azure"],
            index=["openai", "anthropic", "azure"].index(
                st.session_state.config.get('llm', {}).get('provider', "openai")
            ),
            key="llm_provider",
            help="使用するLLMプロバイダー",
            on_change=lambda: update_config('llm.provider', st.session_state.llm_provider)
        )
        
        st.text_input(
            "モデル名",
            value=st.session_state.config.get('llm', {}).get('model', "gpt-4o-mini"),
            key="llm_model",
            help="使用するモデル名",
            on_change=lambda: update_config('llm.model', st.session_state.llm_model)
        )
    
    with col2:
        st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            step=0.1,
            value=st.session_state.config.get('llm', {}).get('temperature', 0.1),
            key="llm_temperature",
            help="モデルの創造性（低い値=一貫性、高い値=創造性）",
            on_change=lambda: update_config('llm.temperature', st.session_state.llm_temperature)
        )
        
        st.number_input(
            "最大トークン数",
            min_value=100,
            max_value=16000,
            step=100,
            value=st.session_state.config.get('llm', {}).get('max_tokens', 4000),
            key="llm_max_tokens",
            help="生成するテキストの最大トークン数",
            on_change=lambda: update_config('llm.max_tokens', st.session_state.llm_max_tokens)
        )
    
    # APIキー設定
    api_key = os.environ.get('OPENAI_API_KEY', '')
    st.text_input(
        "APIキー",
        value=api_key,
        key="llm_api_key",
        type="password",
        help="LLM APIキー（環境変数で設定することも可能）",
    )
    if st.button("APIキーを環境変数に設定", help="入力されたAPIキーを一時的な環境変数として設定します"):
        os.environ['OPENAI_API_KEY'] = st.session_state.llm_api_key
        st.success("APIキーを環境変数に設定しました")


def render_log_settings():
    """ログ設定の描画"""
    st.markdown('<h2 class="sub-header">ログ設定</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox(
            "ログレベル",
            options=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            index=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"].index(
                st.session_state.config.get('logging', {}).get('level', "INFO")
            ),
            key="logging_level",
            help="ログの詳細レベル",
            on_change=lambda: update_config('logging.level', st.session_state.logging_level)
        )
    
    with col2:
        st.text_input(
            "ログファイル",
            value=st.session_state.config.get('logging', {}).get('file', "auto_analyze.log"),
            key="logging_file",
            help="ログを保存するファイル名",
            on_change=lambda: update_config('logging.file', st.session_state.logging_file)
        )


def update_config(path, value):
    """
    設定を更新する
    
    Args:
        path (str): ドット区切りのパス（例: 'crawler.headless'）
        value: 設定値
    """
    parts = path.split('.')
    config = st.session_state.config
    
    # 必要なディクショナリを作成
    temp = config
    for i in range(len(parts) - 1):
        part = parts[i]
        if part not in temp:
            temp[part] = {}
        temp = temp[part]
    
    # 値を設定
    temp[parts[-1]] = value 