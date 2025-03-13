#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web自動解析システム - Webクローリング機能
"""

import os
import re
import time
import logging
import urllib.parse
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.helpers import normalize_url, get_url_hash, get_safe_filename
from crawler.screenshot import ScreenshotTaker
from crawler.storage import PageStorage
from datetime import datetime


class WebCrawler:
    """
    Webクローラークラス
    指定されたURLからリンクをたどり、HTMLとスクリーンショットを保存する
    """
    
    def __init__(self, browser, config, dirs):
        """
        初期化

        Args:
            browser: Seleniumのブラウザインスタンス
            config: 設定情報
            dirs: 出力ディレクトリ情報
        """
        self.browser = browser
        self.config = config
        self.dirs = dirs
        self.visited_urls = set()
        self.pages = []
        
        # ロガー設定
        self.logger = setup_logger('crawler')
        
        # クローリング設定
        crawler_config = config.get('crawler', {})
        self.max_depth = crawler_config.get('max_depth', 3)
        self.include_patterns = crawler_config.get('include_patterns', ['.*'])
        self.exclude_patterns = crawler_config.get('exclude_patterns', [])
        
        # 状態管理
        self.running = True
        
        # コールバック関数（通知用）
        self.callback = None
        
        # 訪問済みURLの追跡
        self.to_visit_urls = []
        
        # ベースURL設定
        self.base_url = config['target']['base_url']
        
        # ページ読み込み待機時間
        self.delay = config['crawler'].get('delay', 1.5)
        
        # スクリーンショット設定
        self.take_screenshots = config['crawler'].get('screenshot', True)
        
        # ヘルパークラス
        self.screenshot_taker = ScreenshotTaker(browser, dirs)
        self.page_storage = PageStorage(dirs)
    
    def set_callback(self, callback_function):
        """
        コールバック関数を設定
        
        Args:
            callback_function: イベントとデータを受け取るコールバック関数
        """
        self.callback = callback_function
    
    def notify(self, event, data):
        """
        イベント通知
        
        Args:
            event: イベント名
            data: イベントデータ
        """
        if self.callback:
            self.callback(event, data)
    
    def should_visit(self, url):
        """
        URLを訪問すべきか判断する
        
        Args:
            url (str): 訪問候補のURL
            
        Returns:
            bool: 訪問すべきかどうか
        """
        # 正規化
        normalized_url = normalize_url(url)
        
        # 訪問済みチェック
        if normalized_url in self.visited_urls:
            return False
        
        # ドメインチェック（同一ドメインのみクロール）
        parsed_url = urllib.parse.urlparse(normalized_url)
        parsed_base = urllib.parse.urlparse(self.base_url)
        
        if parsed_url.netloc != parsed_base.netloc:
            return False
        
        # 除外パターンチェック
        for pattern in self.exclude_patterns:
            if re.search(pattern, normalized_url):
                return False
        
        return True
    
    def extract_links(self):
        """
        現在のページから全てのリンクを抽出する
        
        Returns:
            list: 抽出されたリンクのリスト
        """
        links = []
        
        try:
            # ページ内の全リンクを取得
            elements = self.browser.find_elements(By.TAG_NAME, "a")
            
            # href属性を取得
            for element in elements:
                href = element.get_attribute("href")
                if href and href.startswith("http"):
                    links.append(href)
        
        except Exception as e:
            self.logger.error(f"リンク抽出中にエラーが発生しました: {e}")
        
        return links
    
    def process_page(self, url, depth=0):
        """
        指定されたURLのページを処理する
        
        Args:
            url (str): 処理するURL
            depth (int): 現在のクロール深度
            
        Returns:
            dict: 処理したページの情報
        """
        normalized_url = normalize_url(url)
        self.visited_urls.add(normalized_url)
        
        self.logger.info(f"ページ処理中: {url} (深度: {depth})")
        
        # ページ読み込み
        try:
            self.browser.get(url)
            
            # ページが読み込まれるのを待機
            WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 追加の待機時間（JavaScript実行など）
            time.sleep(self.delay)
            
            # 現在のURL（リダイレクト後の可能性あり）
            current_url = self.browser.current_url
            normalized_url = normalize_url(current_url)
            
            # ページタイトル取得
            title = self.browser.title
            
            # HTML取得
            html_content = self.browser.page_source
            
            # スクリーンショット取得
            screenshot_path = None
            if self.take_screenshots:
                screenshot_path = self.screenshot_taker.take_screenshot(normalized_url)
            
            # HTML保存
            html_path = self.page_storage.save_html(normalized_url, html_content)
            
            # ページ情報を作成
            page_info = {
                'url': normalized_url,
                'title': title,
                'html_path': html_path,
                'screenshot_path': screenshot_path,
                'depth': depth
            }
            
            # 結果に追加
            self.pages.append(page_info)
            
            # リンク抽出（次の深度用）
            if depth < self.max_depth:
                links = self.extract_links()
                
                for link in links:
                    if self.should_visit(link):
                        self.to_visit_urls.append((link, depth + 1))
            
            return page_info
            
        except TimeoutException:
            self.logger.warning(f"ページのロードがタイムアウトしました: {url}")
        except Exception as e:
            self.logger.error(f"ページ処理中にエラーが発生しました: {url}, エラー: {e}")
        
        return None
    
    def crawl(self):
        """
        クローリングを実行
        
        Returns:
            list: 訪問したページ情報のリスト
        """
        start_url = self.config.get('target', {}).get('url', '')
        if not start_url:
            self.logger.error("開始URLが設定されていません")
            return []
        
        self.logger.info(f"クローリングを開始します: {start_url}")
        self.notify('start_crawl', {'url': start_url})
        
        # 初期ページを処理
        try:
            self._process_page(start_url, 1)
        except Exception as e:
            self.logger.error(f"クローリング中にエラーが発生しました: {str(e)}")
            self.notify('error', {'message': str(e)})
        
        self.logger.info(f"クローリングが完了しました: {len(self.pages)}ページを処理しました")
        self.notify('finish_crawl', {'page_count': len(self.pages)})
        
        # 結果をJSONファイルに保存
        self._save_results()
        
        return self.pages
    
    def _process_page(self, url, depth=0):
        """
        ページを処理する
        
        Args:
            url (str): 処理するURL
            depth (int): 現在のクロール深度
        """
        try:
            # URLの正規化
            url = self._normalize_url(url)
            
            # すでに訪問済みの場合はスキップ
            if url in self.visited_urls:
                return
            
            # 訪問済みに追加
            self.visited_urls.add(url)
            
            # ページ訪問を通知
            self.notify('page_visit', {'url': url, 'depth': depth})
            
            # ページを開く
            self.browser.get(url)
            
            # ページ読み込み待機
            WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # ページタイトルを取得
            title = self.browser.title
            
            # ページIDを生成
            page_id = get_url_hash(url)
            
            # スクリーンショットを保存
            screenshot_path = None
            try:
                screenshot_file = f"{page_id}.png"
                screenshot_path = os.path.join(self.dirs['screenshots'], screenshot_file)
                self.browser.save_screenshot(screenshot_path)
                self.logger.debug(f"スクリーンショット保存: {screenshot_path}")
                
                # スクリーンショットのファイルサイズを確認して通知
                if os.path.exists(screenshot_path):
                    file_size = os.path.getsize(screenshot_path) / 1024  # KB単位
                    self.notify('screenshot_save', {'path': screenshot_path, 'url': url, 'size': f"{file_size:.1f}KB"})
                    self.logger.info(f"スクリーンショット保存成功: {screenshot_path} (サイズ: {file_size:.1f}KB)")
                else:
                    self.logger.error(f"スクリーンショットが保存されていません: {screenshot_path}")
                    self.notify('error', {'message': f"スクリーンショットの保存に失敗しました: {screenshot_path}"})
            except Exception as e:
                self.logger.error(f"スクリーンショット保存エラー: {str(e)}")
                self.notify('error', {'message': f"スクリーンショット保存エラー: {str(e)}"})
            
            # HTMLソースを取得
            html_source = self.browser.page_source
            
            # HTMLソースの最初の1000文字をコンソールに出力
            html_preview = html_source[:1000] + "..." if len(html_source) > 1000 else html_source
            print(f"\n===== HTML SOURCE PREVIEW ({url}) =====\n{html_preview}\n==============================\n")
            self.notify('html_content', {'url': url, 'preview': html_preview})
            
            # HTMLを保存
            html_file = f"{page_id}.html"
            html_path = os.path.join(self.dirs['html'], html_file)
            try:
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_source)
                
                # HTMLファイルが実際に保存されたか確認
                if os.path.exists(html_path):
                    file_size = os.path.getsize(html_path) / 1024  # KB単位
                    self.logger.info(f"HTML保存成功: {html_path} (サイズ: {file_size:.1f}KB)")
                    self.notify('html_save', {'path': html_path, 'url': url, 'size': f"{file_size:.1f}KB"})
                else:
                    self.logger.error(f"HTMLファイルが保存されていません: {html_path}")
                    self.notify('error', {'message': f"HTMLの保存に失敗しました: {html_path}"})
            except Exception as e:
                self.logger.error(f"HTML保存エラー: {str(e)}")
                self.notify('error', {'message': f"HTML保存エラー: {str(e)}"})
            
            # ページ情報を記録
            page_info = {
                'id': page_id,
                'url': url,
                'title': title,
                'depth': depth,
                'screenshot_path': screenshot_path,
                'html_path': html_path,
                'timestamp': datetime.now().isoformat()
            }
            self.pages.append(page_info)
            
            # 次の深さが最大深さを超えている場合は終了
            if depth >= self.max_depth:
                return
            
            # リンクを収集して次のページへ
            links = self._extract_links()
            
            # リンク情報を通知
            for link in links:
                self.notify('link_found', {'url': link['url'], 'text': link['text']})
            
            for link in links:
                next_url = link['url']
                if next_url not in self.visited_urls:
                    self._process_page(next_url, depth + 1)
                    
        except Exception as e:
            self.logger.error(f"ページ処理中にエラーが発生しました ({url}): {str(e)}")
            self.notify('error', {'url': url, 'message': str(e)})
    
    def _normalize_url(self, url):
        """
        URLを正規化する
        
        Args:
            url (str): 正規化するURL
            
        Returns:
            str: 正規化されたURL
        """
        return normalize_url(url)
    
    def _is_excluded(self, url):
        """
        URLが除外パターンに一致するかどうかを判断する
        
        Args:
            url (str): チェックするURL
            
        Returns:
            bool: URLが除外パターンに一致するかどうか
        """
        for pattern in self.exclude_patterns:
            if re.search(pattern, url):
                return True
        return False
    
    def _generate_page_id(self, url):
        """
        URLからページIDを生成する
        
        Args:
            url (str): ページIDを生成するためのURL
            
        Returns:
            str: 生成されたページID
        """
        return get_url_hash(url)
    
    def _extract_links(self):
        """
        現在のページから全てのリンクを抽出する
        
        Returns:
            list: 抽出されたリンクのリスト
        """
        links = []
        
        try:
            # ページ内の全リンクを取得
            elements = self.browser.find_elements(By.TAG_NAME, "a")
            
            # href属性を取得
            for element in elements:
                href = element.get_attribute("href")
                if href and href.startswith("http"):
                    links.append(href)
        
        except Exception as e:
            self.logger.error(f"リンク抽出中にエラーが発生しました: {e}")
        
        return links
    
    def _save_results(self):
        """
        クローリング結果をJSONファイルに保存する
        """
        # 結果をJSONファイルに保存
        json_path = os.path.join(self.dirs['results'], 'crawl_results.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.pages, f)
        self.logger.info(f"クローリング結果をJSONファイルに保存しました: {json_path}") 