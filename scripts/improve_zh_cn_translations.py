#!/usr/bin/env python3
"""
Improve zh-CN translations for Twenty CRM.
This script adds missing Chinese translations to the zh-CN.po file.
"""

import re
import os

ZH_CN_PO = "/Volumes/CachesDrive/twenty/packages/twenty-front/src/locales/zh-CN.po"

# Translations for untranslated strings
TRANSLATIONS = {
    # Time related
    "{0} used": "{0} 已使用",
    "12h": "12小时",
    "24h": "24小时",

    # Plural forms
    "{count, plural, one {E.g. {0}{1} for {count} decimal} other {E.g. {2}{3} for {count} decimals}}":
        "{count, plural, one {例如 {0}{1} 为 {count} 位小数} other {例如 {2}{3} 为 {count} 位小数}}",
    "{decimals, plural, one {E.g. {0} for {decimals} decimal} other {E.g. {1} for {decimals} decimals}}":
        "{decimals, plural, one {例如 {0} 为 {decimals} 位小数} other {例如 {1} 为 {decimals} 位小数}}",
    "{deletedCount, plural, one {Successfully deleted {deletedCount} job} other {Successfully deleted {deletedCount} jobs}}":
        "{deletedCount, plural, one {成功删除 {deletedCount} 个任务} other {成功删除 {deletedCount} 个任务}}",
    "{grantedBy, plural, one {Granted for {grantedBy} object} other {Granted for {grantedBy} objects}}":
        "{grantedBy, plural, one {已授予 {grantedBy} 个对象} other {已授予 {grantedBy} 个对象}}",
    "{jobCount, plural, one {Delete {jobCount} Job} other {Delete {jobCount} Jobs}}":
        "{jobCount, plural, one {删除 {jobCount} 个任务} other {删除 {jobCount} 个任务}}",
    "{jobCount, plural, one {Retry {jobCount} Job} other {Retry {jobCount} Jobs}}":
        "{jobCount, plural, one {重试 {jobCount} 个任务} other {重试 {jobCount} 个任务}}",
    "{jobCount, plural, one {This will permanently remove it from the queue. This action cannot be undone.} other {This will permanently remove them from the queue. This action cannot be undone.}}":
        "{jobCount, plural, one {这将永久从队列中删除它。此操作无法撤销。} other {这将永久从队列中删除它们。此操作无法撤销。}}",
    "{jobCount, plural, one {This will retry the selected job. It will be re-executed from the beginning.} other {This will retry the selected jobs. They will be re-executed from the beginning.}}":
        "{jobCount, plural, one {这将重试选定的任务。它将从头开始重新执行。} other {这将重试选定的任务。它们将从头开始重新执行。}}",
    "{retriedCount, plural, one {Successfully retried {retriedCount} job} other {Successfully retried {retriedCount} jobs}}":
        "{retriedCount, plural, one {成功重试 {retriedCount} 个任务} other {成功重试 {retriedCount} 个任务}}",
    "{revokedBy, plural, one {Revoked for {revokedBy} object} other {Revoked for {revokedBy} objects}}":
        "{revokedBy, plural, one {已撤销 {revokedBy} 个对象} other {已撤销 {revokedBy} 个对象}}",
    "{selectedCount, plural, one {Delete {selectedCount} Job} other {Delete {selectedCount} Jobs}}":
        "{selectedCount, plural, one {删除 {selectedCount} 个任务} other {删除 {selectedCount} 个任务}}",
    "{selectedCount, plural, one {Retry {selectedCount} Job} other {Retry {selectedCount} Jobs}}":
        "{selectedCount, plural, one {重试 {selectedCount} 个任务} other {重试 {selectedCount} 个任务}}",

    # Permissions
    "{permissionLabel} permission removed": "{permissionLabel} 权限已移除",
    "{permissionLabel} Permission removed": "{permissionLabel} 权限已移除",
    "Add permission": "添加权限",
    "Admin": "管理员",

    # Agents and AI
    "Agent interactions will appear here once the agent is used in conversations": "代理在对话中使用后，交互将显示在这里",
    "Agent roles": "代理角色",
    "agents": "代理",
    "Agents provided by this app": "此应用提供的代理",
    "Add test input for evaluation (e.g., \"Find all customers in NY\")": "添加测试输入进行评估（例如，\"查找纽约的所有客户\"）",
    "AI consumption across all workspaces.": "所有工作区的 AI 消耗。",
    "AI consumption over time.": "AI 消耗随时间变化。",
    "AI Usage": "AI 使用",
    "AI usage analytics across workspaces is available with an Enterprise key.": "跨工作区的 AI 使用分析需要企业版密钥。",
    "AI usage analytics is available with an Enterprise key.": "AI 使用分析需要企业版密钥。",
    "AI usage analytics requires ClickHouse. Contact your administrator.": "AI 使用分析需要 ClickHouse。请联系您的管理员。",
    "AI Usage by Model": "按模型分类的 AI 使用",
    "AI Usage by Type": "按类型分类的 AI 使用",
    "AI Usage by User": "按用户分类的 AI 使用",
    "AI Usage by Workspace": "按工作区分类的 AI 使用",
    "AI User Usage": "AI 用户使用",
    "AI Workflow": "AI 工作流",

    # Objects and Data
    "All objects": "所有对象",
    "API key name cannot be empty": "API 密钥名称不能为空",
    "API key roles": "API 密钥角色",
    "Apostrophe and dot": "撇号和点",
    "Application successfully uninstalled.": "应用已成功卸载。",
    "Are you sure you want to delete this evaluation input?": "您确定要删除此评估输入吗？",
    "Are you sure you want to delete this tool? This action cannot be undone.": "您确定要删除此工具吗？此操作无法撤销。",
    "Are you sure you want to destroy these {0}? They won't be recoverable anymore.": "您确定要销毁这些 {0} 吗？它们将无法恢复。",
    "Are you sure you want to destroy this {0}? It cannot be recovered anymore.": "您确定要销毁此 {0} 吗？它无法恢复。",
    "Are you sure you want to restore these {0}?": "您确定要恢复这些 {0} 吗？",
    "Are you sure you want to restore this {0}?": "您确定要恢复此 {0} 吗？",

    # MCP
    "Access your workspace data from your favorite MCP client like Claude Desktop, Windsurf or Cursor.":
        "从您喜欢的 MCP 客户端（如 Claude Desktop、Windsurf 或 Cursor）访问工作区数据。",

    # Charts
    "Aggregate Chart": "聚合图表",

    # Jobs
    "Job ID": "任务 ID",
    "Job Queue": "任务队列",
    "Jobs": "任务",

    # Settings
    "Settings saved": "设置已保存",

    # Views
    "View": "视图",
    "Views": "视图",

    # Records
    "Record": "记录",
    "Records": "记录",

    # Fields
    "Field": "字段",
    "Fields": "字段",

    # Users
    "User": "用户",
    "Users": "用户",

    # Workspaces
    "Workspace": "工作区",
    "Workspaces": "工作区",

    # Import/Export
    "Import": "导入",
    "Export": "导出",

    # Buttons and Actions
    "Cancel": "取消",
    "Save": "保存",
    "Delete": "删除",
    "Edit": "编辑",
    "Create": "创建",
    "Update": "更新",
    "Search": "搜索",
    "Filter": "筛选",
    "Sort": "排序",
    "Refresh": "刷新",

    # Status
    "Active": "激活",
    "Inactive": "未激活",
    "Pending": "待处理",
    "Completed": "已完成",
    "Failed": "失败",
    "Running": "运行中",

    # Errors
    "An error occurred": "发生错误",
    "Error": "错误",
    "Warning": "警告",
    "Success": "成功",
    "Info": "信息",

    # Confirmation
    "Confirm": "确认",
    "Yes": "是",
    "No": "否",
    "OK": "确定",

    # Navigation
    "Back": "返回",
    "Next": "下一步",
    "Previous": "上一步",
    "Close": "关闭",

    # Forms
    "Required": "必填",
    "Optional": "可选",
    "Name": "名称",
    "Description": "描述",
    "Type": "类型",
    "Value": "值",
    "Label": "标签",

    # Date/Time
    "Date": "日期",
    "Time": "时间",
    "Created": "创建时间",
    "Updated": "更新时间",

    # Empty states
    "No data": "暂无数据",
    "No results": "暂无结果",
    "No items": "暂无项目",

    # Common
    "Loading": "加载中",
    "Loading...": "加载中...",
    "More": "更多",
    "Less": "收起",
    "Show more": "显示更多",
    "Show less": "显示更少",
    "All": "全部",
    "None": "无",
    "Default": "默认",
    "Custom": "自定义",
}

def update_po_file():
    """Update the zh-CN.po file with translations."""
    with open(ZH_CN_PO, 'r', encoding='utf-8') as f:
        content = f.read()

    updated_count = 0

    for msgid, msgstr in TRANSLATIONS.items():
        # Escape special characters in msgid for regex
        escaped_msgid = re.escape(msgid)

        # Pattern to find untranslated string
        pattern = rf'(^msgid "{escaped_msgid}"\n^msgstr ""$)'

        # Check if this string exists and is untranslated
        if re.search(rf'msgid "{escaped_msgid}"\nmsgstr ""', content, re.MULTILINE):
            replacement = f'msgid "{msgid}"\nmsgstr "{msgstr}"'
            content = re.sub(
                rf'msgid "{escaped_msgid}"\nmsgstr ""',
                replacement,
                content,
                flags=re.MULTILINE
            )
            updated_count += 1
            print(f"Translated: {msgid[:50]}...")

    with open(ZH_CN_PO, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\nUpdated {updated_count} translations")

if __name__ == "__main__":
    update_po_file()