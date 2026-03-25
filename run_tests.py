#!/usr/bin/env python3
"""
测试运行脚本
运行认证系统的所有测试
"""

import subprocess
import sys
import os


def run_tests():
    """运行所有测试"""
    print("🚀 开始运行认证系统测试...")

    # 添加当前目录到Python路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)

    # 运行pytest
    cmd = [
        sys.executable, "-m", "pytest",
        "app/test/",
        "-v",  # 详细输出
        "--tb=short",  # 简短的错误回溯
        "--cov=app",  # 覆盖率报告
        "--cov-report=term-missing",  # 显示缺失的覆盖率
        "--cov-report=html",  # 生成HTML覆盖率报告
        "--cov-fail-under=80",  # 覆盖率低于80%时失败
    ]

    print(f"运行命令: {' '.join(cmd)}")
    print("-" * 80)

    result = subprocess.run(cmd, capture_output=False)

    print("-" * 80)
    if result.returncode == 0:
        print("✅ 所有测试通过！")
    else:
        print("❌ 测试失败！")

    return result.returncode


def run_specific_test(test_path):
    """运行特定测试"""
    print(f"🚀 运行特定测试: {test_path}")

    cmd = [
        sys.executable, "-m", "pytest",
        test_path,
        "-v",
        "--tb=short",
    ]

    print(f"运行命令: {' '.join(cmd)}")
    print("-" * 80)

    result = subprocess.run(cmd, capture_output=False)

    print("-" * 80)
    if result.returncode == 0:
        print("✅ 测试通过！")
    else:
        print("❌ 测试失败！")

    return result.returncode


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 运行特定测试
        test_path = sys.argv[1]
        exit_code = run_specific_test(test_path)
    else:
        # 运行所有测试
        exit_code = run_tests()

    sys.exit(exit_code)