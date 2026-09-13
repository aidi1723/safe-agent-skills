#!/bin/bash
# Phase 4 部署到 n100 的完整脚本
# 请手动执行此脚本中的命令

set -e

echo "==================================================================="
echo "Phase 4 部署到 n100"
echo "==================================================================="
echo ""

echo "步骤 1: 确认部署包存在"
echo "-------------------------------------------------------------------"
if [ -f "phase4-deployment.tar.gz" ]; then
    echo "✓ 部署包已就绪: phase4-deployment.tar.gz ($(du -h phase4-deployment.tar.gz | cut -f1))"
else
    echo "✗ 错误: 部署包不存在"
    exit 1
fi
echo ""

echo "步骤 2: 在 n100 上创建目录"
echo "-------------------------------------------------------------------"
echo "执行: ssh n100 'mkdir -p ~/phase4-test'"
ssh n100 'mkdir -p ~/phase4-test'
echo "✓ 目录创建成功"
echo ""

echo "步骤 3: 上传部署包到 n100"
echo "-------------------------------------------------------------------"
echo "执行: scp phase4-deployment.tar.gz n100:~/phase4-test/"
scp phase4-deployment.tar.gz n100:~/phase4-test/
echo "✓ 上传成功"
echo ""

echo "步骤 4: 解压并验证"
echo "-------------------------------------------------------------------"
echo "执行远程命令..."
ssh n100 << 'ENDSSH'
cd ~/phase4-test
echo "当前目录: $(pwd)"
echo "解压部署包..."
tar -xzf phase4-deployment.tar.gz
echo ""
echo "文件清单:"
find . -type f | grep -v ".tar.gz" | head -20
echo ""
echo "✓ 解压完成"
ENDSSH
echo ""

echo "==================================================================="
echo "部署成功!"
echo "==================================================================="
echo ""
echo "下一步: SSH 到 n100 运行测试"
echo ""
echo "  ssh n100"
echo "  cd ~/phase4-test"
echo "  bash validate_phase4.sh"
echo ""
