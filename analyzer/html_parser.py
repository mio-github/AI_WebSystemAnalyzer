#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web自動解析システム - HTML解析機能
"""

import os
import json
import logging
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin


class HTMLParser:
    """HTMLファイルを解析するクラス"""
    
    def __init__(self, dirs):
        """
        初期化メソッド
        
        Args:
            dirs (dict): 出力ディレクトリ情報
        """
        self.html_dir = dirs['html']
        self.base_dir = dirs['base']
        self.logger = logging.getLogger(__name__)
        
        # 解析結果
        self.parsed_data = []
        
        # インデックスファイル
        self.index_file = os.path.join(self.base_dir, 'page_index.json')
        
        # 構造データ出力ファイル
        self.structure_file = os.path.join(self.base_dir, 'structure_data.json')
    
    def load_index(self):
        """
        ページインデックスを読み込む
        
        Returns:
            list: ページ情報のリスト
        """
        try:
            if os.path.exists(self.index_file):
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            self.logger.error(f"インデックス読み込み中にエラーが発生しました: {e}")
            return []
    
    def extract_elements(self, soup, page_url):
        """
        重要な要素を抽出する
        
        Args:
            soup (BeautifulSoup): パース済みのHTMLオブジェクト
            page_url (str): ページURL
            
        Returns:
            dict: 抽出された要素データ
        """
        elements = {}
        
        # タイトル抽出
        try:
            elements['title'] = soup.title.string.strip() if soup.title else ""
        except:
            elements['title'] = ""
        
        # ヘッダー抽出
        elements['headers'] = []
        for i in range(1, 7):
            for header in soup.find_all(f'h{i}'):
                elements['headers'].append({
                    'level': i,
                    'text': header.get_text().strip()
                })
        
        # メタデータ抽出
        elements['meta'] = {}
        for meta in soup.find_all('meta'):
            name = meta.get('name', meta.get('property', ''))
            content = meta.get('content', '')
            if name and content:
                elements['meta'][name] = content
        
        # リンク抽出
        elements['links'] = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href.startswith('javascript:') or href == '#':
                continue
                
            text = link.get_text().strip()
            title = link.get('title', '')
            
            # 相対URLを絶対URLに変換
            absolute_url = urljoin(page_url, href)
            
            elements['links'].append({
                'url': absolute_url,
                'text': text,
                'title': title
            })
        
        # フォーム抽出
        elements['forms'] = []
        for form in soup.find_all('form'):
            action = form.get('action', '')
            method = form.get('method', 'get').upper()
            
            # 相対URLを絶対URLに変換
            action_url = urljoin(page_url, action) if action else page_url
            
            form_fields = []
            for input_tag in form.find_all(['input', 'select', 'textarea']):
                field_type = input_tag.get('type', input_tag.name)
                field_name = input_tag.get('name', '')
                field_id = input_tag.get('id', '')
                field_value = input_tag.get('value', '')
                
                form_fields.append({
                    'type': field_type,
                    'name': field_name,
                    'id': field_id,
                    'value': field_value
                })
            
            elements['forms'].append({
                'action': action_url,
                'method': method,
                'fields': form_fields
            })
        
        # テーブル抽出
        elements['tables'] = []
        for table in soup.find_all('table'):
            rows = []
            
            # ヘッダー行の処理
            headers = []
            for th in table.find_all('th'):
                headers.append(th.get_text().strip())
            
            # データ行の処理
            for tr in table.find_all('tr'):
                cells = []
                for td in tr.find_all(['td', 'th']):
                    cells.append(td.get_text().strip())
                
                if cells:
                    rows.append(cells)
            
            elements['tables'].append({
                'headers': headers,
                'rows': rows
            })
        
        # 重要な<div>や<section>のテキスト（コンテンツブロック）
        elements['content_blocks'] = []
        important_tags = soup.find_all(['div', 'section', 'article', 'main'])
        for tag in important_tags:
            # IDやクラスを持つブロックのみを対象にする
            if tag.get('id') or tag.get('class'):
                block_id = tag.get('id', '')
                block_class = ' '.join(tag.get('class', []))
                
                # 100文字以上のテキストブロックのみを抽出
                text = tag.get_text().strip()
                if len(text) > 100:
                    elements['content_blocks'].append({
                        'id': block_id,
                        'class': block_class,
                        'text': text[:500] + ('...' if len(text) > 500 else '')  # 長すぎるテキストは省略
                    })
        
        return elements
    
    def analyze_page_structure(self, soup):
        """
        ページの構造を分析する
        
        Args:
            soup (BeautifulSoup): パース済みのHTMLオブジェクト
            
        Returns:
            dict: ページ構造情報
        """
        structure = {}
        
        # ページの基本構造を検出
        structure['has_header'] = bool(soup.find(['header', 'div.header', '#header']))
        structure['has_footer'] = bool(soup.find(['footer', 'div.footer', '#footer']))
        structure['has_sidebar'] = bool(soup.find(['aside', 'div.sidebar', '#sidebar']))
        structure['has_navigation'] = bool(soup.find(['nav', 'div.nav', '#nav']))
        structure['has_main_content'] = bool(soup.find(['main', 'div.content', '#content']))
        
        # ページタイプの推測
        structure['page_type'] = self._guess_page_type(soup)
        
        # フォームの有無をチェック
        structure['has_login_form'] = self._has_login_form(soup)
        structure['has_search_form'] = self._has_search_form(soup)
        structure['has_registration_form'] = self._has_registration_form(soup)
        
        # データ表示の種類をチェック
        structure['has_table'] = bool(soup.find('table'))
        structure['has_list'] = bool(soup.find(['ul', 'ol']))
        structure['has_pagination'] = self._has_pagination(soup)
        
        return structure
    
    def _guess_page_type(self, soup):
        """
        ページタイプを推測する
        
        Args:
            soup (BeautifulSoup): パース済みのHTMLオブジェクト
            
        Returns:
            str: 推測されたページタイプ
        """
        # タイトルやURLからページタイプを推測
        title_text = soup.title.string.lower() if soup.title else ""
        
        # ログイン・認証ページ
        if any(keyword in title_text for keyword in ['login', 'sign in', 'ログイン', '認証']):
            return 'login'
        
        # ホームページ
        if any(keyword in title_text for keyword in ['home', 'top', 'ホーム', 'トップ']):
            return 'home'
        
        # 検索結果ページ
        if any(keyword in title_text for keyword in ['search', 'result', '検索', '結果']):
            return 'search'
        
        # プロフィールページ
        if any(keyword in title_text for keyword in ['profile', 'account', 'user', 'プロフィール', 'アカウント']):
            return 'profile'
        
        # 詳細ページ
        if any(keyword in title_text for keyword in ['detail', 'view', '詳細', '表示']):
            return 'detail'
        
        # リスト/一覧ページ
        if any(keyword in title_text for keyword in ['list', 'index', '一覧', 'リスト']):
            return 'list'
        
        # フォームページ
        if soup.find('form') and (any(keyword in title_text for keyword in ['form', 'edit', 'create', 'フォーム', '編集', '作成'])):
            return 'form'
        
        # エラーページ
        if any(keyword in title_text for keyword in ['error', '404', 'not found', 'エラー']):
            return 'error'
        
        # 構造的特徴からの推測
        if self._has_login_form(soup):
            return 'login'
        
        if soup.find('table') and len(soup.find_all('tr')) > 5:
            return 'list'
        
        if len(soup.find_all(['h1', 'h2', 'h3'])) >= 5:
            return 'article'
        
        # 判別できない場合
        return 'unknown'
    
    def _has_login_form(self, soup):
        """ログインフォームの有無を判定"""
        # ユーザー名/Eメールとパスワードの入力フィールドがあるフォームを探す
        for form in soup.find_all('form'):
            password_input = form.find('input', {'type': 'password'})
            if not password_input:
                continue
                
            # ユーザー名/Eメール入力があるか確認
            username_input = form.find('input', {'type': ['text', 'email']})
            
            if username_input:
                return True
        
        return False
    
    def _has_search_form(self, soup):
        """検索フォームの有無を判定"""
        # type="search"の入力か、name/id/placeholder属性に"search"を含む入力を探す
        search_inputs = soup.find_all('input', {'type': 'search'})
        if search_inputs:
            return True
            
        for input_tag in soup.find_all('input'):
            attrs = ['name', 'id', 'placeholder']
            values = [input_tag.get(attr, '').lower() for attr in attrs]
            
            if any('search' in value or '検索' in value for value in values):
                return True
        
        return False
    
    def _has_registration_form(self, soup):
        """登録フォームの有無を判定"""
        # 登録フォームの特徴を探す
        for form in soup.find_all('form'):
            # パスワード入力が2つある場合は登録フォームの可能性が高い
            password_inputs = form.find_all('input', {'type': 'password'})
            if len(password_inputs) >= 2:
                return True
                
            # Eメール入力とパスワード入力がある場合も登録フォームの可能性
            email_input = form.find('input', {'type': 'email'})
            password_input = form.find('input', {'type': 'password'})
            
            if email_input and password_input:
                # フォームのテキストに登録/サインアップの単語があるか確認
                form_text = form.get_text().lower()
                if any(word in form_text for word in ['register', 'sign up', 'create account', '登録', 'アカウント作成']):
                    return True
        
        return False
    
    def _has_pagination(self, soup):
        """ページネーションの有無を判定"""
        # ページネーション要素を探す
        pagination_candidates = [
            'ul.pagination', 'div.pagination', '.pager', 'nav.pagination',
            '.pagenavi', '.wp-pagenavi', '.page-numbers'
        ]
        
        for selector in pagination_candidates:
            if soup.select(selector):
                return True
        
        # 数字の連続したリンクがあればページネーションと判断
        links = soup.find_all('a')
        page_number_links = []
        
        for link in links:
            text = link.get_text().strip()
            if text.isdigit():
                page_number_links.append(int(text))
        
        # 連続した数字のリンクが3つ以上あればページネーションと判断
        page_number_links.sort()
        if len(page_number_links) >= 3:
            for i in range(len(page_number_links) - 2):
                if page_number_links[i] + 1 == page_number_links[i+1] and page_number_links[i+1] + 1 == page_number_links[i+2]:
                    return True
        
        return False
    
    def parse_html_file(self, html_path, page_url):
        """
        HTMLファイルを解析する
        
        Args:
            html_path (str): HTMLファイルのパス
            page_url (str): ページのURL
            
        Returns:
            dict: 解析結果
        """
        try:
            self.logger.info(f"HTML解析中: {html_path}")
            
            # HTMLファイルを読み込む
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # BeautifulSoupでパース
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 要素抽出
            elements = self.extract_elements(soup, page_url)
            
            # 構造分析
            structure = self.analyze_page_structure(soup)
            
            # 解析結果
            result = {
                'url': page_url,
                'file_path': html_path,
                'elements': elements,
                'structure': structure
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"HTML解析中にエラーが発生しました: {html_path}, エラー: {e}")
            return None
    
    def parse_all(self):
        """
        全てのHTMLファイルを解析する
        
        Returns:
            list: 全ページの解析結果
        """
        # インデックスを読み込む
        page_index = self.load_index()
        
        if not page_index:
            # インデックスが無い場合はHTMLディレクトリから直接ファイルを探す
            html_files = [f for f in os.listdir(self.html_dir) 
                         if f.endswith('.html') and os.path.isfile(os.path.join(self.html_dir, f))]
            
            for html_file in html_files:
                html_path = os.path.join(self.html_dir, html_file)
                # URLが不明なのでファイル名をURLとして扱う
                page_url = html_file
                
                result = self.parse_html_file(html_path, page_url)
                if result:
                    self.parsed_data.append(result)
        else:
            # インデックスから解析
            for page_info in page_index:
                html_path = page_info.get('html_path')
                page_url = page_info.get('url')
                
                if html_path and page_url and os.path.exists(html_path):
                    result = self.parse_html_file(html_path, page_url)
                    if result:
                        # スクリーンショットパスを追加
                        result['screenshot_path'] = page_info.get('screenshot_path')
                        self.parsed_data.append(result)
        
        # 構造データを保存
        self._save_structure_data()
        
        return self.parsed_data
    
    def _save_structure_data(self):
        """解析した構造データをJSONファイルに保存する"""
        try:
            with open(self.structure_file, 'w', encoding='utf-8') as f:
                json.dump(self.parsed_data, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"構造データを保存しました: {self.structure_file}")
        except Exception as e:
            self.logger.error(f"構造データ保存中にエラーが発生しました: {e}") 