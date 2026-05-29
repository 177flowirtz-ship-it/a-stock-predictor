import json
import time
import requests
from config.settings import EASTMONEY_STOCK_LIST_URL, HEADERS, REQUEST_TIMEOUT, MAX_RETRIES


def fetch_stock_list():
    stocks = _try_eastmoney()
    if stocks:
        return _filter_invalid_stocks(stocks)

    stocks = _try_sina()
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
            if prefix == "sh":
                market = 1
            elif prefix == "sz":
                market = 0
            else:
                continue
            stocks.append({"code": code, "market": market, "name": name, "total_market_cap": 0, "pe": 0, "industry": ""})
        return stocks if stocks else None
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
        ("300122", "智飞生物"), ("002129", "TCL中环"), ("002010", "传化智联"),
        ("603288", "海天味业"), ("601100", "恒立液压"), ("000661", "长春高新"),
        ("002340", "格林美"), ("601985", "中国核电"), ("002074", "国轩高科"),
        ("600016", "民生银行"), ("002236", "大华股份"), ("601186", "中国铁建"),
        ("002812", "恩捷股份"), ("603799", "华友钴业"), ("002271", "东方雨虹"),
        ("601636", "旗滨集团"), ("000977", "浪潮信息"), ("601390", "中国中铁"),
    ]
    return [{"code": c, "market": 1 if c.startswith("6") else 0, "name": n, "total_market_cap": 0, "pe": 0, "industry": ""} for c, n in major_stocks]


def _filter_invalid_stocks(stocks):
    result = []
    for s in stocks:
        code = s.get("code", "")
        name = s.get("name", "")
        if not code or not name:
            continue
        if name and ("退市" in name):
            continue
        result.append(s)
    return result
