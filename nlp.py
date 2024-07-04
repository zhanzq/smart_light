import os
import time
import json
from flask import Flask, render_template, request, session, jsonify, redirect, url_for, render_template_string
from datetime import datetime
from tpl_service.tpl import TPL
from protocol import RoomInfo, Intent, Lightness
from util import convert_chinese_time_to_seconds

# 定义一个全局变量来保存定时器完成的状态
timer_completed = False

app = Flask(__name__)
app.secret_key = 'your_secret_key'

keyword_dct_path = "/Users/zhanzq/gitProjects/smart_light/data/keyword_dct.json"
tpl_service = TPL(keyword_dct_or_path=keyword_dct_path)
tpl_service.load_tpl(tpl_path="/Users/zhanzq/gitProjects/smart_light/data/template.json")


def get_user_id():
    if "login_time" not in session:
        session["login_time"] = time.ctime()
    user_id = str(hash(session['login_time']))[-6:]

    if "user_info" not in session:
        session["user_info"] = {user_id: {}}

    if "room_info" not in session["user_info"][user_id]:
        session["user_info"][user_id]["room_info"] = RoomInfo.get_instance()

    return user_id


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'login_time' in session:
        user_id = get_user_id()
        print(f'user_id: {user_id}, session: {session}')
        if 'user_info' not in session:
            session['user_info'] = {}
        if user_id not in session['user_info']:
            session['user_info'][user_id] = {'user_id': user_id, 'room_info': RoomInfo.get_instance()}
        user_info = session['user_info'][user_id]
        if request.method == 'POST':
            input_data = request.form
            if len(input_data) == 0:
                info_key = "user_id"
                info_value = user_id
            else:
                info_key = input_data["info_key"]
                info_value = input_data['info_value']
            user_info['info'][info_key] = info_value
            session["info"] = {info_key: info_value}
            session["user_info"].update({user_id: user_info})
        print(f"user_info: {user_info}")
        return render_template('index.html', user_info=user_info)
    else:
        print("not login before")
        print(session)
        session["login_time"] = time.ctime()
    if request.method == 'POST':
        session['login_time'] = datetime.utcnow()
        return render_template('index.html')
    return render_template('index.html')


@app.route('/', methods=['GET', 'POST'])
def index():
    # 测试
    # return render_template("test.html")
    room_info = get_room_info()
    living_room_image_path = room_info["客厅"]["image_path"]
    bedroom_image_path = room_info["卧室"]["image_path"]
    bathroom_image_path = room_info["卫生间"]["image_path"]
    dining_room_image_path = room_info["餐厅"]["image_path"]
    return render_template("house.html",
                           living_room_image_path=living_room_image_path,
                           bedroom_image_path=bedroom_image_path,
                           bathroom_image_path=bathroom_image_path,
                           dining_room_image_path=dining_room_image_path
                           )


@app.route('/nlu', methods=['POST'])
def process_text():
    input_text = request.json.get('input_text')
    nlu_info = do_nlu(input_text)

    update_room_info(nlu_info=nlu_info)
    return jsonify({'nlu_info': json.dumps(nlu_info, ensure_ascii=False, indent=4),
                    "user_info": json.dumps(get_user_info(), ensure_ascii=False, indent=4),
                    "room_info": json.dumps(get_room_info(), ensure_ascii=False, indent=4)
                    })


def get_room_info():
    user_id = get_user_id()
    room_info = session["user_info"][user_id]["room_info"]
    return room_info


def get_user_info():
    user_id = get_user_id()
    user_info = session["user_info"]
    return user_info


def update_room_info(nlu_info):
    user_id = get_user_id()
    user_info = session['user_info']
    room_info = user_info[user_id]["room_info"]
    intent = nlu_info.get("intent")
    default_room = user_info.get("room", "客厅")
    image_dir = "static/images/"
    # 更新上下文room信息
    room = nlu_info.get("slot").get("room")
    mode = nlu_info.get("slot").get("mode")
    if not room:
        room = default_room
    if not mode:
        mode = room_info[room]["mode"]
    user_info["room"] = room
    if intent == Intent.OPEN_DEVICE.code:
        room_info[room]["lightness"] = Lightness.OPEN.lightness
    elif intent == Intent.CLOSE_DEVICE.code:
        room_info[room]["lightness"] = Lightness.CLOSE.lightness
    elif intent == Intent.INCREASE_LIGHTNESS.code:
        lightness = room_info[room]["lightness"] + 1
        room_info[room]["lightness"] = min(lightness, Lightness.BRIGHTEST.lightness)
    elif intent == Intent.DECREASE_LIGHTNESS.code:
        lightness = room_info[room]["lightness"] - 1
        room_info[room]["lightness"] = max(lightness, Lightness.DARKEST.lightness)
    elif intent == Intent.SET_MODE.code:
        mode = nlu_info.get("slot").get("mode")
        room_info[room]["mode"] = mode
    elif intent == Intent.SET_LIGHTNESS.code:
        lightness = nlu_info.get("slot").get("lightness")
        lightness = convert_lightness(lightness)
        room_info[room]["lightness"] = lightness
    elif intent == Intent.COUNTDOWN.code:
        tm = nlu_info.get("slot").get("time")
        tm = convert_chinese_time_to_seconds(tm)
        open = nlu_info.get("slot").get("open")
        close = nlu_info.get("slot").get("close")

        # 启动一个定时器，tm秒后执行 `timer_task`
        time.sleep(tm)
        if open:
            room_info[room]["lightness"] = Lightness.OPEN.lightness
        elif close:
            room_info[room]["lightness"] = Lightness.CLOSE.lightness
        else:
            pass
    else:
        pass
    room_info[room]["image_path"] = os.path.join(image_dir, room, mode, f"{room_info[room]['lightness']}.jpg")
    user_info[user_id]["room_info"].update(room_info)
    session["user_info"] = user_info

    return


def convert_lightness(lightness):
    if lightness in ["最高", "最亮", "最大", "最明", "最高档", "最大档"]:
        return Lightness.BRIGHTEST.lightness
    elif lightness in ["最低", "最暗", "最小", "最黑", "最低档", "最小档"]:
        return Lightness.DARKEST.lightness
    elif "1" in lightness or "一" in lightness:
        return Lightness.DARKEST.lightness
    elif "2" in lightness or "二" in lightness:
        return Lightness.DIMMER.lightness
    elif "3" in lightness or "三" in lightness:
        return Lightness.MIDDEL.lightness
    elif "4" in lightness or "四" in lightness:
        return Lightness.BRIGHTER.lightness
    elif "5" in lightness or "五" in lightness:
        return Lightness.BRIGHTEST.lightness
    else:
        return Lightness.MIDDEL


def do_nlu(query):
    domain, intent, slot = tpl_service.match_tpl(query=query)
    nlu_info = {
        "domain": domain,
        "intent": intent,
        "slot": slot
    }
    # nlu_info = json.dumps(nlu_info, indent=4, ensure_ascii=False)

    return nlu_info

