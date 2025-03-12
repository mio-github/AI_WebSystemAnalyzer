# Web自動解析システムの実装ガイド

このドキュメントでは、Web自動解析システムの実装手順と使用方法について説明します。

## 開発ステップ

Web自動解析システムの開発は、以下のステップで進めることをお勧めします：

### ステップ1: 環境セットアップ

1. 依存パッケージのインストール
```
pip install -r requirements.txt
```

2. WebDriverのインストール（Seleniumで使用）
   - Chromeを使用する場合は、ChromeDriverをインストール
   - または、PlaywrightまたはSeleniumの自動インストーラーを使用

3. 環境変数の設定（LLM APIキーなど）
```
export OPENAI_API_KEY=your_api_key_here
```

### ステップ2: 対象システムの設定

1. `config.yaml`ファイルを編集し、対象システムの情報を設定
   - ターゲットURL
   - ログイン情報
   - クローリング設定
   - LLM設定

2. 必要に応じて、カスタムログイン処理やクローリングルールを実装

### ステップ3: 動作確認と段階的開発

1. ログイン機能の動作確認
```
python -c "from crawler.login import LoginManager; import yaml; config = yaml.safe_load(open('config.yaml')); login = LoginManager(config); browser = login.login()"
```

2. クローラーの動作確認
   - 少ないページ数でテスト
   - 画面保存の確認

3. 解析機能の段階的実装
   - HTML解析
   - LLM解析（各機能を個別にテスト）
   - ドキュメント生成

4. データ抽出機能の実装とテスト

### ステップ4: 完全な実行と最適化

1. 全システムの実行
```
python main.py
```

2. 結果の確認と最適化
   - パフォーマンス改善
   - エラー処理の強化
   - 対象システムに合わせたカスタマイズ

## コードの拡張方法

### 新しいデータソースタイプの追加

データ抽出機能に新しいソースタイプを追加する場合：

1. `data_extractor/data_finder.py`を編集
   - 新しいデータソースの検出ロジックを追加

2. `data_extractor/downloader.py`を編集
   - 新しいダウンロードメソッドを実装

### LLM解析機能の拡張

1. 新しい解析機能の実装
   - `analyzer/llm_analyzer.py`に新しい分析メソッドを追加
   - プロンプトの調整とレスポンス処理の実装

2. ドキュメント生成の拡張
   - `analyzer/doc_generator.py`に新しいドキュメント生成メソッドを追加

### 異なるブラウザバックエンドの使用

1. PlaywrightやPuppeteerなど異なるブラウザ自動化ツールを使用する場合：
   - `crawler/login.py`の`setup_browser`メソッドを変更
   - `crawler/crawler.py`と`crawler/screenshot.py`の関連メソッドを更新

## トラブルシューティング

### ログイン問題

ログインに失敗する場合の対処法：

1. ログインセレクターのカスタマイズ
   - `crawler/login.py`のセレクターリストを対象サイトに合わせて更新

2. 2段階認証などの特殊なログイン処理の実装
   - `login`メソッドをカスタマイズ

### クローリング問題

クローリングが適切に動作しない場合の対処法：

1. 待機時間の調整
   - `config.yaml`の`delay`パラメータを増加

2. URLフィルタリングの調整
   - `exclude_patterns`の設定を確認・修正

3. JavaScript制御サイトの対応
   - `crawler/crawler.py`の`process_page`メソッドで追加のJavaScript実行を実装

### LLM関連の問題

LLM解析が適切に動作しない場合の対処法：

1. APIキーの確認
   - 環境変数が正しく設定されているか確認

2. プロンプトの調整
   - `analyzer/llm_analyzer.py`の各分析メソッドのプロンプトを改善

3. モデルやパラメータの変更
   - `config.yaml`のLLM設定を調整

## 応用例

このシステムは以下のような用途に応用できます：

1. レガシーシステムの自動ドキュメント生成
2. 競合サイトの分析と比較
3. Web APIのリバースエンジニアリング
4. デザインリファレンスの自動収集
5. アクセシビリティチェックの自動化

## 注意事項

このツールを使用する際の注意点：

1. 対象システムの利用規約を遵守すること
2. 過剰なリクエストを送らないよう適切な待機時間を設定すること
3. 収集したデータの取り扱いに注意すること
4. API利用料金（LLM）に注意すること 