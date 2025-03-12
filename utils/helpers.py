#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ヘルパー関数を提供するユーティリティモジュール
"""

import os
import re
import hashlib
import urllib.parse
from datetime import datetime


def normalize_url(url):
    """
    URLを正規化する（クエリパラメータのソートなど）
    
    Args:
        url (str): 正規化するURL
        
    Returns:
        str: 正規化されたURL
    """
    parsed = urllib.parse.urlparse(url)
    
    # クエリパラメータをソート
    query_params = urllib.parse.parse_qsl(parsed.query)
    sorted_query = urllib.parse.urlencode(sorted(query_params))
    
    # 新しいURLを構築
    normalized = urllib.parse.urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        sorted_query,
        ''  # フラグメントは除外
    ))
    
    # 末尾のスラッシュを統一
    if normalized.endswith('/'):
        normalized = normalized[:-1]
    
    return normalized


def get_url_hash(url):
    """
    URLからハッシュ値を生成する
    
    Args:
        url (str): ハッシュを生成するURL
        
    Returns:
        str: URLのハッシュ値
    """
    normalized = normalize_url(url)
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()


def get_safe_filename(url):
    """
    URLから安全なファイル名を生成する
    
    Args:
        url (str): 変換するURL
        
    Returns:
        str: 安全なファイル名
    """
    url_hash = get_url_hash(url)
    path = urllib.parse.urlparse(url).path
    
    # パスの最後の部分を取得
    filename = os.path.basename(path)
    
    # ファイル名が空の場合はindex.htmlとする
    if not filename:
        filename = 'index.html'
    
    # 拡張子がない場合はhtmlとする
    if '.' not in filename:
        filename += '.html'
    
    # ハッシュを追加
    base, ext = os.path.splitext(filename)
    safe_filename = f"{base}_{url_hash[:8]}{ext}"
    
    # 安全でない文字を置き換え
    safe_filename = re.sub(r'[^\w\-\.]', '_', safe_filename)
    
    return safe_filename


def get_timestamp():
    """
    現在のタイムスタンプを取得する
    
    Returns:
        str: フォーマットされたタイムスタンプ
    """
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def extract_domain(url):
    """
    URLからドメイン名を抽出する
    
    Args:
        url (str): 抽出するURL
        
    Returns:
        str: ドメイン名
    """
    parsed = urllib.parse.urlparse(url)
    return parsed.netloc 