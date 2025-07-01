# Telegram Questionnaire Bot

一个基于 Python 的 Telegram 问卷调查机器人，支持管理员创建问卷、用户填写问卷、查看统计和导出结果。

## 功能特性

### 🔧 管理员功能
- 创建任意数量的问卷调查
- 支持多选题和主观题
- 问卷状态管理（草稿、激活、关闭）
- 查看问卷统计数据
- 导出详细结果到 Excel

### 📋 用户功能
- 浏览可用问卷
- 逐步填写问卷
- 自动保存答案进度

### 🎯 UX 设计
- 直观的内联键盘操作
- 清晰的步骤指导
- 错误处理和验证
- 多语言支持（英文界面）

## 安装配置

### 1. 克隆项目
```bash
git clone <repository-url>
cd Telegram-Questionnaire-Bot
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置机器人
编辑 `config.py` 文件，填入你的配置信息：

```python
class Config:
    # Bot configuration
    BOT_TOKEN = 'your_telegram_bot_token_here'
    
    # Admin configuration (list of user IDs)
    ADMIN_USER_IDS = [
        123456789,  # Replace with actual admin user IDs
        987654321,  # Add more admin IDs as needed
    ]
    
    # Other settings remain as default
```

### 4. 获取 Bot Token
1. 在 Telegram 中找到 [@BotFather](https://t.me/BotFather)
2. 发送 `/newbot` 创建新机器人
3. 按照指示设置机器人名称和用户名
4. 复制获得的 Token 到 `config.py` 文件中

### 5. 获取用户 ID
1. 在 Telegram 中找到 [@userinfobot](https://t.me/userinfobot)
2. 发送任意消息获取你的用户 ID
3. 将管理员的用户 ID 添加到 `config.py` 文件的 `ADMIN_USER_IDS` 列表中

### 6. 运行机器人
```bash
python bot.py
```

## 使用说明

### 管理员操作流程

#### 1. 创建问卷
```
/create_questionnaire
```
- 输入问卷标题
- 输入问卷描述
- 添加问题：
  - 多选题：`mc: 问题内容? 选项1, 选项2, 选项3`
  - 主观题：`text: 问题内容?`
- 输入 `done` 完成创建

#### 2. 管理问卷
```
/my_questionnaires
```
- 查看所有问卷
- 激活草稿状态的问卷
- 关闭活跃的问卷
- 查看问卷统计

#### 3. 查看结果
```
/view_results
```
- 选择问卷查看统计数据
- 查看参与人数和完成情况

#### 4. 导出数据
```
/export_results
```
- 选择问卷导出 Excel 文件
- 包含所有用户的详细回答

### 用户操作流程

#### 1. 查看可用问卷
```
/surveys
```

#### 2. 参与问卷
- 点击"🚀 Start Survey"按钮
- 逐步回答问题
- 系统自动保存进度

#### 3. 获取帮助
```
/help
```

## 项目架构

```
Telegram-Questionnaire-Bot/
├── bot.py              # 主机器人逻辑
├── config.py           # 配置管理 (需要编辑)
├── config.example.py   # 配置示例
├── database.py         # 数据库操作
├── models.py           # 数据模型定义
├── utils.py            # 工具函数
├── requirements.txt    # 项目依赖
├── CONFIG_GUIDE.md     # 详细配置指南
└── README.md          # 项目说明
```

## 数据库结构

### 表结构
- `users` - 用户信息
- `questionnaires` - 问卷信息
- `questions` - 问题信息
- `responses` - 用户回答
- `questionnaire_responses` - 问卷完成状态

### 关系图
```
users 1:N questionnaires (创建关系)
questionnaires 1:N questions
questionnaires 1:N questionnaire_responses
questions 1:N responses
users 1:N responses
```

## 命令列表

### 基础命令
- `/start` - 开始使用机器人
- `/help` - 显示帮助信息
- `/surveys` - 查看可用问卷

### 管理员命令
- `/admin` - 管理员控制面板
- `/create_questionnaire` - 创建新问卷
- `/my_questionnaires` - 查看我的问卷
- `/view_results` - 查看问卷结果
- `/export_results` - 导出问卷数据

## 问题类型

### 多选题 (Multiple Choice)
- 用户从预定义选项中选择
- 支持 2-10 个选项
- 用户回复选项编号

### 主观题 (Text)
- 用户自由输入文本回答
- 支持多行文本
- 自动验证非空

## 技术栈

- **Python 3.7+**
- **python-telegram-bot 20.7** - Telegram Bot API
- **SQLite** - 数据存储
- **pandas** - 数据处理
- **openpyxl** - Excel 导出

## 部署建议

### 开发环境
```bash
python bot.py
```

### 生产环境
使用 systemd 或 docker 部署：

```bash
# 使用 nohup 后台运行
nohup python bot.py &

# 或使用 systemd 服务
sudo systemctl start questionnaire-bot
```

## 许可证

本项目使用 MIT 许可证。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 支持

如果遇到问题，请：
1. 检查 `config.py` 配置是否正确
2. 确认 Bot Token 有效
3. 验证管理员 ID 设置正确
4. 查看日志输出排查错误

## 更新日志

### v1.0.0
- 初始版本发布
- 支持问卷创建和管理
- 支持用户填写问卷
- 支持结果查看和导出 