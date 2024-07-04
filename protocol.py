# encoding=utf-8
# created @2024/6/27
# created by zhanzq
#

class RoomType:
    def __init__(self, name, code, image_path=None):
        self.name = name
        self.code = code
        self.image_path = image_path


class Room:
    NULL = RoomType("未知房间", "unknown_room")
    LIVING_ROOM = RoomType("客厅", "living_room")
    BEDROOM = RoomType("卧室", "bedroom")
    DINING_ROOM = RoomType("餐厅", "dining_room")
    BATHROOM = RoomType("卫生间", "bathroom")


class ModeType:
    def __init__(self, name, code):
        self.name = name
        self.code = code


class Mode:
    NULL = ModeType("未知", "unknown_mode")
    NORMAL = ModeType("正常", "normal")
    LEISURE = ModeType("休闲", "leisure")


class LightnessType:
    def __init__(self, name, code, lightness):
        self.name = name
        self.code = code
        self.lightness = lightness


class Lightness:
    BRIGHTEST = LightnessType("最亮", "brightest", 5)
    BRIGHTER = LightnessType("比较亮", "brighter", 4)
    MIDDEL = LightnessType("亮度适中", "middle", 3)
    DIMMER = LightnessType("比较暗", "dimmer", 2)
    DARKEST = LightnessType("最暗", "darkest", 1)

    CLOSE = LightnessType("关灯", "close", 0)
    OPEN = LightnessType("开灯", "open", 3)


class RoomInfo:
    def __init__(self, user_info):
        self.user_info = user_info
        pass

    @staticmethod
    def get_instance():
        room_info = {
            Room.DINING_ROOM.name: {
                "mode": Mode.NORMAL.name,
                "lightness": Lightness.CLOSE.lightness,
                "image_path": "static/images/餐厅/close.png"
            },
            Room.LIVING_ROOM.name: {
                "mode": Mode.NORMAL.name,
                "lightness": Lightness.CLOSE.lightness,
                "image_path": "static/images/客厅/close.png"
            },
            Room.BEDROOM.name: {
                "mode": Mode.NORMAL.name,
                "lightness": Lightness.CLOSE.lightness,
                "image_path": "static/images/卧室/close.png"
            },
            Room.BATHROOM.name: {
                "mode": Mode.NORMAL.name,
                "lightness": Lightness.CLOSE.lightness,
                "image_path": "static/images/卫生间/close.png"
            }
        }

        return room_info


class IntentType:
    def __init__(self, name, code):
        self.name = name
        self.code = code


class Intent:
    NULL = IntentType("未知意图", "unknown_intent")
    OPEN_DEVICE = IntentType("开机", "openDevice")
    CLOSE_DEVICE = IntentType("关机", "closeDevice")
    INCREASE_LIGHTNESS = IntentType("亮度调高", "increaseLightness")
    DECREASE_LIGHTNESS = IntentType("亮度调低", "decreaseLightness")
    SET_LIGHTNESS = IntentType("亮度设置", "setLightness")
    SET_MODE = IntentType("模式设置", "setMode")
    COUNTDOWN = IntentType("倒计时", "countDown")

