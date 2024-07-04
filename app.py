import os
import json
from speech import do_asr
from nlp import do_nlu, convert_lightness

from flask import Flask, render_template, request, session, jsonify, Response
from protocol import RoomInfo, Intent, Lightness
from util import convert_chinese_time_to_seconds
import time

app = Flask(__name__)
app.secret_key = 'smart_light_system'


def get_user_id():
    """
    获取用户id，如果是新用户，则生成新的id
    :return:
    """
    if "login_time" not in session:
        session["login_time"] = time.ctime()
    user_id = str(hash(session['login_time']))[-6:]

    if "user_info" not in session:
        session["user_info"] = {user_id: {}}

    if user_id not in session["user_info"]:
        session["user_info"][user_id] = {}
    if "room_info" not in session["user_info"][user_id]:
        session["user_info"][user_id]["room_info"] = RoomInfo.get_instance()

    return user_id


def get_room_info():
    """
    获取房间信息
    :return:
    """
    user_id = get_user_id()
    room_info = session["user_info"][user_id]["room_info"]
    return room_info


def get_user_info():
    """
    获取用户信息
    :return:
    """
    user_id = get_user_id()
    user_info = session["user_info"]
    return user_info


def update_room_info(nlu_info):
    """
    更新用户的房间信息
    :param nlu_info: 解析出的NLU信息
    :return:
    """
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
    lightness = room_info[room]['lightness']
    if lightness != 0:
        room_info[room]["image_path"] = os.path.join(image_dir, room, mode, f"{room_info[room]['lightness']}.jpg")
    else:
        room_info[room]["image_path"] = os.path.join(image_dir, room, "close.png")
    user_info[user_id]["room_info"].update(room_info)
    session["user_info"] = user_info

    return


@app.route('/', methods=['GET', 'POST'])
def index():
    room_info = get_room_info()
    living_room_image_path = room_info["客厅"]["image_path"]
    bedroom_image_path = room_info["卧室"]["image_path"]
    bathroom_image_path = room_info["卫生间"]["image_path"]
    dining_room_image_path = room_info["餐厅"]["image_path"]
    return render_template("index.html",
                           living_room_image_path=living_room_image_path,
                           bedroom_image_path=bedroom_image_path,
                           bathroom_image_path=bathroom_image_path,
                           dining_room_image_path=dining_room_image_path
                           )


# 显示当前用户的信息
@app.route("/user_info")
def print_user_info():
    return render_template("user_info.html", room_info=get_room_info(), user_id=get_user_id())


# 显示所有用户的信息
@app.route("/all_user_info")
def print_all_user_info():
    all_user_info = get_user_info()
    return render_template("all_user_info.html", all_user_info=all_user_info)


# 显示当前用户的所有房间信息
@app.route("/room_info")
def print_room_info():
    room_info = get_room_info()
    # 使用 json.dumps 并设置 ensure_ascii=False
    response_json = json.dumps(room_info, indent=4, ensure_ascii=False)
    return Response(response=response_json, content_type="application/json; charset=utf-8")


# 调用百度的ASR服务，将语音转成文本
@app.route('/asr', methods=['POST'])
def asr():
    data = request.json
    speech_path = data.get('path')
    print(speech_path)
    if not speech_path or not os.path.exists(speech_path):
        return jsonify({'error': 'Invalid path'}), 400
    try:
        result = do_asr(speech_path)
        return jsonify({'transcript': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 进行语义解析
@app.route('/nlu', methods=['POST'])
def nlu():
    data = request.json
    text = data.get('query')
    print(text)

    nlu_info = do_nlu(text)
    update_room_info(nlu_info)
    room_info = get_room_info()
    return jsonify({'room_info': json.dumps(room_info, indent=4, ensure_ascii=False)})


UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# 上传录音文件到服务器(即本地)
@app.route('/upload', methods=['POST'])
def upload():
    print('Upload endpoint called')
    if 'audio' not in request.files:
        print('No file part')
        return jsonify({'error': 'No file part'}), 400

    file = request.files['audio']
    if file.filename == '':
        print('No selected file')
        return jsonify({'error': 'No selected file'}), 400

    if file:
        filename = 'recording.wav'
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        print('File saved at', filepath)
        return jsonify({'path': filepath}), 200


if __name__ == '__main__':
    app.run(debug=True)     # 默认端口为5000
