#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web自動解析システム - メインエントリーポイント
"""

import os
import sys
import yaml
import argparse
import logging
from datetime import datetime

# 内部モジュールのインポート
from utils.logger import setup_logger
from crawler.login import LoginManager
from crawler.crawler import WebCrawler
from analyzer.html_parser import HTMLParser
from analyzer.llm_analyzer import LLMAnalyzer
from analyzer.doc_generator import DocumentGenerator
from data_extractor.data_finder import DataFinder
from data_extractor.downloader import DataDownloader


def load_config(config_path="config.yaml"):
    """設定ファイルを読み込む"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"設定ファイルの読み込みに失敗しました: {e}")
        sys.exit(1)


def setup_directories(config):
    """必要なディレクトリを作成"""
    base_dir = config['storage']['base_dir']
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(base_dir, timestamp)
    
    dirs = {
        'base': output_dir,
        'html': os.path.join(output_dir, config['storage']['html_dir']),
        'screenshots': os.path.join(output_dir, config['storage']['screenshots_dir']),
        'docs': os.path.join(output_dir, config['storage']['docs_dir']),
        'data': os.path.join(output_dir, config['storage']['data_dir']),
    }
    
    for dir_path in dirs.values():
        os.makedirs(dir_path, exist_ok=True)
    
    return dirs


def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description="Web自動解析システム")
    parser.add_argument("-c", "--config", default="config.yaml", help="設定ファイルのパス")
    args = parser.parse_args()
    
    # 設定読み込み
    config = load_config(args.config)
    
    # ロガー設定
    logger = setup_logger(config['logging']['level'], config['logging']['file'])
    logger.info("Web自動解析システムを開始します")
    
    # ディレクトリ作成
    dirs = setup_directories(config)
    logger.info(f"出力ディレクトリを作成しました: {dirs['base']}")
    
    try:
        # ステップ1: ログイン
        login_manager = LoginManager(config)
        browser = login_manager.login()
        logger.info("ログインに成功しました")
        
        # ステップ2: クローリング
        crawler = WebCrawler(browser, config, dirs)
        pages = crawler.crawl()
        logger.info(f"クローリングが完了しました。合計{len(pages)}ページを取得しました")
        
        # ステップ3: HTML解析
        html_parser = HTMLParser(dirs)
        parsed_data = html_parser.parse_all()
        logger.info("HTML解析が完了しました")
        
        # ステップ4: LLM解析
        llm_analyzer = LLMAnalyzer(config, parsed_data)
        analysis_results = llm_analyzer.analyze()
        logger.info("LLM解析が完了しました")
        
        # ステップ5: ドキュメント生成
        doc_generator = DocumentGenerator(dirs, analysis_results)
        doc_generator.generate_all()
        logger.info("ドキュメント生成が完了しました")
        
        # ステップ6: データ抽出（オプション）
        if config.get('data_extraction', {}).get('enabled', False):
            data_finder = DataFinder(parsed_data, config)
            data_targets = data_finder.find_data_sources()
            
            downloader = DataDownloader(browser, dirs, config)
            downloader.download_all(data_targets)
            logger.info("データ抽出が完了しました")
            
        logger.info(f"すべての処理が完了しました。結果は {dirs['base']} に保存されています")
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # ブラウザを閉じる
        if 'browser' in locals():
            browser.quit()
            logger.info("ブラウザを終了しました")


if __name__ == "__main__":
    main() 