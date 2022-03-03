import sys
import os.path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from src.tensorboard_display import tensorboard_display
import pytest

def test_tensorboard_display():
    pass