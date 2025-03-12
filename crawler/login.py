#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web自動解析システム - 自動ログイン機能
"""

import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class LoginManager:
    """Webサイトへの自動ログイン処理を担当するクラス"""
    
    def __init__(self, config):
        """
        初期化メソッド
        
        Args:
            config (dict): アプリケーション設定
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.browser = None
    
    def setup_browser(self):
        """
        ブラウザを設定
        
        Returns:
            webdriver: 設定済みのWebDriverインスタンス
        """
        self.logger.info("ブラウザを設定中...")
        
        chrome_options = Options()
        
        # ヘッドレスモードの設定
        if self.config['crawler'].get('headless', True):
            chrome_options.add_argument('--headless')
        
        # その他のオプション
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # ユーザーエージェント設定
        user_agent = self.config.get('crawler', {}).get('user_agent', 
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36')
        chrome_options.add_argument(f'--user-agent={user_agent}')
        
        # ブラウザの作成
        try:
            service = Service()
            self.browser = webdriver.Chrome(service=service, options=chrome_options)
            self.browser.set_page_load_timeout(30)  # ページロードタイムアウト (秒)
            self.logger.info("ブラウザが正常に設定されました")
            return self.browser
        except Exception as e:
            self.logger.error(f"ブラウザの設定中にエラーが発生しました: {e}")
            raise
    
    def login(self):
        """
        ターゲットシステムにログインする
        
        Returns:
            webdriver: ログイン済みのWebDriverインスタンス
        """
        if not self.browser:
            self.setup_browser()
        
        target_url = self.config['target']['login_url']
        credentials = self.config['target']['credentials']
        
        self.logger.info(f"ログインページにアクセス中: {target_url}")
        
        try:
            # ログインページにアクセス
            self.browser.get(target_url)
            
            # ログインページが読み込まれるのを待機
            WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # クレデンシャル取得
            username = credentials.get('username', '')
            password = credentials.get('password', '')
            
            if not username or not password:
                self.logger.warning("ユーザー名またはパスワードが設定されていません")
            
            # ログインフォームの検出を試みる
            username_field_selectors = [
                "input[type='email']", 
                "input[type='text']", 
                "input[name='username']", 
                "input[id='username']",
                "input[name='user']",
                "input[id='user']",
                "input[name='userid']",
                "input[id='userid']"
            ]
            
            password_field_selectors = [
                "input[type='password']", 
                "input[name='password']", 
                "input[id='password']"
            ]
            
            # ユーザー名フィールドを検索
            username_field = None
            for selector in username_field_selectors:
                try:
                    username_field = self.browser.find_element(By.CSS_SELECTOR, selector)
                    self.logger.info(f"ユーザー名フィールドを検出: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            # パスワードフィールドを検索
            password_field = None
            for selector in password_field_selectors:
                try:
                    password_field = self.browser.find_element(By.CSS_SELECTOR, selector)
                    self.logger.info(f"パスワードフィールドを検出: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            # ログインボタンを検索
            login_button = None
            login_button_selectors = [
                "button[type='submit']", 
                "input[type='submit']", 
                "button.login", 
                "input.login",
                "button:contains('Login')",
                "button:contains('ログイン')"
            ]
            
            for selector in login_button_selectors:
                try:
                    login_button = self.browser.find_element(By.CSS_SELECTOR, selector)
                    self.logger.info(f"ログインボタンを検出: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            # フォームフィールドが見つからない場合
            if not username_field or not password_field or not login_button:
                self.logger.warning("ログインフォームを検出できませんでした。カスタム設定が必要かもしれません。")
                return self.browser
            
            # フォームに入力
            username_field.clear()
            username_field.send_keys(username)
            
            password_field.clear()
            password_field.send_keys(password)
            
            # フォーム送信
            self.logger.info("ログイン情報を送信中...")
            login_button.click()
            
            # ログイン後のページ読み込み待機
            time.sleep(3)  # 短い遅延
            
            # ログイン成功の確認 (URLやページ内容で判断)
            current_url = self.browser.current_url
            if current_url != target_url:
                self.logger.info(f"URLが変更されました。ログイン成功の可能性: {current_url}")
            else:
                # ログイン失敗メッセージの検出を試みる
                try:
                    error_elements = self.browser.find_elements(By.CSS_SELECTOR, ".error, .alert, .message-error")
                    if error_elements:
                        error_text = error_elements[0].text
                        self.logger.warning(f"ログインに失敗した可能性があります: {error_text}")
                    else:
                        self.logger.info("ログイン成功と推測されます")
                except:
                    self.logger.info("ログイン結果を確認できませんでした")
            
            return self.browser
            
        except TimeoutException:
            self.logger.error("ログインページのロードがタイムアウトしました")
            raise
        except Exception as e:
            self.logger.error(f"ログイン処理中にエラーが発生しました: {e}")
            raise 