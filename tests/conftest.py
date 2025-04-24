# tests/conftest.py
import sys, os

# встать в корень проекта (где лежат папки backend/, tools/, config.py)
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, root)
