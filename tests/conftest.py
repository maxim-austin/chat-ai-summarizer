import sys
import os

# Add lambda_src/ to Python's module search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../lambda_src")))
