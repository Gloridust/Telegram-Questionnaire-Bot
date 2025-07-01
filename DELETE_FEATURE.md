# 🗑️ 删除问卷功能说明

## 功能概述

管理员现在可以永久删除问卷及其所有相关数据，包括问题、用户回答和统计信息。

## 🔐 安全特性

### 权限控制
- ✅ 只有管理员可以删除问卷
- ✅ 管理员只能删除自己创建的问卷
- ✅ 严格的身份验证机制

### 数据完整性
- ✅ 事务性删除，确保数据一致性
- ✅ 按正确顺序删除关联数据
- ✅ 删除失败时自动回滚

### 确认机制
- ✅ 二次确认防止误删
- ✅ 显示详细统计信息
- ✅ 明确警告不可恢复

## 📱 使用方法

### 方法一：通过问卷列表
1. 使用 `/my_questionnaires` 查看问卷列表
2. 每个问卷下方都有 "🗑️ Delete" 按钮
3. 点击按钮进入删除确认页面

### 方法二：通过管理面板
1. 使用 `/admin` 打开管理面板
2. 点击 "🗑️ Delete Questionnaire"
3. 选择要删除的问卷

### 方法三：直接命令
1. 使用 `/delete_questionnaire` 命令
2. 从列表中选择要删除的问卷

## ⚠️ 删除确认流程

当点击删除按钮时，系统会显示确认页面：

```
⚠️ DELETE CONFIRMATION

📋 Questionnaire: [问卷标题]
❓ Questions: [问题数量]
👥 Total Responses: [总回答数]
✅ Completed: [完成数]

🚨 WARNING: This action cannot be undone!
All questions, responses, and data will be permanently deleted.

Are you sure you want to delete this questionnaire?

[🗑️ Yes, Delete Forever] [❌ Cancel]
```

### 确认删除
点击 "🗑️ Yes, Delete Forever" 后：
- 系统永久删除问卷及所有数据
- 显示删除成功确认消息
- 无法恢复任何数据

### 取消删除
点击 "❌ Cancel" 后：
- 取消删除操作
- 问卷和数据保持不变
- 返回管理界面

## 🗂️ 删除的数据范围

删除问卷时，以下数据会被永久删除：

### 1. 问卷基本信息
- 问卷标题和描述
- 创建时间和状态
- 所有元数据

### 2. 问题数据
- 所有问题文本
- 选择题的选项
- 问题类型和设置

### 3. 用户回答
- 所有用户的回答内容
- 选择题的选择记录
- 主观题的文本回答

### 4. 统计数据
- 参与人数统计
- 完成率数据
- 回答时间记录

## 🛡️ 安全保护措施

### 权限验证
```python
# 检查管理员权限
if not Config.is_admin(user.id):
    return "❌ Access denied"

# 检查问卷所有权
if questionnaire.created_by != user.id:
    return "❌ You can only delete your own questionnaires"
```

### 数据库事务
```python
try:
    # 按顺序删除关联数据
    cursor.execute('DELETE FROM responses WHERE questionnaire_id = ?')
    cursor.execute('DELETE FROM questionnaire_responses WHERE questionnaire_id = ?')
    cursor.execute('DELETE FROM questions WHERE questionnaire_id = ?')
    cursor.execute('DELETE FROM questionnaires WHERE id = ?')
    conn.commit()
except Exception:
    conn.rollback()  # 发生错误时回滚
    raise
```

## 📊 删除前的数据备份建议

在删除重要问卷前，建议：

1. **导出数据**
   ```
   /export_results → 选择问卷 → 下载 Excel 文件
   ```

2. **备份数据库**
   ```bash
   cp questionnaire_bot.db questionnaire_bot_backup.db
   ```

3. **记录重要信息**
   - 问卷标题和描述
   - 问题列表
   - 参与统计

## 🚨 注意事项

### ⚠️ 不可恢复
- **删除操作无法撤销**
- **数据无法恢复**
- **请谨慎操作**

### 📋 删除建议
- 删除前先导出重要数据
- 确认问卷确实不再需要
- 考虑关闭而非删除活跃问卷

### 🔄 替代方案
如果不确定是否要永久删除，可以考虑：
- 将问卷状态改为"关闭"
- 导出数据后再删除
- 创建数据库备份

## 🧪 测试验证

删除功能已通过全面测试：

✅ **权限测试**
- 非管理员无法删除
- 管理员只能删除自己的问卷

✅ **数据完整性测试**
- 所有关联数据正确删除
- 数据库约束正常工作

✅ **错误处理测试**
- 删除不存在的问卷
- 网络错误时的回滚

✅ **界面测试**
- 确认对话框正常显示
- 按钮功能正确

## 📞 技术支持

如果在使用删除功能时遇到问题：

1. 检查管理员权限设置
2. 确认问卷所有权
3. 查看机器人日志
4. 联系技术支持

---

**⚠️ 重要提醒：删除操作不可恢复，请谨慎使用！** 