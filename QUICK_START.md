# 快速使用指南

## 🚀 5 分钟启动指南

### 1. 获取 Bot Token
1. 在 Telegram 中找到 [@BotFather](https://t.me/BotFather)
2. 发送 `/newbot` 并按指示创建机器人
3. 复制获得的 Token

### 2. 获取管理员 ID
1. 在 Telegram 中找到 [@userinfobot](https://t.me/userinfobot)  
2. 发送任意消息获取你的用户 ID

### 3. 配置机器人
```python
# 编辑 config.py 文件，填入你的信息
class Config:
    BOT_TOKEN = 'your_telegram_bot_token_here'
    ADMIN_USER_IDS = [123456789]  # 你的用户 ID
```

### 4. 安装依赖
```bash
pip install -r requirements.txt
```

### 5. 启动机器人
```bash
# 方式1：直接运行
python bot.py

# 方式2：使用启动脚本
python start.py

# 方式3：使用系统脚本
# Linux/Mac: ./run.sh
# Windows: run.bat
```

## 📋 基本使用

### 管理员操作
1. 发送 `/start` 开始
2. 发送 `/create_questionnaire` 创建问卷
3. 按提示输入标题、描述和问题
4. 发送 `/my_questionnaires` 管理问卷
5. 激活问卷后用户可以填写

### 用户操作
1. 发送 `/start` 开始  
2. 发送 `/surveys` 查看可用问卷
3. 点击按钮开始填写问卷

## 🔧 问题排查

### 常见错误
- `Invalid configuration`: 检查 config.py 文件中的 BOT_TOKEN 和 ADMIN_USER_IDS
- `No module named 'telegram'`: 运行 `pip install -r requirements.txt`
- `Permission denied`: 在 Linux/Mac 上运行 `chmod +x run.sh`

### 获取帮助
- 检查 README.md 详细说明
- 查看日志输出找出具体错误
- 确保 Python 版本 >= 3.7

## 📊 创建问卷示例

```
/create_questionnaire

# 输入标题
Customer Satisfaction Survey

# 输入描述  
Please help us improve our service

# 添加问题
mc: How satisfied are you with our service? Very Satisfied, Satisfied, Neutral, Dissatisfied, Very Dissatisfied

text: What can we improve?

mc: Would you recommend us to others? Yes, Maybe, No

done
```

## 🎯 最佳实践

1. **问卷设计**
   - 问题简洁明了
   - 选项不超过 5-6 个
   - 混合使用多选题和主观题

2. **管理建议**
   - 定期查看问卷统计
   - 及时导出重要数据
   - 适时关闭过期问卷

3. **用户体验**
   - 问卷不要过长（建议 10 题以内）
   - 提供清晰的问题描述
   - 设置合理的问题顺序 