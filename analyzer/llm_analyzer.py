#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web自動解析システム - LLM解析機能
"""

import os
import json
import logging
import time
from openai import OpenAI


class LLMAnalyzer:
    """LLMを使ってWebサイトを解析するクラス"""
    
    def __init__(self, config, parsed_data):
        """
        初期化メソッド
        
        Args:
            config (dict): アプリケーション設定
            parsed_data (list): 解析済みのページデータ
        """
        self.config = config
        self.parsed_data = parsed_data
        self.logger = logging.getLogger(__name__)
        
        # LLM設定
        self.provider = config['llm']['provider']
        self.model = config['llm']['model']
        self.temperature = config['llm'].get('temperature', 0.1)
        self.max_tokens = config['llm'].get('max_tokens', 4000)
        
        # OpenAI API設定
        if self.provider == 'openai':
            self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        # 解析結果
        self.analysis_results = {
            'system_overview': None,
            'screen_specs': [],
            'screen_flow': None,
            'data_structure': None
        }
        
        # 出力先ディレクトリ
        self.base_dir = config['storage']['base_dir']
        self.docs_dir = os.path.join(self.base_dir, config['storage']['docs_dir'])
        
        # 出力ファイルパス
        self.analysis_file = os.path.join(self.base_dir, 'analysis_results.json')
    
    def analyze(self):
        """
        LLMを使って解析を実行する
        
        Returns:
            dict: 解析結果
        """
        self.logger.info("LLMによる解析を開始します")
        
        # システム概要の解析
        self.analysis_results['system_overview'] = self.analyze_system_overview()
        
        # 画面仕様の解析
        self.analysis_results['screen_specs'] = self.analyze_screen_specs()
        
        # 画面遷移の解析
        self.analysis_results['screen_flow'] = self.analyze_screen_flow()
        
        # データ構造の解析
        self.analysis_results['data_structure'] = self.analyze_data_structure()
        
        # 解析結果を保存
        self._save_analysis_results()
        
        self.logger.info("LLMによる解析が完了しました")
        
        return self.analysis_results
    
    def analyze_system_overview(self):
        """
        システム概要を解析する
        
        Returns:
            dict: システム概要の解析結果
        """
        self.logger.info("システム概要を解析中...")
        
        # 解析用のデータ準備
        system_data = {
            'pages': len(self.parsed_data),
            'page_types': {},
            'common_elements': self._get_common_elements(),
            'sample_pages': self._get_sample_pages(3)
        }
        
        # ページタイプの集計
        for page in self.parsed_data:
            page_type = page.get('structure', {}).get('page_type', 'unknown')
            if page_type in system_data['page_types']:
                system_data['page_types'][page_type] += 1
            else:
                system_data['page_types'][page_type] = 1
        
        # LLMへのプロンプト作成
        prompt = """
        あなたはWebシステム解析の専門家です。以下のデータに基づいて、システムの概要を分析してください。

        システムデータ:
        """
        prompt += json.dumps(system_data, ensure_ascii=False, indent=2)
        
        prompt += """
        
        以下の情報を含む、システム概要を作成してください:
        1. システムの目的と機能概要
        2. 主要な画面タイプとその役割
        3. システムの全体的な構造
        4. 想定されるユーザー層とユースケース
        5. システムの特徴と強み

        回答は、Markdownフォーマットで、見出しと箇条書きを使用して構造化してください。
        """
        
        # LLMによる解析
        response = self._call_llm(prompt)
        
        if not response:
            self.logger.error("システム概要の解析に失敗しました")
            return None
        
        # 結果を整形
        result = {
            'content': response,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # システム概要をファイルに保存
        self._save_markdown_file('system_overview.md', response)
        
        return result
    
    def analyze_screen_specs(self):
        """
        画面仕様を解析する
        
        Returns:
            list: 画面仕様の解析結果
        """
        self.logger.info("画面仕様を解析中...")
        
        screen_specs = []
        
        # 重要なページタイプを優先
        important_types = ['login', 'home', 'list', 'detail', 'form', 'search', 'profile']
        
        # 各ページの解析
        for page in self.parsed_data:
            page_url = page.get('url', '')
            page_type = page.get('structure', {}).get('page_type', 'unknown')
            elements = page.get('elements', {})
            structure = page.get('structure', {})
            
            # シンプルなページ情報
            page_info = {
                'url': page_url,
                'title': elements.get('title', ''),
                'type': page_type,
                'has_table': structure.get('has_table', False),
                'has_form': bool(elements.get('forms', [])),
                'header_texts': [h.get('text', '') for h in elements.get('headers', [])[:5]],
                'link_count': len(elements.get('links', [])),
                'form_count': len(elements.get('forms', [])),
                'table_count': len(elements.get('tables', []))
            }
            
            # LLMへのプロンプト作成
            prompt = f"""
            あなたはUI/UX専門家です。以下のWebページデータに基づいて、詳細な画面仕様を作成してください。

            ページ情報:
            """
            prompt += json.dumps(page_info, ensure_ascii=False, indent=2)
            
            # より詳細な情報を追加
            prompt += """
            
            要素詳細:
            """
            prompt += json.dumps({
                'forms': elements.get('forms', [])[:2],  # サンプルとして最初の2つのみ
                'tables': elements.get('tables', [])[:1],  # サンプルとして最初の1つのみ
                'content_blocks': elements.get('content_blocks', [])[:3]  # サンプルとして最初の3つのみ
            }, ensure_ascii=False, indent=2)
            
            prompt += """
            
            以下の情報を含む、画面仕様を作成してください:
            1. 画面の目的と主要機能
            2. 画面の構成要素と配置
            3. 入力項目とバリデーション（存在する場合）
            4. データ表示形式（テーブル、リスト、カードなど）
            5. ユーザー操作と遷移先

            回答は、Markdownフォーマットで、見出しと箇条書きを使用して構造化してください。
            300〜500単語程度で簡潔に記述してください。
            """
            
            # LLMによる解析
            response = self._call_llm(prompt)
            
            if not response:
                self.logger.warning(f"画面仕様の解析に失敗しました: {page_url}")
                continue
            
            # 結果を整形
            result = {
                'url': page_url,
                'title': elements.get('title', ''),
                'type': page_type,
                'content': response,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            screen_specs.append(result)
            
            # ファイル名を作成
            safe_filename = page_url.replace(':', '_').replace('/', '_').replace('?', '_')
            if len(safe_filename) > 50:
                safe_filename = safe_filename[:50]
            
            # 画面仕様をファイルに保存
            self._save_markdown_file(f'screen_spec_{safe_filename}.md', response)
            
            # 重要なページタイプが一定数解析できたら終了（時間短縮のため）
            analyzed_important = sum(1 for spec in screen_specs if spec['type'] in important_types)
            if analyzed_important >= 10:  # 重要なページタイプを最大10種類まで
                break
        
        return screen_specs
    
    def analyze_screen_flow(self):
        """
        画面遷移を解析する
        
        Returns:
            dict: 画面遷移の解析結果
        """
        self.logger.info("画面遷移を解析中...")
        
        # 遷移関係の抽出
        flow_data = self._extract_screen_flow()
        
        # LLMへのプロンプト作成
        prompt = """
        あなたはWebシステム設計の専門家です。以下のデータに基づいて、画面遷移図のための情報を作成してください。

        画面遷移データ:
        """
        prompt += json.dumps(flow_data, ensure_ascii=False, indent=2)
        
        prompt += """
        
        以下の情報を含む、画面遷移の説明を作成してください:
        1. 主要な画面遷移フロー（ログイン→ホーム→各機能など）
        2. 典型的なユーザージャーニー
        3. 画面間の関連性と遷移条件
        4. 画面遷移図（mermaid記法で記述）

        回答は、Markdownフォーマットで、見出しと箇条書きを使用して構造化してください。
        特に、mermaid記法を使った画面遷移図を必ず含めてください。
        """
        
        # LLMによる解析
        response = self._call_llm(prompt)
        
        if not response:
            self.logger.error("画面遷移の解析に失敗しました")
            return None
        
        # 結果を整形
        result = {
            'content': response,
            'raw_flow_data': flow_data,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 画面遷移をファイルに保存
        self._save_markdown_file('screen_flow.md', response)
        
        return result
    
    def analyze_data_structure(self):
        """
        データ構造を解析する
        
        Returns:
            dict: データ構造の解析結果
        """
        self.logger.info("データ構造を解析中...")
        
        # テーブルデータの収集
        tables_data = []
        forms_data = []
        
        for page in self.parsed_data:
            elements = page.get('elements', {})
            
            # テーブル情報を収集
            for table in elements.get('tables', []):
                if table.get('headers') and len(table.get('headers', [])) > 0:
                    tables_data.append({
                        'page': elements.get('title', ''),
                        'headers': table.get('headers', []),
                        'sample_rows': table.get('rows', [])[:3]  # サンプルとして最初の3行
                    })
            
            # フォーム情報を収集
            for form in elements.get('forms', []):
                if form.get('fields') and len(form.get('fields', [])) > 0:
                    forms_data.append({
                        'page': elements.get('title', ''),
                        'action': form.get('action', ''),
                        'method': form.get('method', ''),
                        'fields': form.get('fields', [])
                    })
        
        # データセット
        data_set = {
            'tables': tables_data[:10],  # 最大10テーブル
            'forms': forms_data[:10]    # 最大10フォーム
        }
        
        # LLMへのプロンプト作成
        prompt = """
        あなたはデータモデリングの専門家です。以下のWebシステムのテーブルとフォームデータに基づいて、データ構造を分析してください。

        データ:
        """
        prompt += json.dumps(data_set, ensure_ascii=False, indent=2)
        
        prompt += """
        
        以下の情報を含む、データ構造の分析結果を作成してください:
        1. 主要なエンティティとその属性
        2. エンティティ間の関連性
        3. 想定されるデータモデル（ER図の説明）
        4. データ入力と表示のパターン
        5. データフローの概要

        回答は、Markdownフォーマットで、見出しと箇条書きを使用して構造化してください。
        可能であれば、mermaid記法を使ったER図も含めてください。
        """
        
        # LLMによる解析
        response = self._call_llm(prompt)
        
        if not response:
            self.logger.error("データ構造の解析に失敗しました")
            return None
        
        # 結果を整形
        result = {
            'content': response,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # データ構造をファイルに保存
        self._save_markdown_file('data_structure.md', response)
        
        return result
    
    def _call_llm(self, prompt):
        """
        LLMを呼び出す
        
        Args:
            prompt (str): LLMに送信するプロンプト
            
        Returns:
            str: LLMの応答テキスト
        """
        try:
            if self.provider == 'openai':
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "あなたはWebシステム解析の専門家です。与えられたデータを分析して、詳細かつ構造化された文書を作成します。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                return response.choices[0].message.content
            else:
                self.logger.error(f"未対応のLLMプロバイダです: {self.provider}")
                return None
                
        except Exception as e:
            self.logger.error(f"LLM呼び出し中にエラーが発生しました: {e}")
            return None
    
    def _get_common_elements(self):
        """
        共通要素を抽出する
        
        Returns:
            dict: 共通要素のリスト
        """
        # ヘッダー、フッター、ナビゲーションなどの共通要素を特定
        common = {
            'has_header': sum(1 for p in self.parsed_data if p.get('structure', {}).get('has_header', False)),
            'has_footer': sum(1 for p in self.parsed_data if p.get('structure', {}).get('has_footer', False)),
            'has_navigation': sum(1 for p in self.parsed_data if p.get('structure', {}).get('has_navigation', False)),
            'has_sidebar': sum(1 for p in self.parsed_data if p.get('structure', {}).get('has_sidebar', False))
        }
        
        # 全ページ数
        total_pages = len(self.parsed_data)
        
        # パーセンテージに変換
        if total_pages > 0:
            for key in common:
                common[key] = int((common[key] / total_pages) * 100)
        
        return common
    
    def _get_sample_pages(self, count=3):
        """
        サンプルページを取得する
        
        Args:
            count (int): 取得するサンプル数
            
        Returns:
            list: サンプルページのリスト
        """
        samples = []
        
        # 重要なページタイプ
        important_types = ['home', 'login', 'list', 'detail', 'form']
        
        # 重要なページタイプから1つずつ選択
        for page_type in important_types:
            for page in self.parsed_data:
                if page.get('structure', {}).get('page_type') == page_type:
                    title = page.get('elements', {}).get('title', '')
                    url = page.get('url', '')
                    samples.append({'type': page_type, 'title': title, 'url': url})
                    break
            
            # 指定数に達したら終了
            if len(samples) >= count:
                break
        
        # まだ足りない場合は他のページから追加
        if len(samples) < count:
            for page in self.parsed_data:
                page_type = page.get('structure', {}).get('page_type')
                
                # すでに選択されたタイプは除外
                if any(s['type'] == page_type for s in samples):
                    continue
                
                title = page.get('elements', {}).get('title', '')
                url = page.get('url', '')
                samples.append({'type': page_type, 'title': title, 'url': url})
                
                if len(samples) >= count:
                    break
        
        return samples
    
    def _extract_screen_flow(self):
        """
        画面遷移を抽出する
        
        Returns:
            dict: 画面遷移データ
        """
        flow_data = {
            'nodes': [],
            'edges': []
        }
        
        # ノード（画面）の追加
        for page in self.parsed_data:
            page_url = page.get('url', '')
            page_title = page.get('elements', {}).get('title', '')
            page_type = page.get('structure', {}).get('page_type', 'unknown')
            
            # 短いID生成
            page_id = page_url.split('/')[-1]
            if not page_id or page_id == '':
                page_id = 'home'
            
            # 特殊文字を削除
            page_id = ''.join(c for c in page_id if c.isalnum())
            
            # ノード追加
            flow_data['nodes'].append({
                'id': page_id,
                'url': page_url,
                'title': page_title,
                'type': page_type
            })
        
        # エッジ（遷移）の追加
        for page in self.parsed_data:
            source_url = page.get('url', '')
            source_id = source_url.split('/')[-1]
            if not source_id or source_id == '':
                source_id = 'home'
            source_id = ''.join(c for c in source_id if c.isalnum())
            
            # リンクを抽出
            links = page.get('elements', {}).get('links', [])
            for link in links:
                target_url = link.get('url', '')
                target_text = link.get('text', '')
                
                # 内部リンクかどうか確認
                is_internal = False
                target_id = None
                
                for node in flow_data['nodes']:
                    if node['url'] == target_url:
                        is_internal = True
                        target_id = node['id']
                        break
                
                if is_internal and target_id and source_id != target_id:
                    flow_data['edges'].append({
                        'source': source_id,
                        'target': target_id,
                        'label': target_text[:20]  # ラベルが長すぎる場合は切り詰め
                    })
        
        return flow_data
    
    def _save_analysis_results(self):
        """解析結果をJSONファイルに保存する"""
        try:
            with open(self.analysis_file, 'w', encoding='utf-8') as f:
                json.dump(self.analysis_results, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"解析結果を保存しました: {self.analysis_file}")
        except Exception as e:
            self.logger.error(f"解析結果保存中にエラーが発生しました: {e}")
    
    def _save_markdown_file(self, filename, content):
        """解析結果をMarkdownファイルに保存する"""
        try:
            # ドキュメントディレクトリの確認
            os.makedirs(self.docs_dir, exist_ok=True)
            
            # ファイルパス
            file_path = os.path.join(self.docs_dir, filename)
            
            # ファイル保存
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            self.logger.info(f"Markdownファイルを保存しました: {file_path}")
        except Exception as e:
            self.logger.error(f"Markdownファイル保存中にエラーが発生しました: {e}") 