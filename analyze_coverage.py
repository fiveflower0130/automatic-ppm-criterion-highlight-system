#!/usr/bin/env python3
"""
測試覆蓋率分析工具
分析 backup_service.py 的測試覆蓋情況
"""

import ast
import os
from typing import Dict, List, Set

def analyze_test_coverage():
    """分析測試覆蓋率"""
    
    # 讀取原始程式碼
    service_file = "app/services/backup_service.py"
    test_file = "app/tests/services/test_backup_service.py"
    
    if not os.path.exists(service_file):
        print(f"❌ 找不到服務檔案: {service_file}")
        return
        
    if not os.path.exists(test_file):
        print(f"❌ 找不到測試檔案: {test_file}")
        return
    
    # 分析原始程式碼
    with open(service_file, 'r', encoding='utf-8') as f:
        service_content = f.read()
    
    with open(test_file, 'r', encoding='utf-8') as f:
        test_content = f.read()
    
    # 使用 AST 分析
    service_tree = ast.parse(service_content)
    test_tree = ast.parse(test_content)
    
    # 提取類別和方法
    service_classes = {}
    service_functions = []
    
    for node in ast.walk(service_tree):
        if isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    methods.append(item.name)
            service_classes[node.name] = methods
        elif isinstance(node, ast.FunctionDef) and node.name not in [m for methods in service_classes.values() for m in methods]:
            service_functions.append(node.name)
    
    # 提取測試方法
    test_methods = []
    for node in ast.walk(test_tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
            test_methods.append(node.name)
    
    # 產生報告
    print("🧪 **Backup Service 測試覆蓋率分析**")
    print("=" * 60)
    
    print(f"📁 **檔案路徑**:")
    print(f"   服務檔案: {service_file}")
    print(f"   測試檔案: {test_file}")
    print()
    
    print(f"📊 **統計資訊**:")
    print(f"   發現的類別數: {len(service_classes)}")
    print(f"   發現的測試方法數: {len(test_methods)}")
    print()
    
    print("🎯 **類別覆蓋情況**:")
    for class_name, methods in service_classes.items():
        print(f"   📂 {class_name}:")
        print(f"      方法數: {len(methods)}")
        print(f"      方法清單: {', '.join(methods)}")
        
        # 檢查測試覆蓋
        class_tests = [t for t in test_methods if class_name.lower() in t.lower()]
        print(f"      相關測試數: {len(class_tests)}")
        print()
    
    print("🧩 **測試方法清單**:")
    for test_method in sorted(test_methods):
        print(f"   ✅ {test_method}")
    
    print()
    print("📈 **覆蓋率評估**:")
    total_methods = sum(len(methods) for methods in service_classes.values())
    print(f"   總方法數: {total_methods}")
    print(f"   測試方法數: {len(test_methods)}")
    print(f"   覆蓋率估算: {len(test_methods) / max(total_methods, 1) * 100:.1f}%")

if __name__ == "__main__":
    analyze_test_coverage()