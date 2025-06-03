# Using the LLM to analyze Taiwan Stocks with the MCP Server

## 簡介
台灣股票趨勢與購買建議分析系統，使用 FastMCP 套件實作 Model Context Protocol (MCP) Server，並結合大型語言模型 (LLM) 提供更智能的分析能力。此系統能根據股票的技術指標、趨勢判斷、支撐與阻力位，生成購買建議，並支持多支股票的批量分析。

![台灣股票分析系統截圖](media/twstock_mcp_screenshot.png)

## 功能展示
觀看示範影片了解系統功能：

[![示範影片]](media/twstock_mcp_video.mp4)

## 核心概念
此系統透過 MCP Server 與 LLM 的結合，實現以下功能：
- MCP Server 作為中介，提供股票分析工具的接口。
- LLM 負責解讀使用者的自然語言指令，並調用 MCP Server 的工具進行分析。
- 分析結果以結構化格式返回，供使用者進一步操作或決策。

## 功能
- **股票基本資訊查詢**：獲取股票代碼、名稱、產業分類等基本資訊。
- **單支股票分析**：分析股票的技術指標、趨勢判斷、支撐與阻力位，以及購買建議。
- **批量股票分析**：一次分析多支股票，並返回分析結果列表。
- **關鍵字搜尋股票**：根據股票名稱或代碼的一部分進行搜尋。
- **產業分類篩選股票**：根據指定的產業分類篩選股票。
- **推薦摘要**：根據分析結果生成推薦摘要，按信心度排序。

## 系統需求
- Python 3.10+
- 相依套件 (見 requirements.txt)
- 使用 `uv` 管理開發環境

## 安裝步驟
1. 複製專案
```bash
git clone https://github.com/yourusername/taiwan-stock-analysis.git
cd taiwan-stock-analysis
```

2. 使用 `uv` 管理開發環境
   - 安裝 `uv`：
     ```bash
     pip install uv
     ```
   - 初始化開發環境：
     ```bash
     uv init
     ```
   - 安裝相依套件：
     ```bash
     uv sync
     ```

## 使用說明
### 啟動 MCP Server
使用 `uv` 啟動 MCP Server：
```bash
uv run twstock_mcp.py
```

### 在 Cline Host 設置 MCP Server
若使用 Cline Host，請在設定檔中新增以下內容：
```json
"taiwan-stock-analysis": {
  "disabled": false,
  "timeout": 60,
  "command": "uv",
  "args": [
    "--directory",
    "/Users/pololin/twstock_analysis",
    "run",
    "twstock_mcp.py"
  ],
  "transportType": "stdio"
}
```

### API 功能說明
1. **單支股票分析**
```python
result = analyze_stock("2330", months=3)
```
返回格式：
```python
{
    "success": True,
    "data": {
        "stock_info": {...},
        "technical_indicators": {...},
        "recommendations": {...}
    }
}
```

2. **批量股票分析**
```python
result = analyze_multiple_stocks(["2330", "2317", "2454"], months=3)
```
返回格式：
```python
{
    "success": True,
    "data": {
        "results": [...],
        "errors": [...],
        "total_analyzed": 3,
        "total_errors": 0
    }
}
```

## 專案架構
```
taiwan-stock-analysis/
├── twstock_mcp.py      # 主程式
├── requirements.txt    # 相依套件清單
├── README.md          # 說明文件
└── media/             # 圖片與影片
    ├── twstock_mcp_screenshot.png
    ├── twstock_mcp_video.mov
└── tests/             # 測試程式碼
```

## 技術指標說明
- RSI (相對強弱指標)
- MACD (移動平均收斂/發散指標)
- 布林通道 (Bollinger Bands)
- 移動平均線 (MA)

## 開發者指南
### 新增分析工具
1. 在 TaiwanStockAnalyzer 類別中實作新方法
2. 使用 @mcp.tool() 裝飾器註冊新工具
3. 在主程式中新增相應的處理邏輯

## 常見問題
1. Q: 為什麼無法取得股票資料？
   A: 請確認網路連線正常，且 twstock 套件設定正確。

2. Q: 如何自訂技術指標參數？
   A: 可以修改相應方法中的預設參數。

## 貢獻指南
1. Fork 此專案
2. 建立特性分支 (git checkout -b feature/AmazingFeature)
3. 提交變更 (git commit -m 'Add some AmazingFeature')
4. 推送至分支 (git push origin feature/AmazingFeature)
5. 開啟 Pull Request

## 授權條款
本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案

## 作者
- [Your Name](https://github.com/yourusername)

## 致謝
- [twstock](https://github.com/mlouielu/twstock)
- [FastMCP](https://github.com/microsoft/FastMCP)
- [TA-Lib](https://github.com/mrjbq7/ta-lib)