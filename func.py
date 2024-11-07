import json
import time
import threading
import config
import re
tools = {'LLM_circuit_parameter_calculation': {'type': 'function', 'function': {'name': 'LLM_circuit_parameter_calculation', 'description': '电路参数设计函数，该函数定义了根据给定的电压、电流计算电路功率的功能，功率单位为千瓦', 'parameters': {'type': 'object', 'properties': {'voltage': {'description': '电压', 'type': 'int'}, 'current': {'description': '电流', 'type': 'int'}}, 'required': ['voltage', 'current']}}}, 'LLM_simulink_interact': {'type': 'function', 'function': {'name': 'LLM_simulink_interact', 'description': 'python与matlab/simulink的交互程序，该函数定义了从LLM输出中提取matlab程序并运行的功能', 'parameters': {'type': 'object', 'properties': {'matlab_code': {'description': '以字符串格式表示的matlab程序', 'type': 'str'}}, 'required': ['matlab_code']}}}, 'load_button_from_message': {'type': 'function', 'function': {'name': 'load_button_from_message', 'description': '按键内部参数提取函数，该函数定义了根据大语言模型的回答内容提取按钮内部参数的功能', 'parameters': {'type': 'object', 'properties': {'message': {'description': "用于提取信息的字符串，一般为历史对话中以{'button_x': {'button_name': '', 'user_prompt': '', 'system_prompt': '', 'api': 'default'}}的格式的系统输出", 'type': 'str'}}, 'required': ['message']}}}, 'function_example': {'type': 'function', 'function': {'name': 'function_example', 'description': '数学计算函数，可以根据提供的参数a和参数b计算结果', 'parameters': {'type': 'object', 'properties': {'a': {'description': '参数a', 'type': 'float'}, 'b': {'description': '参数b', 'type': 'float'}}, 'required': ['a', 'b']}}}}

def LLM_circuit_parameter_calculation(voltage, current):
    """
    电路参数设计函数，该函数定义了根据给定的电压、电流计算电路功率的功能
    :param voltage: 必要参数，表示电路的电压
    :param current: 必要参数，表示电路的电流
    :return：函数计算后的结果，表示为JSON格式的电路参数
    """
    return json.dumps(voltage * current * 0.001)

def LLM_simulink_interact(matlab_code):
    """
    python与matlab/simulink的交互程序，该函数定义了从LLM输出中提取matlab程序并运行的功能
    :param matlab_code: 必要参数，以字符串格式表示的matlab程序
    """

    def matlab_func(code):
        eng = matlab.engine.start_matlab()
        eng.eval(code, nargout=0)
        while config.matlab_threading:
            print('matlab working')
        print('matlab Quit')
    thread = threading.Thread(target=matlab_func, args=(matlab_code,))
    thread.start()
    return

def load_button_from_message(message):
    """
    按键内部参数提取函数，该函数定义了根据大语言模型的回答内容提取按钮内部参数的功能
    :param message: 必要参数，表示用于提取信息的字符串
    :return：函数从message中提取出符合格式的结果，表示为字典格式的按键内部参数
    """
    pattern = '[\'"]button_\\d+[\'"]:\\s*{[^}]+}'
    matches = re.findall(pattern, message)
    print(matches)
    extracted_content = {}
    for match in matches:
        try:
            button_dict = json.loads('{' + match.replace("'", '"') + '}')
            extracted_content.update(button_dict)
        except json.JSONDecodeError:
            print(f'无法解析以下内容: {match}')
    return extracted_content

def function_example(a, b):
    """
    电路参数设计函数，该函数定义了根据给定的参数a和参数b计算平方和的功能
    :param a: 必要参数，表示参数a
    :param b: 必要参数，表示参数b
    :return：函数计算后的结果，表示为JSON格式的平方和
    """
    c = a * a + b * b
    return json.dumps(str(c))