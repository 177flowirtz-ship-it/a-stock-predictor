import json
import time
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from config.settings import EASTMONEY_STOCK_LIST_URL, HEADERS, REQUEST_TIMEOUT, MAX_RETRIES


def fetch_stock_list():
    stocks = _try_eastmoney()
    if stocks:
        return _filter_invalid_stocks(stocks)

    stocks = _try_sina()
    if stocks:
        return _filter_invalid_stocks(stocks)

    stocks = _try_yfinance()
    if stocks:
        return _filter_invalid_stocks(stocks)

    return _fallback_stocks()


def _try_eastmoney():
    for attempt in range(MAX_RETRIES):
        try:
            params = {
                "pn": 1, "pz": 6000, "po": 1, "np": 1,
                "ut": "bd1d9ddb04089700cf9c27f6f7426281",
                "fltt": 2, "invt": 2, "fid": "f3",
                "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
                "fields": "f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f100,f115",
                "_": int(time.time() * 1000),
            }
            resp = requests.get(EASTMONEY_STOCK_LIST_URL, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            data = resp.json()
            stocks = []
            if data.get("data") and data["data"].get("diff"):
                for item in data["data"]["diff"]:
                    stocks.append({
                        "code": item.get("f12", ""),
                        "market": item.get("f13", 0),
                        "name": item.get("f14", ""),
                        "total_market_cap": item.get("f20") or 0,
                        "pe": item.get("f115") or 0,
                        "industry": item.get("f100", ""),
                    })
            if stocks:
                return stocks
        except Exception:
            if attempt < MAX_RETRIES - 1:
                time.sleep(1)
    return None


def _try_sina():
    try:
        url = "https://vip.stock.finance.sina.com.cn/q/go.php/vIR_CustomSearch/stocklist/constituent/index.phtml"
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.encoding = "gb2312"
        import re
        pattern = r'<a[^>]*href="[^"]*?symbol=(\w{2})(\d{6})"[^>]*>(.*?)</a>'
        matches = re.findall(pattern, resp.text)
        stocks = []
        for prefix, code, name in matches:
            market = 1 if prefix == "sh" else 0
            stocks.append({"code": code, "market": market, "name": name, "total_market_cap": 0, "pe": 0, "industry": ""})
        return stocks if stocks else None
    except Exception:
        return None


def _try_yfinance():
    try:
        indices = {
            "000300.SS": "沪深300",
            "000905.SS": "中证500",
            "000852.SS": "中证1000",
        }
        seen = set()
        stocks = []
        for idx_ticker, idx_name in indices.items():
            try:
                tickers = yf.Tickers(idx_ticker)
                hist = tickers.history(period="1d")
                if not hist.empty:
                    continue
            except Exception:
                pass

            try:
                components = pd.read_html(f"https://en.wikipedia.org/wiki/{idx_name.replace('沪深300', 'CSI_300_Index').replace('中证500', 'CSI_500_Index').replace('中证1000', 'CSI_1000_Index')}")
                for table in components:
                    if "Ticker" in str(table.columns):
                        for _, row in table.iterrows():
                            ticker = str(row.get("Ticker", "")) if "Ticker" in table.columns else ""
                            if ticker and ticker not in seen:
                                seen.add(ticker)
            except Exception:
                pass

        if not seen:
            return None

        major_list = _fallback_stocks()
        result = []
        existing_codes = {s["code"] for s in major_list}
        for s in major_list:
            result.append(s)

        return result if result else None
    except Exception:
        return None


def _fallback_stocks():
    major_stocks = [
        ("600519", "贵州茅台"), ("601318", "中国平安"), ("000858", "五粮液"),
        ("600036", "招商银行"), ("000333", "美的集团"), ("600276", "恒瑞医药"),
        ("601166", "兴业银行"), ("000651", "格力电器"), ("600030", "中信证券"),
        ("002415", "海康威视"), ("000725", "京东方A"), ("601398", "工商银行"),
        ("600900", "长江电力"), ("000002", "万科A"), ("600887", "伊利股份"),
        ("601888", "中国中免"), ("002475", "立讯精密"), ("000568", "泸州老窖"),
        ("600585", "海螺水泥"), ("601688", "华泰证券"), ("000001", "平安银行"),
        ("600588", "用友网络"), ("000063", "中兴通讯"), ("601899", "紫金矿业"),
        ("002230", "科大讯飞"), ("600809", "山西汾酒"), ("600309", "万华化学"),
        ("000625", "长安汽车"), ("601012", "隆基绿能"), ("002594", "比亚迪"),
        ("600031", "三一重工"), ("000338", "潍柴动力"), ("601088", "中国神华"),
        ("300750", "宁德时代"), ("600104", "上汽集团"), ("601211", "国泰君安"),
        ("002142", "宁波银行"), ("000538", "云南白药"), ("002129", "中环股份"),
        ("601601", "中国太保"), ("600837", "海通证券"), ("002714", "牧原股份"),
        ("601668", "中国建筑"), ("000100", "TCL科技"), ("002459", "晶澳科技"),
        ("300124", "汇川技术"), ("600919", "江苏银行"), ("601225", "陕西煤业"),
        ("002304", "洋河股份"), ("000895", "双汇发展"), ("002049", "紫光国微"),
        ("601988", "中国银行"), ("600048", "保利发展"), ("000301", "东方盛虹"),
        ("300014", "亿纬锂能"), ("600028", "中国石化"), ("603259", "药明康德"),
        ("002460", "赣锋锂业"), ("601919", "中远海控"), ("000792", "盐湖股份"),
        ("300015", "爱尔眼科"), ("601857", "中国石油"), ("600436", "片仔癀"),
        ("002466", "天齐锂业"), ("600570", "恒生电子"), ("300059", "东方财富"),
        ("600111", "北方稀土"), ("000776", "广发证券"), ("002007", "华兰生物"),
        ("601727", "上海电气"), ("600690", "海尔智家"), ("300033", "同花顺"),
        ("601138", "工业富联"), ("600000", "浦发银行"), ("300274", "阳光电源"),
        ("000425", "徐工机械"), ("601328", "交通银行"), ("300760", "迈瑞医疗"),
        ("603993", "洛阳钼业"), ("600438", "通威股份"), ("002709", "天赐材料"),
        ("300498", "温氏股份"), ("601669", "中国电建"), ("600415", "小商品城"),
        ("002192", "融捷股份"), ("600406", "国电南瑞"), ("601939", "建设银行"),
        ("300122", "智飞生物"), ("603288", "海天味业"), ("000661", "长春高新"),
        ("002340", "格林美"), ("601985", "中国核电"), ("002074", "国轩高科"),
        ("600016", "民生银行"), ("002236", "大华股份"), ("601186", "中国铁建"),
        ("002812", "恩捷股份"), ("603799", "华友钴业"), ("002271", "东方雨虹"),
        ("601636", "旗滨集团"), ("000977", "浪潮信息"), ("601390", "中国中铁"),
        ("601939", "建设银行"), ("601818", "光大银行"), ("600015", "华夏银行"),
        ("600009", "上海机场"), ("601066", "中信建投"), ("600346", "恒力石化"),
        ("000876", "新希望"), ("600050", "中国联通"), ("002311", "海大集团"),
        ("002352", "顺丰控股"), ("300413", "芒果超媒"), ("002841", "视源股份"),
        ("600745", "闻泰科技"), ("603501", "韦尔股份"), ("002601", "龙佰集团"),
        ("300408", "三环集团"), ("002410", "广联达"), ("300347", "泰格医药"),
        ("002916", "深南电路"), ("300529", "健帆生物"), ("603986", "兆易创新"),
        ("600703", "三安光电"), ("002050", "三花智控"), ("000786", "北新建材"),
        ("600176", "中国巨石"), ("002508", "老板电器"), ("600660", "福耀玻璃"),
        ("600886", "国投电力"), ("002001", "新和成"), ("300316", "晶盛机电"),
        ("300601", "康泰生物"), ("603160", "汇顶科技"), ("600298", "安琪酵母"),
        ("002241", "歌尔股份"), ("000963", "华东医药"), ("300628", "亿联网络"),
        ("002624", "完美世界"), ("002602", "世纪华通"), ("300433", "蓝思科技"),
        ("603899", "晨光股份"), ("600741", "华域汽车"), ("000069", "华侨城A"),
        ("002739", "万达电影"), ("600183", "生益科技"), ("002600", "领益智造"),
        ("300136", "信维通信"), ("002027", "分众传媒"), ("600143", "金发科技"),
        ("000157", "中联重科"), ("002110", "三钢闽光"), ("600018", "上港集团"),
        ("601006", "大秦铁路"), ("600011", "华能国际"), ("603019", "中科曙光"),
        ("300003", "乐普医疗"), ("603658", "安图生物"), ("300146", "汤臣倍健"),
        ("600196", "复星医药"), ("002044", "美年健康"), ("002153", "石基信息"),
        ("603939", "益丰药房"), ("002727", "一心堂"), ("600763", "通策医疗"),
        ("600079", "人福医药"), ("600085", "同仁堂"), ("002294", "信立泰"),
        ("000423", "东阿阿胶"), ("002372", "伟星新材"), ("601877", "正泰电器"),
        ("600516", "方大炭素"), ("600352", "浙江龙盛"), ("002408", "齐翔腾达"),
        ("600026", "中远海能"), ("600019", "宝钢股份"), ("600010", "包钢股份"),
        ("601800", "中国交建"), ("600150", "中国船舶"), ("600893", "航发动力"),
        ("002179", "中航光电"), ("000768", "中航西飞"), ("600760", "中航沈飞"),
        ("600372", "中航机载"), ("002025", "航天电器"), ("600118", "中国卫星"),
        ("600685", "中船防务"), ("002262", "恩华药业"), ("600332", "白云山"),
        ("000999", "华润三九"), ("600535", "天士力"), ("600566", "济川药业"),
        ("603369", "今世缘"), ("002568", "百润股份"), ("600132", "重庆啤酒"),
        ("000596", "古井贡酒"), ("002557", "洽洽食品"), ("600305", "恒顺醋业"),
        ("601933", "永辉超市"), ("603708", "家家悦"), ("000930", "中粮科技"),
        ("600737", "中粮糖业"), ("603517", "绝味食品"), ("002714", "牧原股份"),
        ("300146", "汤臣倍健"), ("600754", "锦江酒店"), ("601111", "中国国航"),
        ("600029", "南方航空"), ("600115", "中国东航"), ("600004", "白云机场"),
        ("603885", "吉祥航空"), ("300577", "开润股份"), ("603129", "春风动力"),
        ("601689", "拓普集团"), ("002920", "德赛西威"), ("002812", "恩捷股份"),
        ("603596", "伯特利"), ("000338", "潍柴动力"), ("600104", "上汽集团"),
    ]
    return [
        {"code": c, "market": 1 if c.startswith("6") else 0, "name": n, "total_market_cap": 0, "pe": 0, "industry": ""}
        for c, n in major_stocks
    ]


def _filter_invalid_stocks(stocks):
    seen = set()
    result = []
    for s in stocks:
        code = s.get("code", "")
        name = s.get("name", "")
        if not code or not name:
            continue
        if "退市" in name:
            continue
        if code not in seen:
            seen.add(code)
            result.append(s)
    return result
