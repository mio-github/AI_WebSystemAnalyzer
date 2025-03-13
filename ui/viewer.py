#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web自動解析システム - ドキュメント閲覧画面コンポーネント
"""

import os
import json
import base64
import streamlit as st
from pathlib import Path


def render_viewer_page():
    """ドキュメント閲覧画面の描画"""
    st.markdown('<h1 class="main-header">ドキュメント閲覧</h1>', unsafe_allow_html=True)
    
    # 利用可能な出力ディレクトリがない場合
    if not st.session_state.available_output_dirs:
        st.warning("クローリング結果が見つかりません。先にクローラーを実行してください。")
        if st.button("クローラー実行画面へ", use_container_width=True):
            st.session_state.current_page = "crawler"
            st.rerun()
        return
    
    # 選択されたディレクトリのパスを取得
    selected_dir = st.session_state.selected_output_dir
    base_dir = st.session_state.config.get('storage', {}).get('base_dir', './output')
    output_dir = os.path.join(base_dir, selected_dir)
    docs_dir = os.path.join(output_dir, st.session_state.config.get('storage', {}).get('docs_dir', 'documents'))
    screenshots_dir = os.path.join(output_dir, st.session_state.config.get('storage', {}).get('screenshots_dir', 'screenshots'))
    html_dir = os.path.join(output_dir, st.session_state.config.get('storage', {}).get('html_dir', 'html'))
    
    # ドキュメントタブの作成
    tabs = st.tabs(["システム概要", "画面一覧", "画面仕様", "画面遷移", "画面ギャラリー", "HTML閲覧"])
    
    with tabs[0]:  # システム概要
        render_system_overview(docs_dir)
    
    with tabs[1]:  # 画面一覧
        render_screen_list(docs_dir)
    
    with tabs[2]:  # 画面仕様
        render_screen_specs(docs_dir)
    
    with tabs[3]:  # 画面遷移
        render_screen_flow(docs_dir)
    
    with tabs[4]:  # 画面ギャラリー
        render_screenshot_gallery(output_dir, screenshots_dir)
    
    with tabs[5]:  # HTML閲覧
        render_html_viewer(html_dir)


def render_system_overview(docs_dir):
    """システム概要の表示"""
    st.markdown('<h2 class="sub-header">システム概要</h2>', unsafe_allow_html=True)
    
    # システム概要のMarkdownファイルを探す
    overview_path = os.path.join(docs_dir, 'system_overview.md')
    overview_html_path = os.path.join(docs_dir, 'html', 'system_overview.html')
    
    if os.path.exists(overview_html_path):
        # HTMLファイルが存在する場合、iframeで表示
        render_html_iframe(overview_html_path)
    elif os.path.exists(overview_path):
        # Markdownファイルが存在する場合、そのまま表示
        with open(overview_path, 'r', encoding='utf-8') as f:
            overview_content = f.read()
        st.markdown(overview_content)
    else:
        st.warning("システム概要のドキュメントが見つかりません")


def render_screen_list(docs_dir):
    """画面一覧の表示"""
    st.markdown('<h2 class="sub-header">画面一覧</h2>', unsafe_allow_html=True)
    
    # 画面一覧のMarkdownファイルを探す
    screen_list_path = os.path.join(docs_dir, 'screen_list.md')
    screen_list_html_path = os.path.join(docs_dir, 'html', 'screen_list.html')
    
    if os.path.exists(screen_list_html_path):
        # HTMLファイルが存在する場合、iframeで表示
        render_html_iframe(screen_list_html_path)
    elif os.path.exists(screen_list_path):
        # Markdownファイルが存在する場合、そのまま表示
        with open(screen_list_path, 'r', encoding='utf-8') as f:
            screen_list_content = f.read()
        st.markdown(screen_list_content)
    else:
        st.warning("画面一覧のドキュメントが見つかりません")


def render_screen_specs(docs_dir):
    """画面仕様の表示"""
    st.markdown('<h2 class="sub-header">画面仕様</h2>', unsafe_allow_html=True)
    
    # 画面仕様のディレクトリを探す
    specs_dir = os.path.join(docs_dir, 'screen_specs')
    specs_html_dir = os.path.join(docs_dir, 'html', 'screen_specs')
    
    if os.path.exists(specs_dir) and os.path.isdir(specs_dir):
        # 画面仕様のファイル一覧を取得
        spec_files = [f for f in os.listdir(specs_dir) if f.endswith('.md')]
        
        if not spec_files:
            st.warning("画面仕様のドキュメントが見つかりません")
            return
        
        # 画面仕様ファイルのセレクトボックス
        selected_spec = st.selectbox(
            "画面を選択",
            sorted(spec_files),
            format_func=lambda x: x.replace('.md', '').replace('_', ' ').title()
        )
        
        # 選択された画面仕様を表示
        if selected_spec:
            spec_path = os.path.join(specs_dir, selected_spec)
            spec_html_path = os.path.join(specs_html_dir, selected_spec.replace('.md', '.html'))
            
            if os.path.exists(spec_html_path):
                # HTMLファイルが存在する場合、iframeで表示
                render_html_iframe(spec_html_path)
            elif os.path.exists(spec_path):
                # Markdownファイルが存在する場合、そのまま表示
                with open(spec_path, 'r', encoding='utf-8') as f:
                    spec_content = f.read()
                st.markdown(spec_content)
    else:
        st.warning("画面仕様のディレクトリが見つかりません")


def render_screen_flow(docs_dir):
    """画面遷移の表示"""
    st.markdown('<h2 class="sub-header">画面遷移</h2>', unsafe_allow_html=True)
    
    # 画面遷移のMarkdownファイルを探す
    flow_path = os.path.join(docs_dir, 'screen_flow.md')
    flow_html_path = os.path.join(docs_dir, 'html', 'screen_flow.html')
    
    if os.path.exists(flow_html_path):
        # HTMLファイルが存在する場合、iframeで表示
        render_html_iframe(flow_html_path)
    elif os.path.exists(flow_path):
        # Markdownファイルが存在する場合、そのまま表示
        with open(flow_path, 'r', encoding='utf-8') as f:
            flow_content = f.read()
        st.markdown(flow_content)
    else:
        st.warning("画面遷移のドキュメントが見つかりません")
    
    # 画面遷移図の表示（mermaidグラフがあれば）
    flow_diagram_path = os.path.join(docs_dir, 'screen_flow_diagram.md')
    if os.path.exists(flow_diagram_path):
        with open(flow_diagram_path, 'r', encoding='utf-8') as f:
            diagram_content = f.read()
        st.markdown(diagram_content)


def render_screenshot_gallery(output_dir, screenshots_dir):
    """スクリーンショットギャラリーの表示"""
    st.markdown('<h2 class="sub-header">画面ギャラリー</h2>', unsafe_allow_html=True)
    
    if os.path.exists(screenshots_dir) and os.path.isdir(screenshots_dir):
        # スクリーンショットファイルの一覧を取得
        screenshot_files = [f for f in os.listdir(screenshots_dir) 
                          if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if not screenshot_files:
            st.warning("スクリーンショットが見つかりません")
            return
        
        # ページインデックスファイルを読み込んでURL情報を取得
        index_file = os.path.join(output_dir, 'page_index.json')
        url_info = {}
        if os.path.exists(index_file):
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    page_index = json.load(f)
                    
                for page in page_index:
                    if 'screenshot_path' in page and page['screenshot_path']:
                        screenshot_name = os.path.basename(page['screenshot_path'])
                        url_info[screenshot_name] = {
                            'url': page.get('url', ''),
                            'title': page.get('title', '')
                        }
            except:
                pass
        
        # 5列表示
        cols = st.columns(5)
        
        # スクリーンショットをループで表示
        for i, file_name in enumerate(sorted(screenshot_files)):
            col_idx = i % 5
            with cols[col_idx]:
                # 画像パス
                img_path = os.path.join(screenshots_dir, file_name)
                
                # 画像を表示
                st.image(img_path, use_column_width=True)
                
                # 画像情報
                if file_name in url_info:
                    title = url_info[file_name].get('title', file_name)
                    url = url_info[file_name].get('url', '')
                    if url:
                        st.caption(f"**{title}**  \n{url}")
                    else:
                        st.caption(f"**{title}**")
                else:
                    st.caption(file_name)
                
                # 拡大表示ボタン
                with st.expander("拡大表示"):
                    st.image(img_path)
    else:
        st.warning("スクリーンショットのディレクトリが見つかりません")


def render_html_viewer(html_dir):
    """HTML閲覧機能の表示"""
    st.markdown('<h2 class="sub-header">HTML閲覧</h2>', unsafe_allow_html=True)
    
    if os.path.exists(html_dir) and os.path.isdir(html_dir):
        # HTMLファイルの一覧を取得
        html_files = [f for f in os.listdir(html_dir) if f.endswith('.html')]
        
        if not html_files:
            st.warning("HTMLファイルが見つかりません")
            return
        
        # HTMLファイルのセレクトボックス
        selected_html = st.selectbox(
            "HTMLファイルを選択",
            sorted(html_files),
            format_func=lambda x: x.replace('.html', '').replace('_', ' ').title()
        )
        
        # 選択されたHTMLファイルを表示
        if selected_html:
            html_path = os.path.join(html_dir, selected_html)
            
            # HTMLファイルを読み込み
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # HTMLをiframeで表示
            render_html_content(html_content)
            
            # ソースコード表示オプション
            with st.expander("HTMLソースコードを表示", expanded=False):
                st.code(html_content, language="html")
    else:
        st.warning("HTMLディレクトリが見つかりません")


def render_html_iframe(html_path):
    """HTMLファイルをiframeで表示"""
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        render_html_content(html_content)
    except Exception as e:
        st.error(f"HTMLファイルの読み込みに失敗しました: {e}")


def render_html_content(html_content):
    """HTML内容をiframeで表示"""
    # HTMLをbase64エンコード
    b64_html = base64.b64encode(html_content.encode()).decode()
    
    # iframeで表示
    iframe_html = f"""
        <iframe 
            src="data:text/html;base64,{b64_html}" 
            width="100%" 
            height="600px" 
            style="border:none; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);"
        ></iframe>
    """
    st.markdown(iframe_html, unsafe_allow_html=True) 