# Kimi: sk-ssIiJ9ew0DDFKRca55Xal467dkjsVzS7h7YqVSD1l1Qz8Oik
# GLM: ae7ad378a70b73614082aefef9ba63be.8faLo5y18RQwJ0sN

API_key = None
model = None
client = None

matlab_threading = True
LLM = "GLM"
tools = {
    'LLM_circuit_parameter_calculation': {
        "type": "function",
        "function": {
            "name": "LLM_circuit_parameter_calculation",
            "description": "电路参数设计函数，该函数定义了根据给定的电压、电流计算电路功率的功能",
            "parameters": {
                "type": "object",
                "properties": {
                    "voltage": {
                        "description": "电压",
                        "type": "int"
                    },
                    "current": {
                        "description": "电流",
                        "type": "int"
                    }
                },
                "required": ["voltage", "current"]
            }
        }
    },
    'LLM_simulink_interact': {
        "type": "function",
        "function": {
            "name": "LLM_simulink_interact",
            "description": "python与matlab/simulink的交互程序，该函数定义了从LLM输出中提取matlab程序并运行的功能",
            "parameters": {
                "type": "object",
                "properties": {
                    "matlab_code": {
                        "description": "以字符串格式表示的matlab程序",
                        "type": "str"
                    }
                },
                "required": ["matlab_code"]
            }
        }
    },
    'load_button_from_message': {
        "type": "function",
        "function": {
            "name": "load_button_from_message",
            "description": "按键内部参数提取函数，该函数定义了根据大语言模型的回答内容提取按钮内部参数的功能",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "description": "用于提取信息的字符串，一般为历史对话中以{'button_x': {'button_name': '', 'user_prompt': '', 'system_prompt': '', 'api': 'default'}}的格式的系统输出",
                        "type": "str"
                    }
                },
                "required": ["message"]
            }
        }
    }
}
