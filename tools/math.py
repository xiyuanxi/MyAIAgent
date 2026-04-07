from langchain_core.tools import tool


@tool
def multiply(a: float, b: float) -> float:
    """当你需要计算两个数字相乘时，调用此工具。"""
    print(f"[Tool Called] multiply(a={a}, b={b})")
    return a * b
