from flask import Flask, request, jsonify, render_template
import os,re
import json
import requests

app = Flask(__name__)

# 获取配置文件信息
def get_config():
    script_dir = os.path.dirname(__file__)
    config_file_path = os.path.join(script_dir, 'config.json')
    try:
        with open(config_file_path, 'r', encoding='utf-8') as f:
            config_info = json.load(f)
        return config_info
    except Exception as e:
        print(f"配置文件读取错误: {e}")
        return {"api_key": "", "ai_model": "deepseek-chat"}

# 调用 DeepSeek AI 接口分析文本
def analyze_fake_information(text):
    try:
        config_info = get_config()
        
        # 直接使用requests库调用DeepSeek API
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config_info['api_key']}"
        }
        
        payload = {
            "model": config_info.get("ai_model"),
            "messages": [
                {
                    "role": "system", 
                    "content": """请对以下文本进行虚假信息分析，从以下三个层面提供分析结果：

1. 原始文本解析层
* 文本内容：完整保留输入文章的段落结构、标点符号、特殊字符
* 元数据：提取可能的发布时间、作者信息、发布平台、阅读/转发量等传播属性
* 多模态数据：识别文本中提到的图片、视频、超链接等非文本元素

2. 语义特征提取层
* 情感极性：量化文本的情绪强度及正负面倾向（1-10分）
* 语义角色标注：识别施事者、受事者、时间地点等语义框架
* 实体关系图谱：构建人物、机构、事件间的关联
* 立场检测：分析作者对核心议题的立场倾向性

3. 传播特征分析层
* 扩散可能性：评估信息在社交网络传播的可能性
* 传播速率潜力：评估传播潜在速度
* 用户参与可能性：评估转发、评论的可能性

4. 虚假信息评估
* 可信度评分：给出0-100的可信度评分
* 虚假信息特征：列出文本中可能的虚假信息特征
* 建议：给出识别类似虚假信息的建议

请按照上述结构以JSON格式返回分析结果。"""
                },
                {"role": "user", "content": text}
            ],
            "max_tokens": 2048,
            "temperature": 0.5
        }
        
        # 记录API请求日志，帮助调试
        print(f"正在发送请求到DeepSeek API...")
        
        response = requests.post(
            "https://api.deepseek.com/chat/completions", 
            headers=headers, 
            json=payload
        )
        
        # 检查响应状态码
        if response.status_code != 200:
            # 记录错误详情
            error_detail = response.json() if response.text else "无详细错误信息"
            print(f"API请求失败, 状态码: {response.status_code}, 错误信息: {error_detail}")
            return {
                "error": f"API请求失败 (HTTP {response.status_code})",
                "details": error_detail
            }
            
        # 解析响应
        result = response.json()
        # print(f"API请求成功, 响应结果: {result}")
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            clean_content = content.strip().strip("```json").strip("```")
            clean_content = re.sub(r"\s+", " ", clean_content)
            
            # 尝试解析为JSON
            try:
                json_result = json.loads(clean_content)
                return json_result
            except json.JSONDecodeError:
                # 原始文本结果
                return {
                    "原始文本解析层": {
                        "文本内容": text[:500] + "..."  # 返回部分原始文本
                    },
                    "语义特征提取层": {
                        "情感极性": 5,
                        "语义角色标注": "API返回的结果无法解析为JSON",
                        "实体关系图谱": [],
                        "立场检测": "无法分析"
                    },
                    "传播特征分析层": {
                        "扩散可能性": "无法分析",
                        "传播速率潜力": "无法分析",
                        "用户参与可能性": "无法分析"
                    },
                    "虚假信息评估": {
                        "可信度评分": 50,
                        "虚假信息特征": ["无法进行详细分析"],
                        "建议": ["建议手动分析该文本"]
                    },
                    "raw_result": content
                }
        else:
            return {"error": "API响应格式错误", "raw_response": result}
            
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"分析过程发生异常: {str(e)}\n{error_trace}")
        return {"error": f"分析过程发生异常: {str(e)}"}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    text = request.form.get('text')
    if not text:
        return jsonify({"error": "未提供文本"}), 400

    try:
        # 调用 DeepSeek 进行虚假信息检测分析
        result = analyze_fake_information(text)
        return jsonify(result)
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"分析过程发生异常: {str(e)}\n{error_trace}")
        return jsonify({"error": f"分析过程发生异常: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)