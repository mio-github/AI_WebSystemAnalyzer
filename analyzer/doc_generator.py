#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web自動解析システム - ドキュメント生成機能
"""

import os
import json
import logging
import time
import shutil
from datetime import datetime


class DocumentGenerator:
    """ドキュメントを生成するクラス"""
    
    def __init__(self, dirs, analysis_results):
        """
        初期化メソッド
        
        Args:
            dirs (dict): 出力ディレクトリ情報
            analysis_results (dict): LLM解析結果
        """
        self.dirs = dirs
        self.analysis_results = analysis_results
        self.logger = logging.getLogger(__name__)
        
        # 出力ディレクトリ
        self.docs_dir = dirs['docs']
        
        # ドキュメントのタイムスタンプ
        self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def generate_all(self):
        """
        全てのドキュメントを生成する
        
        Returns:
            bool: 生成成功の場合はTrue
        """
        self.logger.info("ドキュメント生成を開始します")
        
        try:
            # 出力ディレクトリの確認
            os.makedirs(self.docs_dir, exist_ok=True)
            
            # システム概要ドキュメント
            self.generate_system_overview()
            
            # 画面一覧ドキュメント
            self.generate_screen_list()
            
            # 画面仕様ドキュメント
            self.generate_screen_specs()
            
            # 画面遷移図ドキュメント
            self.generate_screen_flow()
            
            # データ構造ドキュメント
            self.generate_data_structure()
            
            # インデックスページ
            self.generate_index_page()
            
            # スクリーンショットギャラリー
            self.generate_screenshot_gallery()
            
            self.logger.info("すべてのドキュメントが生成されました")
            return True
            
        except Exception as e:
            self.logger.error(f"ドキュメント生成中にエラーが発生しました: {e}")
            return False
    
    def generate_system_overview(self):
        """システム概要ドキュメントを生成する"""
        self.logger.info("システム概要ドキュメントを生成中...")
        
        try:
            # システム概要情報
            overview = self.analysis_results.get('system_overview', {})
            if not overview:
                self.logger.warning("システム概要情報がありません")
                return
            
            content = overview.get('content', '')
            
            # 出力ファイルパス
            output_file = os.path.join(self.docs_dir, 'system_overview.md')
            
            # ヘッダー情報の追加
            header = f"""# システム概要

> 生成日時: {self.timestamp}

"""
            
            # ドキュメント保存
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(header + content)
                
            self.logger.info(f"システム概要ドキュメントを保存しました: {output_file}")
            
        except Exception as e:
            self.logger.error(f"システム概要ドキュメント生成中にエラーが発生しました: {e}")
    
    def generate_screen_list(self):
        """画面一覧ドキュメントを生成する"""
        self.logger.info("画面一覧ドキュメントを生成中...")
        
        try:
            # 画面仕様情報
            screen_specs = self.analysis_results.get('screen_specs', [])
            if not screen_specs:
                self.logger.warning("画面仕様情報がありません")
                return
            
            # 出力ファイルパス
            output_file = os.path.join(self.docs_dir, 'screen_list.md')
            
            # ヘッダー情報
            header = f"""# 画面一覧

> 生成日時: {self.timestamp}

本ドキュメントは、システム内の全画面の概要と一覧を提供します。

## 画面分類

画面は以下のタイプに分類されています：

"""
            
            # 画面タイプの集計
            page_types = {}
            for spec in screen_specs:
                page_type = spec.get('type', 'unknown')
                if page_type in page_types:
                    page_types[page_type] += 1
                else:
                    page_types[page_type] = 1
            
            # 画面タイプの一覧を追加
            types_content = ""
            for page_type, count in page_types.items():
                types_content += f"- **{page_type}**: {count}画面\n"
            
            # 画面一覧テーブル
            table_header = """
## 画面一覧

| No. | 画面名 | タイプ | 画面ID | 備考 |
|-----|--------|--------|--------|------|
"""
            
            table_rows = ""
            for i, spec in enumerate(screen_specs, 1):
                title = spec.get('title', '')
                page_type = spec.get('type', 'unknown')
                url = spec.get('url', '')
                
                # 画面IDの生成（URLの最後の部分）
                screen_id = url.split('/')[-1]
                if not screen_id:
                    screen_id = 'home'
                
                # ファイル名を作成（詳細へのリンク用）
                safe_filename = url.replace(':', '_').replace('/', '_').replace('?', '_')
                if len(safe_filename) > 50:
                    safe_filename = safe_filename[:50]
                
                table_rows += f"| {i} | [{title}](screen_spec_{safe_filename}.md) | {page_type} | {screen_id} | |\n"
            
            # ドキュメント保存
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(header + types_content + table_header + table_rows)
                
            self.logger.info(f"画面一覧ドキュメントを保存しました: {output_file}")
            
        except Exception as e:
            self.logger.error(f"画面一覧ドキュメント生成中にエラーが発生しました: {e}")
    
    def generate_screen_specs(self):
        """画面仕様ドキュメントを生成する"""
        self.logger.info("画面仕様ドキュメントを生成中...")
        
        try:
            # 画面仕様情報
            screen_specs = self.analysis_results.get('screen_specs', [])
            if not screen_specs:
                self.logger.warning("画面仕様情報がありません")
                return
            
            # 各画面の仕様ドキュメントを生成
            for i, spec in enumerate(screen_specs, 1):
                title = spec.get('title', '')
                page_type = spec.get('type', 'unknown')
                url = spec.get('url', '')
                content = spec.get('content', '')
                
                # ファイル名を作成
                safe_filename = url.replace(':', '_').replace('/', '_').replace('?', '_')
                if len(safe_filename) > 50:
                    safe_filename = safe_filename[:50]
                
                output_file = os.path.join(self.docs_dir, f'screen_spec_{safe_filename}.md')
                
                # ヘッダー情報
                header = f"""# 画面仕様: {title}

> 生成日時: {self.timestamp}

- **画面ID**: {i}
- **画面タイプ**: {page_type}
- **URL**: {url}

"""
                
                # スクリーンショットがあれば参照を追加
                screenshots_dir = self.dirs.get('screenshots', '')
                if screenshots_dir:
                    screenshot_files = [f for f in os.listdir(screenshots_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
                    for screenshot in screenshot_files:
                        if safe_filename in screenshot or url.split('/')[-1] in screenshot:
                            screenshot_path = os.path.join('../screenshots', screenshot)
                            header += f"""
## スクリーンショット

![{title}]({screenshot_path})

"""
                            break
                
                # ドキュメント保存
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(header + content)
                
            self.logger.info(f"画面仕様ドキュメントを生成しました: {len(screen_specs)}ファイル")
            
        except Exception as e:
            self.logger.error(f"画面仕様ドキュメント生成中にエラーが発生しました: {e}")
    
    def generate_screen_flow(self):
        """画面遷移図ドキュメントを生成する"""
        self.logger.info("画面遷移図ドキュメントを生成中...")
        
        try:
            # 画面遷移情報
            screen_flow = self.analysis_results.get('screen_flow', {})
            if not screen_flow:
                self.logger.warning("画面遷移情報がありません")
                return
            
            content = screen_flow.get('content', '')
            
            # 出力ファイルパス
            output_file = os.path.join(self.docs_dir, 'screen_flow.md')
            
            # ヘッダー情報
            header = f"""# 画面遷移図

> 生成日時: {self.timestamp}

本ドキュメントは、システム内の画面遷移を図示したものです。

"""
            
            # ドキュメント保存
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(header + content)
                
            self.logger.info(f"画面遷移図ドキュメントを保存しました: {output_file}")
            
        except Exception as e:
            self.logger.error(f"画面遷移図ドキュメント生成中にエラーが発生しました: {e}")
    
    def generate_data_structure(self):
        """データ構造ドキュメントを生成する"""
        self.logger.info("データ構造ドキュメントを生成中...")
        
        try:
            # データ構造情報
            data_structure = self.analysis_results.get('data_structure', {})
            if not data_structure:
                self.logger.warning("データ構造情報がありません")
                return
            
            content = data_structure.get('content', '')
            
            # 出力ファイルパス
            output_file = os.path.join(self.docs_dir, 'data_structure.md')
            
            # ヘッダー情報
            header = f"""# データ構造

> 生成日時: {self.timestamp}

本ドキュメントは、システム内のデータ構造を分析したものです。

"""
            
            # ドキュメント保存
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(header + content)
                
            self.logger.info(f"データ構造ドキュメントを保存しました: {output_file}")
            
        except Exception as e:
            self.logger.error(f"データ構造ドキュメント生成中にエラーが発生しました: {e}")
    
    def generate_index_page(self):
        """インデックスページを生成する"""
        self.logger.info("インデックスページを生成中...")
        
        try:
            # 出力ファイルパス
            output_file = os.path.join(self.docs_dir, 'index.md')
            
            # ヘッダー情報
            content = f"""# システム解析ドキュメント

> 生成日時: {self.timestamp}

本ドキュメントは、Webシステムを自動解析して生成されたものです。

## 目次

1. [システム概要](system_overview.md)
2. [画面一覧](screen_list.md)
3. [画面遷移図](screen_flow.md)
4. [データ構造](data_structure.md)
5. [スクリーンショットギャラリー](screenshot_gallery.md)

## 画面仕様書

"""
            
            # 画面仕様へのリンク
            screen_specs = self.analysis_results.get('screen_specs', [])
            for spec in screen_specs:
                title = spec.get('title', '')
                url = spec.get('url', '')
                
                # ファイル名を作成
                safe_filename = url.replace(':', '_').replace('/', '_').replace('?', '_')
                if len(safe_filename) > 50:
                    safe_filename = safe_filename[:50]
                
                content += f"- [{title}](screen_spec_{safe_filename}.md)\n"
            
            # ドキュメント保存
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
            self.logger.info(f"インデックスページを保存しました: {output_file}")
            
            # HTMLインデックスも生成（オプション）
            self._generate_html_index()
            
        except Exception as e:
            self.logger.error(f"インデックスページ生成中にエラーが発生しました: {e}")
    
    def generate_screenshot_gallery(self):
        """スクリーンショットギャラリーを生成する"""
        self.logger.info("スクリーンショットギャラリーを生成中...")
        
        try:
            # スクリーンショットディレクトリ
            screenshots_dir = self.dirs.get('screenshots', '')
            if not screenshots_dir or not os.path.exists(screenshots_dir):
                self.logger.warning("スクリーンショットディレクトリが存在しません")
                return
            
            # スクリーンショットファイル一覧
            screenshot_files = [f for f in os.listdir(screenshots_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
            if not screenshot_files:
                self.logger.warning("スクリーンショットファイルが存在しません")
                return
            
            # 出力ファイルパス
            output_file = os.path.join(self.docs_dir, 'screenshot_gallery.md')
            
            # ヘッダー情報
            content = f"""# スクリーンショットギャラリー

> 生成日時: {self.timestamp}

本ドキュメントは、システム内の全画面のスクリーンショットを一覧表示しています。

"""
            
            # 画面仕様情報
            screen_specs = self.analysis_results.get('screen_specs', [])
            spec_map = {}
            for spec in screen_specs:
                url = spec.get('url', '')
                title = spec.get('title', '')
                spec_map[url] = title
            
            # スクリーンショットごとにセクションを作成
            for i, screenshot in enumerate(screenshot_files, 1):
                screenshot_path = os.path.join('../screenshots', screenshot)
                
                # タイトルの特定
                title = f"画面 {i}"
                for url, page_title in spec_map.items():
                    if url.split('/')[-1] in screenshot:
                        title = page_title
                        break
                
                content += f"""
## {title}

![{title}]({screenshot_path})

"""
            
            # ドキュメント保存
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
            self.logger.info(f"スクリーンショットギャラリーを保存しました: {output_file}")
            
        except Exception as e:
            self.logger.error(f"スクリーンショットギャラリー生成中にエラーが発生しました: {e}")
    
    def _generate_html_index(self):
        """HTMLインデックスを生成する"""
        try:
            # 出力ファイルパス
            output_file = os.path.join(self.docs_dir, 'index.html')
            
            # HTMLコンテンツ
            html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>システム解析ドキュメント</title>
    <style>
        body {{
            font-family: 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3 {{
            color: #2c3e50;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .timestamp {{
            color: #7f8c8d;
            font-style: italic;
            margin-bottom: 20px;
        }}
        .container {{
            display: grid;
            grid-template-columns: 250px 1fr;
            gap: 20px;
        }}
        .sidebar {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
        }}
        .content {{
            padding: 20px;
        }}
        .menu {{
            list-style: none;
            padding: 0;
        }}
        .menu li {{
            margin-bottom: 10px;
        }}
        .menu li.section-title {{
            font-weight: bold;
            margin-top: 15px;
            border-bottom: 1px solid #ddd;
            padding-bottom: 5px;
        }}
    </style>
</head>
<body>
    <h1>システム解析ドキュメント</h1>
    <div class="timestamp">生成日時: {self.timestamp}</div>
    
    <div class="container">
        <div class="sidebar">
            <ul class="menu">
                <li><a href="index.html">ホーム</a></li>
                <li class="section-title">基本ドキュメント</li>
                <li><a href="system_overview.html">システム概要</a></li>
                <li><a href="screen_list.html">画面一覧</a></li>
                <li><a href="screen_flow.html">画面遷移図</a></li>
                <li><a href="data_structure.html">データ構造</a></li>
                <li><a href="screenshot_gallery.html">スクリーンショットギャラリー</a></li>
                
                <li class="section-title">画面仕様書</li>
"""
            
            # 画面仕様へのリンク
            screen_specs = self.analysis_results.get('screen_specs', [])
            for spec in screen_specs:
                title = spec.get('title', '')
                url = spec.get('url', '')
                
                # ファイル名を作成
                safe_filename = url.replace(':', '_').replace('/', '_').replace('?', '_')
                if len(safe_filename) > 50:
                    safe_filename = safe_filename[:50]
                
                html_content += f'                <li><a href="screen_spec_{safe_filename}.html">{title}</a></li>\n'
            
            html_content += """            </ul>
        </div>
        
        <div class="content">
            <h2>ドキュメント概要</h2>
            <p>
                本ドキュメントは、Webシステムを自動解析して生成されたものです。
                システムの概要、画面仕様、画面遷移、データ構造などの情報を提供します。
            </p>
            
            <h3>ドキュメント構成</h3>
            <ul>
                <li><strong>システム概要</strong>: システム全体の目的と機能の概要</li>
                <li><strong>画面一覧</strong>: システム内の全画面のリスト</li>
                <li><strong>画面仕様書</strong>: 各画面の詳細な仕様</li>
                <li><strong>画面遷移図</strong>: 画面間の遷移関係</li>
                <li><strong>データ構造</strong>: システム内のデータ構造の分析</li>
                <li><strong>スクリーンショットギャラリー</strong>: 全画面のスクリーンショット</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""
            
            # HTMLファイル保存
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            self.logger.info(f"HTMLインデックスを保存しました: {output_file}")
            
            # マークダウンからHTMLへの変換
            self._convert_md_to_html()
            
        except Exception as e:
            self.logger.error(f"HTMLインデックス生成中にエラーが発生しました: {e}")
    
    def _convert_md_to_html(self):
        """
        マークダウンファイルをHTMLに変換する
        注意: この機能はPythonの外部ツール（例: pandocなど）に依存する場合があります
        """
        try:
            # マークダウンファイル一覧
            md_files = [f for f in os.listdir(self.docs_dir) if f.endswith('.md')]
            
            for md_file in md_files:
                md_path = os.path.join(self.docs_dir, md_file)
                html_file = md_file.replace('.md', '.html')
                html_path = os.path.join(self.docs_dir, html_file)
                
                # マークダウンの内容を読み込む
                with open(md_path, 'r', encoding='utf-8') as f:
                    md_content = f.read()
                
                # 簡易的なHTML変換（正確な変換にはpandocなどの外部ツールが望ましい）
                html_content = self._simple_md_to_html(md_content, html_file)
                
                # HTMLファイル保存
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
            
            self.logger.info(f"マークダウンファイルをHTMLに変換しました: {len(md_files)}ファイル")
            
        except Exception as e:
            self.logger.error(f"マークダウン変換中にエラーが発生しました: {e}")
    
    def _simple_md_to_html(self, md_content, html_filename):
        """
        非常に簡易的なマークダウンからHTMLへの変換
        注意: これは完全な変換ではなく、基本的な要素のみを変換します
        """
        # ベースHTMLテンプレート
        html_template = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>システム解析ドキュメント</title>
    <style>
        body {{
            font-family: 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #2c3e50;
            margin-top: 1.5em;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        pre, code {{
            background-color: #f8f9fa;
            border-radius: 3px;
            padding: 2px 5px;
            font-family: monospace;
        }}
        pre {{
            padding: 15px;
            overflow-x: auto;
        }}
        blockquote {{
            border-left: 4px solid #ddd;
            padding-left: 15px;
            color: #666;
            margin-left: 0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        img {{
            max-width: 100%;
            height: auto;
        }}
        .container {{
            display: grid;
            grid-template-columns: 250px 1fr;
            gap: 20px;
        }}
        .sidebar {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
        }}
        .content {{
            padding: 20px;
        }}
        .menu {{
            list-style: none;
            padding: 0;
        }}
        .menu li {{
            margin-bottom: 10px;
        }}
        .menu li.section-title {{
            font-weight: bold;
            margin-top: 15px;
            border-bottom: 1px solid #ddd;
            padding-bottom: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <ul class="menu">
                <li><a href="index.html">ホーム</a></li>
                <li class="section-title">基本ドキュメント</li>
                <li><a href="system_overview.html">システム概要</a></li>
                <li><a href="screen_list.html">画面一覧</a></li>
                <li><a href="screen_flow.html">画面遷移図</a></li>
                <li><a href="data_structure.html">データ構造</a></li>
                <li><a href="screenshot_gallery.html">スクリーンショットギャラリー</a></li>
            </ul>
        </div>
        
        <div class="content">
            <!-- コンテンツ -->
            {self._convert_md_content(md_content)}
        </div>
    </div>
</body>
</html>
"""
        
        return html_template
    
    def _convert_md_content(self, md_content):
        """
        マークダウンコンテンツをHTMLに変換する
        注意: これは非常に簡易的な変換です
        """
        import re
        
        # 見出しの変換
        content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', md_content, flags=re.MULTILINE)
        content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)
        content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
        content = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', content, flags=re.MULTILINE)
        
        # 引用の変換
        content = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', content, flags=re.MULTILINE)
        
        # 箇条書きの変換
        content = re.sub(r'^- (.+)$', r'<li>\1</li>', content, flags=re.MULTILINE)
        content = re.sub(r'(<li>.+</li>\n)+', r'<ul>\g<0></ul>', content, flags=re.MULTILINE)
        
        # リンクの変換
        content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', content)
        
        # 画像の変換
        content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1">', content)
        
        # コードブロックの変換
        content = re.sub(r'```(.+?)```', r'<pre><code>\1</code></pre>', content, flags=re.DOTALL)
        
        # 強調の変換
        content = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', content)
        content = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', content)
        
        # 段落の変換
        content = re.sub(r'(?<!\n)\n(?!\n)(.+?)(?=\n\n|\n<|\n$)', r'<p>\1</p>', content, flags=re.DOTALL)
        
        # テーブルの変換（非常に簡易的）
        table_pattern = r'\|(.+?)\|\n\|[-|]+\|\n((?:\|.+?\|\n)+)'
        
        def table_replace(match):
            header = match.group(1)
            rows = match.group(2).strip().split('\n')
            
            header_cells = [cell.strip() for cell in header.split('|') if cell.strip()]
            header_html = '<tr>' + ''.join([f'<th>{cell}</th>' for cell in header_cells]) + '</tr>'
            
            rows_html = ''
            for row in rows:
                cells = [cell.strip() for cell in row.split('|') if cell.strip()]
                rows_html += '<tr>' + ''.join([f'<td>{cell}</td>' for cell in cells]) + '</tr>'
            
            return f'<table>{header_html}{rows_html}</table>'
        
        content = re.sub(table_pattern, table_replace, content, flags=re.DOTALL)
        
        return content 