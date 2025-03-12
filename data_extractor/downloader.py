#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web自動解析システム - データダウンロード機能
"""

import os
import logging
import time
import requests
import pandas as pd
from io import BytesIO
from urllib.parse import urljoin
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class DataDownloader:
    """データをダウンロードするクラス"""
    
    def __init__(self, browser, dirs, config):
        """
        初期化メソッド
        
        Args:
            browser: Seleniumブラウザインスタンス
            dirs (dict): 出力ディレクトリ情報
            config (dict): アプリケーション設定
        """
        self.browser = browser
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 出力ディレクトリ
        self.data_dir = dirs['data']
        
        # データ抽出設定
        self.extraction_config = config.get('data_extraction', {})
        self.delay = self.extraction_config.get('delay', 2)
        
        # セッションの作成（Cookie継承）
        self.session = requests.Session()
        self._update_session_cookies()
    
    def download_all(self, data_sources):
        """
        全データソースからデータをダウンロードする
        
        Args:
            data_sources (list): ダウンロード対象のデータソースリスト
            
        Returns:
            list: ダウンロード結果のリスト
        """
        self.logger.info(f"データダウンロードを開始します: {len(data_sources)}個のソース")
        
        results = []
        
        # 出力ディレクトリの確認
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 各データソースを処理
        for source in data_sources:
            source_type = source.get('type')
            
            try:
                if source_type == 'link':
                    result = self._download_link(source)
                elif source_type == 'form':
                    result = self._download_form(source)
                elif source_type == 'api':
                    result = self._download_api(source)
                elif source_type == 'table':
                    result = self._scrape_table(source)
                else:
                    self.logger.warning(f"未対応のソースタイプ: {source_type}")
                    continue
                
                if result:
                    results.append(result)
                    self.logger.info(f"ダウンロード成功: {result.get('file_path')}")
                
                # 連続アクセスを避けるための遅延
                time.sleep(self.delay)
                
            except Exception as e:
                self.logger.error(f"ダウンロード中にエラーが発生しました: {e}")
        
        self.logger.info(f"データダウンロード完了: {len(results)}/{len(data_sources)}個成功")
        
        return results
    
    def _download_link(self, source):
        """
        リンクからファイルをダウンロードする
        
        Args:
            source (dict): データソース情報
            
        Returns:
            dict: ダウンロード結果
        """
        url = source.get('url')
        file_type = source.get('file_type', 'unknown')
        
        self.logger.info(f"リンクからファイルをダウンロード中: {url}")
        
        # セッションCookieの更新
        self._update_session_cookies()
        
        # ファイル名の生成
        file_name = self._generate_filename(url, file_type)
        file_path = os.path.join(self.data_dir, file_name)
        
        # ダウンロード
        response = self.session.get(url, stream=True)
        
        # ステータスコードの確認
        if response.status_code != 200:
            self.logger.error(f"ダウンロード失敗 ({response.status_code}): {url}")
            return None
        
        # ファイル保存
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # 結果の作成
        result = {
            'source_type': 'link',
            'url': url,
            'file_type': file_type,
            'file_path': file_path,
            'size': os.path.getsize(file_path)
        }
        
        return result
    
    def _download_form(self, source):
        """
        フォーム送信によりデータをダウンロードする
        
        Args:
            source (dict): データソース情報
            
        Returns:
            dict: ダウンロード結果
        """
        url = source.get('url')
        method = source.get('method', 'GET')
        export_field = source.get('export_field')
        page_url = source.get('page_url')
        
        self.logger.info(f"フォームからデータをダウンロード中: {url}")
        
        # ブラウザでページに移動
        try:
            self.browser.get(page_url)
            WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # フォーム要素を探す
            form_found = False
            for form in self.browser.find_elements(By.TAG_NAME, "form"):
                form_action = form.get_attribute("action")
                if not form_action:
                    continue
                
                # フォームのアクションURLが一致するか確認
                absolute_action = urljoin(page_url, form_action)
                if absolute_action == url:
                    form_found = True
                    
                    # エクスポート関連のボタンを探す
                    export_button = None
                    
                    # export_fieldが設定されている場合はその要素を探す
                    if export_field:
                        try:
                            export_button = form.find_element(By.NAME, export_field)
                        except NoSuchElementException:
                            pass
                    
                    # ボタンが見つからない場合は、テキストからエクスポート関連のボタンを探す
                    if not export_button:
                        for button in form.find_elements(By.TAG_NAME, "button"):
                            button_text = button.text.lower()
                            if any(keyword in button_text for keyword in ['export', 'download', 'エクスポート', 'ダウンロード']):
                                export_button = button
                                break
                    
                    # ボタンが見つからない場合は、input type="submit"を探す
                    if not export_button:
                        for input_elem in form.find_elements(By.CSS_SELECTOR, "input[type='submit']"):
                            input_value = input_elem.get_attribute("value").lower()
                            if any(keyword in input_value for keyword in ['export', 'download', 'エクスポート', 'ダウンロード']):
                                export_button = input_elem
                                break
                    
                    # ボタンが見つからない場合は、フォーム自体を送信
                    if not export_button:
                        form.submit()
                    else:
                        export_button.click()
                    
                    self.logger.info("フォームを送信しました")
                    break
            
            if not form_found:
                self.logger.warning(f"指定されたフォームが見つかりませんでした: {url}")
                return None
            
            # ダウンロードの完了を待機
            time.sleep(5)  # ダウンロードの完了を待つ
            
            # ダウンロードしたファイルのパスを特定
            # 注意: ブラウザがファイルを自動的にダウンロードする場合、
            # そのパスを特定するには環境に応じた実装が必要
            
            # ここでは簡易的に、最も新しいファイルを利用
            latest_file = self._find_latest_download()
            
            if not latest_file:
                self.logger.warning("ダウンロードされたファイルが見つかりませんでした")
                return None
            
            # データディレクトリにコピー
            dest_path = os.path.join(self.data_dir, os.path.basename(latest_file))
            shutil.copy2(latest_file, dest_path)
            
            # 結果の作成
            result = {
                'source_type': 'form',
                'url': url,
                'file_path': dest_path,
                'size': os.path.getsize(dest_path)
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"フォームからのダウンロード中にエラーが発生しました: {e}")
            return None
    
    def _download_api(self, source):
        """
        APIからデータをダウンロードする
        
        Args:
            source (dict): データソース情報
            
        Returns:
            dict: ダウンロード結果
        """
        url = source.get('url')
        
        self.logger.info(f"APIからデータをダウンロード中: {url}")
        
        # セッションCookieの更新
        self._update_session_cookies()
        
        # ファイル名の生成
        file_name = self._generate_filename(url, 'json')
        file_path = os.path.join(self.data_dir, file_name)
        
        # ダウンロード
        response = self.session.get(url)
        
        # ステータスコードの確認
        if response.status_code != 200:
            self.logger.error(f"API呼び出し失敗 ({response.status_code}): {url}")
            return None
        
        # レスポンスのContent-Typeを確認
        content_type = response.headers.get('Content-Type', '')
        
        if 'json' in content_type:
            # JSONレスポンス
            data = response.json()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        elif 'xml' in content_type:
            # XMLレスポンス
            file_name = file_name.replace('.json', '.xml')
            file_path = os.path.join(self.data_dir, file_name)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
        else:
            # その他のレスポンス
            with open(file_path, 'wb') as f:
                f.write(response.content)
        
        # 結果の作成
        result = {
            'source_type': 'api',
            'url': url,
            'file_path': file_path,
            'size': os.path.getsize(file_path),
            'content_type': content_type
        }
        
        return result
    
    def _scrape_table(self, source):
        """
        テーブルからデータをスクレイピングする
        
        Args:
            source (dict): データソース情報
            
        Returns:
            dict: ダウンロード結果
        """
        page_url = source.get('page_url')
        table_index = source.get('table_index', 1)
        headers = source.get('headers', [])
        
        self.logger.info(f"テーブルをスクレイピング中: {page_url}, テーブル#{table_index}")
        
        try:
            # ページにアクセス
            self.browser.get(page_url)
            WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            # テーブル要素を取得
            tables = self.browser.find_elements(By.TAG_NAME, "table")
            
            if table_index > len(tables):
                self.logger.warning(f"テーブル#{table_index}が見つかりません。テーブル数: {len(tables)}")
                return None
            
            # インデックスは1始まりだがPythonのリストは0始まり
            table = tables[table_index - 1]
            
            # テーブルデータの抽出
            data = []
            
            # ヘッダー行
            if not headers:
                headers = []
                header_cells = table.find_elements(By.TAG_NAME, "th")
                for cell in header_cells:
                    headers.append(cell.text.strip())
            
            # データ行
            rows = table.find_elements(By.TAG_NAME, "tr")
            for row in rows:
                # th要素がある行はヘッダー行の可能性があるのでスキップ
                if row.find_elements(By.TAG_NAME, "th"):
                    continue
                
                # tdセルからデータを取得
                cells = row.find_elements(By.TAG_NAME, "td")
                if cells:
                    row_data = {}
                    for i, cell in enumerate(cells):
                        # ヘッダーがある場合はそれを列名として使用
                        if i < len(headers):
                            column_name = headers[i]
                        else:
                            column_name = f"Column{i+1}"
                        
                        row_data[column_name] = cell.text.strip()
                    
                    data.append(row_data)
            
            # データがない場合
            if not data:
                self.logger.warning(f"テーブル#{table_index}にデータがありません")
                return None
            
            # DataFrameに変換
            df = pd.DataFrame(data)
            
            # CSVとして保存
            file_name = self._generate_filename(page_url, 'csv', f'table{table_index}')
            file_path = os.path.join(self.data_dir, file_name)
            
            df.to_csv(file_path, index=False, encoding='utf-8')
            
            # 結果の作成
            result = {
                'source_type': 'table',
                'url': page_url,
                'table_index': table_index,
                'file_path': file_path,
                'size': os.path.getsize(file_path),
                'rows': len(data)
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"テーブルスクレイピング中にエラーが発生しました: {e}")
            return None
    
    def _update_session_cookies(self):
        """ブラウザのCookieをrequestsセッションに反映する"""
        try:
            # ブラウザのCookieを取得
            browser_cookies = self.browser.get_cookies()
            
            # requestsセッションのCookieを更新
            for cookie in browser_cookies:
                self.session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain'))
            
            self.logger.debug("セッションCookieを更新しました")
            
        except Exception as e:
            self.logger.error(f"セッションCookie更新中にエラーが発生しました: {e}")
    
    def _generate_filename(self, url, file_type, prefix=''):
        """
        URLとファイルタイプからファイル名を生成する
        
        Args:
            url (str): 対象のURL
            file_type (str): ファイルタイプ
            prefix (str): ファイル名の接頭辞
            
        Returns:
            str: 生成されたファイル名
        """
        # URLからファイル名を抽出
        file_name = url.split('/')[-1]
        
        # クエリパラメータを削除
        file_name = file_name.split('?')[0]
        
        # 適切な拡張子を持たない場合は追加
        if not file_name or '.' not in file_name:
            timestamp = int(time.time())
            
            if prefix:
                file_name = f"{prefix}_{timestamp}.{file_type}"
            else:
                file_name = f"data_{timestamp}.{file_type}"
        
        # 特殊文字を置換
        file_name = file_name.replace(':', '_').replace('/', '_').replace('?', '_')
        
        return file_name
    
    def _find_latest_download(self, download_dir=None):
        """
        最も新しくダウンロードされたファイルを探す
        
        Args:
            download_dir (str): ダウンロードディレクトリ
            
        Returns:
            str: 最新のファイルのパス
        """
        # ダウンロードディレクトリが指定されていない場合はデフォルト値を使用
        if not download_dir:
            # ユーザーのダウンロードディレクトリを推測
            home_dir = os.path.expanduser('~')
            download_dir = os.path.join(home_dir, 'Downloads')
        
        # ディレクトリが存在するか確認
        if not os.path.exists(download_dir):
            self.logger.warning(f"ダウンロードディレクトリが見つかりません: {download_dir}")
            return None
        
        # 最も新しいファイルを探す
        files = [os.path.join(download_dir, f) for f in os.listdir(download_dir) 
                if os.path.isfile(os.path.join(download_dir, f))]
        
        if not files:
            return None
        
        latest_file = max(files, key=os.path.getmtime)
        
        # 最近作成されたファイルかどうか確認
        file_mtime = os.path.getmtime(latest_file)
        current_time = time.time()
        
        # 1分以内に作成されたファイルのみを対象
        if current_time - file_mtime > 60:
            self.logger.warning("最近ダウンロードされたファイルがありません")
            return None
        
        return latest_file 