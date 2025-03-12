#!/bin/bash

# Web自動解析システム - GUI起動スクリプト

# 仮想環境がある場合はアクティベート
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Streamlitアプリケーションを起動
streamlit run app.py 