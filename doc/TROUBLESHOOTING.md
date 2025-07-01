# 问题排查指南

## 🔍 用户扫描二维码或打开链接无响应

### 问题描述
用户通过二维码或深度链接访问问卷时，机器人的 `/start` 命令无响应。

### 已修复的问题
1. **Markdown 解析错误** - 移除了复杂的 Markdown 格式，使用简单文本
2. **深度链接解析** - 添加了错误处理和调试日志
3. **字符转义问题** - 简化了文本格式，避免特殊字符冲突

### 修复内容

#### 1. 简化文本格式
```python
# 修复前（会导致 Markdown 解析错误）
question_text = f"**Question {question_number}/{total_questions}:**\n{question.question_text}\n\n"

# 修复后（简单文本格式）
question_text = f"📝 Question {question_number}/{total_questions}:\n{question.question_text}\n\n"
```

#### 2. 添加深度链接错误处理
```python
# 添加了 try-catch 处理深度链接解析
if context.args and len(context.args) > 0 and context.args[0].startswith('survey_'):
    try:
        questionnaire_id = int(context.args[0].split('_')[1])
        await self.handle_direct_survey_access(update, context, questionnaire_id)
        return
    except (ValueError, IndexError) as e:
        logger.error(f"Error parsing survey link: {e}")
        await update.message.reply_text("❌ Invalid survey link. Please check the link and try again.")
        return
```

#### 3. 添加调试日志
```python
logger.info(f"Start command from user {user.id} with args: {context.args}")
logger.info(f"Direct survey access: user {user.id}, questionnaire {questionnaire_id}")
```

### 测试步骤

1. **创建测试问卷**：
   ```bash
   python test_deep_link.py
   ```

2. **获取机器人用户名**：
   - 在 Telegram 中搜索你的机器人
   - 查看机器人的用户名（@your_bot_username）

3. **生成测试链接**：
   ```
   https://t.me/your_bot_username?start=survey_2
   ```

4. **测试流程**：
   - 点击链接或扫描二维码
   - 检查机器人是否响应
   - 查看日志输出

### 常见问题解决

#### 问题1：机器人无响应
**解决方案**：
- 检查机器人是否在运行：`ps aux | grep python`
- 检查配置是否正确：`config.py` 中的 BOT_TOKEN 和 ADMIN_USER_IDS
- 查看日志输出是否有错误

#### 问题2：深度链接格式错误
**正确格式**：
```
https://t.me/机器人用户名?start=survey_问卷ID
```

**错误示例**：
- `https://t.me/机器人用户名/start=survey_1` ❌
- `https://t.me/机器人用户名?survey_1` ❌

#### 问题3：问卷状态不正确
**检查问卷状态**：
- 只有 `active` 状态的问卷才能通过链接访问
- 使用 `/my_questionnaires` 检查问卷状态
- 必要时重新激活问卷

#### 问题4：权限问题
**确认权限设置**：
- 普通用户只能通过链接访问问卷
- 管理员可以使用所有功能
- 检查 `config.py` 中的 `ADMIN_USER_IDS` 设置

### 调试方法

#### 1. 查看实时日志
```bash
# 启动机器人时会显示日志
python start.py

# 查看日志中的关键信息
# - "Start command from user XXX with args: ['survey_X']"
# - "Direct survey access: user XXX, questionnaire X"
```

#### 2. 手动测试深度链接
```python
# 在 Python 中测试
from database import Database
db = Database()

# 检查问卷是否存在且为活跃状态
questionnaire = db.get_questionnaire(2)  # 替换为实际ID
print(f"Status: {questionnaire.status}")
print(f"Questions: {len(db.get_questions(2))}")
```

#### 3. 测试机器人响应
- 直接发送 `/start` 命令测试基本功能
- 发送 `/start survey_2` 测试深度链接功能
- 检查机器人是否正确解析参数

### 成功标志

当修复成功时，用户点击链接后应该看到：
```
📋 Test Survey

📝 This is a test survey for deep link testing

❓ Total Questions: 1

Let's begin!

📝 Question 1/1:
What is your favorite color?

🔘 Select ONE option:
1. Red
2. Blue  
3. Green
4. Yellow

Reply with the number of your choice (1-4)

⚠️ This question is required.

[🔄 Restart Survey]
```

### 预防措施

1. **避免特殊字符**：问卷标题和描述中避免使用 Markdown 特殊字符
2. **测试链接**：每次激活问卷后测试生成的链接
3. **监控日志**：定期检查机器人日志，及时发现问题
4. **备份数据**：定期备份数据库文件 