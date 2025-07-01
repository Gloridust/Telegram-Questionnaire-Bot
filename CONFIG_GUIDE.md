# 配置指南

## 📋 快速配置

### 1. 编辑 config.py 文件

打开 `config.py` 文件，你会看到以下内容：

```python
class Config:
    # Bot configuration
    # Replace with your actual bot token from @BotFather
    BOT_TOKEN = 'YOUR_BOT_TOKEN_HERE'
    
    # Admin configuration (list of user IDs)
    # Replace with actual admin user IDs
    # Get your user ID from @userinfobot on Telegram
    ADMIN_USER_IDS = [
        # 123456789,  # Replace with actual admin user IDs
        # 987654321,  # Add more admin IDs as needed
    ]
    
    # Database configuration
    DATABASE_PATH = 'questionnaire_bot.db'
    
    # Other settings
    MAX_QUESTIONS_PER_QUESTIONNAIRE = 20
    MAX_OPTIONS_PER_QUESTION = 10
```

### 2. 获取 Bot Token

1. 在 Telegram 中搜索 [@BotFather](https://t.me/BotFather)
2. 发送 `/newbot` 命令
3. 按照提示输入机器人名称和用户名
4. 复制获得的 Token

### 3. 获取管理员用户 ID

1. 在 Telegram 中搜索 [@userinfobot](https://t.me/userinfobot)
2. 发送任意消息给机器人
3. 复制返回的用户 ID

### 4. 配置示例

```python
class Config:
    # Bot configuration
    BOT_TOKEN = '123456789:ABCdefGHIjklMNOpqrsTUVwxyz'
    
    # Admin configuration (list of user IDs)
    ADMIN_USER_IDS = [
        123456789,    # 你的用户 ID
        987654321,    # 其他管理员的用户 ID（可选）
    ]
    
    # 其他配置保持默认即可
    DATABASE_PATH = 'questionnaire_bot.db'
    MAX_QUESTIONS_PER_QUESTIONNAIRE = 20
    MAX_OPTIONS_PER_QUESTION = 10
```

### 5. 验证配置

运行以下命令验证配置是否正确：

```bash
python start.py
```

如果配置正确，你会看到：
```
✅ Configuration is valid
🤖 Starting Telegram Questionnaire Bot...
```

## 🔧 高级配置

### 数据库配置

- `DATABASE_PATH`: SQLite 数据库文件路径
- 默认值：`questionnaire_bot.db`

### 问卷限制

- `MAX_QUESTIONS_PER_QUESTIONNAIRE`: 每个问卷最多问题数
- `MAX_OPTIONS_PER_QUESTION`: 每个多选题最多选项数

### 多管理员配置

你可以添加多个管理员：

```python
ADMIN_USER_IDS = [
    123456789,    # 主管理员
    111222333,    # 副管理员
    444555666,    # 其他管理员
]
```

## ❗ 注意事项

1. **保护敏感信息**：不要将包含真实 Token 的 config.py 文件上传到公开仓库
2. **备份配置**：建议备份你的配置文件
3. **权限管理**：只有在 `ADMIN_USER_IDS` 列表中的用户才能创建和管理问卷

## 🚨 故障排除

### 常见问题

1. **"Please set your BOT_TOKEN in config.py"**
   - 检查 BOT_TOKEN 是否正确设置
   - 确认 Token 格式正确（格式：数字:字母数字字符串）

2. **"Please add at least one ADMIN_USER_ID in config.py"**
   - 检查 ADMIN_USER_IDS 列表是否为空
   - 确认用户 ID 格式正确（纯数字）

3. **机器人无响应**
   - 检查 Bot Token 是否有效
   - 确认机器人已启动
   - 验证网络连接

### 测试配置

1. 启动机器人
2. 在 Telegram 中找到你的机器人
3. 发送 `/start` 命令
4. 如果配置正确，机器人会回复欢迎消息 