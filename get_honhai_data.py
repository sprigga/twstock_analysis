#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
獲取鴻海股票半年內的股價明細
"""

import twstock
from datetime import datetime
import pandas as pd


def get_honhai_stock_data():
    """獲取鴻海股票半年內的詳細數據"""
    stock_id = "2317"  # 鴻海股票代碼

    print("正在獲取鴻海股票數據...")
    print(f"股票代碼: {stock_id}")
    print(f"查詢期間: 最近6個月")
    print("-" * 60)

    try:
        # 創建股票物件
        stock = twstock.Stock(stock_id)

        # 獲取6個月的數據 (從今年3月到現在)
        current_date = datetime.now()
        target_year = current_date.year
        target_month = current_date.month - 6

        if target_month <= 0:
            target_month += 12
            target_year -= 1

        print(f"數據起始時間: {target_year}年{target_month}月")

        # 獲取數據
        stock.fetch_from(target_year, target_month)

        # 檢查數據完整性
        if not stock.date or not stock.price:
            print("錯誤: 無法獲取股票數據")
            return

        print(f"成功獲取數據，共 {len(stock.date)} 筆記錄")
        print()

        # 顯示基本資訊
        stock_info = twstock.codes[stock_id]
        print("股票基本資訊:")
        print(f"代碼: {stock_id}")
        print(f"名稱: {getattr(stock_info, 'name', '鴻海')}")
        print(f"產業: {getattr(stock_info, 'group', '電子業')}")
        print()

        # 創建DataFrame來整理數據
        data = {
            '日期': [d.strftime('%Y-%m-%d') for d in stock.date],
            '開盤價': stock.open,
            '最高價': stock.high,
            '最低價': stock.low,
            '收盤價': stock.close,
            '成交量': stock.capacity
        }

        df = pd.DataFrame(data)

        # 顯示最近10筆記錄作為樣本
        print("最近10個交易日的股價明細:")
        print("-" * 80)
        print(f"{'日期':<12} {'開盤':>8} {'最高':>8} {'最低':>8} {'收盤':>8} {'成交量':>10}")
        print("-" * 80)

        # 顯示最新的10筆數據
        recent_data = df.tail(10)
        for _, row in recent_data.iterrows():
            print(f"{row['日期']:<12} {row['開盤價']:>8.2f} {row['最高價']:>8.2f} "
                  f"{row['最低價']:>8.2f} {row['收盤價']:>8.2f} {int(row['成交量']):>10,}")

        print("-" * 80)

        # 顯示統計資訊
        print("\n統計資訊 (最近6個月):")
        print(f"數據筆數: {len(df)}")
        print(f"平均收盤價: {df['收盤價'].mean():.2f}")
        print(f"最高收盤價: {df['收盤價'].max():.2f} (日期: {df.loc[df['收盤價'].idxmax(), '日期']})")
        print(f"最低收盤價: {df['收盤價'].min():.2f} (日期: {df.loc[df['收盤價'].idxmin(), '日期']})")
        print(f"總成交量: {df['成交量'].sum():,}")
        print(f"平均成交量: {df['成交量'].mean():,.0f}")

        # 計算價格變化
        if len(df) >= 2:
            first_price = df['收盤價'].iloc[0]
            last_price = df['收盤價'].iloc[-1]
            change = last_price - first_price
            change_percent = (change / first_price) * 100

            print(f"\n價格變化:")
            print(f"起始價格: {first_price:.2f} ({df['日期'].iloc[0]})")
            print(f"最新價格: {last_price:.2f} ({df['日期'].iloc[-1]})")
            print(f"漲跌金額: {change:+.2f}")
            print(f"漲跌幅度: {change_percent:+.2f}%")

        # 保存完整數據到CSV文件
        csv_filename = f"honhai_stock_data_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        print(f"\n完整數據已保存到文件: {csv_filename}")

        return df

    except Exception as e:
        print(f"獲取數據時發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    get_honhai_stock_data()
