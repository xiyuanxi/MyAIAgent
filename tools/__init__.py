from .stock import get_stock_price, get_stock_history, get_sector_performance
from .weather import get_weather
from .math import multiply
from .search import create_tavily_search


def create_tools():
    return [create_tavily_search(), get_stock_price, get_stock_history, get_sector_performance, multiply, get_weather]
