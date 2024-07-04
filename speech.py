# encoding=utf-8
# created @2024/7/2
# created by zhanzq
#

import json
import time
import base64
import urllib

from urllib.request import urlopen
from urllib.request import Request
from urllib.error import URLError
from urllib.parse import urlencode

timer = time.time


class DemoError(Exception):
    pass


def do_asr(speech_path):
    token = "24.390439a32cb6eba88fbd4ba8d5458fd6.2592000.1722496624.282335-16515363"
    speech_data = []
    with open(speech_path, 'rb') as speech_file:
        speech_data = speech_file.read()
    length = len(speech_data)
    if length == 0:
        raise DemoError('file %s length read 0 bytes' % speech_path)

    # 1537;  # 1537 表示识别普通话，使用输入法模型。根据文档填写PID，选择语言及识别模型
    params = {'cuid': '123456PYTHON', 'token': token, 'dev_pid': 1537}
    params_query = urlencode(params)

    FORMAT = speech_path[-3:]
    headers = {
        'Content-Type': 'audio/' + FORMAT + '; rate=16000',
        'Content-Length': length
    }

    url = "http://vop.baidu.com/server_api?" + params_query
    try:
        begin = timer()
        req = Request(url, speech_data, headers)
        f = urlopen(req)
        asr_data = f.read().decode("utf-8")
        asr_resp = json.loads(asr_data)
        result_str = asr_resp.get("result")[0]
        print("Request time cost %f" % (timer() - begin))
    except URLError as err:
        print('asr http response http code : ' + str(err.code))
        result_str = err.read().decode("utf-8")

    result_str = remove_punctuation(result_str)
    return result_str


def remove_punctuation(text):
    output = ""
    for ch in text:
        if ch not in ".,?!。，？！":
            output += ch

    return output


def get_file_content_as_base64(path, urlencoded=False):
    """
    获取文件base64编码
    :param path: 文件路径
    :param urlencoded: 是否对结果进行urlencoded
    :return: base64编码信息
    """
    with open(path, "rb") as f:
        content = base64.b64encode(f.read())
        if urlencoded:
            content = urllib.parse.quote_plus(content)
    return content


def main():
    speech_path = "recording.wav"
    # speech_path = "/Users/zhanzq/Downloads/e8185a2b-ff78-4d98-b9d1-0362553a1362.wav"
    # speech_path = "/Users/zhanzq/Downloads/859e52ac-9141-4891-8aae-577e4666900c.wav"
    asr = do_asr(speech_path)
    print(f"asr: {asr}")


if __name__ == "__main__":
    main()
