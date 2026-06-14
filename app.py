from pathlib import Path
from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import joblib
import pandas as pd
import os
import requests
import urllib3
import re

app = Flask("skystyle")

model = joblib.load("model.pkl")

API_KEY = os.getenv("CWA_API_KEY")
CWA_BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/"
TZ = ZoneInfo("Asia/Taipei")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

COUNTY_DATASET = {
    "宜蘭縣": "F-D0047-001",
    "桃園市": "F-D0047-005",
    "新竹縣": "F-D0047-009",
    "苗栗縣": "F-D0047-013",
    "彰化縣": "F-D0047-017",
    "南投縣": "F-D0047-021",
    "雲林縣": "F-D0047-025",
    "嘉義縣": "F-D0047-029",
    "屏東縣": "F-D0047-033",
    "臺東縣": "F-D0047-037",
    "花蓮縣": "F-D0047-041",
    "澎湖縣": "F-D0047-045",
    "基隆市": "F-D0047-049",
    "新竹市": "F-D0047-053",
    "嘉義市": "F-D0047-057",
    "臺北市": "F-D0047-061",
    "高雄市": "F-D0047-065",
    "新北市": "F-D0047-069",
    "臺中市": "F-D0047-073",
    "臺南市": "F-D0047-077",
    "連江縣": "F-D0047-081",
    "金門縣": "F-D0047-085"
}

TOWN_MAP = {
    "臺北市": ["中正區", "大同區", "中山區", "松山區", "大安區", "萬華區", "信義區", "士林區", "北投區", "內湖區", "南港區", "文山區"],
    "新北市": ["板橋區", "三重區", "中和區", "永和區", "新莊區", "新店區", "樹林區", "鶯歌區", "三峽區", "淡水區", "汐止區", "瑞芳區", "土城區", "蘆洲區", "五股區", "泰山區", "林口區", "深坑區", "石碇區", "坪林區", "三芝區", "石門區", "八里區", "平溪區", "雙溪區", "貢寮區", "金山區", "萬里區", "烏來區"],
    "基隆市": ["仁愛區", "信義區", "中正區", "中山區", "安樂區", "暖暖區", "七堵區"],
    "桃園市": ["桃園區", "中壢區", "大溪區", "楊梅區", "蘆竹區", "大園區", "龜山區", "八德區", "龍潭區", "平鎮區", "新屋區", "觀音區", "復興區"],
    "新竹市": ["東區", "北區", "香山區"],
    "新竹縣": ["竹北市", "竹東鎮", "新埔鎮", "關西鎮", "湖口鄉", "新豐鄉", "芎林鄉", "橫山鄉", "北埔鄉", "寶山鄉", "峨眉鄉", "尖石鄉", "五峰鄉"],
    "宜蘭縣": ["宜蘭市", "羅東鎮", "蘇澳鎮", "頭城鎮", "礁溪鄉", "壯圍鄉", "員山鄉", "冬山鄉", "五結鄉", "三星鄉", "大同鄉", "南澳鄉"],
    "苗栗縣": ["苗栗市", "頭份市", "苑裡鎮", "通霄鎮", "竹南鎮", "後龍鎮", "卓蘭鎮", "大湖鄉", "公館鄉", "銅鑼鄉", "南庄鄉", "頭屋鄉", "三義鄉", "西湖鄉", "造橋鄉", "三灣鄉", "獅潭鄉", "泰安鄉"],
    "臺中市": ["中區", "東區", "南區", "西區", "北區", "西屯區", "南屯區", "北屯區", "豐原區", "東勢區", "大甲區", "清水區", "沙鹿區", "梧棲區", "后里區", "神岡區", "潭子區", "大雅區", "新社區", "石岡區", "外埔區", "大安區", "烏日區", "大肚區", "龍井區", "霧峰區", "太平區", "大里區", "和平區"],
    "彰化縣": ["彰化市", "鹿港鎮", "和美鎮", "線西鄉", "伸港鄉", "福興鄉", "秀水鄉", "花壇鄉", "芬園鄉", "員林市", "溪湖鎮", "田中鎮", "大村鄉", "埔鹽鄉", "埔心鄉", "永靖鄉", "社頭鄉", "二水鄉", "北斗鎮", "二林鎮", "田尾鄉", "埤頭鄉", "芳苑鄉", "大城鄉", "竹塘鄉", "溪州鄉"],
    "南投縣": ["南投市", "埔里鎮", "草屯鎮", "竹山鎮", "集集鎮", "名間鄉", "鹿谷鄉", "中寮鄉", "魚池鄉", "國姓鄉", "水里鄉", "信義鄉", "仁愛鄉"],
    "雲林縣": ["斗六市", "斗南鎮", "虎尾鎮", "西螺鎮", "土庫鎮", "北港鎮", "古坑鄉", "大埤鄉", "莿桐鄉", "林內鄉", "二崙鄉", "崙背鄉", "麥寮鄉", "東勢鄉", "褒忠鄉", "臺西鄉", "元長鄉", "四湖鄉", "口湖鄉", "水林鄉"],
    "嘉義市": ["東區", "西區"],
    "嘉義縣": ["太保市", "朴子市", "布袋鎮", "大林鎮", "民雄鄉", "溪口鄉", "新港鄉", "六腳鄉", "東石鄉", "義竹鄉", "鹿草鄉", "水上鄉", "中埔鄉", "竹崎鄉", "梅山鄉", "番路鄉", "大埔鄉", "阿里山鄉"],
    "臺南市": ["新營區", "鹽水區", "白河區", "柳營區", "後壁區", "東山區", "麻豆區", "下營區", "六甲區", "官田區", "大內區", "佳里區", "學甲區", "西港區", "七股區", "將軍區", "北門區", "新化區", "善化區", "新市區", "安定區", "山上區", "玉井區", "楠西區", "南化區", "左鎮區", "仁德區", "歸仁區", "關廟區", "龍崎區", "永康區", "東區", "南區", "北區", "安南區", "安平區", "中西區"],
    "高雄市": ["鹽埕區", "鼓山區", "左營區", "楠梓區", "三民區", "新興區", "前金區", "苓雅區", "前鎮區", "旗津區", "小港區", "鳳山區", "林園區", "大寮區", "大樹區", "大社區", "仁武區", "鳥松區", "岡山區", "橋頭區", "燕巢區", "田寮區", "阿蓮區", "路竹區", "湖內區", "茄萣區", "永安區", "彌陀區", "梓官區", "旗山區", "美濃區", "六龜區", "甲仙區", "杉林區", "內門區", "茂林區", "桃源區", "那瑪夏區"],
    "屏東縣": ["屏東市", "潮州鎮", "東港鎮", "恆春鎮", "萬丹鄉", "長治鄉", "麟洛鄉", "九如鄉", "里港鄉", "鹽埔鄉", "高樹鄉", "萬巒鄉", "內埔鄉", "竹田鄉", "新埤鄉", "枋寮鄉", "新園鄉", "崁頂鄉", "林邊鄉", "南州鄉", "佳冬鄉", "琉球鄉", "車城鄉", "滿州鄉", "枋山鄉", "三地門鄉", "霧臺鄉", "瑪家鄉", "泰武鄉", "來義鄉", "春日鄉", "獅子鄉", "牡丹鄉"],
    "花蓮縣": ["花蓮市", "鳳林鎮", "玉里鎮", "新城鄉", "吉安鄉", "壽豐鄉", "光復鄉", "豐濱鄉", "瑞穗鄉", "富里鄉", "秀林鄉", "萬榮鄉", "卓溪鄉"],
    "臺東縣": ["臺東市", "成功鎮", "關山鎮", "卑南鄉", "大武鄉", "太麻里鄉", "東河鄉", "長濱鄉", "鹿野鄉", "池上鄉", "綠島鄉", "延平鄉", "海端鄉", "達仁鄉", "金峰鄉", "蘭嶼鄉"],
    "澎湖縣": ["馬公市", "湖西鄉", "白沙鄉", "西嶼鄉", "望安鄉", "七美鄉"],
    "金門縣": ["金城鎮", "金沙鎮", "金湖鎮", "金寧鄉", "烈嶼鄉", "烏坵鄉"],
    "連江縣": ["南竿鄉", "北竿鄉", "莒光鄉", "東引鄉"]
}

COUNTY_ORDER = [
    "臺北市", "新北市", "基隆市", "桃園市", "新竹市", "新竹縣", "宜蘭縣",
    "苗栗縣", "臺中市", "彰化縣", "南投縣", "雲林縣", "嘉義市", "嘉義縣",
    "臺南市", "高雄市", "屏東縣", "花蓮縣", "臺東縣", "澎湖縣", "金門縣", "連江縣"
]

clothing_map = {
    "A": "無袖上衣 / 背心 + 涼感短褲",
    "B": "短袖上衣 + 短褲",
    "C": "短袖上衣 + 及膝短褲",
    "D": "短袖上衣 + 七分褲",
    "E": "針織短衫 + 七分褲",
    "F": "短袖上衣 + 薄長褲",
    "G": "薄長袖 + 薄長褲",
    "H": "薄長袖 + 棉褲",
    "I": "針織長袖 + 棉褲",
    "J": "帽 T / 大學 T + 厚長褲",
    "K": "刷毛帽 T + 厚長褲",
    "L": "發熱衣 + 刷毛長褲",
    "M": "厚毛衣 + 刷毛長褲",
    "N": "高領毛衣 + 刷毛防風長褲",
    "O": "極暖發熱衣 + 刷毛防風長褲"
}

umbrella_map = {
    "X": "無需攜帶雨具",
    "Y": "可斟酌是否攜帶雨具",
    "Z": "需要攜帶雨具"
}

coat_map = {
    1: "不需穿著外套",
    2: "薄外套",
    3: "防風外套",
    4: "保暖外套"
}


def normalize_tw(text):
    return text.strip().replace("台", "臺")


def to_number(value):
    if value is None:
        return None
    match = re.search(r"-?\d+(\.\d+)?", str(value))
    if match:
        return float(match.group())
    return None


def decode_target(target):
    target = int(target)
    value = target - 1
    clothing_index = value // 12
    remain = value % 12
    umbrella_index = remain // 4
    coat_type = remain % 4 + 1
    clothing_code = chr(clothing_index + 65)
    umbrella_code = chr(umbrella_index + 88)

    return {
        "clothing": clothing_map.get(clothing_code, "未知衣著"),
        "umbrella": umbrella_map.get(umbrella_code, "未知雨具建議"),
        "coat": coat_map.get(coat_type, "未知外套")
    }


def parse_cwa_time(time_str):
    dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TZ)
    else:
        dt = dt.astimezone(TZ)
    return dt


def get_time_string(time_item):
    return (
        time_item.get("DataTime")
        or time_item.get("dataTime")
        or time_item.get("StartTime")
        or time_item.get("startTime")
    )


def get_element_value(time_item, prefer_key=None):
    values = time_item.get("ElementValue") or time_item.get("elementValue") or []

    if not values:
        return None

    first = values[0]

    if isinstance(first, dict):
        if prefer_key and prefer_key in first and first[prefer_key] not in [None, ""]:
            return first[prefer_key]

        keys = [
            "ProbabilityOfPrecipitation",
            "PoP",
            "PoP6h",
            "PoP12h",
            "ComfortIndexDescription",
            "ComfortIndex",
            "Weather",
            "Temperature",
            "RelativeHumidity",
            "ApparentTemperature",
            "WindSpeed",
            "value",
            "Value"
        ]

        for key in keys:
            if key in first and first[key] not in [None, ""]:
                return first[key]

        for value in first.values():
            if value not in [None, ""]:
                return value

    return first


def fetch_cwa_weather(county):
    county = normalize_tw(county)
    dataset_id = COUNTY_DATASET.get(county)

    if dataset_id is None:
        raise ValueError("找不到這個縣市的資料集")

    url = CWA_BASE_URL + dataset_id
    params = {
        "Authorization": API_KEY,
        "format": "JSON"
    }

    response = requests.get(url, params=params, timeout=20, verify=False)
    response.raise_for_status()
    return response.json()


def find_location(cwa_data, town):
    town = normalize_tw(town)
    records = cwa_data.get("records", {})
    groups = records.get("Locations") or records.get("locations") or []

    for group in groups:
        county_name = group.get("LocationsName") or group.get("locationsName") or ""
        locations = group.get("Location") or group.get("location") or []

        for loc in locations:
            loc_name = loc.get("LocationName") or loc.get("locationName") or ""
            if town == loc_name:
                return county_name, loc

    return None, None


def normalize_weather_code_final_safe(value):
    if value is None:
        return ""

    s = str(value).strip()

    if s.isdigit():
        n = int(s)
        if 1 <= n <= 57:
            return f"{n:02d}"

    m = re.search(r'(?<!\\d)([1-9]|[1-4]\\d|5[0-7])(?!\\d)', s)
    if m:
        n = int(m.group(1))
        if 1 <= n <= 57:
            return f"{n:02d}"

    return ""


def extract_weather_code_final_safe(time_item):
    if not isinstance(time_item, dict):
        return ""

    value_lists = []

    for key in [
        "WeatherElementValue",
        "weatherElementValue",
        "ElementValue",
        "elementValue",
        "elementValues"
    ]:
        v = time_item.get(key)
        if isinstance(v, list):
            value_lists.extend(v)

    for item in value_lists:
        if not isinstance(item, dict):
            continue

        for key in ["WeatherCode", "weatherCode"]:
            code = normalize_weather_code_final_safe(item.get(key))
            if code:
                return code

        label = str(
            item.get("measures")
            or item.get("Measures")
            or item.get("measure")
            or item.get("Measure")
            or item.get("elementName")
            or item.get("ElementName")
            or ""
        )

        if "WeatherCode" in label or "weatherCode" in label or "天氣代碼" in label:
            for key in ["value", "Value", "parameterValue", "ParameterValue"]:
                code = normalize_weather_code_final_safe(item.get(key))
                if code:
                    return code

    for item in value_lists:
        if not isinstance(item, dict):
            continue

        for key in ["value", "Value", "parameterValue", "ParameterValue"]:
            raw = item.get(key)
            if raw is None:
                continue

            s = str(raw).strip()
            if s.isdigit():
                code = normalize_weather_code_final_safe(s)
                if code:
                    return code

    return ""


def choose_weather_icon_final_safe(weather_code, weather_text, forecast_time=None):
    text = str(weather_text or "")
    code = normalize_weather_code_final_safe(weather_code)

    hour = 12
    try:
        if forecast_time:
            hour = forecast_time.hour
    except Exception:
        hour = 12

    is_day = 6 <= hour < 18

    day_to_night = {
        "01": "02",
        "03": "04",
        "05": "06",
        "07": "08",
        "23": "24",
        "25": "26",
        "27": "28",
        "29": "30",
        "32": "33",
        "34": "35",
        "36": "37",
        "38": "39",
        "41": "42",
        "44": "45",
        "47": "48",
        "50": "51"
    }

    night_to_day = {night: day for day, night in day_to_night.items()}

    if code:
        final_code = code

        if is_day and code in night_to_day:
            final_code = night_to_day[code]

        if not is_day and code in day_to_night:
            final_code = day_to_night[code]

        return f"{final_code}.svg"

    if "雷" in text and "雨" in text:
        return "19.svg"

    if "雨" in text or "陣雨" in text:
        return "12.svg"

    if "霧" in text:
        return "40.svg"

    if "雪" in text or "冰" in text:
        return "57.svg"

    if "晴時多雲" in text:
        return "03.svg" if is_day else "04.svg"

    if "多雲時晴" in text:
        return "05.svg" if is_day else "06.svg"

    if "晴" in text and "雲" in text:
        return "03.svg" if is_day else "04.svg"

    if "晴" in text:
        return "01.svg" if is_day else "02.svg"

    if "多雲" in text:
        return "05.svg" if is_day else "06.svg"

    if "陰" in text:
        return "11.svg"

    return ""


def find_nearest_weather(location, target_time):
    elements = location.get("WeatherElement") or location.get("weatherElement") or []
    result = {}
    matched_times = []

    for element in elements:
        name = element.get("ElementName") or element.get("elementName") or ""
        times = element.get("Time") or element.get("time") or []

        field = None
        prefer_key = None

        if name in ["T", "溫度"]:
            field = "temp"
            prefer_key = "Temperature"

        elif name in ["RH", "相對濕度"]:
            field = "humidity"
            prefer_key = "RelativeHumidity"

        elif name in ["AT", "體感溫度"]:
            field = "apparent_temp"
            prefer_key = "ApparentTemperature"

        elif name in ["Wind", "風向風速", "風速"]:
            field = "wind_speed"
            prefer_key = "WindSpeed"

        elif name in ["Wx", "天氣現象"]:
            field = "weather"
            prefer_key = "Weather"

        elif "降雨機率" in name or "PoP" in name:
            field = "rain_prob"
            prefer_key = "ProbabilityOfPrecipitation"

        elif name in ["CI", "舒適度", "舒適度指數", "ComfortIndex", "Comfort"]:
            field = "comfort"
            prefer_key = "ComfortIndexDescription"

        if field is None:
            continue

        best_time = None
        best_value = None
        best_time_item = None

        for t in times:
            time_str = get_time_string(t)

            if not time_str:
                continue

            forecast_time = parse_cwa_time(time_str)
            value = get_element_value(t, prefer_key)

            if value is None:
                continue

            if best_time is None:
                best_time = forecast_time
                best_value = value
                best_time_item = t
            else:
                old_diff = abs((best_time - target_time).total_seconds())
                new_diff = abs((forecast_time - target_time).total_seconds())

                if new_diff < old_diff:
                    best_time = forecast_time
                    best_value = value
                    best_time_item = t

        if best_value is not None:
            result[field] = best_value
            matched_times.append(best_time)

            if field == "weather":
                weather_code = extract_weather_code_final_safe(best_time_item)
                weather_icon = choose_weather_icon_final_safe(weather_code, best_value, best_time)

                result["weather_code"] = weather_code
                result["weather_icon"] = weather_icon

    if (
        to_number(result.get("humidity")) is None
        or to_number(result.get("wind_speed")) is None
        or to_number(result.get("apparent_temp")) is None
    ):
        return None

    nearest_time = min(
        matched_times,
        key=lambda x: abs((x - target_time).total_seconds())
    )

    result["matched_time"] = nearest_time.strftime("%Y/%m/%d %H:%M")
    return result


@app.context_processor
def inject_template_data():
    return {
        "TOWN_MAP": TOWN_MAP,
        "COUNTY_ORDER": COUNTY_ORDER,
        "counties": COUNTY_ORDER
    }


@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    error = None

    default_time = datetime.now(TZ) + timedelta(hours=1)

    form_date = default_time.strftime("%Y-%m-%d")
    form_hour = default_time.strftime("%H")
    form_minute = default_time.strftime("%M")
    form_county = "新北市"
    form_town = ""

    counties = list(COUNTY_DATASET.keys())
    hours = [f"{i:02d}" for i in range(24)]
    minutes = [f"{i:02d}" for i in range(60)]

    if request.method == "POST":
        try:
            form_date = request.form.get("date", "")
            form_hour = request.form.get("hour", "")
            form_minute = request.form.get("minute", "")
            form_county = normalize_tw(request.form.get("county", ""))
            form_town = normalize_tw(request.form.get("town", ""))

            if not form_date or not form_hour or not form_minute or not form_county or not form_town:
                error = "請完整選擇日期、時間、縣市與鄉鎮市區"
                return render_template("main.html", **locals())

            form_time = f"{form_hour}:{form_minute}"
            now = datetime.now(TZ)
            target_time = datetime.fromisoformat(form_date + "T" + form_time).replace(tzinfo=TZ)

            if target_time < now:
                error = "只能選擇未來 24 小時內的時間"
                return render_template("main.html", **locals())

            if target_time > now + timedelta(hours=24):
                error = "只能選擇未來 24 小時內的時間"
                return render_template("main.html", **locals())

            cwa_data = fetch_cwa_weather(form_county)
            county_name, location = find_location(cwa_data, form_town)

            if location is None:
                error = "找不到這個地點，請確認縣市與鄉鎮市區是否相符"
                return render_template("main.html", **locals())

            weather_info = find_nearest_weather(location, target_time)

            if weather_info is None:
                error = "找不到可用的氣象資料，請換一個時間或地點"
                return render_template("main.html", **locals())

            temp = to_number(weather_info.get("temp"))
            humidity = to_number(weather_info.get("humidity"))
            wind_speed = to_number(weather_info.get("wind_speed"))
            apparent_temp = to_number(weather_info.get("apparent_temp"))
            rain_prob_number = to_number(weather_info.get("rain_prob"))

            if rain_prob_number is None:
                rain_prob = "無資料"
            else:
                rain_prob = f"{rain_prob_number:g}%"

            comfort = weather_info.get("comfort")

            if comfort is None or comfort == "無資料":
                if apparent_temp >= 33:
                    comfort = "悶熱"
                elif apparent_temp >= 29:
                    comfort = "稍悶熱"
                elif apparent_temp >= 23:
                    comfort = "舒適"
                elif apparent_temp >= 18:
                    comfort = "稍涼"
                else:
                    comfort = "寒冷"

            X = pd.DataFrame([{
                "RelativeHumidity": humidity,
                "WindSpeed": wind_speed,
                "ApparentTemperature": apparent_temp
            }])

            prediction = model.predict(X)[0]
            outfit = decode_target(prediction)

            result = {
                "location": form_county + " " + form_town,
                "target_time": target_time.strftime("%Y/%m/%d %H:%M"),
                "matched_time": weather_info["matched_time"],
                "weather": weather_info.get("weather", "無資料"),
                "temp": temp,
                "humidity": humidity,
                "wind_speed": wind_speed,
                "apparent_temp": apparent_temp,
                "rain_prob": rain_prob,
                "comfort": comfort,
                "weather_code": weather_info.get("weather_code", ""),
                "weather_icon": weather_info.get("weather_icon", ""),
                "clothing": outfit["clothing"],
                "umbrella": outfit["umbrella"],
                "coat": outfit["coat"]
            }

            if rain_prob_number is not None and rain_prob_number >= 60:
                result["umbrella"] = "需要攜帶雨具"

        except Exception as e:
            error = str(e)

    return render_template("main.html", **locals())


@app.route("/history")
def history():
    return render_template("history.html")


if __name__ == "__main__":
    app.run(debug=True)


from pathlib import Path
from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import joblib
import pandas as pd
import os
import requests
import urllib3
import re

app = Flask("skystyle")

model = joblib.load("model.pkl")

API_KEY = os.getenv("CWA_API_KEY")
CWA_BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/"
TZ = ZoneInfo("Asia/Taipei")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

COUNTY_DATASET = {
    "宜蘭縣": "F-D0047-001",
    "桃園市": "F-D0047-005",
    "新竹縣": "F-D0047-009",
    "苗栗縣": "F-D0047-013",
    "彰化縣": "F-D0047-017",
    "南投縣": "F-D0047-021",
    "雲林縣": "F-D0047-025",
    "嘉義縣": "F-D0047-029",
    "屏東縣": "F-D0047-033",
    "臺東縣": "F-D0047-037",
    "花蓮縣": "F-D0047-041",
    "澎湖縣": "F-D0047-045",
    "基隆市": "F-D0047-049",
    "新竹市": "F-D0047-053",
    "嘉義市": "F-D0047-057",
    "臺北市": "F-D0047-061",
    "高雄市": "F-D0047-065",
    "新北市": "F-D0047-069",
    "臺中市": "F-D0047-073",
    "臺南市": "F-D0047-077",
    "連江縣": "F-D0047-081",
    "金門縣": "F-D0047-085"
}

TOWN_MAP = {
    "新北市": ["板橋區", "三重區", "中和區", "永和區", "新莊區", "新店區", "樹林區", "鶯歌區", "三峽區", "淡水區", "汐止區", "瑞芳區", "土城區", "蘆洲區", "五股區", "泰山區", "林口區", "深坑區", "石碇區", "坪林區", "三芝區", "石門區", "八里區", "平溪區", "雙溪區", "貢寮區", "金山區", "萬里區", "烏來區"],
    "臺北市": ["中正區", "大同區", "中山區", "松山區", "大安區", "萬華區", "信義區", "士林區", "北投區", "內湖區", "南港區", "文山區"],
    "臺中市": ["中區", "東區", "南區", "西區", "北區", "西屯區", "南屯區", "北屯區", "豐原區", "東勢區", "大甲區", "清水區", "沙鹿區", "梧棲區", "后里區", "神岡區", "潭子區", "大雅區", "新社區", "石岡區", "外埔區", "大安區", "烏日區", "大肚區", "龍井區", "霧峰區", "太平區", "大里區", "和平區"],
    "臺南市": ["中西區", "東區", "南區", "北區", "安平區", "安南區", "永康區", "歸仁區", "新化區", "左鎮區", "玉井區", "楠西區", "南化區", "仁德區", "關廟區", "龍崎區", "官田區", "麻豆區", "佳里區", "西港區", "七股區", "將軍區", "學甲區", "北門區", "新營區", "後壁區", "白河區", "東山區", "六甲區", "下營區", "柳營區", "鹽水區", "善化區", "大內區", "山上區", "新市區", "安定區"],
    "高雄市": ["鹽埕區", "鼓山區", "左營區", "楠梓區", "三民區", "新興區", "前金區", "苓雅區", "前鎮區", "旗津區", "小港區", "鳳山區", "林園區", "大寮區", "大樹區", "大社區", "仁武區", "鳥松區", "岡山區", "橋頭區", "燕巢區", "田寮區", "阿蓮區", "路竹區", "湖內區", "茄萣區", "永安區", "彌陀區", "梓官區", "旗山區", "美濃區", "六龜區", "甲仙區", "杉林區", "內門區", "茂林區", "桃源區", "那瑪夏區"],
    "宜蘭縣": ["宜蘭市", "羅東鎮", "蘇澳鎮", "頭城鎮", "礁溪鄉", "壯圍鄉", "員山鄉", "冬山鄉", "五結鄉", "三星鄉", "大同鄉", "南澳鄉"],
    "桃園市": ["桃園區", "中壢區", "平鎮區", "八德區", "楊梅區", "蘆竹區", "大溪區", "龍潭區", "龜山區", "大園區", "觀音區", "新屋區", "復興區"],
    "新竹縣": ["竹北市", "竹東鎮", "新埔鎮", "關西鎮", "湖口鄉", "新豐鄉", "芎林鄉", "橫山鄉", "北埔鄉", "寶山鄉", "峨眉鄉", "尖石鄉", "五峰鄉"],
    "苗栗縣": ["苗栗市", "頭份市", "竹南鎮", "後龍鎮", "通霄鎮", "苑裡鎮", "卓蘭鎮", "造橋鄉", "西湖鄉", "頭屋鄉", "公館鄉", "銅鑼鄉", "三義鄉", "大湖鄉", "獅潭鄉", "三灣鄉", "南庄鄉", "泰安鄉"],
    "彰化縣": ["彰化市", "員林市", "和美鎮", "鹿港鎮", "溪湖鎮", "二林鎮", "田中鎮", "北斗鎮", "花壇鄉", "芬園鄉", "大村鄉", "永靖鄉", "伸港鄉", "線西鄉", "福興鄉", "秀水鄉", "埔心鄉", "埔鹽鄉", "大城鄉", "芳苑鄉", "竹塘鄉", "社頭鄉", "二水鄉", "田尾鄉", "埤頭鄉", "溪州鄉"],
    "南投縣": ["南投市", "埔里鎮", "草屯鎮", "竹山鎮", "集集鎮", "名間鄉", "鹿谷鄉", "中寮鄉", "魚池鄉", "國姓鄉", "水里鄉", "信義鄉", "仁愛鄉"],
    "雲林縣": ["斗六市", "斗南鎮", "虎尾鎮", "西螺鎮", "土庫鎮", "北港鎮", "古坑鄉", "大埤鄉", "莿桐鄉", "林內鄉", "二崙鄉", "崙背鄉", "麥寮鄉", "東勢鄉", "褒忠鄉", "臺西鄉", "元長鄉", "四湖鄉", "口湖鄉", "水林鄉"],
    "嘉義縣": ["太保市", "朴子市", "布袋鎮", "大林鎮", "民雄鄉", "溪口鄉", "新港鄉", "六腳鄉", "東石鄉", "義竹鄉", "鹿草鄉", "水上鄉", "中埔鄉", "竹崎鄉", "梅山鄉", "番路鄉", "大埔鄉", "阿里山鄉"],
    "屏東縣": ["屏東市", "潮州鎮", "東港鎮", "恆春鎮", "萬丹鄉", "長治鄉", "麟洛鄉", "九如鄉", "里港鄉", "鹽埔鄉", "高樹鄉", "萬巒鄉", "內埔鄉", "竹田鄉", "新埤鄉", "枋寮鄉", "新園鄉", "崁頂鄉", "林邊鄉", "南州鄉", "佳冬鄉", "琉球鄉", "車城鄉", "滿州鄉", "枋山鄉", "三地門鄉", "霧臺鄉", "瑪家鄉", "泰武鄉", "來義鄉", "春日鄉", "獅子鄉", "牡丹鄉"],
    "臺東縣": ["臺東市", "成功鎮", "關山鎮", "卑南鄉", "鹿野鄉", "池上鄉", "東河鄉", "長濱鄉", "太麻里鄉", "大武鄉", "綠島鄉", "海端鄉", "延平鄉", "金峰鄉", "達仁鄉", "蘭嶼鄉"],
    "花蓮縣": ["花蓮市", "鳳林鎮", "玉里鎮", "新城鄉", "吉安鄉", "壽豐鄉", "光復鄉", "豐濱鄉", "瑞穗鄉", "富里鄉", "秀林鄉", "萬榮鄉", "卓溪鄉"],
    "澎湖縣": ["馬公市", "湖西鄉", "白沙鄉", "西嶼鄉", "望安鄉", "七美鄉"],
    "基隆市": ["中正區", "七堵區", "暖暖區", "仁愛區", "中山區", "安樂區", "信義區"],
    "新竹市": ["東區", "北區", "香山區"],
    "嘉義市": ["東區", "西區"],
    "連江縣": ["南竿鄉", "北竿鄉", "莒光鄉", "東引鄉"],
    "金門縣": ["金城鎮", "金湖鎮", "金沙鎮", "金寧鄉", "烈嶼鄉", "烏坵鄉"]
}


# ===== LOCATION_ORDER_START =====
COUNTY_ORDER = [
    "臺北市", "新北市", "基隆市", "桃園市", "新竹市", "新竹縣", "宜蘭縣",
    "苗栗縣", "臺中市", "彰化縣", "南投縣", "雲林縣", "嘉義市", "嘉義縣",
    "臺南市", "高雄市", "屏東縣", "花蓮縣", "臺東縣", "澎湖縣", "金門縣", "連江縣"
]

TOWN_ORDER = {
    "臺北市": ["中正區", "大同區", "中山區", "松山區", "大安區", "萬華區", "信義區", "士林區", "北投區", "內湖區", "南港區", "文山區"],

    "新北市": ["板橋區", "三重區", "中和區", "永和區", "新莊區", "新店區", "樹林區", "鶯歌區", "三峽區", "淡水區", "汐止區", "瑞芳區", "土城區", "蘆洲區", "五股區", "泰山區", "林口區", "深坑區", "石碇區", "坪林區", "三芝區", "石門區", "八里區", "平溪區", "雙溪區", "貢寮區", "金山區", "萬里區", "烏來區"],

    "基隆市": ["仁愛區", "信義區", "中正區", "中山區", "安樂區", "暖暖區", "七堵區"],

    "桃園市": ["桃園區", "中壢區", "大溪區", "楊梅區", "蘆竹區", "大園區", "龜山區", "八德區", "龍潭區", "平鎮區", "新屋區", "觀音區", "復興區"],

    "新竹市": ["東區", "北區", "香山區"],

    "新竹縣": ["竹北市", "竹東鎮", "新埔鎮", "關西鎮", "湖口鄉", "新豐鄉", "芎林鄉", "橫山鄉", "北埔鄉", "寶山鄉", "峨眉鄉", "尖石鄉", "五峰鄉"],

    "宜蘭縣": ["宜蘭市", "羅東鎮", "蘇澳鎮", "頭城鎮", "礁溪鄉", "壯圍鄉", "員山鄉", "冬山鄉", "五結鄉", "三星鄉", "大同鄉", "南澳鄉"],

    "苗栗縣": ["苗栗市", "頭份市", "苑裡鎮", "通霄鎮", "竹南鎮", "後龍鎮", "卓蘭鎮", "大湖鄉", "公館鄉", "銅鑼鄉", "南庄鄉", "頭屋鄉", "三義鄉", "西湖鄉", "造橋鄉", "三灣鄉", "獅潭鄉", "泰安鄉"],

    "臺中市": ["中區", "東區", "南區", "西區", "北區", "西屯區", "南屯區", "北屯區", "豐原區", "東勢區", "大甲區", "清水區", "沙鹿區", "梧棲區", "后里區", "神岡區", "潭子區", "大雅區", "新社區", "石岡區", "外埔區", "大安區", "烏日區", "大肚區", "龍井區", "霧峰區", "太平區", "大里區", "和平區"],

    "彰化縣": ["彰化市", "鹿港鎮", "和美鎮", "線西鄉", "伸港鄉", "福興鄉", "秀水鄉", "花壇鄉", "芬園鄉", "員林市", "溪湖鎮", "田中鎮", "大村鄉", "埔鹽鄉", "埔心鄉", "永靖鄉", "社頭鄉", "二水鄉", "北斗鎮", "二林鎮", "田尾鄉", "埤頭鄉", "芳苑鄉", "大城鄉", "竹塘鄉", "溪州鄉"],

    "南投縣": ["南投市", "埔里鎮", "草屯鎮", "竹山鎮", "集集鎮", "名間鄉", "鹿谷鄉", "中寮鄉", "魚池鄉", "國姓鄉", "水里鄉", "信義鄉", "仁愛鄉"],

    "雲林縣": ["斗六市", "斗南鎮", "虎尾鎮", "西螺鎮", "土庫鎮", "北港鎮", "古坑鄉", "大埤鄉", "莿桐鄉", "林內鄉", "二崙鄉", "崙背鄉", "麥寮鄉", "東勢鄉", "褒忠鄉", "臺西鄉", "元長鄉", "四湖鄉", "口湖鄉", "水林鄉"],

    "嘉義市": ["東區", "西區"],

    "嘉義縣": ["太保市", "朴子市", "布袋鎮", "大林鎮", "民雄鄉", "溪口鄉", "新港鄉", "六腳鄉", "東石鄉", "義竹鄉", "鹿草鄉", "水上鄉", "中埔鄉", "竹崎鄉", "梅山鄉", "番路鄉", "大埔鄉", "阿里山鄉"],

    "臺南市": ["新營區", "鹽水區", "白河區", "柳營區", "後壁區", "東山區", "麻豆區", "下營區", "六甲區", "官田區", "大內區", "佳里區", "學甲區", "西港區", "七股區", "將軍區", "北門區", "新化區", "善化區", "新市區", "安定區", "山上區", "玉井區", "楠西區", "南化區", "左鎮區", "仁德區", "歸仁區", "關廟區", "龍崎區", "永康區", "東區", "南區", "北區", "安南區", "安平區", "中西區"],

    "高雄市": ["鹽埕區", "鼓山區", "左營區", "楠梓區", "三民區", "新興區", "前金區", "苓雅區", "前鎮區", "旗津區", "小港區", "鳳山區", "林園區", "大寮區", "大樹區", "大社區", "仁武區", "鳥松區", "岡山區", "橋頭區", "燕巢區", "田寮區", "阿蓮區", "路竹區", "湖內區", "茄萣區", "永安區", "彌陀區", "梓官區", "旗山區", "美濃區", "六龜區", "甲仙區", "杉林區", "內門區", "茂林區", "桃源區", "那瑪夏區"],

    "屏東縣": ["屏東市", "潮州鎮", "東港鎮", "恆春鎮", "萬丹鄉", "長治鄉", "麟洛鄉", "九如鄉", "里港鄉", "鹽埔鄉", "高樹鄉", "萬巒鄉", "內埔鄉", "竹田鄉", "新埤鄉", "枋寮鄉", "新園鄉", "崁頂鄉", "林邊鄉", "南州鄉", "佳冬鄉", "琉球鄉", "車城鄉", "滿州鄉", "枋山鄉", "三地門鄉", "霧臺鄉", "瑪家鄉", "泰武鄉", "來義鄉", "春日鄉", "獅子鄉", "牡丹鄉"],

    "花蓮縣": ["花蓮市", "鳳林鎮", "玉里鎮", "新城鄉", "吉安鄉", "壽豐鄉", "光復鄉", "豐濱鄉", "瑞穗鄉", "富里鄉", "秀林鄉", "萬榮鄉", "卓溪鄉"],

    "臺東縣": ["臺東市", "成功鎮", "關山鎮", "卑南鄉", "大武鄉", "太麻里鄉", "東河鄉", "長濱鄉", "鹿野鄉", "池上鄉", "綠島鄉", "延平鄉", "海端鄉", "達仁鄉", "金峰鄉", "蘭嶼鄉"],

    "澎湖縣": ["馬公市", "湖西鄉", "白沙鄉", "西嶼鄉", "望安鄉", "七美鄉"],

    "金門縣": ["金城鎮", "金沙鎮", "金湖鎮", "金寧鄉", "烈嶼鄉", "烏坵鄉"],

    "連江縣": ["南竿鄉", "北竿鄉", "莒光鄉", "東引鄉"]
}

try:
    TOWN_MAP.update(TOWN_ORDER)
except Exception:
    TOWN_MAP = TOWN_ORDER
# ===== LOCATION_ORDER_END =====




COUNTY_ORDER = [
    "臺北市",
    "新北市",
    "基隆市",
    "桃園市",
    "新竹市",
    "新竹縣",
    "宜蘭縣",
    "苗栗縣",
    "臺中市",
    "彰化縣",
    "南投縣",
    "雲林縣",
    "嘉義市",
    "嘉義縣",
    "臺南市",
    "高雄市",
    "屏東縣",
    "花蓮縣",
    "臺東縣",
    "澎湖縣",
    "金門縣",
    "連江縣"
]



clothing_map = {
    "A": "無袖上衣 / 背心 + 涼感短褲",
    "B": "短袖上衣 + 短褲",
    "C": "短袖上衣 + 及膝短褲",
    "D": "短袖上衣 + 七分褲",
    "E": "針織短衫 + 七分褲",
    "F": "短袖上衣 + 薄長褲",
    "G": "薄長袖 + 薄長褲",
    "H": "薄長袖 + 棉褲",
    "I": "針織長袖 + 棉褲",
    "J": "帽 T / 大學 T + 厚長褲",
    "K": "刷毛帽 T + 厚長褲",
    "L": "發熱衣 + 刷毛長褲",
    "M": "厚毛衣 + 刷毛長褲",
    "N": "高領毛衣 + 刷毛防風長褲",
    "O": "極暖發熱衣 + 刷毛防風長褲"
}

umbrella_map = {
    "X": "無需攜帶雨具",
    "Y": "可斟酌是否攜帶雨具",
    "Z": "需要攜帶雨具"
}

coat_map = {
    1: "不需穿著外套",
    2: "薄外套",
    3: "防風外套",
    4: "保暖外套"
}


def normalize_tw(text):
    return text.strip().replace("台", "臺")


def to_number(value):
    if value is None:
        return None
    match = re.search(r"-?\d+(\.\d+)?", str(value))
    if match:
        return float(match.group())
    return None


def decode_target(target):
    target = int(target)
    value = target - 1
    clothing_index = value // 12
    remain = value % 12
    umbrella_index = remain // 4
    coat_type = remain % 4 + 1
    clothing_code = chr(clothing_index + 65)
    umbrella_code = chr(umbrella_index + 88)

    return {
        "clothing": clothing_map.get(clothing_code, "未知衣著"),
        "umbrella": umbrella_map.get(umbrella_code, "未知雨具建議"),
        "coat": coat_map.get(coat_type, "未知外套")
    }


def parse_cwa_time(time_str):
    dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TZ)
    else:
        dt = dt.astimezone(TZ)
    return dt


def get_time_string(time_item):
    return (
        time_item.get("DataTime")
        or time_item.get("dataTime")
        or time_item.get("StartTime")
        or time_item.get("startTime")
    )


def get_element_value(time_item, prefer_key=None):
    values = time_item.get("ElementValue") or time_item.get("elementValue") or []

    if not values:
        return None

    first = values[0]

    if isinstance(first, dict):
        if prefer_key and prefer_key in first and first[prefer_key] not in [None, ""]:
            return first[prefer_key]

        keys = [
            "ProbabilityOfPrecipitation",
            "PoP",
            "PoP6h",
            "PoP12h",
            "ComfortIndexDescription",
            "ComfortIndex",
            "Weather",
            "Temperature",
            "RelativeHumidity",
            "ApparentTemperature",
            "WindSpeed",
            "value",
            "Value"
        ]

        for key in keys:
            if key in first and first[key] not in [None, ""]:
                return first[key]

        for value in first.values():
            if value not in [None, ""]:
                return value

    return first


def fetch_cwa_weather(county):
    county = normalize_tw(county)
    dataset_id = COUNTY_DATASET.get(county)

    if dataset_id is None:
        raise ValueError("找不到這個縣市的資料集")

    url = CWA_BASE_URL + dataset_id
    params = {
        "Authorization": API_KEY,
        "format": "JSON"
    }

    response = requests.get(url, params=params, timeout=20, verify=False)
    response.raise_for_status()
    return response.json()


def find_location(cwa_data, town):
    town = normalize_tw(town)
    records = cwa_data.get("records", {})
    groups = records.get("Locations") or records.get("locations") or []

    for group in groups:
        county_name = group.get("LocationsName") or group.get("locationsName") or ""
        locations = group.get("Location") or group.get("location") or []

        for loc in locations:
            loc_name = loc.get("LocationName") or loc.get("locationName") or ""
            if town == loc_name:
                return county_name, loc

    return None, None



def guess_weather_icon_from_text(weather_text):
    """
    如果 API 沒有成功抓到 WeatherCode，就用天氣文字保底判斷。
    有對應到才回傳 SVG，沒對應到就回傳空字串。
    """
    text = str(weather_text or "")

    if not text:
        return ""

    # 優先順序很重要：雷雨 > 雪 > 霧 > 雨 > 晴雲 > 晴 > 多雲 > 陰
    if "雷" in text:
        return "19.svg"

    if "雪" in text or "冰" in text:
        return "57.svg"

    if "霧" in text:
        return "40.svg"

    if "雨" in text or "陣雨" in text:
        return "12.svg"

    if "晴" in text and "雲" in text:
        return "05.svg"

    if "晴" in text:
        return "01.svg"

    if "多雲" in text or "雲" in text:
        return "09.svg"

    if "陰" in text:
        return "11.svg"

    return ""



def normalize_weather_code_v2(value):
    """把中央氣象署天氣代碼整理成 01、02、03 這種格式。"""
    if value is None:
        return ""

    text = str(value).strip()

    if not text:
        return ""

    match = re.search(r"\d+", text)

    if not match:
        return ""

    return f"{int(match.group()):02d}"


def extract_weather_code_from_time_v2(time_item):
    """從中央氣象署 Wx 的 time 資料裡抓 WeatherCode。"""
    if not isinstance(time_item, dict):
        return ""

    values = time_item.get("ElementValue") or time_item.get("elementValue") or []

    if isinstance(values, dict):
        values = [values]

    for item in values:
        if not isinstance(item, dict):
            continue

        for key in ["WeatherCode", "weatherCode", "weather_code"]:
            code = normalize_weather_code_v2(item.get(key))
            if code:
                return code

        measure = str(
            item.get("Measures")
            or item.get("measures")
            or item.get("Measure")
            or item.get("measure")
            or ""
        )

        value = item.get("Value") or item.get("value") or ""

        if (
            "WeatherCode" in measure
            or "天氣代碼" in measure
            or "天氣現象代碼" in measure
            or "天氣編號" in measure
            or "天氣現象編號" in measure
        ):
            code = normalize_weather_code_v2(value)
            if code:
                return code

    for item in values:
        if not isinstance(item, dict):
            continue

        value = item.get("Value") or item.get("value") or ""

        if re.fullmatch(r"\s*\d+\s*", str(value)):
            code = normalize_weather_code_v2(value)
            if code:
                return code

    return ""


def get_weather_icon_file_v2(weather_code):
    """WeatherCode = 01 → static/weather_icon/01.svg。"""
    code = normalize_weather_code_v2(weather_code)

    if not code:
        return ""

    icon_path = Path(app.root_path) / "static" / "weather_icon" / f"{code}.svg"

    if icon_path.exists():
        return f"{code}.svg"

    return ""


def guess_weather_icon_from_text_v2(weather_text, forecast_time=None):
    """
    如果 API 沒有 WeatherCode，就用天氣文字保底判斷。
    這不是取代 WeatherCode，只是避免圖片空白。
    """
    text = str(weather_text or "")

    if not text:
        return ""

    hour = 12

    try:
        if forecast_time:
            hour = forecast_time.hour
    except Exception:
        hour = 12

    is_day = 6 <= hour < 18

    if "雪" in text or "冰" in text:
        return "57.svg"

    if "霧" in text:
        return "40.svg"

    if "雷" in text:
        return "19.svg" if is_day else "24.svg"

    if "雨" in text or "陣雨" in text:
        return "12.svg"

    if "晴" in text and "雲" in text:
        return "03.svg" if is_day else "04.svg"

    if "晴" in text:
        return "01.svg" if is_day else "02.svg"

    if "多雲" in text or "雲" in text:
        return "09.svg"

    if "陰" in text:
        return "11.svg"

    return ""




# ===== DAY_NIGHT_WEATHER_ICON_START =====
def choose_weather_icon_final_safe(weather_code, weather_text, forecast_time=None):
    """
    依照使用預報時間強制切換日間 / 夜間 SVG 圖示。
    06:00～17:59 使用日間圖示。
    18:00～05:59 使用夜間圖示。
    """
    text = str(weather_text or "")

    def normalize_code_local(code):
        try:
            return normalize_weather_code_v2(code)
        except Exception:
            pass

        if code is None:
            return ""

        s = str(code).strip()
        nums = "".join(ch for ch in s if ch.isdigit())

        if not nums:
            return ""

        return nums.zfill(2)

    code = normalize_code_local(weather_code)

    hour = 12
    try:
        if forecast_time:
            hour = forecast_time.hour
    except Exception:
        hour = 12

    # 中央氣象署圖示：06:00 開始用日間圖示，18:00 開始用夜間圖示
    is_day = 6 <= hour < 18

    # 日間圖示 → 夜間圖示
    day_to_night = {
        "01": "02",
        "03": "04",
        "05": "06",
        "07": "08",
        "23": "24",
        "25": "26",
        "27": "28",
        "29": "30",
        "32": "33",
        "34": "35",
        "36": "37",
        "38": "39",
        "41": "42",
        "44": "45",
        "47": "48",
        "50": "51"
    }

    # 夜間圖示 → 日間圖示
    night_to_day = {night: day for day, night in day_to_night.items()}

    # 優先使用 API 回傳的 weather code，但依照時間修正成日間 / 夜間版本
    if code:
        final_code = code

        if is_day and code in night_to_day:
            final_code = night_to_day[code]

        if not is_day and code in day_to_night:
            final_code = day_to_night[code]

        try:
            icon = get_weather_icon_file_v2(final_code)
            if icon:
                return icon
        except Exception:
            pass

    # 如果 API code 抓不到，才用文字保底
    if "雪" in text or "冰" in text:
        return "57.svg"

    if "霧" in text:
        return "40.svg"

    if "雷" in text:
        return "27.svg" if is_day else "28.svg"

    if "晴" in text and "雲" not in text and "雨" not in text and "雷" not in text:
        return "01.svg" if is_day else "02.svg"

    if "晴時多雲" in text:
        return "03.svg" if is_day else "04.svg"

    if "多雲時晴" in text:
        return "05.svg" if is_day else "06.svg"

    if "多雲" in text:
        return "05.svg" if is_day else "06.svg"

    if "陰" in text:
        return "11.svg"

    if "雨" in text or "陣雨" in text:
        return "12.svg"

    return ""
# ===== DAY_NIGHT_WEATHER_ICON_END =====



# ===== SAFE_WEATHER_ICON_FIX_START =====
def normalize_weather_code_final_safe(value):
    if value is None:
        return ""

    s = str(value).strip()

    if s.isdigit():
        n = int(s)
        if 1 <= n <= 57:
            return f"{n:02d}"

    m = re.search(r'(?<!\\d)([1-9]|[1-4]\\d|5[0-7])(?!\\d)', s)
    if m:
        n = int(m.group(1))
        if 1 <= n <= 57:
            return f"{n:02d}"

    return ""


def extract_weather_code_final_safe(time_item):
    """
    從中央氣象署 Wx 的 elementValue 裡抓 WeatherCode。
    不抓時間數字，避免 04:00 被誤判成 04.svg。
    """
    if not isinstance(time_item, dict):
        return ""

    value_lists = []

    for key in [
        "WeatherElementValue",
        "weatherElementValue",
        "ElementValue",
        "elementValue",
        "elementValues"
    ]:
        v = time_item.get(key)
        if isinstance(v, list):
            value_lists.extend(v)

    # 優先抓明確的 WeatherCode
    for item in value_lists:
        if not isinstance(item, dict):
            continue

        for key in ["WeatherCode", "weatherCode"]:
            code = normalize_weather_code_final_safe(item.get(key))
            if code:
                return code

        label = str(
            item.get("measures")
            or item.get("Measures")
            or item.get("measure")
            or item.get("Measure")
            or item.get("elementName")
            or item.get("ElementName")
            or ""
        )

        if "WeatherCode" in label or "weatherCode" in label or "天氣代碼" in label:
            for key in ["value", "Value", "parameterValue", "ParameterValue"]:
                code = normalize_weather_code_final_safe(item.get(key))
                if code:
                    return code

    # 只有在 Wx 的 elementValue 裡看到純數字 1~57，才當成天氣代碼
    for item in value_lists:
        if not isinstance(item, dict):
            continue

        for key in ["value", "Value", "parameterValue", "ParameterValue"]:
            raw = item.get(key)
            if raw is None:
                continue

            s = str(raw).strip()
            if s.isdigit():
                code = normalize_weather_code_final_safe(s)
                if code:
                    return code

    return ""


def choose_weather_icon_final_safe(weather_code, weather_text, forecast_time=None):
    """
    優先使用中央氣象署 API 的 WeatherCode。
    06:00～17:59 用日間圖示，18:00～05:59 用夜間圖示。
    """
    text = str(weather_text or "")
    code = normalize_weather_code_final_safe(weather_code)

    hour = 12
    try:
        if forecast_time:
            hour = forecast_time.hour
    except Exception:
        hour = 12

    is_day = 6 <= hour < 18

    day_to_night = {
        "01": "02",
        "03": "04",
        "05": "06",
        "07": "08",
        "23": "24",
        "25": "26",
        "27": "28",
        "29": "30",
        "32": "33",
        "34": "35",
        "36": "37",
        "38": "39",
        "41": "42",
        "44": "45",
        "47": "48",
        "50": "51"
    }

    night_to_day = {night: day for day, night in day_to_night.items()}

    if code:
        final_code = code

        if is_day and code in night_to_day:
            final_code = night_to_day[code]

        if not is_day and code in day_to_night:
            final_code = day_to_night[code]

        return f"{final_code}.svg"

    # 沒抓到 WeatherCode 才用文字保底，而且雨優先
    if "雷" in text and "雨" in text:
        return "19.svg"

    if "雨" in text or "陣雨" in text:
        return "12.svg"

    if "霧" in text:
        return "40.svg"

    if "雪" in text or "冰" in text:
        return "57.svg"

    if "晴時多雲" in text:
        return "03.svg" if is_day else "04.svg"

    if "多雲時晴" in text:
        return "05.svg" if is_day else "06.svg"

    if "晴" in text and "雲" in text:
        return "03.svg" if is_day else "04.svg"

    if "晴" in text:
        return "01.svg" if is_day else "02.svg"

    if "多雲" in text:
        return "05.svg" if is_day else "06.svg"

    if "陰" in text:
        return "11.svg"

    return ""
# ===== SAFE_WEATHER_ICON_FIX_END =====


def find_nearest_weather(location, target_time):
    elements = location.get("WeatherElement") or location.get("weatherElement") or []
    result = {}
    matched_times = []

    for element in elements:
        name = element.get("ElementName") or element.get("elementName") or ""
        times = element.get("Time") or element.get("time") or []

        field = None
        prefer_key = None

        if name in ["T", "溫度"]:
            field = "temp"
            prefer_key = "Temperature"

        elif name in ["RH", "相對濕度"]:
            field = "humidity"
            prefer_key = "RelativeHumidity"

        elif name in ["AT", "體感溫度"]:
            field = "apparent_temp"
            prefer_key = "ApparentTemperature"

        elif name in ["Wind", "風向風速", "風速"]:
            field = "wind_speed"
            prefer_key = "WindSpeed"

        elif name in ["Wx", "天氣現象"]:
            field = "weather"
            prefer_key = "Weather"

        elif "降雨機率" in name or "PoP" in name:
            field = "rain_prob"
            prefer_key = "ProbabilityOfPrecipitation"

        elif name in ["CI", "舒適度", "舒適度指數", "ComfortIndex", "Comfort"]:
            field = "comfort"
            prefer_key = "ComfortIndexDescription"

        if field is None:
            continue

        best_time = None
        best_value = None
        best_time_item = None

        for t in times:
            time_str = get_time_string(t)

            if not time_str:
                continue

            forecast_time = parse_cwa_time(time_str)
            value = get_element_value(t, prefer_key)

            if value is None:
                continue

            if best_time is None:
                best_time = forecast_time
                best_value = value
                best_time_item = t
            else:
                old_diff = abs((best_time - target_time).total_seconds())
                new_diff = abs((forecast_time - target_time).total_seconds())

                if new_diff < old_diff:
                    best_time = forecast_time
                    best_value = value
                    best_time_item = t

        if best_value is not None:
            result[field] = best_value
            matched_times.append(best_time)

            if field == "weather":
                weather_code = extract_weather_code_final_safe(best_time_item)
                weather_icon = choose_weather_icon_final_safe(weather_code, best_value, best_time)

                result["weather_code"] = weather_code
                result["weather_icon"] = weather_icon

    if (
        to_number(result.get("humidity")) is None
        or to_number(result.get("wind_speed")) is None
        or to_number(result.get("apparent_temp")) is None
    ):
        return None

    nearest_time = min(
        matched_times,
        key=lambda x: abs((x - target_time).total_seconds())
    )

    result["matched_time"] = nearest_time.strftime("%Y/%m/%d %H:%M")
    return result



@app.context_processor
def inject_template_data():
    return {
        "TOWN_MAP": TOWN_MAP,
        "COUNTY_ORDER": COUNTY_ORDER,
        "counties": COUNTY_ORDER
    }


@app.context_processor
def inject_location_template_data_v2():
    return {
        "TOWN_MAP": TOWN_MAP,
        "COUNTY_ORDER": COUNTY_ORDER,
        "counties": COUNTY_ORDER
    }


@app.context_processor
def inject_location_template_data_final():
    return {
        "TOWN_MAP": TOWN_MAP,
        "COUNTY_ORDER": COUNTY_ORDER,
        "counties": COUNTY_ORDER
    }

@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    error = None

    default_time = datetime.now(TZ) + timedelta(hours=1)

    form_date = default_time.strftime("%Y-%m-%d")
    form_hour = default_time.strftime("%H")
    form_minute = default_time.strftime("%M")
    form_county = "新北市"
    form_town = ""

    counties = list(COUNTY_DATASET.keys())
    hours = [f"{i:02d}" for i in range(24)]
    minutes = [f"{i:02d}" for i in range(60)]
    TOWN_MAP = globals()["TOWN_MAP"]

    if request.method == "POST":
        try:
            form_date = request.form.get("date", "")
            form_hour = request.form.get("hour", "")
            form_minute = request.form.get("minute", "")
            form_county = normalize_tw(request.form.get("county", ""))
            form_town = normalize_tw(request.form.get("town", ""))

            if not form_date or not form_hour or not form_minute or not form_county or not form_town:
                error = "請完整選擇日期、時間、縣市與鄉鎮市區"
                return render_template("main.html", **locals())

            form_time = f"{form_hour}:{form_minute}"
            now = datetime.now(TZ)
            target_time = datetime.fromisoformat(form_date + "T" + form_time).replace(tzinfo=TZ)

            if target_time < now:
                error = "只能選擇未來 24 小時內的時間"
                return render_template("main.html", **locals())

            if target_time > now + timedelta(hours=24):
                error = "只能選擇未來 24 小時內的時間"
                return render_template("main.html", **locals())

            cwa_data = fetch_cwa_weather(form_county)
            county_name, location = find_location(cwa_data, form_town)

            if location is None:
                error = "找不到這個地點，請確認縣市與鄉鎮市區是否相符"
                return render_template("main.html", **locals())

            weather_info = find_nearest_weather(location, target_time)

            if weather_info is None:
                error = "找不到可用的氣象資料，請換一個時間或地點"
                return render_template("main.html", **locals())

            temp = to_number(weather_info.get("temp"))
            humidity = to_number(weather_info.get("humidity"))
            wind_speed = to_number(weather_info.get("wind_speed"))
            apparent_temp = to_number(weather_info.get("apparent_temp"))
            rain_prob_number = to_number(weather_info.get("rain_prob"))

            if rain_prob_number is None:
                rain_prob = "無資料"
            else:
                rain_prob = f"{rain_prob_number:g}%"

            comfort = weather_info.get("comfort")

            if comfort is None or comfort == "無資料":
                if apparent_temp >= 33:
                    comfort = "悶熱"
                elif apparent_temp >= 29:
                    comfort = "稍悶熱"
                elif apparent_temp >= 23:
                    comfort = "舒適"
                elif apparent_temp >= 18:
                    comfort = "稍涼"
                else:
                    comfort = "寒冷"

            X = pd.DataFrame([{
                "RelativeHumidity": humidity,
                "WindSpeed": wind_speed,
                "ApparentTemperature": apparent_temp
            }])

            prediction = model.predict(X)[0]
            outfit = decode_target(prediction)

            result = {
                "location": form_county + " " + form_town,
                "target_time": target_time.strftime("%Y/%m/%d %H:%M"),
                "matched_time": weather_info["matched_time"],
                "weather": weather_info.get("weather", "無資料"),
                "temp": temp,
                "humidity": humidity,
                "wind_speed": wind_speed,
                "apparent_temp": apparent_temp,
                "rain_prob": rain_prob,
                "comfort": comfort,
                "weather_code": weather_info.get("weather_code", ""),
                "weather_icon": weather_info.get("weather_icon", ""),
                "clothing": outfit["clothing"],
                "umbrella": outfit["umbrella"],
                "coat": outfit["coat"]
            }

            if rain_prob_number is not None and rain_prob_number >= 60:
                result["umbrella"] = "需要攜帶雨具"

        except Exception as e:
            error = str(e)

    return render_template("main.html", **locals())




@app.route("/history")
def history():
    return render_template("history.html")



def normalize_weather_code(value):
    """把中央氣象署 WeatherCode 整理成 01、02、03 這種檔名格式。"""
    if value is None:
        return ""

    text = str(value).strip()

    if not text:
        return ""

    match = re.search(r"\d+", text)

    if not match:
        return ""

    number = int(match.group())

    return f"{number:02d}"


def extract_weather_code_from_time(time_item):
    """
    從中央氣象署 Wx 的 time 資料裡抓 WeatherCode。
    支援：
    1. WeatherCode 欄位
    2. elementValue 裡第二個 value 是數字代碼
    3. measures 裡含 WeatherCode / 天氣代碼
    """
    if not isinstance(time_item, dict):
        return ""

    values = time_item.get("elementValue", [])

    if isinstance(values, dict):
        values = [values]

    # 先找明確的 WeatherCode
    for item in values:
        if not isinstance(item, dict):
            continue

        for key in ["WeatherCode", "weatherCode", "weather_code"]:
            if key in item:
                code = normalize_weather_code(item.get(key))
                if code:
                    return code

        measure = str(item.get("measures", "") or item.get("measure", ""))
        value = item.get("value", item.get("Value", ""))

        if "WeatherCode" in measure or "天氣代碼" in measure or "天氣現象代碼" in measure or "天氣編號" in measure:
            code = normalize_weather_code(value)
            if code:
                return code

    # 再找 elementValue 裡的數字 value
    for item in values:
        if not isinstance(item, dict):
            continue

        value = item.get("value", item.get("Value", ""))

        if re.fullmatch(r"\s*\d+\s*", str(value)):
            code = normalize_weather_code(value)
            if code:
                return code

    return ""


def get_weather_icon_file(weather_code):
    """
    WeatherCode = 01 → static/weather_icon/01.svg
    如果找不到檔案，就回傳空字串，畫面不顯示圖。
    """
    code = normalize_weather_code(weather_code)

    if not code:
        return ""

    icon_dir = Path(app.root_path) / "static" / "weather_icon"
    filename = f"{code}.svg"

    if (icon_dir / filename).exists():
        return filename

    return ""

if __name__ == "__main__":
    app.run(debug=True)
