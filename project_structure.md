# Web自動解析システム - プロジェクト構造

```
AutoAnalyzeSystem/
├── README.md                     # プロジェクト概要
├── requirements.txt              # 依存パッケージリスト
├── config.yaml                   # 設定ファイル
├── main.py                       # メインエントリーポイント
├── crawler/                      # Webクローリングモジュール
│   ├── __init__.py
│   ├── login.py                  # 自動ログイン機能
│   ├── crawler.py                # 画面クローリング機能
│   ├── screenshot.py             # スクリーンショット取得機能
│   └── storage.py                # HTML・画像保存機能
├── analyzer/                     # 解析モジュール
│   ├── __init__.py
│   ├── html_parser.py            # HTML解析機能
│   ├── llm_analyzer.py           # LLMを使った解析機能
│   └── doc_generator.py          # ドキュメント生成機能
├── data_extractor/               # データ抽出モジュール
│   ├── __init__.py
│   ├── data_finder.py            # データ検出機能
│   └── downloader.py             # データダウンロード機能
└── utils/                        # ユーティリティ
    ├── __init__.py
    ├── logger.py                 # ロギング
    └── helpers.py                # ヘルパー関数
``` 