# -*- coding: utf-8 -*-
"""
配置模板。

用法：把这个文件复制一份改名为 config.py，然后填上你自己的值。

    Windows:          copy config.example.py config.py
    macOS / Linux:    cp config.example.py config.py

config.py 已在 .gitignore 里，不会被提交 —— 密钥只留在你本机。
"""

# 1) 你的 API Key
#    DeepSeek 的 Key 在 https://platform.deepseek.com 申请。
API_KEY = "sk-在这里粘贴你的key"

# 2) 模型服务地址
#    DeepSeek 的接口完全兼容 OpenAI 的格式，所以换别家（OpenAI / 通义 / 智谱）
#    只需要改下面这两行，其余代码一个字都不用动。
BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-chat"

# 3) 你的 Obsidian 笔记库根目录
#    在 Obsidian 里右键任意笔记 → 在文件管理器中显示，看看它的上层目录。
VAULT_PATH = r"C:\你的\Obsidian\vault\路径"
