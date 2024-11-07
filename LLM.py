from zhipuai import ZhipuAI
from openai import OpenAI
import json
from pathlib import Path
import config

# config.client = ZhipuAI(api_key=config.API_key)

def client_select():
    if config.LLM == 'GLM':
        config.client = ZhipuAI(api_key=config.API_key)
        config.model = 'glm-4'
    elif config.LLM == 'Kimi':
        config.client = OpenAI(api_key=config.API_key, base_url="https://api.moonshot.cn/v1",)
        config.model = 'moonshot-v1-128k'
    elif config.LLM == 'Qwen':
        config.client = OpenAI(api_key=config.API_key, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",)
        config.model = 'qwen-plus'


def ask_question(messages, tools, stream=True):
    if config.LLM == 'GLM':
        response = config.client.chat.completions.create(
            model=config.model,  # 填写需要调用的模型名称
            messages=messages,
            tools=tools,
            tool_choice="auto",  # auto is default, but we'll be explicit
            stream=stream
        )
    elif config.LLM == 'Kimi' or config.LLM == 'Qwen':
        response = config.client.chat.completions.create(
            model=config.model,  # 填写需要调用的模型名称
            messages=messages,
            stream=stream
        )

    # print(response)
    return response


def create_file(path):
    file_object = config.client.files.create(file=Path(path), purpose="file-extract")
    # 获取文本内容
    file_content = json.loads(config.client.files.content(file_id=file_object.id).content)["content"]
    message_content = f"上传的文件内容为：\n{file_content}\n"
    config.client.files.delete(file_id=file_object.id)
    return message_content


