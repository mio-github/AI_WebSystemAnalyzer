#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web自動解析システム - スクリーンショット取得機能
"""

import os
import logging
import time
from PIL import Image
from io import BytesIO
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from utils.helpers import get_url_hash, get_safe_filename


class ScreenshotTaker:
    """ウェブページのスクリーンショットを取得するクラス"""
    
    def __init__(self, browser, dirs):
        """
        初期化メソッド
        
        Args:
            browser: Seleniumブラウザインスタンス
            dirs (dict): 出力ディレクトリ情報
        """
        self.browser = browser
        self.screenshots_dir = dirs['screenshots']
        self.logger = logging.getLogger(__name__)
    
    def take_screenshot(self, url):
        """
        指定されたURLのページのスクリーンショットを撮影する
        
        Args:
            url (str): スクリーンショットを撮影するURL
            
        Returns:
            str: 保存されたスクリーンショットのパス、または失敗した場合はNone
        """
        try:
            self.logger.info(f"スクリーンショット撮影中: {url}")
            
            # スクリーンショットファイル名
            url_hash = get_url_hash(url)
            safe_name = get_safe_filename(url)
            screenshot_filename = f"{safe_name}"
            screenshot_path = os.path.join(self.screenshots_dir, screenshot_filename)
            
            # 一度スクロールしてから撮影
            self._scroll_page()
            
            # フルページスクリーンショットをキャプチャ
            self._capture_full_page_screenshot(screenshot_path)
            
            self.logger.info(f"スクリーンショット保存完了: {screenshot_path}")
            
            return screenshot_path
            
        except Exception as e:
            self.logger.error(f"スクリーンショット撮影中にエラーが発生しました: {e}")
            return None
    
    def _scroll_page(self):
        """
        ページを下部までスクロールして全体を読み込む
        """
        try:
            # 画面の高さを取得
            last_height = self.browser.execute_script("return document.body.scrollHeight")
            
            while True:
                # 下へスクロール
                self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # 読み込みを待機
                time.sleep(1)
                
                # 新しい高さを計算
                new_height = self.browser.execute_script("return document.body.scrollHeight")
                
                # スクロールが終了したか確認
                if new_height == last_height:
                    break
                    
                last_height = new_height
                
            # トップに戻る
            self.browser.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.5)
            
        except Exception as e:
            self.logger.warning(f"ページスクロール中にエラーが発生しました: {e}")
    
    def _capture_full_page_screenshot(self, output_path):
        """
        フルページスクリーンショットを撮影して保存する
        
        Args:
            output_path (str): 保存先パス
        """
        try:
            # ページの全体の高さと幅を取得
            total_width = self.browser.execute_script("return document.body.offsetWidth")
            total_height = self.browser.execute_script("return document.body.parentNode.scrollHeight")
            
            # 画面の高さと幅を取得
            viewport_width = self.browser.execute_script("return window.innerWidth")
            viewport_height = self.browser.execute_script("return window.innerHeight")
            
            # スクリーンショット枚数を計算
            rectangles = []
            
            # スクロール位置を計算
            i = 0
            while i < total_height:
                j = 0
                while j < total_width:
                    # スクロール位置
                    top_height = i
                    # ブラウザの表示領域を考慮
                    if i + viewport_height > total_height:
                        top_height = total_height - viewport_height
                    
                    # スクロール
                    self.browser.execute_script(f"window.scrollTo({j}, {top_height})")
                    time.sleep(0.2)
                    
                    # 領域を追加
                    rectangles.append((j, top_height, viewport_width, viewport_height))
                    
                    j += viewport_width
                
                i += viewport_height
            
            # スクリーンショット合成用の画像を作成
            stitched_image = Image.new('RGB', (total_width, total_height))
            
            # 各領域のスクリーンショットを取得して合成
            for i, rect in enumerate(rectangles):
                left, top, width, height = rect
                
                # スクロール
                self.browser.execute_script(f"window.scrollTo({left}, {top})")
                time.sleep(0.2)
                
                # スクリーンショット取得
                screenshot = self.browser.get_screenshot_as_png()
                image = Image.open(BytesIO(screenshot))
                
                # 合成
                stitched_image.paste(image, (left, top))
            
            # 最終的な画像を保存
            stitched_image.save(output_path)
            
        except Exception as e:
            self.logger.error(f"フルページスクリーンショット作成中にエラーが発生しました: {e}")
            
            # エラー時は通常のスクリーンショットを取得
            try:
                self.browser.save_screenshot(output_path)
                self.logger.info("通常のスクリーンショットを代わりに保存しました")
            except:
                self.logger.error("スクリーンショットの保存に失敗しました") 