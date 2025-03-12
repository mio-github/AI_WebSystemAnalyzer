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


class WebCrawler:
    """Webクローリングを行うクラス"""
    
    def __init__(self, browser, config, dirs):
        """
        初期化メソッド
        
        Args:
            browser: Seleniumブラウザインスタンス
            config (dict): アプリケーション設定
            dirs (dict): 出力ディレクトリ情報
        """
        self.browser = browser
        self.config = config
        self.dirs = dirs
        self.logger = logging.getLogger(__name__)
        
        # 訪問済みURLの追跡
        self.visited_urls = set()
        self.to_visit_urls = []
        
        # ベースURL設定
        self.base_url = config['target']['base_url']
        
        # 除外パターン設定
        self.exclude_patterns = config['crawler'].get('exclude_patterns', [])
        
        # ページ読み込み待機時間
        self.delay = config['crawler'].get('delay', 1.5)
        
        # 最大クロール深度
        self.max_depth = config['crawler'].get('max_depth', 3)
        
        # スクリーンショット設定
        self.take_screenshots = config['crawler'].get('screenshot', True)
        
        # ヘルパークラス
        self.screenshot_taker = ScreenshotTaker(browser, dirs)
        self.page_storage = PageStorage(dirs)
        
        # クロール結果保存用
        self.pages = []
    
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
        Webサイトのクローリングを開始する
        
        Returns:
            list: 処理したページ情報のリスト
        """
        self.logger.info("クローリングを開始します")
        
        # 最初のURLを追加
        start_url = self.browser.current_url
        self.to_visit_urls.append((start_url, 0))
        
        # クロール処理
        while self.to_visit_urls:
            # キューからURLを取得
            url, depth = self.to_visit_urls.pop(0)
            
            # 再チェック（他のパスから追加された可能性がある）
            if normalize_url(url) in self.visited_urls:
                continue
                
            # ページ処理
            self.process_page(url, depth)
        
        self.logger.info(f"クローリングが完了しました。合計{len(self.pages)}ページを処理しました。")
        
        return self.pages 