#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web自動解析システム - HTML・画像保存機能
"""

import os
import json
import logging
import shutil
from utils.helpers import get_url_hash, get_safe_filename


class PageStorage:
    """ウェブページのHTML・画像を保存するクラス"""
    
    def __init__(self, dirs):
        """
        初期化メソッド
        
        Args:
            dirs (dict): 出力ディレクトリ情報
        """
        self.html_dir = dirs['html']
        self.screenshots_dir = dirs['screenshots']
        self.base_dir = dirs['base']
        self.logger = logging.getLogger(__name__)
        
        # インデックスファイル
        self.index_file = os.path.join(self.base_dir, 'page_index.json')
        self.page_index = []
    
    def save_html(self, url, html_content):
        """
        HTMLを保存する
        
        Args:
            url (str): 対象のURL
            html_content (str): HTML内容
            
        Returns:
            str: 保存されたHTMLのパス
        """
        try:
            self.logger.info(f"HTML保存中: {url}")
            
            # ファイル名を生成
            safe_name = get_safe_filename(url)
            html_path = os.path.join(self.html_dir, safe_name)
            
            # HTMLを保存
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"HTML保存完了: {html_path}")
            
            return html_path
            
        except Exception as e:
            self.logger.error(f"HTML保存中にエラーが発生しました: {e}")
            return None
    
    def add_to_index(self, page_info):
        """
        ページ情報をインデックスに追加する
        
        Args:
            page_info (dict): ページ情報
        """
        try:
            # インデックスに追加
            self.page_index.append(page_info)
            
            # インデックスファイルを更新
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.page_index, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"インデックスを更新しました: {len(self.page_index)}ページ")
            
        except Exception as e:
            self.logger.error(f"インデックス更新中にエラーが発生しました: {e}")
    
    def create_resources_dir(self, url):
        """
        リソース用のディレクトリを作成する
        
        Args:
            url (str): 対象のURL
            
        Returns:
            str: リソースディレクトリのパス
        """
        try:
            # URLからハッシュを生成
            url_hash = get_url_hash(url)
            
            # リソースディレクトリパス
            resources_dir = os.path.join(self.html_dir, f"resources_{url_hash}")
            
            # ディレクトリが存在しない場合は作成
            os.makedirs(resources_dir, exist_ok=True)
            
            return resources_dir
            
        except Exception as e:
            self.logger.error(f"リソースディレクトリ作成中にエラーが発生しました: {e}")
            return None
    
    def save_resource(self, url, resource_url, content):
        """
        リソース（画像、CSS、JSなど）を保存する
        
        Args:
            url (str): 元のページURL
            resource_url (str): リソースのURL
            content (bytes): リソースの内容
            
        Returns:
            str: 保存されたリソースのパス
        """
        try:
            # リソースディレクトリを取得
            resources_dir = self.create_resources_dir(url)
            
            if not resources_dir:
                return None
            
            # リソースのファイル名を生成
            resource_filename = get_safe_filename(resource_url)
            resource_path = os.path.join(resources_dir, resource_filename)
            
            # リソースを保存
            with open(resource_path, 'wb') as f:
                f.write(content)
            
            self.logger.debug(f"リソースを保存しました: {resource_path}")
            
            return resource_path
            
        except Exception as e:
            self.logger.error(f"リソース保存中にエラーが発生しました: {e}")
            return None
    
    def create_static_html(self, url, html_content, resource_map=None):
        """
        静的HTMLを作成（リソースパスを相対パスに書き換え）
        
        Args:
            url (str): 対象のURL
            html_content (str): HTML内容
            resource_map (dict): リソースのマッピング情報
            
        Returns:
            str: 静的HTMLのパス
        """
        try:
            # ファイル名を生成
            url_hash = get_url_hash(url)
            static_html_filename = f"static_{url_hash}.html"
            static_html_path = os.path.join(self.html_dir, static_html_filename)
            
            # リソースマップが提供されている場合は相対パスに書き換え
            modified_html = html_content
            if resource_map:
                for original_url, local_path in resource_map.items():
                    # 絶対パスから相対パスへの変換
                    relative_path = os.path.relpath(local_path, self.html_dir)
                    # HTMLの書き換え
                    modified_html = modified_html.replace(original_url, relative_path)
            
            # 静的HTMLを保存
            with open(static_html_path, 'w', encoding='utf-8') as f:
                f.write(modified_html)
            
            self.logger.info(f"静的HTMLを保存しました: {static_html_path}")
            
            return static_html_path
            
        except Exception as e:
            self.logger.error(f"静的HTML作成中にエラーが発生しました: {e}")
            return None
    
    def copy_screenshot_to_html_dir(self, url, screenshot_path):
        """
        スクリーンショットをHTML保存ディレクトリにコピーする（相対パス参照用）
        
        Args:
            url (str): 対象のURL
            screenshot_path (str): スクリーンショットのパス
            
        Returns:
            str: コピーされたスクリーンショットのパス
        """
        try:
            if not screenshot_path or not os.path.exists(screenshot_path):
                return None
            
            # URLからハッシュを生成
            url_hash = get_url_hash(url)
            
            # リソースディレクトリを取得
            resources_dir = self.create_resources_dir(url)
            
            if not resources_dir:
                return None
            
            # スクリーンショットのファイル名を取得
            screenshot_filename = os.path.basename(screenshot_path)
            
            # コピー先のパス
            dest_path = os.path.join(resources_dir, screenshot_filename)
            
            # スクリーンショットをコピー
            shutil.copy2(screenshot_path, dest_path)
            
            self.logger.debug(f"スクリーンショットをHTMLディレクトリにコピーしました: {dest_path}")
            
            return dest_path
            
        except Exception as e:
            self.logger.error(f"スクリーンショットコピー中にエラーが発生しました: {e}")
            return None 