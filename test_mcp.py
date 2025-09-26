#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化的 MCP Server 測試版本
"""

import sys
from mcp.server.fastmcp import FastMCP

# 初始化 MCP server
mcp = FastMCP("Test Stock Analysis Server")

@mcp.tool()
def hello_world() -> str:
    """
    測試工具：返回 Hello World

    Returns:
        簡單的問候語
    """
    return "Hello from Taiwan Stock Analysis MCP Server!"

@mcp.tool()
def get_server_status() -> dict:
    """
    獲取伺服器狀態

    Returns:
        伺服器狀態信息
    """
    return {
        "status": "running",
        "server": "Taiwan Stock Analysis",
        "version": "1.0.0"
    }

def main():
    """啟動簡化的 MCP server"""
    try:
        print("正在啟動簡化的 MCP Server...", file=sys.stderr)
        print("Server 名稱: Test Stock Analysis Server", file=sys.stderr)
        print("可用工具: hello_world, get_server_status", file=sys.stderr)
        print("正在等待連接...", file=sys.stderr)

        # 啟動 MCP server
        mcp.run(transport="stdio")

    except Exception as e:
        print(f"MCP Server 啟動失敗: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return

if __name__ == "__main__":
    main()