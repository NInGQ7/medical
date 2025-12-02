#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
医疗设备参数融合工具 - GUI应用
可视化界面，支持选择Excel文件进行参数融合
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog, QTextEdit,
    QProgressBar, QMessageBox, QTabWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QTextCursor, QTextCharFormat, QBrush
import pandas as pd
from main import MedicalDeviceFusion

class FusionWorker(QThread):
    """后台融合线程"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, input_file):
        super().__init__()
        self.input_file = input_file
    
    def run(self):
        try:
            self.progress.emit("正在初始化融合工具...")
            tool = MedicalDeviceFusion()
            
            self.progress.emit(f"正在处理文件: {self.input_file}")
            tool.process_excel(self.input_file)
            
            self.progress.emit("融合完成！")
            self.finished.emit(True, f"成功处理文件: {self.input_file}")
        except Exception as e:
            self.finished.emit(False, f"错误: {str(e)}")

class MedicalDeviceFusionGUI(QMainWindow):
    """医疗设备参数融合工具GUI"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("医疗设备参数融合工具")
        self.setGeometry(100, 100, 1000, 700)
        self.setStyleSheet(self.get_stylesheet())
        
        self.input_file = None
        self.worker = None
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        # 创建中心窗口
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建标签页
        tabs = QTabWidget()
        central_widget.layout = QVBoxLayout()
        central_widget.layout.addWidget(tabs)
        central_widget.setLayout(central_widget.layout)
        
        # 第一个标签页 - 融合工具
        fusion_widget = self.create_fusion_tab()
        tabs.addTab(fusion_widget, "融合工具")
        
        # 第二个标签页 - 说明
        info_widget = self.create_info_tab()
        tabs.addTab(info_widget, "使用说明")
    
    def create_fusion_tab(self):
        """创建融合工具标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("选择Excel文件进行参数融合")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 文件选择区域
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("输入文件:"))
        self.file_input = QLineEdit()
        self.file_input.setReadOnly(True)
        file_layout.addWidget(self.file_input)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.select_file)
        browse_btn.setMinimumWidth(100)
        file_layout.addWidget(browse_btn)
        layout.addLayout(file_layout)
        
        # 融合按钮
        fusion_btn = QPushButton("开始融合")
        fusion_btn.setMinimumHeight(40)
        fusion_btn.clicked.connect(self.start_fusion)
        fusion_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        layout.addWidget(fusion_btn)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 日志输出
        log_label = QLabel("处理日志:")
        log_label.setFont(QFont("Arial", 10))
        layout.addWidget(log_label)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(300)
        layout.addWidget(self.log_output)
        
        # 添加弹性空间
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def create_info_tab(self):
        """创建说明标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setText("""
        医疗设备参数融合工具 - 使用说明
        
        功能介绍：
        本工具用于融合多家供应商的医疗设备技术参数，
        自动识别和合并相同参数的不同表述形式。
        
        使用步骤：
        1. 点击"浏览..."按钮选择包含医疗设备参数的Excel文件
        2. 确保Excel文件格式正确：
           - 第一列：参数名称（如CPU、内存、硬盘等）
           - 第2-N列：各供应商提供的参数值
        3. 点击"开始融合"按钮启动融合过程
        4. 等待处理完成，融合结果将保存为新的Excel文件
        
        融合算法：
        • 精确匹配：多个相同的参数值
        • 高相似度融合：相似度≥80%的参数值
        • 中等相似度融合：相似度≥60%的参数值
        • 语义匹配：基于同义词库的参数匹配
        • 数字范围融合：纯数字参数的范围融合
        • 单位兼容性检查：防止不同单位的数据混合
        • 型号保护：防止产品型号被错误融合
        • 尺寸规格保护：防止尺寸规格被拆分
        • 误差容差保护：防止误差范围被错误处理
        
        输出文件：
        融合完成后，将在output目录下生成：
        - [文件名]_融合结果_[时间戳].xlsx：融合后的参数数据
        - fusion_log_[时间戳].txt：详细的融合日志
        
        支持的参数类型：
        • CPU、内存、硬盘等计算机硬件参数
        • 显示器、键盘等输入输出设备参数
        • 操作系统、软件版本等系统参数
        • 频率、功率等物理参数
        • 尺寸、重量等机械参数
        • 误差范围、精度等性能指标
        """)
        layout.addWidget(info_text)
        
        widget.setLayout(layout)
        return widget
    
    def select_file(self):
        """选择文件"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "选择Excel文件",
            "",
            "Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        
        if file_path:
            self.input_file = file_path
            self.file_input.setText(file_path)
            self.log_output.append(f"✓ 已选择文件: {file_path}")
    
    def start_fusion(self):
        """开始融合"""
        if not self.input_file:
            QMessageBox.warning(self, "警告", "请先选择一个Excel文件")
            return
        
        if not os.path.exists(self.input_file):
            QMessageBox.warning(self, "错误", "选定的文件不存在")
            return
        
        # 清空日志
        self.log_output.clear()
        self.log_output.append("=" * 50)
        self.log_output.append("开始融合过程...")
        self.log_output.append("=" * 50)
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 启动融合线程
        self.worker = FusionWorker(self.input_file)
        self.worker.progress.connect(self.update_log)
        self.worker.finished.connect(self.fusion_finished)
        self.worker.start()
    
    def update_log(self, message):
        """更新日志"""
        # 检查是否包含"需人工审核"
        if "需人工审核" in message:
            # 获取文本编辑器的文本光标
            cursor = self.log_output.textCursor()
            cursor.movePosition(QTextCursor.End)
            
            # 创建字符格式，设置黄色背景
            char_format = QTextCharFormat()
            char_format.setBackground(QBrush(QColor(255, 255, 0)))  # 黄色背景
            
            # 插入带格式的文本
            cursor.insertText(message + "\n", char_format)
            self.log_output.setTextCursor(cursor)
        else:
            self.log_output.append(message)
        
        # 自动滚动到底部
        self.log_output.verticalScrollBar().setValue(
            self.log_output.verticalScrollBar().maximum()
        )
    
    def fusion_finished(self, success, message):
        """融合完成"""
        self.progress_bar.setVisible(False)
        self.log_output.append("=" * 50)
        self.log_output.append(message)
        self.log_output.append("=" * 50)
        
        if success:
            QMessageBox.information(self, "成功", message)
        else:
            QMessageBox.critical(self, "失败", message)
    
    def get_stylesheet(self):
        """获取应用样式表"""
        return """
        QMainWindow {
            background-color: #f5f5f5;
        }
        QLabel {
            color: #333333;
        }
        QPushButton {
            border-radius: 3px;
            border: 1px solid #cccccc;
            padding: 5px;
            background-color: #ffffff;
        }
        QPushButton:hover {
            background-color: #e0e0e0;
        }
        QLineEdit, QTextEdit {
            border: 1px solid #cccccc;
            border-radius: 3px;
            padding: 5px;
            background-color: #ffffff;
        }
        QTabWidget::pane {
            border: 1px solid #cccccc;
        }
        QTabBar::tab {
            background-color: #e0e0e0;
            padding: 8px 20px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: #ffffff;
            border-bottom: 2px solid #4CAF50;
        }
        """

def main():
    app = QApplication(sys.argv)
    window = MedicalDeviceFusionGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
