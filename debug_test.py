#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug script to test stock analysis
"""

import twstock
from datetime import datetime

def test_honhai():
    """Test Hon Hai stock analysis"""
    print("=== Testing Hon Hai Stock Analysis ===")

    try:
        # Get stock data
        stock_id = "2317"
        print(f"Getting data for stock {stock_id}...")

        stock = twstock.Stock(stock_id)
        current_date = datetime.now()

        # Calculate target month (6 months ago)
        target_month = current_date.month - 6
        target_year = current_date.year

        if target_month <= 0:
            target_month += 12
            target_year -= 1

        print(f"Fetching data from {target_year}-{target_month}")

        stock.fetch_from(target_year, target_month)

        print(f"Data fetched. Date length: {len(stock.date) if stock.date else 0}")
        print(f"Price length: {len(stock.price) if stock.price else 0}")
        print(f"Capacity length: {len(stock.capacity) if stock.capacity else 0}")

        # Check for None values
        if stock.price:
            none_count = sum(1 for p in stock.price if p is None)
            print(f"None values in price: {none_count}/{len(stock.price)}")

        if stock.capacity:
            none_count = sum(1 for c in stock.capacity if c is None)
            print(f"None values in capacity: {none_count}/{len(stock.capacity)}")

        # Try basic operations
        print("\n=== Testing basic operations ===")

        # Test sum operations
        if stock.price and len(stock.price) > 5:
            try:
                test_sum = sum(stock.price[-5:])
                print(f"Sum of last 5 prices: {test_sum}")
            except Exception as e:
                print(f"Error summing prices: {e}")

        if stock.capacity and len(stock.capacity) > 5:
            try:
                test_sum = sum(stock.capacity[-5:])
                print(f"Sum of last 5 capacities: {test_sum}")
            except Exception as e:
                print(f"Error summing capacities: {e}")

        # Test min/max operations
        if stock.price and len(stock.price) > 5:
            try:
                test_min = min(stock.price[-5:])
                test_max = max(stock.price[-5:])
                print(f"Min/Max of last 5 prices: {test_min}/{test_max}")
            except Exception as e:
                print(f"Error getting min/max prices: {e}")

        print("\n=== Test completed ===")

    except Exception as e:
        import traceback
        print(f"Error during test: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_honhai()
