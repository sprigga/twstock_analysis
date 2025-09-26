#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台灣股票趨勢與購買建議分析系統 - MCP Server
使用 FastMCP 套件實作 Model Context Protocol server
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta


# 股票分析相關套件
import twstock
import pandas as pd
import matplotlib

# 設定 matplotlib 後端為非互動式
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import mplfinance as mpf
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands


# FastMCP 套件
from mcp.server.fastmcp import FastMCP

# 初始化 MCP server
mcp = FastMCP("Taiwan Stock Analysis Server")


class TaiwanStockAnalyzer:
    """台灣股票分析器"""

    def __init__(self):
        """初始化分析器"""
        self.stock_list = twstock.codes
        self.analyzed_stocks = {}

    def get_stock_info(self, stock_id: str) -> Optional[Dict]:
        """獲取股票基本信息"""
        if stock_id in self.stock_list:
            info = self.stock_list[stock_id]
            return {
                "code": stock_id,
                "name": getattr(info, "name", f"未知_{stock_id}"),
                "group": getattr(info, "group", "未知"),
                "market": getattr(info, "market", "未知"),
            }
        return None

    def get_stock_historical_data(
        self, stock_id: str, months: int = 3, max_retries: int = 3
    ):
        """獲取股票歷史數據，包含重試邏輯"""
        for attempt in range(max_retries):
            try:
                print(
                    f"正在獲取 {stock_id} 的歷史數據 (嘗試 {attempt + 1}/{max_retries})..."
                )
                stock = twstock.Stock(stock_id)
                current_date = datetime.now()

                # 計算目標月份
                target_month = current_date.month - months
                target_year = current_date.year

                if target_month <= 0:
                    target_month += 12
                    target_year -= 1

                # 設定超時時間 (30秒)
                import signal

                def timeout_handler(signum, frame):
                    raise TimeoutError("數據獲取超時")

                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(30)  # 30秒超時

                try:
                    stock.fetch_from(target_year, target_month)
                    signal.alarm(0)  # 取消超時
                except TimeoutError:
                    signal.alarm(0)  # 取消超時
                    raise TimeoutError(f"獲取 {stock_id} 數據超時")

                if not stock.date or not stock.capacity or not stock.price:
                    print(f"警告: {stock_id} 數據不完整，缺少必要欄位")
                    return None

                print(f"成功獲取 {stock_id} 的歷史數據，共 {len(stock.date)} 筆記錄")
                return stock

            except TimeoutError as e:
                print(f"第 {attempt + 1} 次嘗試獲取 {stock_id} 數據超時: {str(e)}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # 漸增等待時間
                    print(f"等待 {wait_time} 秒後重試...")
                    time.sleep(wait_time)
                else:
                    print(f"已達最大重試次數，放棄獲取 {stock_id} 數據")
                    return None

            except Exception as e:
                print(
                    f"第 {attempt + 1} 次嘗試獲取 {stock_id} 數據時發生錯誤: {str(e)}"
                )
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"等待 {wait_time} 秒後重試...")
                    time.sleep(wait_time)
                else:
                    print(f"已達最大重試次數，放棄獲取 {stock_id} 數據")
                    return None

        return None

    def calculate_technical_indicators(self, stock) -> Dict:
        """計算技術指標：RSI、MACD、布林通道"""
        df = pd.DataFrame(
            {
                "Date": [d.strftime("%Y-%m-%d") for d in stock.date],
                "Open": stock.open,
                "High": stock.high,
                "Low": stock.low,
                "Close": stock.close,
                "Volume": stock.capacity,
            }
        )
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date")

        # RSI (14日)
        rsi = RSIIndicator(df["Close"], window=14).rsi()

        # MACD (快線12，慢線26，訊號線9)
        macd = MACD(df["Close"], window_slow=26, window_fast=12, window_sign=9)
        macd_line = macd.macd()
        macd_signal = macd.macd_signal()
        macd_hist = macd.macd_diff()

        # 布林通道 (20日，2個標準差)
        bb = BollingerBands(df["Close"], window=20, window_dev=2)
        bb_upper = bb.bollinger_hband()
        bb_lower = bb.bollinger_lband()
        bb_mid = bb.bollinger_mavg()

        return {
            "rsi": rsi,
            "macd_line": macd_line,
            "macd_signal": macd_signal,
            "macd_hist": macd_hist,
            "bb_upper": bb_upper,
            "bb_lower": bb_lower,
            "bb_mid": bb_mid,
            "df": df,
        }

    def calculate_ma(self, stock, days: int):
        """計算移動平均線"""
        prices = stock.price
        dates = stock.date

        if not prices or len(prices) < days:
            return [], []

        # 過濾掉 None 值
        valid_prices = [p for p in prices if p is not None]
        valid_dates = [d for d, p in zip(dates, prices) if p is not None]

        if len(valid_prices) < days:
            return [], []

        ma = []
        ma_dates = []

        for i in range(len(valid_prices) - days + 1):
            window_prices = valid_prices[i : i + days]
            if all(p is not None for p in window_prices):
                ma.append(sum(window_prices) / days)
                ma_dates.append(valid_dates[i + days - 1])

        return ma, ma_dates

    def calculate_support_resistance(self, stock):
        """計算支撐與阻力位"""
        if not stock.price or len(stock.price) < 20:
            return (0, 0)

        recent_prices = stock.price[-20:]
        # 過濾掉 None 值
        valid_prices = [p for p in recent_prices if p is not None]

        if len(valid_prices) < 5:  # 至少需要5個有效數據點
            return (0, 0)

        recent_low = min(valid_prices)
        recent_high = max(valid_prices)

        support = round(recent_low * 0.99, 2)
        resistance = round(recent_high * 1.01, 2)

        return (support, resistance)

    def analyze_stock(self, stock_id: str, months: int = 3) -> Optional[Dict]:
        """分析股票"""
        try:
            # 檢查是否為有效的股票代碼
            if stock_id not in self.stock_list:
                return None

            # 獲取股票數據
            stock = self.get_stock_historical_data(stock_id, months)
            if stock is None:
                return None

            # 使用 twstock 內置的分析工具進行分析
            bfp = twstock.BestFourPoint(stock)
            bfp_buy = bfp.best_four_point_to_buy()
            bfp_sell = bfp.best_four_point_to_sell()

            # 使用 Moving Average 判斷趨勢
            ma5, _ = self.calculate_ma(stock, 5)
            ma10, _ = self.calculate_ma(stock, 10)
            ma20, _ = self.calculate_ma(stock, 20)
            ma60, _ = self.calculate_ma(stock, 60)

            # 計算技術指標
            indicators = self.calculate_technical_indicators(stock)
            rsi = indicators["rsi"]
            macd_line = indicators["macd_line"]
            macd_signal = indicators["macd_signal"]
            bb_upper = indicators["bb_upper"]
            bb_lower = indicators["bb_lower"]

            # 簡易趨勢判斷
            trend = "盤整"
            if len(ma5) > 10 and len(ma20) > 10:
                if ma5[-1] > ma20[-1] and ma5[-5] < ma20[-5]:
                    trend = "上升"
                elif ma5[-1] < ma20[-1] and ma5[-5] > ma20[-5]:
                    trend = "下降"
                elif all(ma5[-i] > ma20[-i] for i in range(1, min(6, len(ma5)))):
                    trend = "強勢上升"
                elif all(ma5[-i] < ma20[-i] for i in range(1, min(6, len(ma5)))):
                    trend = "強勢下降"

            # 計算波動率
            volatility = 0
            if stock.price and len(stock.price) > 20:
                valid_prices = [p for p in stock.price[-20:] if p is not None]
                if len(valid_prices) > 5:
                    price_series = pd.Series(valid_prices)
                    pct_change_std = price_series.pct_change().std()
                    if pd.notna(pct_change_std):
                        volatility = pct_change_std * 100

            # 交易量分析
            volume_increase = False
            if stock.capacity and len(stock.capacity) > 10:
                recent_volumes = [v for v in stock.capacity[-10:] if v is not None]
                if len(recent_volumes) >= 10:
                    avg_volume_5 = sum(recent_volumes[-5:]) / 5
                    avg_volume_prev_5 = sum(recent_volumes[-10:-5]) / 5
                    volume_increase = avg_volume_5 > avg_volume_prev_5 * 1.2

            # 整體推薦
            recommendation = "觀望"
            confidence = 0

            # 使用四大買點與賣點
            if bfp_buy:
                recommendation = "買入"
                confidence = 70
                if trend in ["上升", "強勢上升"]:
                    confidence += 10
                if volume_increase:
                    confidence += 10
            elif bfp_sell:
                recommendation = "賣出"
                confidence = 70
                if trend in ["下降", "強勢下降"]:
                    confidence += 10

            # RSI 分析
            rsi_value = rsi.iloc[-1] if not rsi.empty else None
            rsi_signal = None
            if rsi_value is not None:
                if rsi_value < 30:
                    rsi_signal = "超賣（買入）"
                    if recommendation == "觀望":
                        recommendation = "買入"
                        confidence = 60
                    elif recommendation == "買入":
                        confidence += 10
                elif rsi_value > 70:
                    rsi_signal = "超買（賣出）"
                    if recommendation == "觀望":
                        recommendation = "賣出"
                        confidence = 60
                    elif recommendation == "賣出":
                        confidence += 10

            # MACD 分析
            macd_signal_value = None
            if not macd_line.empty and not macd_signal.empty:
                if len(macd_line) >= 2 and len(macd_signal) >= 2:
                    if (
                        macd_line.iloc[-1] > macd_signal.iloc[-1]
                        and macd_line.iloc[-2] < macd_signal.iloc[-2]
                    ):
                        macd_signal_value = "黃金交叉（買入）"
                        if recommendation == "觀望":
                            recommendation = "買入"
                            confidence = 65
                        elif recommendation == "買入":
                            confidence += 15
                    elif (
                        macd_line.iloc[-1] < macd_signal.iloc[-1]
                        and macd_line.iloc[-2] > macd_signal.iloc[-2]
                    ):
                        macd_signal_value = "死亡交叉（賣出）"
                        if recommendation == "觀望":
                            recommendation = "賣出"
                            confidence = 65
                        elif recommendation == "賣出":
                            confidence += 15

            # 布林通道分析
            bb_signal = None
            current_price = stock.price[-1] if stock.price else 0
            if not bb_upper.empty and not bb_lower.empty:
                if current_price <= bb_lower.iloc[-1]:
                    bb_signal = "觸及下軌（買入）"
                    if recommendation == "觀望":
                        recommendation = "買入"
                        confidence = 60
                    elif recommendation == "買入":
                        confidence += 10
                elif current_price >= bb_upper.iloc[-1]:
                    bb_signal = "觸及上軌（賣出）"
                    if recommendation == "觀望":
                        recommendation = "賣出"
                        confidence = 60
                    elif recommendation == "賣出":
                        confidence += 10

            # 計算支撐與阻力
            support, resistance = self.calculate_support_resistance(stock)

            # 取得股票資訊
            stock_info = self.stock_list[stock_id]

            # 構建結果
            result = {
                "stock_id": stock_id,
                "name": getattr(stock_info, "name", f"未知_{stock_id}"),
                "group": getattr(stock_info, "group", "未知"),
                "current_price": current_price,
                "trend": trend,
                "volatility": round(volatility, 2) if volatility else 0,
                "volume_increase": volume_increase,
                "best_buy_point": bfp_buy,
                "best_sell_point": bfp_sell,
                "recommendation": recommendation,
                "confidence": min(confidence, 100),
                "support": support,
                "resistance": resistance,
                "rsi": round(rsi_value, 2) if rsi_value is not None else None,
                "rsi_signal": rsi_signal,
                "macd_signal": macd_signal_value,
                "bb_signal": bb_signal,
                "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            self.analyzed_stocks[stock_id] = result
            return result
        except Exception as e:
            import traceback
            print(f"分析股票 {stock_id} 時發生錯誤: {str(e)}")
            traceback.print_exc()
            return None


# 創建分析器實例（延遲初始化）
analyzer = None

def get_analyzer():
    """延遲初始化分析器"""
    global analyzer
    if analyzer is None:
        analyzer = TaiwanStockAnalyzer()
    return analyzer


@mcp.tool()
def get_stock_info(stock_id: str) -> Dict[str, Any]:
    """
    獲取股票基本資訊

    Args:
        stock_id: 股票代碼 (例如: 2330)

    Returns:
        股票基本資訊，包含代碼、名稱、產業分類等
    """
    try:
        analyzer = get_analyzer()
        info = analyzer.get_stock_info(stock_id)
        if info:
            return {"success": True, "data": info}
        else:
            return {"success": False, "error": f"找不到股票代碼 {stock_id} 的資訊"}
    except Exception as e:
        return {"success": False, "error": f"獲取股票資訊時發生錯誤: {str(e)}"}


@mcp.tool()
def analyze_stock(stock_id: str, months: int = 3) -> Dict[str, Any]:
    """
    分析單支股票的趨勢與購買建議

    Args:
        stock_id: 股票代碼 (例如: 2330)
        months: 分析幾個月的歷史資料 (預設: 3)

    Returns:
        完整的股票分析結果，包含技術指標、趨勢判斷、購買建議等
    """
    try:
        analyzer = get_analyzer()
        result = analyzer.analyze_stock(stock_id, months)
        if result:
            return {"success": True, "data": result}
        else:
            return {
                "success": False,
                "error": f"無法分析股票 {stock_id}，可能是無效的股票代碼或數據不足",
            }
    except Exception as e:
        return {"success": False, "error": f"分析股票 {stock_id} 時發生錯誤: {str(e)}"}


@mcp.tool()
def analyze_multiple_stocks(stock_ids: List[str], months: int = 3) -> Dict[str, Any]:
    """
    批量分析多支股票

    Args:
        stock_ids: 股票代碼列表 (例如: ["2330", "2317", "2454"])
        months: 分析幾個月的歷史資料 (預設: 3)

    Returns:
        多支股票的分析結果列表
    """
    try:
        results = []
        errors = []

        analyzer = get_analyzer()
        for stock_id in stock_ids:
            try:
                result = analyzer.analyze_stock(stock_id, months)
                if result:
                    results.append(result)
                else:
                    errors.append(f"無法分析股票 {stock_id}")
            except Exception as e:
                errors.append(f"分析股票 {stock_id} 時發生錯誤: {str(e)}")

        return {
            "success": True,
            "data": {
                "results": results,
                "errors": errors,
                "total_analyzed": len(results),
                "total_errors": len(errors),
            },
        }
    except Exception as e:
        return {"success": False, "error": f"批量分析時發生錯誤: {str(e)}"}


@mcp.tool()
def search_stocks_by_keyword(keyword: str) -> Dict[str, Any]:
    """
    根據關鍵字搜尋股票

    Args:
        keyword: 搜尋關鍵字 (可以是股票名稱或代碼的一部分)

    Returns:
        符合關鍵字的股票列表
    """
    try:
        results = []
        keyword_lower = keyword.lower()

        analyzer = get_analyzer()
        for code, info in analyzer.stock_list.items():
            name = getattr(info, "name", "")
            group = getattr(info, "group", "未知")

            if keyword_lower in name.lower() or keyword_lower in code.lower():
                results.append({"code": code, "name": name, "group": group})

        return {
            "success": True,
            "data": {"keyword": keyword, "results": results, "count": len(results)},
        }
    except Exception as e:
        return {"success": False, "error": f"搜尋股票時發生錯誤: {str(e)}"}


@mcp.tool()
def filter_stocks_by_industry(industry: str) -> Dict[str, Any]:
    """
    根據產業分類篩選股票

    Args:
        industry: 產業分類名稱

    Returns:
        屬於指定產業的股票列表
    """
    try:
        results = []

        analyzer = get_analyzer()
        for code, info in analyzer.stock_list.items():
            if hasattr(info, "group") and info.group == industry:
                results.append(
                    {
                        "code": code,
                        "name": getattr(info, "name", f"未知_{code}"),
                        "group": info.group,
                    }
                )

        return {
            "success": True,
            "data": {"industry": industry, "results": results, "count": len(results)},
        }
    except Exception as e:
        return {"success": False, "error": f"篩選產業股票時發生錯誤: {str(e)}"}


@mcp.tool()
def get_recommendation_summary(stock_ids: List[str], months: int = 3) -> Dict[str, Any]:
    """
    獲取多支股票的推薦摘要，按信心度排序

    Args:
        stock_ids: 股票代碼列表
        months: 分析幾個月的歷史資料 (預設: 3)

    Returns:
        按信心度排序的股票推薦摘要
    """
    try:
        results = []

        analyzer = get_analyzer()
        for stock_id in stock_ids:
            result = analyzer.analyze_stock(stock_id, months)
            if result:
                results.append(result)

        # 按信心度排序
        sorted_results = sorted(results, key=lambda x: x["confidence"], reverse=True)

        # 分類推薦
        buy_recommendations = [
            r for r in sorted_results if r["recommendation"] == "買入"
        ]
        sell_recommendations = [
            r for r in sorted_results if r["recommendation"] == "賣出"
        ]
        hold_recommendations = [
            r for r in sorted_results if r["recommendation"] == "觀望"
        ]

        summary = {
            "total_analyzed": len(sorted_results),
            "buy_count": len(buy_recommendations),
            "sell_count": len(sell_recommendations),
            "hold_count": len(hold_recommendations),
            "all_results": sorted_results,
            "buy_recommendations": buy_recommendations,
            "sell_recommendations": sell_recommendations,
            "hold_recommendations": hold_recommendations,
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        return {"success": True, "data": summary}
    except Exception as e:
        return {"success": False, "error": f"生成推薦摘要時發生錯誤: {str(e)}"}


def test_twstock():
    """測試 twstock 基本功能，檢查是否能取得股票資料"""
    print("=== 開始測試 twstock 基本功能 ===")

    try:
        # 初始化分析器
        print("正在初始化台灣股票分析器...")
        analyzer = TaiwanStockAnalyzer()
        print("分析器初始化完成")

        # 測試股票列表
        print(f"\n股票列表總數: {len(analyzer.stock_list)}")

        # 測試鴻海股票 (代碼: 2317)
        test_stock_id = "2317"
        print(f"\n=== 測試鴻海股票 (代碼: {test_stock_id}) ===")

        # 1. 測試基本資訊獲取
        print("1. 測試基本資訊獲取...")
        stock_info = analyzer.get_stock_info(test_stock_id)
        if stock_info:
            print(f"✓ 成功獲取股票資訊: {stock_info}")
        else:
            print(f"✗ 無法獲取股票 {test_stock_id} 的基本資訊")
            return False

        # 2. 測試歷史數據獲取 (1個月)
        print("\n2. 測試歷史數據獲取 (1個月)...")
        stock_data = analyzer.get_stock_historical_data(test_stock_id, months=1)
        if stock_data:
            print(f"✓ 成功獲取歷史數據，共 {len(stock_data.date)} 筆記錄")
            print(f"  最新日期: {stock_data.date[-1] if stock_data.date else '無'}")
            print(f"  最新價格: {stock_data.price[-1] if stock_data.price else '無'}")
            print(f"  最新成交量: {stock_data.capacity[-1] if stock_data.capacity else '無'}")
        else:
            print(f"✗ 無法獲取股票 {test_stock_id} 的歷史數據")
            return False

        # 3. 測試技術指標計算
        print("\n3. 測試技術指標計算...")
        try:
            indicators = analyzer.calculate_technical_indicators(stock_data)
            rsi = indicators["rsi"]
            macd_line = indicators["macd_line"]

            rsi_value = rsi.iloc[-1] if not rsi.empty else None
            macd_value = macd_line.iloc[-1] if not macd_line.empty else None

            print(f"✓ RSI 值: {rsi_value}")
            print(f"✓ MACD 值: {macd_value}")
        except Exception as e:
            print(f"✗ 技術指標計算失敗: {str(e)}")
            return False

        # 4. 測試移動平均線計算
        print("\n4. 測試移動平均線計算...")
        try:
            ma5, ma5_dates = analyzer.calculate_ma(stock_data, 5)
            ma20, ma20_dates = analyzer.calculate_ma(stock_data, 20)

            print(f"✓ 5日均線: 計算了 {len(ma5)} 個數據點")
            print(f"✓ 20日均線: 計算了 {len(ma20)} 個數據點")
        except Exception as e:
            print(f"✗ 移動平均線計算失敗: {str(e)}")
            return False

        # 5. 測試支撐阻力計算
        print("\n5. 測試支撐阻力計算...")
        try:
            support, resistance = analyzer.calculate_support_resistance(stock_data)
            print(f"✓ 支撐位: {support}")
            print(f"✓ 阻力位: {resistance}")
        except Exception as e:
            print(f"✗ 支撐阻力計算失敗: {str(e)}")
            return False

        # 6. 測試完整分析
        print("\n6. 測試完整股票分析...")
        try:
            analysis_result = analyzer.analyze_stock(test_stock_id, months=1)
            if analysis_result:
                print("✓ 完整分析成功")
                print(f"  股票名稱: {analysis_result['name']}")
                print(f"  目前價格: {analysis_result['current_price']}")
                print(f"  趨勢: {analysis_result['trend']}")
                print(f"  推薦: {analysis_result['recommendation']}")
                print(f"  信心度: {analysis_result['confidence']}%")
            else:
                print(f"✗ 完整分析失敗")
                return False
        except Exception as e:
            print(f"✗ 完整分析失敗: {str(e)}")
            return False

        print("\n=== 所有測試通過！twstock 功能正常 ===")
        return True

    except Exception as e:
        print(f"\n✗ 測試過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """啟動 MCP server"""
    try:
        # 使用 stderr 輸出 debug 信息，避免干擾 stdio 通訊
        import sys
        print("正在啟動台灣股票分析 MCP Server...", file=sys.stderr)
        print("Server 名稱: Taiwan Stock Analysis Server", file=sys.stderr)
        print("可用工具:", file=sys.stderr)
        print("- get_stock_info: 獲取股票基本資訊", file=sys.stderr)
        print("- analyze_stock: 分析單支股票", file=sys.stderr)
        print("- analyze_multiple_stocks: 批量分析多支股票", file=sys.stderr)
        print("- search_stocks_by_keyword: 根據關鍵字搜尋股票", file=sys.stderr)
        print("- filter_stocks_by_industry: 根據產業篩選股票", file=sys.stderr)
        print("- get_recommendation_summary: 獲取推薦摘要", file=sys.stderr)
        print("分析器將在首次使用時初始化", file=sys.stderr)
        print("正在等待 LLM host 連接...", file=sys.stderr)

        # 啟動 MCP server
        mcp.run(transport="stdio")

    except Exception as e:
        print(f"MCP Server 啟動失敗: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return


if __name__ == "__main__":
    main()
