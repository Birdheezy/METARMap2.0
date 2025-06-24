#!/usr/bin/env python3
"""
Test script for sunrise/sunset calculations
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import CITIES
from scheduler import calculate_sun_times

def test_sun_times():
    """Test sunrise/sunset calculations for a few cities"""
    print("Testing sunrise/sunset calculations...")
    print("=" * 50)
    
    # Test a few cities
    test_cities = ["New York, NY", "Los Angeles, CA", "Chicago, IL", "Denver, CO"]
    
    for city in test_cities:
        print(f"\nTesting {city}:")
        try:
            sunrise, sunset = calculate_sun_times(city)
            if sunrise and sunset:
                print(f"  Sunrise: {sunrise.strftime('%I:%M %p')}")
                print(f"  Sunset:  {sunset.strftime('%I:%M %p')}")
            else:
                print(f"  Error: Could not calculate times for {city}")
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_sun_times() 