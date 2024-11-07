import customtkinter
import threading
import LLM
# import matlab.engine
import json
import time
import config   # 自定义参数库，存储全局变量
import ast
import os
from CTkMessagebox import CTkMessagebox
import tkinter as tk
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import io
import re
import shutil
import sys

def latex_insert(App, latex_content):
    try:
        # Render LaTeX to image
        fig = plt.figure(figsize=(4, 0.3))  # Reduced height to match font size
        fig.text(0, 0.5, f"${latex_content}$", fontdict={'family': 'Times New Roman', 'fontsize': App.text_font_size, 'color': App.chatbox_text_color}, va='center')
        # plt.rcParams['text.usetex'] = True  # Enable LaTeX rendering
        plt.rcParams['font.size'] = App.text_font_size  # Set font size to match the text
        plt.rcParams['font.family'] = 'serif'  # Use a serif font for better LaTeX rendering
        # Save the figure to a buffer
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1, transparent=True)
        buf.seek(0)
        # Convert to PhotoImage
        image = Image.open(buf)
        photo = ImageTk.PhotoImage(image)
        # Insert the image into the text box
        # self.text_box._textbox.image_create(tk.END, image=photo)
        # self.text_box.image = photo  # Keep a reference
        plt.close(fig)
        return photo
    except Exception as e:
        App.textbox.insert_no_stream(customtkinter.END, "\n[ERROR] Failed to render LaTeX. Please check the format of the formula.\n", "red")
        App.textbox.after(0, lambda: App.textbox.see(customtkinter.END))
        print(f"Error rendering LaTeX: {e}")
        return None

def user_pormpts_stream(App, user_prompt):
    App.stop_generation()
    time.sleep(0.01)
    App.stop_generation_flag = False
    App.stop_generation_button.configure(state="normal")
    App.insert_image('PE Agent-谋略')
    App.textbox._textbox.config(state="normal")
    for chunk in user_prompt:
        if App.stop_generation_flag is True:
            App.stop_generation_flag = False
            return
        App.textbox.insert(customtkinter.END, chunk)
        App.textbox.after(0, lambda: App.textbox.see(customtkinter.END))
        time.sleep(0.001)
    App.textbox._textbox.config(state="disabled")
    App.stop_generation_button.configure(state="disabled")

def knowledge_lib_stream(App, stream):
    App.stop_generation()
    time.sleep(0.01)
    App.stop_generation_flag = False
    App.stop_generation_button.configure(state="normal")
    knowledge_Lib = ''
    App.insert_image('PE Agent-谋略')
    App.textbox.insert_no_stream(customtkinter.END, '总结内容如下：:\n')
    App.textbox._textbox.config(state="normal")
    for chunk in stream:
        if App.stop_generation_flag is True:
            App.stop_generation_flag = False
            return
        if chunk.choices[0].finish_reason == "length":
            App.textbox.insert(customtkinter.END, "\ntoken达到最大上限，请点击“新对话”\n", "red")
            return
        elif chunk.choices[0].finish_reason == "network_error":
            App.textbox.insert(customtkinter.END, "\nAPI key不可用或网络异常，请更换API并检查网络连接\n", "red")
            return
        delta = chunk.choices[0].delta
        if delta.content:
            knowledge_Lib += delta.content
            App.textbox.insert(customtkinter.END, delta.content)
            App.textbox.after(0, lambda: App.textbox.see(customtkinter.END))
    App.textbox._textbox.config(state="disabled")
    App.stop_generation_button.configure(state="disabled")
    knowledge_Lib += '\n'
    with open(os.path.join(App.agent_lib, App.peagent_family_lib, 'knowledge_lib.txt'), 'a', encoding='utf-8') as file:
        json.dump(knowledge_Lib, file, ensure_ascii=False, indent=4)

def process_stream(App, stream, tag1, tag2, tag3, second_process=False):
    App.stop_generation()
    time.sleep(0.01)
    App.stop_generation_flag = False
    App.stop_generation_button.configure(state="normal")
    mode = 0
    pre_char = ''
    global content
    content = ''
    latex_buffer = ''
    if second_process is False:
        App.insert_image('LLM')
    App.textbox._textbox.config(state="normal")
    for chunk in stream:
        if App.stop_generation_flag is True:
            App.stop_generation_flag = False
            return
        if chunk.choices[0].finish_reason == "tool_calls":
            # 解析函数调用结果
            tool_calls = chunk.choices[0].delta.tool_calls
            function_name = tool_calls[0].function.name
            function_to_call = App.available_tools[function_name]
            function_args = json.loads(tool_calls[0].function.arguments)
            # print('function_name', function_name)
            # print('function_args', function_args)
            function_response = function_to_call(**function_args)
            # print('function_response', function_response)

            # if function_name == 'load_button_from_message':
            #     for (key, value) in function_response.items():
            #         if key in App.prompts:
            #             App.prompts[key]['button_name'] = value['button_name']
            #             App.prompts[key]['user_prompt'] = value['user_prompt']
            #             App.prompts[key]['system_prompt'] = value['system_prompt']
            #             App.prompts[key]['api'] = value['api']
            #     with open(App.prompts_filename, 'w', encoding='utf-8') as file:
            #         file.write(json.dumps(App.prompts, ensure_ascii=False))
            #     App.load_button_texts()
            App.messages.append(chunk.choices[0].delta.model_dump())
            App.messages.append({
                "role": "tool",
                "content": f"{json.dumps(function_response)}",
                "tool_call_id": tool_calls[0].id
            })
            print('function_response', function_response)
            second_response = LLM.ask_question(App.messages, [], stream=True)
            second_process = True
            process_stream(App, second_response, tag1, tag2, tag3, second_process)
            return
        # 这部分不确定是否正确
        elif chunk.choices[0].finish_reason == "length":
            App.textbox.insert(customtkinter.END, "\ntoken达到最大上限，请点击“新对话”\n", "red")
            return
        elif chunk.choices[0].finish_reason == "network_error":
            App.textbox.insert(customtkinter.END, "\nAPI key不可用或网络异常，请更换API并检查网络连接\n", "red")
            return

        delta = chunk.choices[0].delta
        if delta.content:
            content += delta.content
            for char in delta.content:
                if mode == 0:
                    if char == '*':
                        mode = "*"
                    elif char == "#":
                        mode = '#'
                    elif char == '\\' and pre_char != '\\':
                        mode = '\\'
                    else:
                        App.textbox.insert(customtkinter.END, char)
                elif mode == "*":
                    if pre_char == '*' and char == '*':
                        continue
                    if pre_char != '*' and char == '*':
                        mode = '**'
                    else:
                        App.textbox.insert(customtkinter.END, char, tag2)
                elif mode == '**':
                    if char == "*":
                        continue
                    else:
                        App.textbox.insert(customtkinter.END, char, tag2)
                        mode = 0
                elif mode == '#':
                    if pre_char == '#' and char == '#':
                        continue
                    elif char == '\n':
                        App.textbox.insert(customtkinter.END, char, tag1)
                        mode = 0
                    else:
                        App.textbox.insert(customtkinter.END, char, tag1)
                elif mode == '\\':
                    if char == '[':
                        mode = 'latex'
                        latex_buffer = '\\['
                    elif char == '(':
                        mode = 'variable'
                        variable_buffer = '\\('
                    else:
                        App.textbox.insert(customtkinter.END, '\\' + char)
                        mode = 0
                elif mode == 'latex':
                    latex_buffer += char
                    if char == ']' and pre_char == '\\':
                        print(latex_buffer)
                        latex_photo = latex_insert(App, latex_buffer[2:-2])
                        App.textbox._textbox.image_create(tk.END, image=latex_photo)
                        if not hasattr(App.textbox, 'images'):
                            App.textbox.images = []
                        App.textbox.images.append(latex_photo)
                        mode = 0
                        latex_buffer = ''
                elif mode == 'variable':
                    variable_buffer += char
                    if char == ')' and pre_char == '\\':
                        print(variable_buffer)
                        variable_photo = latex_insert(App, variable_buffer[2:-2])
                        App.textbox._textbox.image_create(tk.END, image=variable_photo)
                        # Check if the 'images' attribute exists, if not, create it
                        if not hasattr(App.textbox, 'images'):
                            App.textbox.images = []
                        # Append the new image to the 'images' list to keep a reference
                        App.textbox.images.append(variable_photo)
                        # App.textbox.insert(customtkinter.END, variable_buffer[2:-2], tag3)
                        mode = 0
                        variable_buffer = ''

                pre_char = char
                App.textbox.after(0, lambda: App.textbox.see(customtkinter.END))
    App.messages.append({"role": "system", "content": content})
    App.save_data = content
    if App.PreProcess is True:
        # 删除App.textbox中最后一个'LLM:\n'后面的内容
        system_index = App.textbox.search('LLM:\n', '1.0', customtkinter.END)
        while system_index:
            last_system_index = system_index
            system_index = App.textbox.search('LLM:\n', f"{system_index} + 1c", customtkinter.END)
        system_index = last_system_index
        if system_index:
            end_index = App.textbox.index(f"{system_index} lineend")  # 获取'LLM:\n'所在行的行尾索引
            # 删除'LLM:\n'后面的内容
            # App.textbox.delete(f"{system_index} + 8c", customtkinter.END)
            App.textbox.delete(end_index, customtkinter.END)
        App.button_message_preprocess(content)
        App.textbox.after(0, lambda: App.textbox.see(customtkinter.END))
    # print(App.messages)
    App.stop_generation_button.configure(state="disabled")
    print("content:", content)
    App.textbox._textbox.config(state="disabled")
 
class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # configure window
        self.title("PE Agent-谋略")
        self.iconbitmap('photos\\pe_agent.ico')  # 设置软件图标
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.window_width = screen_width // 2
        self.window_height = screen_height-100
        # 计算窗口应该在的x和y坐标以使其居中
        x = (screen_width - self.window_width) // 2
        y = (screen_height - self.window_height) // 2

        self.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")
        self.minsize(800, 600)  # 设置窗口的最小宽度和高度
        # self.configure(fg_color="#2f5597")  # 深灰色背景，更具科技感
        
        
        # 设置字体和颜色
        self.text_font_size = 14
        self.border_width = 2
        self.text_font = ("微软雅黑", self.text_font_size)  # 使用更现代的字体
        self.button_font = ("黑体", 16, "bold")
        self.arrow_font = ("黑体", 40, "bold")
        self.mini_arrow_font = ("黑体", 20, "bold")
        self.title_font = ("黑体", 30, "bold")
        self.mini_title_font = ("黑体", 25, "bold")


        self.user_photo = ImageTk.PhotoImage(Image.open('photos\\user.png'))
        self.LLM_photo = ImageTk.PhotoImage(Image.open('photos\LLM.png'))
        self.pe_agent_photo = ImageTk.PhotoImage(Image.open('photos\pe_agent.png'))
        
        # 对话内容全局变量
        self.messages = []
        self.button_tool = []
        self.button_prompt = ''
        self.last_message = ''
        self.file_uploaded = ''
        self.save_data = ''
        self.PreProcess = False
        self.stop_generation_flag = False
        self.button_num = 7 + 2

        # Load API keys
        self.api_filename = 'api.txt'
        try:
            with open(self.api_filename, 'r', encoding="utf-8") as f:
                self.api_keys = json.load(f)
        except FileNotFoundError:
            self.api_keys = {
                "GLM": "",
                "Kimi": "",
                "Qwen": "",
                "selected_llm": "",  # 添加这一行来存储上次选择的LLM
                "selected_theme": "AI黑",
                "selected_agent": "说明文档",
            }
            with open(self.api_filename, "w", encoding="utf-8") as file:
                    json.dump(self.api_keys, file, ensure_ascii=False, indent=4)
        self.theme = self.api_keys["selected_theme"]
        self.llm_options = []
        for key in self.api_keys.keys():
            self.llm_options.append(key)
        self.llm_options.remove("selected_llm")
        self.llm_options.remove("selected_theme")
        self.llm_options.remove("selected_agent")

        self.messages_reserve = 'all'
        self.agent_lib = 'agent_library\\default'
        self.peagent_family_lib = 'peagent_family_lib'
        self.history_lib = 'history_lib'
        # self.knowledge_lib = 'knowledge_lib'
        self.file_uploaded_lib = 'file_uploaded_lib'
        if not os.path.exists(self.agent_lib):
            os.makedirs(self.agent_lib)
        if not os.path.exists(os.path.join(self.agent_lib, self.peagent_family_lib)):
            os.makedirs(os.path.join(self.agent_lib, self.peagent_family_lib))
        if not os.path.exists(os.path.join(self.agent_lib, self.history_lib)):
            os.makedirs(os.path.join(self.agent_lib, self.history_lib))
        # if not os.path.exists(os.path.join(self.agent_lib, self.knowledge_lib)):
        #     os.makedirs(os.path.join(self.agent_lib, self.knowledge_lib))
        if not os.path.exists(os.path.join(self.agent_lib, self.file_uploaded_lib)):
            os.makedirs(os.path.join(self.agent_lib, self.file_uploaded_lib))
        self.prompts_filename = os.path.join(self.agent_lib, self.peagent_family_lib, 'prompts.json')
        self.default_input_filename = os.path.join(self.agent_lib, self.peagent_family_lib, 'default_input.txt')
        self.func_filename = 'func.py'
        self.history_filename = os.path.join(self.agent_lib, self.history_lib, 'default_history.txt')
        with open(self.default_input_filename, 'w', encoding='utf-8') as file:
            file.write('让我们开始对话吧！')
        self.load_prompts()

        self.agent_lib = 'agent_library\\' + self.api_keys["selected_agent"]
        self.prompts_filename = os.path.join(self.agent_lib, self.peagent_family_lib, 'prompts.json')
        self.default_input_filename = os.path.join(self.agent_lib, self.peagent_family_lib, 'default_input.txt')
        self.func_filename = 'func.py'
        self.history_filename = os.path.join(self.agent_lib, self.history_lib, 'default_history.txt')

        self.execute_buttons = {}  # Initialize this list here
        self.button_index = [f'button_{i}' for i in range(0, self.button_num-1)]
        self.button_index.append('load_history')
        # print(self.button_index)

        with open('func.py', 'r', encoding='utf-8') as file:
            code = file.read()
        func_namespace = {}
        exec(code, func_namespace)

        self.tools_dict = func_namespace.get('tools', {})
        
        self.available_tools = {}
        self.tools = []
        for key, value in func_namespace.items():
            if callable(value):
                self.available_tools[key] = value
                self.tools.append(self.tools_dict[key])
        
        self.active_button = None  # 用于跟踪当前激活的按钮

        self.change_theme()
        self.configure(fg_color=self.primary_color)
        customtkinter.set_default_color_theme("blue")
        customtkinter.set_appearance_mode("Dark" if self.theme == "AI黑" else "Light")  
        self.prompts = self.load_prompts()  # 确保这行在 create_widgets 之前
        self.create_widgets()
        self.load_button_texts()  # 现在可以安全地调用这个方法

        if self.api_keys["selected_llm"] == "" or self.api_keys[self.api_keys["selected_llm"]] == "":
            self.open_api_input()
        else:
            config.API_key = self.api_keys[self.api_keys["selected_llm"]]
            config.LLM = self.api_keys["selected_llm"]
            LLM.client_select()


    def change_theme(self):
        if self.theme == "AI黑":
            self.primary_color = "#252526"
            self.secondary_color = "#4d4d4d"
            self.hover_color = "#2d2d2d"
            self.chatbox_color = "#3d3d3d"
            self.border_color = "#4d4d4d"
            self.active_button_color = "#5d5d5d"
            self.active_font_color = "#ffffff"
            self.chatbox_text_color = "#ffffff"
        elif self.theme == "电气蓝":
            self.primary_color = "#2f5597"  # 使用亮蓝色作为主色调，按钮的颜色
            self.secondary_color = "#ffffff"  # 深灰色作为次要颜色
            self.hover_color = "#005f9e"
            self.chatbox_color = "#ffffff"
            self.border_color = "#ffffff"
            self.active_button_color = "#ffffff"
            self.active_font_color = "#000000"
            self.chatbox_text_color = "#000000"
        self.text_color = "#ffffff"  # 白色文本
        
    def load_prompts(self):
        if not os.path.exists(self.prompts_filename):
            # 如果文件不存在，创建一个包含默认值的新文件
            default_prompts = {
                f'button_{i}': {'func_name': '', 'button_name': '', 'user_prompt': '',
                                'system_prompt': '', 'api': 'default', 'messages_reserve': 'all', 'file_name': '', 'file_content': ''}
                for i in range(0, self.button_num-1)
            }
            default_prompts['button_0']['button_name'] = 'Ai谋略'
            default_prompts['button_0']['user_prompt'] = '告诉我你的需求，我来帮你进行策划！'
            default_prompts['button_0']['system_prompt'] = '''你是一个专业的策划师，任务是把用户交给你的任务拆分成可执行的步骤。不要超过7步。
            你的输出格式是：{'button_x': {'button_name': '', 'user_prompt': '', 'system_prompt': '', 'api': 'default', 'messages_reserve': ''}}，
            其中button_x表示步骤名，x是从1开始的任意数字；button_name是显示在按钮上的文字，不要超过4个字；user_prompt是用户提示词，
            用于提示用户提供所需信息；system_prompt是系统提示词，用于输入给大语言模型指导其执行所需操作；api是大语言模型具体模型的选择，
            可选的有“default”、“GLM”、“Kimi”、“Qwen”，messages_reserve是选择是否保留历史对话的表示位，可选的有“all”、“partial”、“none”，
            分别对应保留全部对话、仅保留上一轮对话和清空历史对话。'''
            default_prompts['batch_modify'] = {'func_name': '', 'button_name': '批量\n修改',
                                               'user_prompt': '上一个回答已迁移至输入文本框，请在此基础上修改',
                                               'system_prompt': '''需要修改的内容以【提示词】的形式呈现，请按照提示词的指示对内容进行修改\n如果【提示词】位置处于文本中间，则修改【提示词】左边的内容\n如果【提示词】处于新的一行，则修改【提示词】上方的内容''', 
                                               'api': 'default', 'messages_reserve': 'all', 'file_name': '', 'file_content': ''}
            default_prompts['load_history'] = {'func_name': '', 'button_name': '历史加载',
                                               'user_prompt': '',
                                               'system_prompt': '', 'api': 'default',
                                               'messages_reserve': 'all', 'file_name': '', 'file_content': ''}
            default_prompts['knowledge_lib'] = {'func_name': '', 'button_name': '',
                                               'user_prompt': '',
                                               'system_prompt': '你是一个中文语言专家，你擅长于从大量的文本当中提炼出关键的信息，并用简洁的语言把表达出来，目标是在保留有用信息的前提下，让token尽量少。', 'api': 'default',
                                               'messages_reserve': 'all', 'file_name': '', 'file_content': ''}
            default_prompts['new_chat'] = {'func_name': '', 'button_name': '',
                                           'user_prompt': '历史对话已清空',
                                           'system_prompt': '', 'api': 'default',
                                           'messages_reserve': 'all', 'file_name': '', 'file_content': ''}
            # # 创建目录（如果不存在）
            # os.makedirs(os.path.dirname(self.prompts_filename), exist_ok=True)
            
            # # 创建新文件
            # with open(self.prompts_filename, "w", encoding="utf-8") as file:
            #     json.dump(default_prompts, file, ensure_ascii=False, indent=4)
            with open(self.prompts_filename, "w", encoding="utf-8") as file:
                json.dump(default_prompts, file, ensure_ascii=False, indent=4)
            return default_prompts
        
        try:
            with open(self.prompts_filename, "r", encoding="utf-8") as file:
                content = file.read().strip()
                if content:
                    return json.loads(content)
                else:
                    return {}
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {self.prompts_filename}. Using empty dict.")
            return {}

    def create_widgets(self):
        # 创建主框架
        main_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 创建左侧按钮面板
        left_panel = customtkinter.CTkFrame(main_frame, fg_color="transparent", corner_radius=10)

        left_panel.pack(side="left", fill="y", padx=(0, 20))

        # logo_frame = customtkinter.CTkFrame(left_panel, fg_color="transparent", height=20)
        # logo_frame.pack(fill="both", expand=True, padx=0, pady=(0, 0))
        # logo_frame.pack_propagate(0)
        logo_image = customtkinter.CTkImage(Image.open('photos\IIL_logo.png'), size=(130, 30))
        logo_label = customtkinter.CTkLabel(left_panel, image=logo_image, text='')
        logo_label.pack(pady=(0, 5))
        
        # 添加下拉按钮
        prompts_options = [f for f in os.listdir('agent_library') if os.path.isdir(os.path.join('agent_library', f))]
        # if '说明文档' not in prompts_options:
        #     prompts_options.append('说明文档')
        prompts_options.append('create new')
        self.prompts_var = customtkinter.StringVar(value=self.api_keys["selected_agent"])
        dropdown_frame = customtkinter.CTkFrame(left_panel, fg_color=self.border_color, corner_radius=10, height=32, width=130)
        dropdown_frame.pack(pady=(10, 0))
        dropdown_frame.pack_propagate(0)
        self.prompts_dropdown = customtkinter.CTkOptionMenu(dropdown_frame, variable=self.prompts_var,
                                                       values=prompts_options,
                                                       command=self.change_prompts_file,
                                                       font=self.button_font,
                                                       fg_color=self.primary_color,
                                                       button_color=self.primary_color,
                                                       button_hover_color=self.hover_color,
                                                       dropdown_fg_color=self.active_button_color,
                                                       dropdown_hover_color=self.hover_color,
                                                       text_color=self.text_color,
                                                       dropdown_text_color=self.chatbox_text_color,
                                                       corner_radius=10,
                                                       width=130-self.border_width*2,
                                                       height=32-self.border_width*2,
                                                       anchor="w")
        self.prompts_dropdown.pack(padx=self.border_width, pady=self.border_width, anchor="center")

        knowledge_lib_options = ['无知识库', '使用知识库']
        self.knowledge_lib_var = customtkinter.StringVar(value=knowledge_lib_options[0])
        dropdown_frame2 = customtkinter.CTkFrame(left_panel, fg_color=self.border_color, corner_radius=10, height=32, width=130)
        dropdown_frame2.pack(pady=(10, 10))
        dropdown_frame2.pack_propagate(0)
        self.knowledge_lib_dropdown = customtkinter.CTkOptionMenu(dropdown_frame2, variable=self.knowledge_lib_var,
                                                       values=knowledge_lib_options,
                                                       command=self.change_knowledge_lib,
                                                       font=self.button_font,
                                                       fg_color=self.primary_color,
                                                       button_color=self.primary_color,
                                                       button_hover_color=self.hover_color,
                                                       dropdown_fg_color=self.active_button_color,
                                                       dropdown_hover_color=self.hover_color,
                                                       text_color=self.text_color,
                                                       dropdown_text_color=self.chatbox_text_color,
                                                       corner_radius=10,
                                                       width=130-self.border_width*2,
                                                       height=32-self.border_width*2,
                                                       anchor="w")
        self.knowledge_lib_dropdown.pack(padx=self.border_width, pady=self.border_width, anchor="center")
        
        # 添加"新对话"按钮
        self.new_chat_button = customtkinter.CTkButton(left_panel, text="新对话", font=self.button_font,
                                                  text_color=self.text_color, fg_color=self.primary_color, 
                                                  border_color=self.border_color, border_width=self.border_width,
                                                  hover_color=self.hover_color, command=self.clear_chat,
                                                  corner_radius=10, width=130, height=60)
        self.new_chat_button.pack(pady=(10, 20))
        self.new_chat_button.bind("<Button-3>", lambda event: self.open_popup('new_chat'))
        
        # 生成按钮
        button_commands = []
        for i in range(0, self.button_num-1):
            button_commands.append(lambda i=i: self.system_prompts(f'button_{i}'))
        button_commands.insert(1, [])
        
        for i in range(self.button_num):
            if i != 1:
                row_frame = customtkinter.CTkFrame(left_panel, fg_color="transparent", width=130, height=30)
                row_frame.pack(pady=(0, 20) if i != 0 else (0, 10))
                row_frame.pack_propagate(0)
                button = customtkinter.CTkButton(row_frame, text='', font=self.button_font,
                                                text_color=self.text_color, command=lambda i=i: self.button_click(i, button_commands),
                                                fg_color=self.primary_color, hover_color=self.hover_color,
                                                border_color=self.border_color, border_width=self.border_width,
                                                width=130, height=30, corner_radius=10)
                button.pack(side="left", padx=0)
                button.bind("<Button-3>", lambda event, i=i: self.open_popup(f'button_{i if i == 0 else i-1}'))
                self.execute_buttons[self.button_index[i if i == 0 else i-1]] = button
            else:
                row_frame = customtkinter.CTkFrame(left_panel, fg_color="transparent", width=130, height=30)
                row_frame.pack(pady=(0, 25))
                row_frame.pack_propagate(0)
                triangle_button = customtkinter.CTkButton(row_frame, text="▼", font=self.button_font,
                                                        text_color=self.text_color,
                                                        command=lambda: self.load_button_from_message(self.messages[-1]['content'] if self.messages else ''),
                                                        fg_color=self.primary_color, hover_color=self.hover_color,
                                                        border_color=self.border_color, border_width=self.border_width,
                                                        width=130, height=30,
                                                        corner_radius=10)
                triangle_button.pack()               
                # Add a white horizontal line below the button
                line_frame = customtkinter.CTkFrame(left_panel, fg_color=self.border_color, width=130, height=2)
                line_frame.pack(pady=(0, 25))
                
    
        # 创建右侧聊天面板
        right_panel = customtkinter.CTkFrame(main_frame, fg_color="transparent")
        right_panel.pack(side="right", fill="both", expand=True)
        
        # 创建一个新的框架来包含textbox和inputbox
        textboxes_frame = customtkinter.CTkFrame(right_panel, fg_color="transparent")
        textboxes_frame.pack(side="left", fill="both", expand=True, pady=(0, 10))
        
        self.textbox = customtkinter.CTkTextbox(textboxes_frame, font=self.text_font, height=int(self.window_height*8/15),
                                                fg_color=self.chatbox_color, text_color=self.chatbox_text_color, corner_radius=15)
        self.textbox.pack(fill="both", expand=True, pady=(0, 10))
        self.textbox._textbox.tag_config("green", foreground="#00ff00", font=("微软雅黑", self.text_font_size, "bold"))  # 亮绿色
        self.textbox._textbox.tag_config("purple", foreground="#ff00ff")  # 亮紫色
        self.textbox._textbox.tag_config("red", foreground="#ff0000")  # 亮红色
        self.textbox._textbox.tag_config("formula", font=("微软雅黑", self.text_font_size, "italic"))  # 斜体
        self.textbox._textbox.tag_config("identity", font=("微软雅黑", self.text_font_size, "bold"))  # 粗体
        self.textbox.bind('<MouseWheel>', self.change_font)
        # 设置为只读模式
        self.textbox._textbox.config(state="disabled")
        # 重写insert方法以允许程序插入文本
        def insert_override(*args, **kwargs):
            self.textbox._textbox.config(state="normal")
            self.textbox._textbox.insert(*args, **kwargs) 
            self.textbox._textbox.config(state="disabled")
        self.textbox.insert_no_stream = insert_override
        

        arrow_frame = customtkinter.CTkFrame(textboxes_frame, fg_color="transparent")
        arrow_frame.pack(fill="both", expand=True, pady=(0, 10))
        arrow_button_width = 120  # 设置统一的按钮宽度

        self.load_history_button = customtkinter.CTkButton(arrow_frame, text="◀前文回顾", font=self.button_font,
                                                      text_color=self.text_color, fg_color=self.primary_color,
                                                      border_color=self.border_color, border_width=self.border_width,
                                                      hover_color=self.hover_color, command=self.load_history,
                                                      corner_radius=10, width=arrow_button_width, height=30)
        self.load_history_button.pack(side="left", padx=(0, 10), expand=True)
        self.load_history_button.bind("<Button-3>", lambda event: self.open_popup('load_history'))

        self.copy_button = customtkinter.CTkButton(arrow_frame, text='▼', font=self.button_font,
                                                   text_color=self.text_color, width=arrow_button_width, height=30,
                                                   border_color=self.border_color, border_width=self.border_width,
                                                   fg_color=self.primary_color, hover_color=self.hover_color,
                                                   command=self.copy_last_message, corner_radius=10)
        self.copy_button.pack(side="left", padx=(0, 10), expand=True)
        self.copy_button.bind("<Button-3>", lambda event: self.open_popup('batch_modify'))

        self.save_history_button = customtkinter.CTkButton(arrow_frame, text="内容存档▶", font=self.button_font,
                                                      text_color=self.text_color, fg_color=self.primary_color,
                                                      border_color=self.border_color, border_width=self.border_width,
                                                      hover_color=self.hover_color, command=self.open_batch_modify,
                                                      corner_radius=10, width=arrow_button_width, height=30)
        self.save_history_button.pack(side="left", padx=(0, 10), expand=True)

        # self.button_input = customtkinter.CTkButton(arrow_frame, text='⇧', font=self.arrow_font,
        #                                             text_color=self.text_color, width=arrow_button_width, height=40,
        #                                             border_color=self.border_color, border_width=self.border_width,
        #                                             fg_color=self.primary_color, hover_color=self.hover_color,
        #                                             command=self.input, corner_radius=10)
        # self.button_input.pack(side="left", expand=True)


        self.inputbox = customtkinter.CTkTextbox(textboxes_frame, font=self.text_font, height=int(self.window_height*5.6/15),
                                                 fg_color=self.chatbox_color, text_color=self.chatbox_text_color, corner_radius=15)
        # self.inputbox.pack(fill="both", expand=True)
        self.inputbox.pack(fill="x")
        self.inputbox.bind('<Return>', self.input_press)
        self.inputbox.bind('<MouseWheel>', self.change_font)
        self.inputbox.bind('<Control-s>', self.default_input_modify)
        try:
            with open(self.default_input_filename, 'r', encoding='utf-8') as file:
                self.inputbox.insert(customtkinter.END, file.read())
        except FileNotFoundError:
            with open(self.default_input_filename, 'w', encoding='utf-8') as file:
                file.write('让我们开始对话吧！')
                self.inputbox.insert(customtkinter.END, '让我们开始对话吧！')
        
        # 创建一个新的框架来包含所有按钮
        button_width = 75  # 设置统一的按钮宽度
        buttons_frame = customtkinter.CTkFrame(right_panel, fg_color="transparent",width=button_width)
        buttons_frame.pack(side="right", padx=(20, 0), fill="y")
        buttons_frame.pack_propagate(0)

        stop_button = customtkinter.CTkButton(buttons_frame, text="关于", font=self.button_font,
                                              text_color=self.text_color, fg_color=self.primary_color,
                                              border_color=self.border_color, border_width=self.border_width,
                                              hover_color=self.hover_color, command=self.related_information,
                                              corner_radius=10, width=button_width, height=40)
        stop_button.pack(pady=(0, 10))

        api_button = customtkinter.CTkButton(buttons_frame, text="API", font=self.button_font,
                                             text_color=self.text_color, fg_color=self.primary_color,
                                             border_color=self.border_color, border_width=self.border_width,
                                             hover_color=self.hover_color, command=self.open_api_input,
                                             corner_radius=10, width=button_width, height=40)
        api_button.pack(pady=(0, 10))

        self.import_button = customtkinter.CTkButton(buttons_frame, text="导入", font=self.button_font,
                                              text_color=self.text_color, fg_color=self.primary_color,
                                              border_color=self.border_color, border_width=self.border_width,
                                              hover_color=self.hover_color, command=self.import_agent,
                                              corner_radius=10, width=button_width, height=40)
        self.import_button.pack(pady=(0, 10))

        self.share_button = customtkinter.CTkButton(buttons_frame, text="导出", font=self.button_font,
                                              text_color=self.text_color, fg_color=self.primary_color,
                                              border_color=self.border_color, border_width=self.border_width,
                                              hover_color=self.hover_color, command=self.share_agent,
                                              corner_radius=10, width=button_width, height=40)
        self.share_button.pack(pady=(0, 10))

        stop_button = customtkinter.CTkButton(buttons_frame, text="Stop", font=self.button_font,
                                              text_color=self.text_color, fg_color=self.primary_color,
                                              border_color=self.border_color, border_width=self.border_width,
                                              hover_color=self.hover_color, command=self.stop_threading,
                                              corner_radius=10, width=button_width, height=40)
        stop_button.pack(pady=(0, 10))

        open_file_folder_button = customtkinter.CTkButton(buttons_frame, text="资料\n总库", font=self.button_font,
                                                text_color=self.text_color, fg_color=self.primary_color,
                                                border_color=self.border_color, border_width=self.border_width,
                                                hover_color=self.hover_color,
                                                command=lambda: self.open_file_folder(),
                                                corner_radius=10, width=button_width, height=40)
        open_file_folder_button.pack(pady=(0, 10))

        self.knowledge_Lib_button = customtkinter.CTkButton(buttons_frame, text="生成\n知识库", font=self.button_font,
                                                text_color=self.text_color, fg_color=self.primary_color,
                                                border_color=self.border_color, border_width=self.border_width,
                                                hover_color=self.hover_color,
                                                command=lambda: self.generate_knowledge_lib(),
                                                corner_radius=10, width=button_width, height=40)
        self.knowledge_Lib_button.pack(pady=(0, 10))
        self.knowledge_Lib_button.bind("<Button-3>", lambda event: self.open_popup('knowledge_lib'))

        self.stop_generation_button = customtkinter.CTkButton(buttons_frame, text="停止\n生成", font=self.button_font,
                                                text_color=self.text_color, fg_color=self.primary_color,
                                                border_color=self.border_color, border_width=self.border_width,
                                                hover_color=self.hover_color,
                                                command=self.stop_generation,
                                                corner_radius=10, width=button_width, height=40)
        self.stop_generation_button.pack(pady=(int(self.window_height*8/15)-50*8, 10))
        self.stop_generation_button.configure(state="disabled")

        self.button_input = customtkinter.CTkButton(buttons_frame, text='▲', font=self.mini_arrow_font,
                                                    text_color=self.text_color, width=button_width, height=80,
                                                    border_color=self.border_color, border_width=self.border_width,
                                                    fg_color=self.primary_color, hover_color=self.hover_color,
                                                    command=self.input, corner_radius=10)
        self.button_input.pack(side="bottom", pady=(0, max(0, 10)))
        
        upload_button = customtkinter.CTkButton(buttons_frame, text="上传\n文件", font=self.button_font,
                                                text_color=self.text_color, fg_color=self.primary_color,
                                                border_color=self.border_color, border_width=self.border_width,
                                                hover_color=self.hover_color,
                                                command=lambda: self.upload(),
                                                corner_radius=10, width=button_width, height=40)
        upload_button.pack(side="bottom", pady=(0, max(0, self.window_height*2.8/15-80)))

        # self.copy_button = customtkinter.CTkButton(buttons_frame, text='⇩', font=self.arrow_font,
        #                                            text_color=self.text_color, width=button_width, height=60,
        #                                            border_color=self.border_color, border_width=self.border_width,
        #                                            fg_color=self.primary_color, hover_color=self.hover_color,
        #                                            command=self.copy_last_message, corner_radius=10)
        # self.copy_button.pack(side="bottom", pady=(0, self.window_height*3/15-85))

        # save_history_button = customtkinter.CTkButton(buttons_frame, text="⇨", font=self.arrow_font,
        #                                               text_color=self.text_color, fg_color=self.primary_color,
        #                                               border_color=self.border_color, border_width=self.border_width,
        #                                               hover_color=self.hover_color, command=self.open_batch_modify,
        #                                               corner_radius=10, width=button_width, height=60)
        # save_history_button.pack(side="bottom", pady=(0, self.window_height*3/15-85))


    def input_press(self, event):
        if event.state & 0x0004:  # 0x0004 是 Control 键的掩码
            self.input()

    def change_font(self, event):
        if event.state & 0x0004 and event.delta > 0:  # 0x0004 是 Control 键的掩码，event.delta > 0 表示滚轮上滑
            self.text_font_size += 1  # Increase font size
        elif event.state & 0x0004 and event.delta < 0:  # event.delta < 0 表示滚轮下滑
            self.text_font_size -= 1  # Decrease font size
        if self.text_font_size < 5:
            self.text_font_size = 5
        elif self.text_font_size > 40:
            self.text_font_size = 40
        self.textbox.configure(font=("微软雅黑", self.text_font_size))
        self.inputbox.configure(font=("微软雅黑", self.text_font_size))
        self.textbox._textbox.tag_config("green", foreground="#00ff00",
                                         font=("微软雅黑", self.text_font_size, "bold"))  # 亮绿色
        self.textbox._textbox.tag_config("purple", foreground="#ff00ff")  # 亮紫色
        self.textbox._textbox.tag_config("formula", font=("微软雅黑", self.text_font_size, "italic"))  # 斜体
        self.textbox._textbox.tag_config("identity", font=("微软雅黑", self.text_font_size+2, "bold"))  # 粗体

    def default_input_modify(self, event):
        with open(self.default_input_filename, 'w', encoding='utf-8') as file:
            file.write(self.inputbox.get("1.0", "end"))

    def share_agent(self):
        # 打开文件选择对话框选择保存路径
        save_path = customtkinter.filedialog.askdirectory()
        if save_path:
            # 获取agent_lib的文件名
            agent_name = os.path.basename(self.agent_lib)
            # 构建目标路径
            destination = os.path.join(save_path, agent_name)
            try:
                # 复制整个目录
                shutil.copytree(self.agent_lib, destination)
                CTkMessagebox(title="成功", message="Agent导出成功!", icon="check")
            except Exception as e:
                CTkMessagebox(title="错误", message=f"导出失败: {str(e)}", icon="cancel")

    def import_agent(self):
        # 打开文件选择对话框选择要导入的文件夹
        import_path = customtkinter.filedialog.askdirectory()
        if import_path:
            # 获取选择的文件夹名称
            agent_name = os.path.basename(import_path)
            # 构建目标路径
            destination = os.path.join('agent_library', agent_name)
            try:
                # 复制整个目录
                shutil.copytree(import_path, destination)
                CTkMessagebox(title="成功", message="Agent导入成功!", icon="check")
            except Exception as e:
                CTkMessagebox(title="错误", message=f"导入失败: {str(e)}", icon="cancel")
            prompts_options = [f for f in os.listdir('agent_library') if os.path.isdir(os.path.join('agent_library', f))]
            # if '说明文档' not in prompts_options:
            #     prompts_options.append('说明文档')
            prompts_options.append('create new')
            self.prompts_dropdown.configure(values=prompts_options)
        

    def copy_last_message(self):
        if self.save_data:
            self.inputbox.delete("1.0", "end")  # Clear existing content
            self.inputbox.insert("1.0", self.save_data)  # Insert the saved data
        self.system_prompts('batch_modify')
        if self.active_button:
            self.active_button.configure(fg_color=self.primary_color, font=self.button_font, text_color=self.text_color)  # 恢复原来的颜色
        self.active_button = self.copy_button
        self.active_button.configure(fg_color=self.active_button_color, text_color=self.active_font_color)  # 设置为浅色

    def upload(self):
        file_path = customtkinter.filedialog.askopenfilename()
        if file_path:
            self.file_uploaded = LLM.create_file(file_path)
            # 复制文件到指定路径
            destination_path = os.path.join(self.agent_lib, self.file_uploaded_lib, os.path.basename(file_path))
            shutil.copy2(file_path, destination_path)
            self.thread = threading.Thread(target=user_pormpts_stream, args=(self, f'文件{os.path.basename(file_path)}上传完毕'))
            self.thread.start()
            self.textbox.after(0, lambda: self.textbox.see(customtkinter.END))

    def load_history(self):
        if not os.path.exists(self.history_filename):
            with open(self.history_filename, 'w', encoding='utf-8') as file:
                file.write('')
        with open(self.history_filename, "r", encoding="utf-8") as file:
            content = file.read()
        if content:
            self.prompts['load_history']['system_prompt'] = content
            with open(self.prompts_filename, "w", encoding="utf-8") as file:
                json.dump(self.prompts, file, ensure_ascii=False, indent=4)
        if self.prompts['load_history']['system_prompt']:
            self.system_prompts('load_history')
            self.insert_image('PE Agent-谋略')
            self.textbox.insert_no_stream(customtkinter.END, '历史对话记录已加载，具体内容如下所示：\n', 'purple')
            self.textbox.insert_no_stream(customtkinter.END, self.prompts['load_history']['system_prompt'])
            self.textbox.after(0, lambda: self.textbox.see(customtkinter.END))
            if self.active_button:
                self.active_button.configure(fg_color=self.primary_color, font=self.button_font, text_color=self.text_color)  # 恢复原来的颜色
            self.active_button = self.load_history_button
            self.active_button.configure(fg_color=self.active_button_color, text_color=self.active_font_color)  # 设置为浅色
        else:
            # self.insert_image('PE Agent-谋略')
            # self.textbox.insert(customtkinter.END, '历史对话记录为空，请先保存历史对话！')
            # self.textbox.after(0, lambda: self.textbox.see(customtkinter.END))  
            self.thread = threading.Thread(target=user_pormpts_stream, args=(self, '历史对话记录为空，请先保存历史对话！'))
            self.thread.start()

    def open_file_folder(self):
        os.startfile(os.path.join(self.agent_lib, self.file_uploaded_lib))

    def generate_knowledge_lib(self):
        try:
            prompt = self.prompts['knowledge_lib']['system_prompt']
            self.messages.append({"role": "user", "content": prompt})
            stream = LLM.ask_question(self.messages, [])
            self.thread = threading.Thread(target=knowledge_lib_stream, args=(self, stream))
            self.thread.start()
        except AttributeError as e:
            CTkMessagebox(title="提示", message="请补充API内容", icon="warning")
        except Exception as e:
            CTkMessagebox(title="提示", message="可能存在API欠费或网络异常等问题，请检查", icon="warning")
        
    def stop_generation(self):
        self.stop_generation_flag = True
        self.stop_generation_button.configure(state="disabled")

    def change_prompts_file(self, choice):
        if self.active_button:
            self.active_button.configure(fg_color=self.primary_color, font=self.button_font, text_color=self.text_color)  # 恢复原来的颜色
        self.active_button = None
        if choice == 'create new':
            self.create_new_agent()
        else:
            self.api_keys["selected_agent"] = choice
            with open(self.api_filename, "w", encoding="utf-8") as file:
                    json.dump(self.api_keys, file, ensure_ascii=False, indent=4)
            self.agent_lib = 'agent_library\\' + choice
            self.prompts_filename = os.path.join(self.agent_lib, self.peagent_family_lib, 'prompts.json')
            self.history_filename = os.path.join(self.agent_lib, self.history_lib, 'default_history.txt')
            self.default_input_filename = os.path.join(self.agent_lib, self.peagent_family_lib, 'default_input.txt')
            # if choice == '说明文档' and not os.path.exists(self.agent_lib):
            #     default_agent_path = 'agent_library\\default'
            #     shutil.copytree(default_agent_path, self.agent_lib)
            self.prompts = self.load_prompts()
            self.load_button_texts()
            self.inputbox.delete("1.0", "end")
            with open(self.default_input_filename, 'r', encoding='utf-8') as file:
                self.inputbox.insert(customtkinter.END, file.read())
            print(f"Changed prompts file to: {choice}")

    def change_knowledge_lib(self, choice):
        if choice == "无知识库":
            return
        elif choice == '使用知识库':
            knowledge_lib_path = os.path.join(self.agent_lib, self.peagent_family_lib, 'knowledge_lib.txt')
            if not os.path.exists(knowledge_lib_path):
                with open(knowledge_lib_path, 'w', encoding='utf-8') as file:
                    file.write('')
            with open(knowledge_lib_path, 'r', encoding='utf-8') as file:
                file_content = file.read()
            self.insert_image('PE Agent-谋略')
            if file_content:
                self.messages.append({"role": "user", "content": file_content})
                self.textbox.insert_no_stream(customtkinter.END, '知识库已加载，具体内容如下所示：\n', 'purple')
                self.textbox.insert_no_stream(customtkinter.END, file_content)
                self.textbox.after(0, lambda: self.textbox.see(customtkinter.END))
                # data = '知识库已加载，具体内容如下所示：\n' + file_content
                # self.thread = threading.Thread(target=user_pormpts_stream, args=(self, data))
                # self.thread.start()
            else:
                self.textbox.insert(customtkinter.END, '知识库为空，请生成知识库')
                # data = '知识库为空，请生成知识库'
                # self.thread = threading.Thread(target=user_pormpts_stream, args=(self, data))
                # self.thread.start()

    def create_new_agent(self):
        popup = customtkinter.CTkToplevel(self)
        popup.geometry("400x170")
        popup.title("创建新Agent")
        popup.resizable(False, False)
        # popup.lift()  # 将窗口置于上一层
        # popup.focus_set()  # 设置焦点到弹窗
        # popup.grab_set()  # 模态化弹窗，防止被主窗口遮挡
        popup.configure(fg_color=self.primary_color)

        customtkinter.CTkLabel(popup, text="请为你的新agent命名", font=self.text_font, text_color=self.text_color).pack(pady=(20, 10))
        
        entry = customtkinter.CTkEntry(popup, width=300, font=self.text_font)
        entry.pack(pady=10)

        def confirm():
            new_name = entry.get().strip()
            if new_name:
                self.api_keys["selected_agent"] = new_name
                with open(self.api_filename, "w", encoding="utf-8") as file:
                    json.dump(self.api_keys, file, ensure_ascii=False, indent=4)
                self.agent_lib = 'agent_library\\' + new_name
                # Copy default agent folder to new agent folder
                default_agent_path = 'agent_library\\default'
                shutil.copytree(default_agent_path, self.agent_lib)
                self.history_filename = os.path.join(self.agent_lib, self.history_lib, 'default_history.txt')
                self.prompts_filename = os.path.join(self.agent_lib, self.peagent_family_lib, 'prompts.json')
                self.prompts = self.load_prompts()
                self.load_button_texts()
                
                # 更新下拉菜单选项
                prompts_options = [f for f in os.listdir('agent_library') if os.path.isdir(os.path.join('agent_library', f))]
                # if '说明文档' not in prompts_options:
                #     prompts_options.append('说明文档')
                prompts_options.append('create new')
                self.prompts_dropdown.configure(values=prompts_options)
                self.prompts_var.set(new_name)
                self.inputbox.delete("1.0", "end")
                with open(self.default_input_filename, 'r', encoding='utf-8') as file:
                    self.inputbox.insert(customtkinter.END, file.read())
                
                popup.destroy()
                print(f"Created new agent: {new_name}")

        customtkinter.CTkButton(popup, text="确认", command=confirm, font=self.button_font,
                                fg_color=self.primary_color, hover_color=self.hover_color,
                                border_color=self.border_color, border_width=self.border_width,
                                width=130, height=35, text_color=self.text_color).pack(pady=10)

        # 确保弹窗关闭时释放grab
        # popup.protocol("WM_DELETE_WINDOW", lambda: self.on_popup_close(popup))
        self.after(100, lambda: self.lift_popup(popup))

    def button_click(self, i, button_commands):
        if self.active_button:
            self.active_button.configure(fg_color=self.primary_color, font=self.button_font, text_color=self.text_color)  # 恢复原来的颜色
        self.active_button = self.execute_buttons[self.button_index[i if i == 0 else i-1]]
        self.active_button.configure(fg_color=self.active_button_color, text_color=self.active_font_color)  # 设置为浅色
        button_commands[i]()  # 执行原来的命令

    def open_api_input(self):
        popup = customtkinter.CTkToplevel(self)
        popup.geometry("400x250")
        popup.title("选择API")
        popup.resizable(False, False)
        # popup.lift()  # 将窗口置于上一层
        # popup.focus_set()  # 设置焦点到弹窗
        # popup.grab_set()  # 模态化弹窗，防止被主窗口遮挡
        popup.configure(fg_color=self.primary_color)  # 设置弹窗背景颜色

        llm_var = customtkinter.StringVar(value=self.api_keys.get("selected_llm", ""))
        api_entries = {}
        
        for llm in self.llm_options:
            frame = customtkinter.CTkFrame(popup, fg_color="transparent")
            frame.pack(pady=10, fill="x", padx=20)
            
            radio_button = customtkinter.CTkRadioButton(frame, text=llm, variable=llm_var, value=llm,
                                                        fg_color='#03E197', text_color=self.text_color, font=self.button_font,
                                                        border_color='#C7C2BD', hover_color=self.hover_color)
            radio_button.pack(side="left")
            
            api_entries[llm] = customtkinter.CTkEntry(frame, width=200)
            api_entries[llm].pack(side="left", padx=(10, 0))
            api_entries[llm].insert(0, self.api_keys.get(llm, ""))

        def set_api_key():
            selected_llm = llm_var.get()
            if selected_llm:
                for llm in self.llm_options:
                    self.api_keys[llm] = api_entries[llm].get()
                self.api_keys["selected_llm"] = selected_llm
                config.API_key = self.api_keys[selected_llm]
                config.LLM = selected_llm
                LLM.client_select()
                with open(self.api_filename, "w", encoding="utf-8") as file:
                    json.dump(self.api_keys, file, ensure_ascii=False, indent=4)
                popup.destroy()
                print(f"API_KEY变量设置为: {config.API_key}")
                print(f"LLM设置为: {config.LLM}")
            else:
                CTkMessagebox(title="提示", message="请选择一个LLM选项", icon="warning")

        confirm_button = customtkinter.CTkButton(popup, text="确认", font=self.button_font,
                                                 command=set_api_key, fg_color=self.primary_color,
                                                 hover_color=self.hover_color, corner_radius=10,
                                                 border_color=self.border_color, border_width=self.border_width,
                                                 width=130, height=35, text_color=self.text_color)
        confirm_button.pack(pady=20)

        # 确保弹窗关闭时释放grab
        # popup.protocol("WM_DELETE_WINDOW", lambda: self.on_popup_close(popup))
        self.after(100, lambda: self.lift_popup(popup))

    def open_batch_modify(self):
        if hasattr(self, 'batch_modify_popup') and self.batch_modify_popup.winfo_exists():
            self.batch_modify_popup.lift()
            self.batch_modify_popup.focus_set()
        else:
            self.batch_modify_popup = customtkinter.CTkToplevel(self)
            self.batch_modify_popup.geometry("800x600")
            self.batch_modify_popup.title("定稿")
            # self.batch_modify_popup.lift()  # 将窗口置于上一层
            # self.batch_modify_popup.focus_set()  # 设置焦点到弹窗
            # self.batch_modify_popup.grab_set()  # 模态化弹窗，防止被主窗口遮挡
            self.batch_modify_popup.configure(fg_color=self.primary_color)  # 设置弹窗背景颜色

            self.batch_modify_textbox = customtkinter.CTkTextbox(self.batch_modify_popup, font=self.text_font, fg_color=self.chatbox_color,
                                            text_color=self.chatbox_text_color, corner_radius=15)
            self.batch_modify_textbox.pack(fill="both", expand=True, padx=20, pady=(20, 10))

            # 读取history.txt文件内容并显示在文本框中，如果不存在则创建
            try:
                with open(self.history_filename, "r", encoding="utf-8") as file:
                    content = file.read()
                    self.batch_modify_textbox.insert("1.0", content)
            except FileNotFoundError:
                # 如果文件不存在，创建一个空文件
                open(self.history_filename, "w", encoding="utf-8").close()

            button_frame = customtkinter.CTkFrame(self.batch_modify_popup, fg_color="transparent")
            button_frame.pack(pady=(0, 20))

            save_button = customtkinter.CTkButton(button_frame, text="保存", font=self.button_font,
                                                fg_color=self.primary_color, hover_color=self.hover_color,
                                                corner_radius=10, text_color=self.text_color, width=130, height=35,
                                                border_color=self.border_color, border_width=self.border_width,
                                                command=lambda: self.save_batch_modify(self.batch_modify_textbox.get("1.0", "end-1c"), self.batch_modify_popup))
            save_button.pack(side="left", padx=(0, 10))

            save_as_button = customtkinter.CTkButton(button_frame, text="打开", font=self.button_font,
                                                    fg_color=self.primary_color, hover_color=self.hover_color,
                                                    corner_radius=10, text_color=self.text_color, width=130, height=35,
                                                border_color=self.border_color, border_width=self.border_width,
                                                    command=lambda: self.openflie_batch_modify(self.batch_modify_textbox, self.batch_modify_popup))
            save_as_button.pack(side="left", padx=(0, 10))

            save_as_button = customtkinter.CTkButton(button_frame, text="另存为", font=self.button_font,
                                                    fg_color=self.primary_color, hover_color=self.hover_color,
                                                    corner_radius=10, text_color=self.text_color, width=130, height=35,
                                                    border_color=self.border_color, border_width=self.border_width,
                                                    command=lambda: self.save_as_batch_modify(self.batch_modify_textbox.get("1.0", "end-1c"),
                                                                                            self.batch_modify_popup))
            save_as_button.pack(side="left")

        if self.messages != [] and self.last_message != self.messages[-1]['content']:
            self.last_message = self.messages[-1]['content']
            self.batch_modify_textbox.insert(customtkinter.END, self.last_message + '\n')

        self.after(100, lambda: self.lift_popup(self.batch_modify_popup))

        # 确保弹窗关闭时释放grab
        # popup.protocol("WM_DELETE_WINDOW", lambda: self.on_popup_close(popup))

    # def on_popup_close(self, popup):
    #     popup.grab_release()
    #     popup.destroy()

    def lift_popup(self, popup):
        popup.lift()  # 将窗口置于上一层
        popup.focus_set()  # 设置焦点到弹窗

    def save_batch_modify(self, content, popup):
        # 保存内容到history.txt文件
        with open(self.history_filename, "w", encoding="utf-8") as file:
            file.write(content)
        # 保存后关闭窗口
        popup.destroy()

    def save_as_batch_modify(self, content, popup):
        # 弹出文件选择对话框
        file_path = customtkinter.filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialdir=self.history_lib
        )
        if file_path:
            # 保存内容到选择的文件
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(content)
        # Clear the content of self.history_filename
        # with open(self.history_filename, "w", encoding="utf-8") as file:
        #     file.write("")
        popup.destroy()

    def openflie_batch_modify(self, textbox, popup):
        # 弹出文件选择对话框
        file_path = customtkinter.filedialog.askopenfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialdir=self.history_lib
        )
        if file_path:
            self.history_filename = file_path
            with open(self.history_filename, "r", encoding="utf-8") as file:
                content = file.read()
                textbox.insert("1.0", content)


    def open_popup(self, index):
        with open(self.prompts_filename, "r", encoding="utf-8") as file:
            self.prompts = json.loads(file.read())
        history_checkbox_var = customtkinter.StringVar(value=self.prompts[index]['messages_reserve'])  # 使用StringVar来存储选中的值
        api_checkbox_var = customtkinter.StringVar(value=self.prompts[index]['api'])

        def update_history_checkbox(value):
            history_checkbox_var.set(value)
            self.prompts[index]['messages_reserve'] = value

        def update_api_checkbox(value):
            api_checkbox_var.set(value)
            self.prompts[index]['api'] = value


        popup = customtkinter.CTkToplevel(self)
        popup_width = 1200
        popup_height = 750
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - popup_width) // 2
        y = (screen_height - popup_height) // 2
        popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")
        popup.title("输入窗口")
        # popup.lift()  # 将窗口置于上一层
        # popup.focus_set()  # 设置焦点到弹窗
        # popup.grab_set()  # 模态化弹窗，防止被主窗口遮挡
        popup.configure(fg_color=self.primary_color)  # 设置弹窗背景颜色

        main_frame = customtkinter.CTkFrame(popup, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # New action name input
        name_frame = customtkinter.CTkFrame(main_frame, fg_color="transparent")
        name_frame.pack(fill="x", pady=(0, 10))

        # Create three equally sized frames
        left_frame = customtkinter.CTkFrame(name_frame, fg_color="transparent")
        middle_frame = customtkinter.CTkFrame(name_frame, fg_color="transparent")
        right_frame = customtkinter.CTkFrame(name_frame, fg_color="transparent")
        left_frame.pack(side="left", expand=True, fill="x")
        middle_frame.pack(side="left", expand=True, fill="x")
        right_frame.pack(side="left", expand=True, fill="x")
        # Place labels in their respective frames
        customtkinter.CTkLabel(left_frame, text="按钮命名", fg_color=self.secondary_color, font=self.mini_title_font, text_color=self.chatbox_text_color, corner_radius=10).pack()
        customtkinter.CTkLabel(middle_frame, text="函数命名", fg_color=self.secondary_color, font=self.mini_title_font, text_color=self.chatbox_text_color, corner_radius=10).pack()
        customtkinter.CTkLabel(right_frame, text="上传文件路径", fg_color=self.secondary_color, font=self.mini_title_font, text_color=self.chatbox_text_color, corner_radius=10).pack()
        entry_frame = customtkinter.CTkFrame(main_frame, fg_color="transparent")
        entry_frame.pack(fill="x", pady=(0, 20))
        action_name_entry = customtkinter.CTkEntry(entry_frame, font=self.text_font,
                                                   fg_color=self.secondary_color, text_color=self.chatbox_text_color)
        action_name_entry.pack(side="left", padx=10, fill="both", expand=True)
        
        func_name_entry = customtkinter.CTkEntry(entry_frame, font=self.text_font,
                                                 fg_color=self.secondary_color, text_color=self.chatbox_text_color)
        func_name_entry.pack(side="left", padx=10, fill="both", expand=True)

        file_name_entry = customtkinter.CTkEntry(entry_frame, font=self.text_font,
                                                 fg_color=self.secondary_color, text_color=self.chatbox_text_color)
        file_name_entry.pack(side="left", padx=10, fill="both", expand=True)

        # New user prompt input
        user_prompt_frame = customtkinter.CTkFrame(main_frame, fg_color="transparent")
        user_prompt_frame.pack(anchor="w", pady=(0, 10))
        customtkinter.CTkLabel(user_prompt_frame, text="用户提示词", fg_color=self.secondary_color, font=self.mini_title_font, text_color=self.chatbox_text_color, corner_radius=10).pack(side="left", padx=(10, 10))
        user_prompt_entry = customtkinter.CTkTextbox(main_frame, width=1000, height=115, font=self.text_font, wrap="word", corner_radius=15,
                                                     fg_color=self.secondary_color, text_color=self.chatbox_text_color)
        user_prompt_entry.pack(fill="both", expand=True, pady=(0, 10))

        prompt_frame = customtkinter.CTkFrame(main_frame, fg_color="transparent")
        prompt_frame.pack(anchor="w", pady=(0, 10))
        customtkinter.CTkLabel(prompt_frame, text="提示词", fg_color=self.secondary_color, font=self.mini_title_font, text_color=self.chatbox_text_color, corner_radius=10).pack(side="left", padx=(10, 10))
        prompt_entry = customtkinter.CTkTextbox(main_frame, width=1000, height=115, font=self.text_font, wrap="word", corner_radius=15,
                                                fg_color=self.secondary_color, text_color=self.chatbox_text_color)
        prompt_entry.pack(fill="both", expand=True, pady=(0, 10))

        func_frame = customtkinter.CTkFrame(main_frame, fg_color="transparent")
        func_frame.pack(anchor="w", pady=(0, 10))
        customtkinter.CTkLabel(func_frame, text="函数", fg_color=self.secondary_color, font=self.mini_title_font, text_color=self.chatbox_text_color, corner_radius=10).pack(side="left", padx=(10, 10))
        function_entry = customtkinter.CTkTextbox(main_frame, width=1000, height=115, font=self.text_font, wrap="word", corner_radius=15,
                                                  fg_color=self.secondary_color, text_color=self.chatbox_text_color)
        function_entry.pack(fill="both", expand=True, pady=(0, 10))

        checkbox_frame = customtkinter.CTkFrame(main_frame, fg_color="transparent")
        checkbox_frame.pack(pady=(0, 20))
        history_checkbox_frame = customtkinter.CTkFrame(checkbox_frame, fg_color="transparent", border_color=self.secondary_color, border_width=self.border_width)
        history_checkbox_frame.pack(side='left', padx=40)
        history_all_checkbox = customtkinter.CTkRadioButton(history_checkbox_frame, text="保留历史对话", variable=history_checkbox_var,
                                                 value="all", command=lambda: update_history_checkbox("all"),
                                                 font=self.button_font,
                                                 fg_color='#03E197', border_color='#C7C2BD', text_color=self.text_color)
        history_all_checkbox.pack(side="left", padx=(30, 10), pady=10)
        history_partial_checkbox = customtkinter.CTkRadioButton(history_checkbox_frame, text="保留上轮对话", variable=history_checkbox_var,
                                                 value="partial", command=lambda: update_history_checkbox("partial"),
                                                 font=self.button_font,
                                                 fg_color='#03E197', border_color='#C7C2BD', text_color=self.text_color)
        history_partial_checkbox.pack(side="left", padx=10, pady=10)
        history_none_checkbox = customtkinter.CTkRadioButton(history_checkbox_frame, text="清空所有对话", variable=history_checkbox_var,
                                                 value="none", command=lambda: update_history_checkbox("none"),
                                                 font=self.button_font,
                                                 fg_color='#03E197', border_color='#C7C2BD', text_color=self.text_color)
        history_none_checkbox.pack(side="left", padx=(10, 30), pady=10)

        api_checkbox_frame = customtkinter.CTkFrame(checkbox_frame, fg_color="transparent", border_color=self.secondary_color, border_width=self.border_width)
        api_checkbox_frame.pack(side='left', padx=40)
        default_checkbox = customtkinter.CTkRadioButton(api_checkbox_frame, text='Default',
                                                variable=api_checkbox_var,
                                                value='default', command=lambda: update_api_checkbox('default'),
                                                font=self.button_font,
                                                fg_color='#03E197', border_color='#C7C2BD',
                                                text_color=self.text_color)
        default_checkbox.pack(side="left", padx=(10, 10), pady=10)
        glm_checkbox = customtkinter.CTkRadioButton(api_checkbox_frame, text='GLM',
                                                        variable=api_checkbox_var,
                                                        value='GLM', command=lambda: update_api_checkbox('GLM'),
                                                        font=self.button_font,
                                                        fg_color='#03E197', border_color='#C7C2BD',
                                                        text_color=self.text_color)
        glm_checkbox.pack(side="left", padx=(10, 10), pady=10)
        kimi_checkbox = customtkinter.CTkRadioButton(api_checkbox_frame, text="Kimi",
                                                                variable=api_checkbox_var,
                                                                value="Kimi",
                                                                command=lambda: update_api_checkbox("Kimi"),
                                                                font=self.button_font,
                                                                fg_color='#03E197', border_color='#C7C2BD',
                                                                text_color=self.text_color)
        kimi_checkbox.pack(side="left", padx=5, pady=10)
        qwen_checkbox = customtkinter.CTkRadioButton(api_checkbox_frame, text="Qwen",
                                                             variable=api_checkbox_var,
                                                             value="Qwen", command=lambda: update_api_checkbox("Qwen"),
                                                             font=self.button_font,
                                                             fg_color='#03E197', border_color='#C7C2BD',
                                                             text_color=self.text_color)
        qwen_checkbox.pack(side="left", padx=5, pady=10)

        func_name = self.prompts[index]['func_name']
        button_name = self.prompts[index]['button_name']
        file_name = self.prompts[index]['file_name']
        user_prompt = self.prompts[index]['user_prompt']
        system_prompt = self.prompts[index]['system_prompt']
        if func_name:
            func_name_entry.insert(0, func_name)
        if button_name:
            action_name_entry.insert(0, button_name)
        if file_name:
            file_name_entry.insert(0, file_name)
        if user_prompt:
            user_prompt_entry.insert("1.0", user_prompt)
        if system_prompt:
            prompt_entry.insert("1.0", system_prompt)

        # 定义一个函数用于从后台读取指定函数内容并显示出来
        def func_update():
            func_name_text = func_name_entry.get()
            if func_name_text:
                # 打开并读取函数文件
                with open(self.func_filename, "r", encoding="utf-8") as file:
                    func_content = file.read()
                
                # 定义一个递归函数来查找特定名称的函数
                def find_function(node, name):
                    # 如果当前节点是函数定义且名称匹配，返回函数的源代码
                    if isinstance(node, ast.FunctionDef) and node.name == name:
                        return ast.unparse(node)
                    # 递归遍历所有子节点
                    for child in ast.iter_child_nodes(node):
                        result = find_function(child, name)
                        if result:
                            return result
                    return None

                # 解析文件内容为AST
                tree = ast.parse(func_content)
                # 在AST中查找名为'func_name'的函数
                func = find_function(tree, func_name_text)

                # 如果找到函数，将其插入到文本框中
                if func:
                    function_entry.delete("1.0", "end-1c")
                    function_entry.insert("1.0", func)
                    if self.tools_dict[func_name_text]:
                        function_entry.insert("1.0", f"tool = {self.tools_dict[func_name_text]}\n\n")
                else:
                    function_entry.delete("1.0", "end-1c")
                    CTkMessagebox(title="提示", message="无可用函数", icon="warning")

                
        # 执行函数更新函数
        func_update()

        def save_and_close():
            destory_flag = True
            user_prompt_text = user_prompt_entry.get("1.0", "end-1c")
            system_prompt_text = prompt_entry.get("1.0", "end-1c")
            func_text = function_entry.get("1.0", "end-1c")
            button_name_text = action_name_entry.get()
            func_name_text = func_name_entry.get()

            self.prompts[index]['func_name'] = func_name_text
            self.prompts[index]['user_prompt'] = user_prompt_text
            self.prompts[index]['system_prompt'] = system_prompt_text
            self.prompts[index]['button_name'] = button_name_text
            with open(self.prompts_filename, "w", encoding="utf-8") as file:
                json.dump(self.prompts, file, ensure_ascii=False, indent=4)

            if func_name_text:
                if not func_text:
                    destory_flag = False
                    CTkMessagebox(title="提示", message="请补充函数内容", icon="warning")
            if func_text:
                if not func_name_text:
                    destory_flag = False
                    CTkMessagebox(title="提示", message="请补充函数命名", icon="warning")
                else:
                    # 读取现有的函数文件内容
                    with open(self.func_filename, "r", encoding="utf-8") as file:
                        existing_content = file.read()

                    # 将文件内容解析为抽象语法树
                    tree = ast.parse(existing_content)
                    
                    # 提取tool字典和函数定义
                    func_tree = ast.parse(func_text)
                    tool_assign = None
                    func_def = None
                    for node in func_tree.body:
                        if isinstance(node, ast.Assign):
                            # 找到tool字典定义
                            if isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'tool':
                                tool_assign = node
                        elif isinstance(node, ast.FunctionDef):
                            func_def = node

                    if not func_def:
                        destory_flag = False
                        CTkMessagebox(title="提示", message="未找到函数定义", icon="warning")
                        return

                    # 检查函数名是否一致
                    if func_def.name != func_name_text:
                        destory_flag = False
                        CTkMessagebox(title="提示", message="函数名不一致！", icon="warning")
                        return

                    # 标记是否找到并更新了函数
                    function_updated = False
                    # 遍历语法树中的所有节点
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef) and node.name == func_name_text:
                            # 更新函数体
                            node.body = func_def.body
                            function_updated = True
                            break

                    # 如果没有找到匹配的函数定义，则添加新函数
                    if not function_updated:
                        tree.body.append(func_def)

                    # 更新或添加tool字典
                    if tool_assign:
                        tool_updated = False
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Assign):
                                if isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'tools':
                                    # 找到tools字典，更新它
                                    if isinstance(node.value, ast.Dict):
                                        # node.value.keys.append(ast.Constant(value=func_name_text))
                                        # node.value.values.append(tool_assign.value)
                                        # 检查是否已存在同名键
                                        for i, key in enumerate(node.value.keys):
                                            if isinstance(key, ast.Constant) and key.value == func_name_text:
                                                # 如果找到同名键，更新对应的值
                                                node.value.values[i] = tool_assign.value
                                                tool_updated = True
                                                break
                                        else:
                                            # 如果没有找到同名键，添加新的键值对
                                            node.value.keys.append(ast.Constant(value=func_name_text))
                                            node.value.values.append(tool_assign.value)
                                            tool_updated = True
                                        break

                        if not tool_updated:
                            # 如果没有找到tools字典，创建一个新的
                            tools_dict = ast.Dict(
                                keys=[ast.Constant(value=func_name_text)],
                                values=[tool_assign.value]
                            )
                            tools_assign = ast.Assign(
                                targets=[ast.Name(id='tools', ctx=ast.Store())],
                                value=tools_dict
                            )
                            tree.body.insert(0, tools_assign)

                    # 将修改后的语法树转换回Python代码
                    updated_content = ast.unparse(tree)

                    # 将更新后的内容写回文件
                    with open(self.func_filename, "w", encoding="utf-8") as file:
                        file.write(updated_content)

                    # 重新加载函数和工具
                    func_namespace = {}
                    exec(updated_content, func_namespace)
                    self.tools_dict = func_namespace.get('tools', {})
                    self.available_tools = {}
                    self.tools = []
                    for key, value in func_namespace.items():
                        if callable(value):
                            self.available_tools[key] = value
                            if key in self.available_tools:
                                self.tools.append(self.available_tools[key])
                    # # 读取现有的函数文件内容
                    # with open(self.func_filename, "r", encoding="utf-8") as file:
                    #     existing_content = file.read()
                    # # 将文件内容解析为抽象语法树
                    # tree = ast.parse(existing_content)
                    # # 标记是否找到并更新了函数
                    # function_updated = False
                    # # 遍历语法树中的所有节点
                    # for node in ast.walk(tree):
                    #     # 如果找到与给定函数名匹配的函数定义
                    #     if isinstance(node, ast.FunctionDef) and node.name == func_name_text:
                    #         # 用新的函数体替换旧的函数体
                    #         node.body = ast.parse(func_text).body[0].body
                    #         function_updated = True
                    #         break
                    # # 如果没有找到匹配的函数定义，则添加新函数
                    # if not function_updated:
                    #     new_function = ast.parse(func_text).body[0]
                    #     # 检查新函数名是否与func_name_text一致
                    #     if new_function.name != func_name_text:
                    #         destory_flag = False
                    #         CTkMessagebox(title="提示", message="函数名不一致！", icon="warning")
                    #     else:
                    #         tree.body.append(new_function)
                    # # 将修改后的语法树转换回Python代码
                    # updated_content = ast.unparse(tree)
                    # # 将更新后的内容写回文件
                    # with open(self.func_filename, "w", encoding="utf-8") as file:
                    #     file.write(updated_content)
                    # func_namespace = {}
                    # exec(updated_content, func_namespace)
                    # self.available_tools = {}
                    # self.tools = []
                    # for key, value in func_namespace.items():
                    #     if callable(value):
                    #         self.available_tools[key] = value
                    #         self.tools.append(config.tools[key])

            # Update the button text
            if index != 'load_history' and index != 'batch_modify' and index != 'knowledge_lib' and index != 'new_chat':
                self.execute_buttons[index].configure(text=button_name_text)

            if destory_flag:
                popup.destroy()

        def file_upload():
            file_path = customtkinter.filedialog.askopenfilename()
            if file_path:
                self.prompts[index]['file_name'] = os.path.basename(file_path)
                self.prompts[index]['file_content'] = LLM.create_file(file_path)
                file_name_entry.delete(0, "end")
                file_name_entry.insert(0, os.path.basename(file_path))
                # 复制文件到指定路径
                destination_path = os.path.join(self.agent_lib, self.file_uploaded_lib, os.path.basename(file_path))
                shutil.copy2(file_path, destination_path)
                # self.insert_image('PE Agent-谋略')
                # self.textbox.insert(customtkinter.END, f'文件{os.path.basename(file_path)}上传完毕')
                # self.textbox.after(0, lambda: self.textbox.see(customtkinter.END))
                data = f'文件{os.path.basename(file_path)}上传完毕'
                self.thread = threading.Thread(target=user_pormpts_stream, args=(self, data))
                self.thread.start()

        def delete_file():
            self.prompts[index]['file_content'] = ''
            self.prompts[index]['file_name'] = ''
            file_name_entry.delete(0, "end")


        button_frame = customtkinter.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack()
        save_button = customtkinter.CTkButton(button_frame, text="保存", command=lambda: save_and_close(),
                                              font=self.button_font, fg_color=self.primary_color,width=130, height=40,
                                              border_color=self.border_color, border_width=self.border_width,
                                              hover_color=self.hover_color, corner_radius=10, text_color=self.text_color)
        save_button.pack(side="left", padx=10)
        func_update_button = customtkinter.CTkButton(button_frame, text="更新函数", command=lambda: func_update(),
                                              font=self.button_font, fg_color=self.primary_color, width=130, height=40,
                                              border_color=self.border_color, border_width=self.border_width,
                                              hover_color=self.hover_color, corner_radius=10,
                                              text_color=self.text_color)
        func_update_button.pack(side="left", padx=10)
        file_button = customtkinter.CTkButton(button_frame, text="上传文件", command=lambda: file_upload(),
                                              font=self.button_font, fg_color=self.primary_color, width=130, height=40,
                                              border_color=self.border_color, border_width=self.border_width,
                                              hover_color=self.hover_color, corner_radius=10,
                                              text_color=self.text_color)
        file_button.pack(side="left", padx=10)
        delete_file_button = customtkinter.CTkButton(button_frame, text="删除文件", command=lambda: delete_file(),
                                              font=self.button_font, fg_color=self.primary_color, width=130, height=40,
                                              border_color=self.border_color, border_width=self.border_width,
                                              hover_color=self.hover_color, corner_radius=10,
                                              text_color=self.text_color)
        delete_file_button.pack(side="left", padx=10)

        # 确保弹窗关闭时释放grab
        # popup.protocol("WM_DELETE_WINDOW", lambda: self.on_popup_close(popup))
        self.after(100, lambda: self.lift_popup(popup))

    def system_prompts(self, index):
        self.button_tool = []
        if index == 'button_0':
            self.PreProcess = True
        else:
            self.PreProcess = False

        with open(self.prompts_filename, "r", encoding="utf-8") as file:
            self.prompts = json.loads(file.read())
        self.button_prompt = self.prompts[index]['system_prompt']
        user_prompt = self.prompts[index]['user_prompt']
        func_name = self.prompts[index]['func_name']
        api = self.prompts[index]['api']
        messages_reserve = self.prompts[index]['messages_reserve']
        file_content = self.prompts[index]['file_content']

        if api == 'default':
            selected_llm = self.api_keys.get("selected_llm")
            print('选择系统默认api：', selected_llm)
        else:
            selected_llm = api
            print('选择自定义api：', selected_llm)
        config.API_key = self.api_keys[selected_llm]
        config.LLM = selected_llm
        LLM.client_select()

        self.messages_modify(messages_reserve)

        if user_prompt:
            # self.insert_image('PE Agent-谋略')
            # self.textbox.insert(customtkinter.END, ' ' + user_prompt)
            # self.textbox.after(0, lambda: self.textbox.see(customtkinter.END))
            data = user_prompt
            self.thread = threading.Thread(target=user_pormpts_stream, args=(self, data))
            self.thread.start()

        if file_content:
            self.messages.append({"role": "system", "content": file_content})
            self.prompts[index]['file_content'] = ''

        if func_name:
            self.button_tool.append(self.tools_dict[func_name])
        

        # print('ssss', self.messages)
        self.save_data = user_prompt
        return self.save_data

    def input(self):
        text = self.inputbox.get('1.0', customtkinter.END)
        if self.file_uploaded:
            self.messages.append({"role": "user", "content": self.file_uploaded})
            self.file_uploaded = ''
        if self.button_prompt:
            self.messages.append({"role": "user", "content": self.button_prompt})
            # self.button_prompt = ''
        # if self.active_button:
        #     self.active_button.configure(fg_color=self.primary_color, font=self.button_font, text_color=self.text_color)  # 恢复原来的颜色
        #     self.active_button = None
        self.messages.append({"role": "user", "content": text})
        self.insert_image('用户')
        self.textbox.insert_no_stream(customtkinter.END, ' ' + text)
        try:
            stream = LLM.ask_question(self.messages, self.button_tool)
            self.thread = threading.Thread(target=process_stream, args=(self, stream, "green", "purple", "formula"))
            self.thread.start()
            self.inputbox.delete("1.0", "end")
        except AttributeError as e:
            CTkMessagebox(title="提示", message="请补充API内容", icon="warning")
        except Exception as e:
            CTkMessagebox(title="提示", message="可能存在API欠费或网络异常等问题，请检查", icon="warning")

                

    def clear_chat(self):
        self.messages = []
        self.textbox._textbox.config(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox._textbox.config(state="disabled")
        with open(self.prompts_filename, "r", encoding="utf-8") as file:
            self.prompts = json.loads(file.read())
        self.system_prompts('new_chat')
        if self.active_button:
            self.active_button.configure(fg_color=self.primary_color, font=self.button_font, text_color=self.text_color)  # 恢复原来的颜色
        self.active_button = self.new_chat_button
        self.active_button.configure(fg_color=self.active_button_color, text_color=self.active_font_color)

    def print_messages(self):
        print(self.messages)

    def insert_image(self, identity):
        if identity == '用户':
            variable_photo = self.user_photo
        elif identity == 'LLM':
            variable_photo = self.LLM_photo
        elif identity == 'PE Agent-谋略':
            variable_photo = self.pe_agent_photo   
        # Resize the image to match self.text_font size
        image = variable_photo._PhotoImage__photo.zoom(int(self.text_font_size*0.2)).subsample(32)
        self.textbox.insert_no_stream(customtkinter.END, '\n\n')
        self.textbox._textbox.image_create(customtkinter.END, image=image)
        # Check if the 'images' attribute exists, if not, create it
        if not hasattr(self.textbox, 'images'):
            self.textbox.images = []
        # Append the new image to the 'images' list to keep a reference
        self.textbox.images.append(image)
        self.textbox.insert_no_stream(customtkinter.END, f'  {identity}:\n', 'identity')

    def stop_threading(self):
        config.matlab_threading = False
        time.sleep(2)
        config.matlab_threading = True

    def messages_modify(self, messages_reserve):
        if messages_reserve == 'all':
            pass
        elif messages_reserve == 'partial':
            self.messages = self.messages[-1]
        elif messages_reserve == 'none':
            self.messages = []
        # print(self.messages)

    def load_button_texts(self):
        for index, button in self.prompts.items():
            button_name = button['button_name']
            if index != 'load_history' and index != 'batch_modify' and index != 'knowledge_lib' and index != 'new_chat':
                self.execute_buttons[index].configure(text=button_name)

    def load_button_from_message(self, message):
        
        def load_button_from_message_inner(flag):
            # self.clear_chat()
            # self.insert_image('PE Agent-谋略')
            # self.textbox.insert(customtkinter.END, '点击下方按钮，开始执行计划！')
            # self.textbox.after(0, lambda: self.textbox.see(customtkinter.END))
            self.messages = []
            data = '点击下方按钮，开始执行计划！'
            self.thread = threading.Thread(target=user_pormpts_stream, args=(self, data))
            self.thread.start()
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

            if flag == 'erase':
                for key, value in self.prompts.items():
                    if key != 'batch_modify' and key != 'load_history' and key != 'button_0' and key != 'knowledge_lib' and key != 'new_chat':
                        value['button_name'] = ''
                        value['user_prompt'] = ''
                        value['system_prompt'] = ''
                        value['api'] = 'default'
            elif flag == 'update':
                pass
            for (key, value) in extracted_content.items():
                if key in self.prompts:
                    self.prompts[key]['button_name'] = value['button_name']
                    self.prompts[key]['user_prompt'] = value['user_prompt']
                    self.prompts[key]['system_prompt'] = value['system_prompt']
                    self.prompts[key]['api'] = value['api']
            with open(self.prompts_filename, 'w', encoding='utf-8') as file:
                file.write(json.dumps(self.prompts, ensure_ascii=False))
            self.load_button_texts()

        # 创建一个新的弹出窗口
        popup = customtkinter.CTkToplevel(self)
        popup.title("确认更新")
        popup.geometry("300x150")
        popup.resizable(False, False)
        popup.configure(fg_color=self.primary_color)

        # 创建一个框架来容纳信息
        info_frame = customtkinter.CTkFrame(popup, fg_color="transparent")
        info_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 添加确认信息
        confirm_label = customtkinter.CTkLabel(info_frame, text="您确定要更新按钮吗？", font=self.button_font, text_color=self.text_color)
        confirm_label.pack(pady=(0, 20))

        # 添加确认和取消按钮
        button_frame = customtkinter.CTkFrame(info_frame, fg_color="transparent")
        button_frame.pack(fill="x", expand=True)

        confirm_button = customtkinter.CTkButton(button_frame, text="仅更新", font=self.button_font, text_color=self.text_color, 
                                                 border_color=self.border_color, border_width=self.border_width, fg_color=self.primary_color, 
                                                 hover_color=self.hover_color, width=100, height=30,
                                                 command=lambda: [load_button_from_message_inner('update'), popup.destroy()])
        confirm_button.pack(side='left', padx=(10, 10), expand=True)

        cancel_button = customtkinter.CTkButton(button_frame, text="擦除并更新", font=self.button_font, text_color=self.text_color, 
                                                 border_color=self.border_color, border_width=self.border_width, fg_color=self.primary_color, 
                                                 hover_color=self.hover_color, width=100, height=30,
                                                 command=lambda: [load_button_from_message_inner('erase'), popup.destroy()])
        cancel_button.pack(side='left', padx=(10, 10), expand=True)

        self.after(100, lambda: self.lift_popup(popup))

    def button_message_preprocess(self, message):
        pattern = '[\'"]button_\\d+[\'"]:\\s*{[^}]+}'
        matches = re.findall(pattern, message)
        extracted_content = {}
        text_content = ''
        for match in matches:
            try:
                button_dict = json.loads('{' + match.replace("'", '"') + '}')
                extracted_content.update(button_dict)
            except json.JSONDecodeError:
                print(f'无法解析以下内容: {match}')
        sorted_keys = sorted(extracted_content.keys(), key=lambda x: int(x.split('_')[1]))
        self.textbox._textbox.config(state="normal")
        for key in sorted_keys:
            print(f"{key}: {extracted_content[key]}")
            self.textbox.insert(customtkinter.END, f"\n步骤{key[7:]}: ", 'purple')
            self.textbox.insert(customtkinter.END, f"{extracted_content[key]['button_name']}\n")
            self.textbox.insert(customtkinter.END, "用户提示词: ", 'purple')
            self.textbox.insert(customtkinter.END, f"{extracted_content[key]['user_prompt']}\n")
            self.textbox.insert(customtkinter.END, "系统提示词: ", 'purple')            
            self.textbox.insert(customtkinter.END, f"{extracted_content[key]['system_prompt']}\n")
            self.textbox.insert(customtkinter.END, "API: ", 'purple')
            self.textbox.insert(customtkinter.END, f"{extracted_content[key]['api']}\n")
        self.textbox._textbox.config(state="disabled")
        return text_content


    def related_information(self):
        # 定义开发人员、版本、参考文献变量
        self.developers = "华中科技大学冲量智能实验室（Impulse Intelligence Lab, IIL）——\n陈宇，商毅，祝之森，陈汉文"
        self.version = "v1.0"
        self.references = "陈宇，祝之森，白敬波，商毅，康勇，\n“电力电子设计智能化：技术路线综述和前沿探索”，中国电机工程学报，\nDOI：10.13334/j.0258-8013.pcsee.241598"
        
        theme_checkbox_var = customtkinter.StringVar(value=self.theme)
        def update_theme_checkbox(theme):
            def update_theme_checkbox_inner():
                self.theme = theme
                self.api_keys['selected_theme'] = theme
                theme_checkbox_var.set(theme)
                with open(self.api_filename, "w", encoding="utf-8") as file:
                    json.dump(self.api_keys, file, ensure_ascii=False, indent=4)
                self.change_theme()
                # 重新启动主页面
                self.quit()
                self.destroy()  # 销毁当前窗口
            
            popup = customtkinter.CTkToplevel(self)
            popup.title("确认修改主题")
            popup.geometry("300x150")
            popup.resizable(False, False)
            popup.configure(fg_color=self.primary_color)

            # 创建一个框架来容纳信息
            info_frame = customtkinter.CTkFrame(popup, fg_color="transparent")
            info_frame.pack(fill="both", expand=True, padx=20, pady=20)

            # 添加确认信息
            confirm_label = customtkinter.CTkLabel(info_frame, text="切换主题需重新启动软件，\n请您重新打开", font=self.button_font, text_color=self.text_color)
            confirm_label.pack(pady=(0, 20))

            # 添加确认和取消按钮
            button_frame = customtkinter.CTkFrame(info_frame, fg_color="transparent")
            button_frame.pack(fill="x", expand=True)

            confirm_button = customtkinter.CTkButton(button_frame, text="确认", font=self.button_font, text_color=self.text_color, 
                                                    border_color=self.border_color, border_width=self.border_width, fg_color=self.primary_color, 
                                                    hover_color=self.hover_color, width=100, height=30,
                                                    command=lambda: [update_theme_checkbox_inner(), popup.destroy()])
            confirm_button.pack(side='left', padx=(10, 10), expand=True)

            cancel_button = customtkinter.CTkButton(button_frame, text="取消", font=self.button_font, text_color=self.text_color, 
                                                    border_color=self.border_color, border_width=self.border_width, fg_color=self.primary_color, 
                                                    hover_color=self.hover_color, width=100, height=30,
                                                    command=popup.destroy)
            cancel_button.pack(side='left', padx=(10, 10), expand=True)

            self.after(100, lambda: self.lift_popup(popup))
        
        # 创建一个新的弹出窗口
        popup = customtkinter.CTkToplevel(self)
        popup.title("相关信息")
        popup.geometry("520x420")
        popup.resizable(False, False)
        # popup.lift()  # 将窗口置于上一层
        # popup.focus_set()  # 设置焦点到弹窗
        # popup.grab_set()  # 模态化弹窗，防止被主窗口遮挡
        popup.configure(fg_color=self.primary_color)

        # 创建一个框架来容纳信息
        info_frame = customtkinter.CTkFrame(popup, fg_color="transparent")
        info_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 添加开发人员信息
        dev_label = customtkinter.CTkLabel(info_frame, text="开发人员：", font=self.text_font, text_color=self.text_color, justify="left")     
        dev_label.pack(pady=(0, 5), anchor="w")
        dev_info = customtkinter.CTkLabel(info_frame, text=self.developers, font=self.text_font, text_color=self.text_color, justify="left")
        dev_info.pack(pady=(0, 0), anchor="w")

        # 添加参考文献
        ref_label = customtkinter.CTkLabel(info_frame, text="参考文献：", font=self.text_font, text_color=self.text_color, justify="left")
        ref_label.pack(pady=(10, 5), anchor="w")
        ref_info = customtkinter.CTkLabel(info_frame, text=self.references, font=self.text_font, text_color=self.text_color, justify="left")
        ref_info.pack(pady=(0, 10), anchor="w")

        # 添加版本信息
        version_label = customtkinter.CTkLabel(info_frame, text="版本：" + self.version, font=self.text_font, text_color=self.text_color, justify="left")
        version_label.pack(pady=(10, 5), anchor="w")
        # version_info = customtkinter.CTkLabel(info_frame, text=self.version, font=self.text_font, text_color=self.text_color, anchor="w")
        # version_info.pack(pady=(0, 10), anchor="w")

        theme_label = customtkinter.CTkLabel(info_frame, text="颜色主题：", font=self.text_font, text_color=self.text_color, anchor="w")
        theme_label.pack(pady=(10, 5), anchor="w")
        checkbox_frame = customtkinter.CTkFrame(info_frame, fg_color="transparent")
        checkbox_frame.pack(pady=(0, 10), anchor="w")
        AI_black_checkbox = customtkinter.CTkRadioButton(checkbox_frame, text="AI黑", variable=theme_checkbox_var,
                                                 value="AI黑", command=lambda: update_theme_checkbox("AI黑"),
                                                 font=self.text_font,
                                                 fg_color='#03E197', border_color='#C7C2BD', text_color=self.text_color)
        AI_black_checkbox.pack(side="left", padx=(30, 10), pady=10)
        electrical_blue_checkbox = customtkinter.CTkRadioButton(checkbox_frame, text="电气蓝", variable=theme_checkbox_var,
                                                 value="电气蓝", command=lambda: update_theme_checkbox("电气蓝"),
                                                 font=self.text_font,
                                                 fg_color='#03E197', border_color='#C7C2BD', text_color=self.text_color)
        electrical_blue_checkbox.pack(side="left", padx=10, pady=10)

        # 添加关闭按钮
        close_button = customtkinter.CTkButton(info_frame, text="关闭", command=popup.destroy, font=self.button_font,
                                               fg_color=self.primary_color, text_color=self.text_color,
                                               border_color=self.border_color, border_width=self.border_width,
                                               hover_color=self.hover_color, corner_radius=10)
        close_button.pack(pady=(0, 0))

        

        # 确保弹窗关闭时释放grab
        # popup.protocol("WM_DELETE_WINDOW", lambda: self.on_popup_close(popup))
        self.after(100, lambda: self.lift_popup(popup))
        

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", lambda: sys.exit(0))
    app.mainloop()
