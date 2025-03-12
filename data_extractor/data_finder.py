#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web自動解析システム - データソース検出機能
"""

import logging
import re
import json
from urllib.parse import urljoin


class DataFinder:
    """ページから主要データソースを検出するクラス"""
    
    def __init__(self, parsed_data, config):
        """
        初期化メソッド
        
        Args:
            parsed_data (list): 解析済みのページデータ
            config (dict): アプリケーション設定
        """
        self.parsed_data = parsed_data
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # データ抽出設定
        self.extraction_config = config.get('data_extraction', {})
        
        # データ抽出ルール
        self.data_patterns = self.extraction_config.get('patterns', [
            'download', 'export', 'csv', 'excel', 'pdf', 'report', 'data',
            'ダウンロード', 'エクスポート', 'レポート', 'データ'
        ])
    
    def find_data_sources(self):
        """
        全ページからデータソースを検出する
        
        Returns:
            list: 検出されたデータソースのリスト
        """
        self.logger.info("データソースの検出を開始します")
        
        data_sources = []
        
        for page in self.parsed_data:
            page_sources = self._find_in_page(page)
            data_sources.extend(page_sources)
        
        self.logger.info(f"データソース検出完了: {len(data_sources)}個のソースを発見")
        
        # 重複除去
        unique_sources = self._remove_duplicates(data_sources)
        
        return unique_sources
    
    def _find_in_page(self, page):
        """
        1ページ内のデータソースを検出する
        
        Args:
            page (dict): ページデータ
            
        Returns:
            list: 検出されたデータソースのリスト
        """
        page_sources = []
        page_url = page.get('url', '')
        elements = page.get('elements', {})
        
        # データが存在するかどうかの特徴を確認
        has_table = bool(elements.get('tables', []))
        has_data_links = False
        
        # リンクからデータソースを検出
        for link in elements.get('links', []):
            link_url = link.get('url', '')
            link_text = link.get('text', '').lower()
            link_title = link.get('title', '').lower()
            
            # ファイル拡張子をチェック
            file_extensions = ['.csv', '.xlsx', '.xls', '.pdf', '.zip', '.json', '.xml']
            is_file_link = any(link_url.endswith(ext) for ext in file_extensions)
            
            # パターンマッチングでデータリンクを検出
            is_data_link = any(pattern.lower() in link_text or pattern.lower() in link_title 
                               for pattern in self.data_patterns)
            
            if is_file_link or is_data_link:
                has_data_links = True
                
                # データソース情報を作成
                source = {
                    'type': 'link',
                    'url': link_url,
                    'text': link_text,
                    'title': link_title,
                    'page_url': page_url,
                    'file_type': self._get_file_type(link_url)
                }
                
                page_sources.append(source)
        
        # フォームからデータエクスポート機能を検出
        for form in elements.get('forms', []):
            form_action = form.get('action', '')
            form_method = form.get('method', '').upper()
            
            # フォーム内にデータエクスポート関連の要素があるか確認
            has_export_element = False
            export_field_name = None
            
            for field in form.get('fields', []):
                field_name = field.get('name', '').lower()
                field_value = field.get('value', '').lower()
                field_id = field.get('id', '').lower()
                
                # エクスポート関連のフィールドを検出
                for pattern in self.data_patterns:
                    if (pattern.lower() in field_name or 
                        pattern.lower() in field_value or 
                        pattern.lower() in field_id):
                        has_export_element = True
                        export_field_name = field_name
                        break
                
                if has_export_element:
                    break
            
            if has_export_element:
                # 絶対URLに変換
                form_url = urljoin(page_url, form_action)
                
                # データソース情報を作成
                source = {
                    'type': 'form',
                    'url': form_url,
                    'method': form_method,
                    'export_field': export_field_name,
                    'page_url': page_url
                }
                
                page_sources.append(source)
        
        # API呼び出しの検出（APIエンドポイントのURLパターン）
        api_patterns = ['/api/', '/rest/', '/data/', '/export/', '/json', '/xml']
        
        for link in elements.get('links', []):
            link_url = link.get('url', '')
            
            # APIパターンマッチング
            is_api = any(pattern in link_url for pattern in api_patterns)
            
            if is_api:
                # データソース情報を作成
                source = {
                    'type': 'api',
                    'url': link_url,
                    'page_url': page_url
                }
                
                page_sources.append(source)
        
        # テーブルからデータソースの可能性を推測
        if has_table and not has_data_links:
            # ページにテーブルはあるがデータダウンロードリンクがない場合、
            # テーブル自体をデータソースとして記録
            for i, table in enumerate(elements.get('tables', []), 1):
                headers = table.get('headers', [])
                
                # 有用なデータテーブルかどうかを判断（ヘッダーがあるなど）
                if headers and len(headers) > 1:
                    source = {
                        'type': 'table',
                        'page_url': page_url,
                        'table_index': i,
                        'headers': headers,
                        'scrape_target': True
                    }
                    
                    page_sources.append(source)
        
        return page_sources
    
    def _get_file_type(self, url):
        """
        URLからファイルタイプを判定する
        
        Args:
            url (str): 判定するURL
            
        Returns:
            str: ファイルタイプ
        """
        # 拡張子マッピング
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
    
    def _remove_duplicates(self, data_sources):
        """
        重複するデータソースを除去する
        
        Args:
            data_sources (list): データソースのリスト
            
        Returns:
            list: 重複を除去したデータソースのリスト
        """
        unique_urls = set()
        unique_sources = []
        
        for source in data_sources:
            url = source.get('url', '')
            
            # URLが既に存在しない場合のみ追加
            if url not in unique_urls:
                unique_urls.add(url)
                unique_sources.append(source)
        
        return unique_sources 