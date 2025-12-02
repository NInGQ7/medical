#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
启动医疗设备参数融合工具GUI应用
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

if __name__ == '__main__':
    from gui_app import main
    main()
