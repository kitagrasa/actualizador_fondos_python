"""
Configuración centralizada
"""
from pathlib import Path

DATA_DIR = Path("data")
JSON_DIR = Path("json")
KEEP_DAYS = 2920

FUNDS = [
    {"isin": "LU0223332320", "name": "KONWAVE Gold Equity Fund B EUR Hedged Cap"},
    {"isin": "LU0524465548", "name": "Amundi Gold Hedged Cap"},
    {"isin": "LU1598720172", "name": "Lyxor Gold Bullion Securities"},
    {"isin": "IE00B3CNHG25", "name": "WisdomTree Gold"},
    {"isin": "IE00B579F325", "name": "iShares Physical Gold ETC"},
    {"isin": "LU0252633754", "name": "Xetra-Gold"},
    {"isin": "DE000A0S9GB0", "name": "EUWAX Gold II"}
]

SOURCE_PRIORITY = {"ft": 20, "fundsquare": 10, "unknown": 0}
