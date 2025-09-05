#!/bin/bash

# GitHub自动推送脚本
# 用于自动化推送股票分析系统到GitHub

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}    GitHub 自动推送脚本${NC}"
    echo -e "${BLUE}    A股散户分析系统${NC}"
    echo -e "${BLUE}================================${NC}"
}

# 检查Git状态
check_git_status() {
    print_message "检查Git状态..."
    
    if [ ! -d ".git" ]; then
        print_error "当前目录不是Git仓库"
        exit 1
    fi
    
    # 检查是否有未提交的更改
    if ! git diff-index --quiet HEAD --; then
        print_warning "检测到未提交的更改"
        git status --porcelain
        
        read -p "是否要提交这些更改？(y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git add .
            read -p "请输入提交信息: " commit_message
            git commit -m "$commit_message"
        else
            print_error "请先提交或暂存更改"
            exit 1
        fi
    fi
    
    print_message "Git状态检查完成"
}

# 检查Git配置
check_git_config() {
    print_message "检查Git配置..."
    
    git_user=$(git config user.name 2>/dev/null || echo "")
    git_email=$(git config user.email 2>/dev/null || echo "")
    
    if [ -z "$git_user" ] || [ -z "$git_email" ]; then
        print_warning "Git用户信息未配置"
        
        read -p "请输入GitHub用户名: " username
        read -p "请输入GitHub邮箱: " email
        
        git config user.name "$username"
        git config user.email "$email"
        
        print_message "Git用户信息已配置"
    else
        print_message "Git用户: $git_user <$git_email>"
    fi
}

# 配置远程仓库
setup_remote() {
    print_message "配置GitHub远程仓库..."
    
    # 检查是否已配置origin
    if git remote get-url origin >/dev/null 2>&1; then
        current_origin=$(git remote get-url origin)
        print_message "已配置远程仓库: $current_origin"
        
        read -p "是否要更改远程仓库地址？(y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            read -p "请输入新的GitHub仓库地址: " repo_url
            git remote set-url origin "$repo_url"
            print_message "远程仓库地址已更新"
        fi
    else
        print_warning "未配置远程仓库"
        
        echo "请选择仓库地址格式："
        echo "1. HTTPS: https://github.com/username/stock_analysis.git"
        echo "2. SSH: git@github.com:username/stock_analysis.git"
        
        read -p "选择格式 (1/2): " -n 1 -r
        echo
        
        if [[ $REPLY == "1" ]]; then
            read -p "请输入GitHub用户名: " github_user
            repo_url="https://github.com/$github_user/stock_analysis.git"
        elif [[ $REPLY == "2" ]]; then
            read -p "请输入GitHub用户名: " github_user
            repo_url="git@github.com:$github_user/stock_analysis.git"
        else
            print_error "无效选择"
            exit 1
        fi
        
        git remote add origin "$repo_url"
        print_message "远程仓库已配置: $repo_url"
    fi
}

# 推送到GitHub
push_to_github() {
    print_message "推送到GitHub..."
    
    # 获取当前分支
    current_branch=$(git rev-parse --abbrev-ref HEAD)
    print_message "当前分支: $current_branch"
    
    # 检查远程分支是否存在
    if git ls-remote --exit-code --heads origin "$current_branch" >/dev/null 2>&1; then
        print_message "推送到现有分支..."
        git push origin "$current_branch"
    else
        print_message "推送到新分支..."
        git push -u origin "$current_branch"
    fi
    
    print_message "推送完成！"
}

# 显示结果
show_result() {
    local repo_url=$(git remote get-url origin)
    local github_url=""
    
    # 转换为浏览器访问地址
    if [[ $repo_url == git@github.com:* ]]; then
        github_url="https://github.com/${repo_url#git@github.com:}"
        github_url="${github_url%.git}"
    elif [[ $repo_url == https://github.com/* ]]; then
        github_url="${repo_url%.git}"
    fi
    
    echo
    print_message "🎉 推送成功！"
    echo
    echo -e "${BLUE}仓库地址:${NC} $github_url"
    echo -e "${BLUE}克隆命令:${NC} git clone $repo_url"
    echo
    echo -e "${GREEN}项目特色:${NC}"
    echo "  📊 完整的A股分析系统"
    echo "  🐳 Docker一键部署"
    echo "  ☁️  阿里云部署支持"
    echo "  📈 海龟交易策略"
    echo "  🔒 免费数据源"
    echo
    echo -e "${YELLOW}下一步操作:${NC}"
    echo "  1. 在GitHub上设置仓库描述和标签"
    echo "  2. 启用Issues和Discussions"
    echo "  3. 设置GitHub Pages（如果需要）"
    echo "  4. 配置GitHub Actions自动化部署"
    echo "  5. 邀请协作者"
}

# 检查网络连接
check_network() {
    print_message "检查网络连接..."
    
    if ! ping -c 1 github.com >/dev/null 2>&1; then
        print_error "无法连接到GitHub，请检查网络连接"
        exit 1
    fi
    
    print_message "网络连接正常"
}

# 验证推送结果
verify_push() {
    print_message "验证推送结果..."
    
    local remote_commits=$(git ls-remote origin HEAD | cut -f1)
    local local_commits=$(git rev-parse HEAD)
    
    if [ "$remote_commits" = "$local_commits" ]; then
        print_message "✅ 验证成功：远程和本地代码同步"
    else
        print_warning "⚠️  远程和本地代码可能不同步"
    fi
}

# 主函数
main() {
    print_header
    
    # 检查参数
    case "${1:-}" in
        "force")
            print_warning "强制推送模式"
            ;;
        "help"|"-h"|"--help")
            echo "用法: $0 [force|help]"
            echo "  force  - 强制推送（跳过某些检查）"
            echo "  help   - 显示帮助信息"
            exit 0
            ;;
    esac
    
    # 执行推送流程
    check_network
    check_git_config
    check_git_status
    setup_remote
    push_to_github
    verify_push
    show_result
    
    echo
    print_message "所有操作完成！"
}

# 错误处理
trap 'echo -e "\n${RED}脚本执行被中断${NC}"; exit 1' INT TERM

# 执行主函数
main "$@"