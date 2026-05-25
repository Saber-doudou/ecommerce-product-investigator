"""pytest 公共配置 — 统一 sys.path 和 fixtures"""
import sys
import os

# 将 scripts/ 目录加入 sys.path，所有测试文件可直接 import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
