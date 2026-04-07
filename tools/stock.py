import yfinance as yf
from langchain_core.tools import tool


@tool
def get_stock_price(ticker: str) -> str:
    """根据股票代码获取当前股票价格。
    支持美股（NVDA、AAPL）、A股（600519.SS、000858.SZ）、港股（0700.HK）等。
    """
    print(f"[Tool Called] get_stock_price(ticker={ticker})")
    stock = yf.Ticker(ticker)
    info = stock.fast_info
    price = info.last_price
    if price is None:
        return f"无法获取 {ticker} 的股票价格"
    currency = getattr(info, "currency", None) or "USD"
    exchange = getattr(info, "exchange", None)
    exchange_str = f"（{exchange}）" if exchange else ""
    return f"{ticker}{exchange_str} 当前股价为 {price:.2f} {currency}"


@tool
def get_stock_history(ticker: str, days: int = 5) -> str:
    """获取股票最近 N 天的历史价格数据（开盘价、收盘价、涨跌幅）。
    当用户询问某股票最近几天/一周/一个月的历史数据或走势时调用此工具。
    days 可设为 5、10、30、60、90 等。
    """
    print(f"[Tool Called] get_stock_history(ticker={ticker}, days={days})")
    stock = yf.Ticker(ticker)
    hist = stock.history(period=f"{days}d")
    if hist.empty:
        return f"无法获取 {ticker} 的历史数据"
    currency = getattr(stock.fast_info, "currency", None) or "USD"
    lines = [f"{ticker} 最近 {len(hist)} 个交易日数据（{currency}）:"]
    for date, row in hist.iterrows():
        date_str = date.strftime("%Y-%m-%d")
        change = row["Close"] - row["Open"]
        change_pct = change / row["Open"] * 100
        sign = "+" if change >= 0 else ""
        lines.append(
            f"  {date_str} | 开 {row['Open']:.2f} | 收 {row['Close']:.2f} | "
            f"{sign}{change_pct:.2f}% | 量 {int(row['Volume']):,}"
        )
    return "\n".join(lines)


@tool
def get_sector_performance() -> str:
    """获取美股主要板块今日涨跌幅排行。当用户询问板块表现、板块涨跌幅、行业排名等问题时调用此工具。"""
    print("[Tool Called] get_sector_performance()")
    sector_etfs = {
        "科技 (Technology)": "XLK",
        "医疗保健 (Health Care)": "XLV",
        "金融 (Financials)": "XLF",
        "非必需消费 (Consumer Discretionary)": "XLY",
        "通信服务 (Communication Services)": "XLC",
        "工业 (Industrials)": "XLI",
        "必需消费 (Consumer Staples)": "XLP",
        "能源 (Energy)": "XLE",
        "公用事业 (Utilities)": "XLU",
        "房地产 (Real Estate)": "XLRE",
        "材料 (Materials)": "XLB",
    }
    results = []
    for name, ticker in sector_etfs.items():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2d")
            if len(hist) >= 2:
                prev_close = hist["Close"].iloc[-2]
                last_close = hist["Close"].iloc[-1]
                change_pct = (last_close - prev_close) / prev_close * 100
                results.append((name, ticker, change_pct))
        except Exception:
            continue
    if not results:
        return "无法获取板块数据"
    results.sort(key=lambda x: x[2], reverse=True)
    lines = ["美股板块今日涨跌幅排行:"]
    for name, ticker, change in results:
        sign = "+" if change >= 0 else ""
        lines.append(f"  {name} ({ticker}): {sign}{change:.2f}%")
    return "\n".join(lines)
