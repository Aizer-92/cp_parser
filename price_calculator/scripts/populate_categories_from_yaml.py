import sys
from pathlib import Path
import yaml

# Add project root to path
root = Path(__file__).parent.parent
sys.path.insert(0, str(root))

from price_calculator import PriceCalculator
from database import upsert_category


if __name__ == "__main__":
    calc = PriceCalculator()
    for cat in calc.categories:
        upsert_category(cat)
    print(f"Inserted {len(calc.categories)} categories into DB")
