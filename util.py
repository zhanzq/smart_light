# encoding=utf-8
# created @2024/7/1
# created by zhanzq
#
import random
import re

# 汉字数字和对应的阿拉伯数字映射
chinese_to_digit = {
    '零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
    '十': 10, '百': 100, '千': 1000
}


def chinese_to_number(chinese):
    if chinese == '十':
        return 10
    total = 0
    unit = 1  # 初始单位是1
    num = 0
    for char in reversed(chinese):
        if char in chinese_to_digit:
            digit = chinese_to_digit[char]
            if digit >= 10:
                if digit > unit:
                    unit = digit
                else:
                    unit *= digit
            else:
                num += digit * unit
        total += num
        num = 0
    if num != 0:
        total += num
    return total


def convert_chinese_time_to_seconds(chinese_time):
    # 提取分钟和秒
    minute_pattern = re.compile(r'(\S+?)分钟?')
    second_pattern = re.compile(r'(\S+?)秒钟?')

    minutes = minute_pattern.search(chinese_time)
    seconds = second_pattern.search(chinese_time)

    total_seconds = 0

    if minutes:
        minute_str = minutes.group(1)
        total_seconds += chinese_to_number(minute_str) * 60

    if seconds:
        second_str = seconds.group(1)
        total_seconds += chinese_to_number(second_str)

    return total_seconds


def number_to_chinese(num):
    units = ['', '十', '百', '千', '万', '十万', '百万', '千万', '亿']
    digits = '零一二三四五六七八九'

    if num == 0:
        return digits[0]

    result = ''
    unit_position = 0
    while num > 0:
        part = num % 10
        if part != 0:
            result = digits[part] + units[unit_position] + result
        elif result and result[0] != digits[0]:
            result = digits[0] + result
        num //= 10
        unit_position += 1

    result = result.rstrip(digits[0])
    result = result.replace('一十', '十')

    return result


def main():
    # 示例用法
    # chinese_time = '三十秒'
    # seconds = convert_chinese_time_to_seconds(chinese_time)
    # print(seconds)  # 输出：2280
    for i in range(100):
        num = random.randint(1, 10000)
        chinese = number_to_chinese(num)
        num2 = chinese_to_number(chinese)
        print(f"chinese={chinese}, num: {num2}")


if __name__ == "__main__":
    main()
