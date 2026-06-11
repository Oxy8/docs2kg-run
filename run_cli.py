import sys
from unittest.mock import MagicMock

# Mock llama_cpp to bypass heavy C++ local compile dependencies
sys.modules['llama_cpp'] = MagicMock()

from Docs2KG.cli import cli

if __name__ == "__main__":
    cli()
