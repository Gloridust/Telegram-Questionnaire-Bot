import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.constants import ParseMode
from datetime import datetime
import os

from config import Config
from database import Database
from models import QuestionType, QuestionnaireStatus
from utils import *

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class QuestionnaireBot:
    def __init__(self):
        if not Config.validate_config():
            raise ValueError("Invalid configuration. Please check your BOT_TOKEN and ADMIN_USER_IDS.")
        
        self.db = Database()
        self.app = Application.builder().token(Config.BOT_TOKEN).build()
        self.bot_username = None  # Will be set when bot starts
        self.setup_handlers()
        
        # Store user states for multi-step operations
        self.user_states = {}
    
    def setup_handlers(self):
        """Setup all command and callback handlers"""
        # Basic commands
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        
        # Admin-only commands
        self.app.add_handler(CommandHandler("admin", self.admin_panel))
        self.app.add_handler(CommandHandler("create_questionnaire", self.create_questionnaire_start))
        self.app.add_handler(CommandHandler("my_questionnaires", self.list_my_questionnaires))
        self.app.add_handler(CommandHandler("view_results", self.view_results))
        self.app.add_handler(CommandHandler("export_results", self.export_results))
        
        # Callback handlers
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Message handlers (for multi-step processes)
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        logger.info(f"Start command from user {user.id} with args: {context.args}")
        
        # Create or update user in database
        self.db.create_or_update_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Check if this is a deep link for a specific questionnaire
        if context.args and len(context.args) > 0 and context.args[0].startswith('survey_'):
            try:
                questionnaire_id = int(context.args[0].split('_')[1])
                await self.handle_direct_survey_access(update, context, questionnaire_id)
                return
            except (ValueError, IndexError) as e:
                logger.error(f"Error parsing survey link: {e}")
                await update.message.reply_text("❌ Invalid survey link. Please check the link and try again.")
                return
        
        welcome_message = f"👋 Welcome to the Questionnaire Bot, {user.first_name}!\n\n"
        
        if Config.is_admin(user.id):
            welcome_message += """🔧 **Admin Panel Available**
Use /admin to access the admin control panel where you can:
• Create new questionnaires
• Manage existing questionnaires  
• View results and export data

📋 **Need Help?**
Use /help for detailed instructions."""
        else:
            welcome_message += """📋 **Survey Participation**
You can participate in surveys through links provided by administrators.

📋 **Need Help?**
Use /help for more information."""
        
        await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_direct_survey_access(self, update: Update, context: ContextTypes.DEFAULT_TYPE, questionnaire_id: int):
        """Handle direct access to a survey via deep link"""
        user = update.effective_user
        logger.info(f"Direct survey access: user {user.id}, questionnaire {questionnaire_id}")
        questionnaire = self.db.get_questionnaire(questionnaire_id)
        
        if not questionnaire:
            await update.message.reply_text("❌ Survey not found.")
            return
        
        if questionnaire.status != QuestionnaireStatus.ACTIVE:
            await update.message.reply_text("❌ This survey is not currently available.")
            return
        
        questions = self.db.get_questions(questionnaire_id)
        if not questions:
            await update.message.reply_text("❌ This survey has no questions.")
            return
        
        # Start questionnaire response
        self.db.start_questionnaire_response(questionnaire_id, user.id)
        
        # Set user state for answering questions
        self.user_states[user.id] = {
            'action': 'answering_questionnaire',
            'questionnaire_id': questionnaire_id,
            'current_question_index': 0,
            'questions': questions
        }
        
        # Show survey info and first question
        intro_message = f"📋 {questionnaire.title}\n\n"
        intro_message += f"📝 {questionnaire.description or 'No description'}\n\n"
        intro_message += f"❓ Total Questions: {len(questions)}\n\n"
        intro_message += "Let's begin!\n\n"
        
        first_question = questions[0]
        question_text = self.format_question_for_display(first_question, 1, len(questions))
        
        keyboard = [[InlineKeyboardButton("🔄 Restart Survey", callback_data=f"restart_survey_{questionnaire_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(intro_message + question_text, 
                                      reply_markup=reply_markup)
    
    def format_question_for_display(self, question, question_number: int, total_questions: int) -> str:
        """Format question for display during questionnaire taking"""
        question_text = f"📝 Question {question_number}/{total_questions}:\n{question.question_text}\n\n"
        
        if question.question_type == QuestionType.SINGLE_CHOICE and question.options:
            question_text += "🔘 Select ONE option:\n"
            for i, option in enumerate(question.options):
                question_text += f"{i + 1}. {option}\n"
            question_text += f"\nReply with the number of your choice (1-{len(question.options)})"
        elif question.question_type == QuestionType.MULTIPLE_CHOICE and question.options:
            question_text += "☑️ Select ONE or MORE options:\n"
            for i, option in enumerate(question.options):
                question_text += f"{i + 1}. {option}\n"
            question_text += "\nReply with numbers separated by commas (e.g., 1,3,5)"
        else:  # TEXT
            question_text += "💬 Please type your answer:"
        
        if question.is_required:
            question_text += "\n\n⚠️ This question is required."
        
        return question_text
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        user = update.effective_user
        
        help_text = "🤖 **Questionnaire Bot Help**\n\n"
        
        if Config.is_admin(user.id):
            help_text += """🔧 **Admin Commands:**
• `/admin` - Open admin control panel
• `/create_questionnaire` - Start creating a new questionnaire
• `/my_questionnaires` - View and manage your questionnaires
• `/view_results` - View response statistics and summaries
• `/export_results` - Export detailed results to Excel

📋 **How to create questionnaires:**
1. Use `/create_questionnaire` to start
2. Enter title and description
3. Add questions step by step
4. Choose question types: Single Choice, Multiple Choice, or Text
5. Activate questionnaire to generate sharing link and QR code

📊 **Question Types:**
• **Single Choice** - Users select one option
• **Multiple Choice** - Users can select multiple options  
• **Text** - Users provide free-form text answers"""
        else:
            help_text += """📋 **For Survey Participants:**
• You can only access surveys through links provided by administrators
• Follow the survey link to participate
• Answer questions step by step
• You can restart a survey if needed

💡 **Tips:**
• Make sure to complete all required questions
• You can use the restart button if you make mistakes
• Contact the survey administrator if you have issues"""
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show admin control panel"""
        user = update.effective_user
        
        if not Config.is_admin(user.id):
            await update.message.reply_text("❌ Access denied. Admin privileges required.")
            return
        
        keyboard = [
            [InlineKeyboardButton("📝 Create Questionnaire", callback_data="admin_create")],
            [InlineKeyboardButton("📋 My Questionnaires", callback_data="admin_list")],
            [InlineKeyboardButton("📊 View Results", callback_data="admin_results")],
            [InlineKeyboardButton("📤 Export Results", callback_data="admin_export")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔧 **Admin Control Panel**\n\nSelect an option:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def create_questionnaire_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start questionnaire creation process"""
        user = update.effective_user
        
        if not Config.is_admin(user.id):
            await update.message.reply_text("❌ Access denied. Admin privileges required.")
            return
        
        # Initialize creation state
        self.user_states[user.id] = {
            'action': 'creating_questionnaire',
            'step': 'title',
            'data': {}
        }
        
        keyboard = [[InlineKeyboardButton("🔄 Cancel Creation", callback_data="cancel_creation")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📝 **Create New Questionnaire**\n\n"
            "Step 1: Please enter the questionnaire title:",
            reply_markup=reply_markup
        )
    
    async def list_my_questionnaires(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List questionnaires created by admin"""
        user = update.effective_user
        
        if not Config.is_admin(user.id):
            await update.message.reply_text("❌ Access denied. Admin privileges required.")
            return
        
        questionnaires = self.db.get_questionnaires_by_admin(user.id)
        
        if not questionnaires:
            await update.message.reply_text("📋 You haven't created any questionnaires yet.")
            return
        
        for q in questionnaires:
            questions = self.db.get_questions(q.id)
            stats = self.db.get_questionnaire_stats(q.id)
            
            message = format_questionnaire_info(q, len(questions), stats)
            
            # Add action buttons based on status
            keyboard = []
            if q.status == QuestionnaireStatus.DRAFT:
                keyboard.append([InlineKeyboardButton("🚀 Activate", callback_data=f"activate_{q.id}")])
                keyboard.append([InlineKeyboardButton("🔄 Restart Creation", callback_data=f"restart_creation_{q.id}")])
            elif q.status == QuestionnaireStatus.ACTIVE:
                keyboard.append([InlineKeyboardButton("🔗 Get Link & QR", callback_data=f"get_link_{q.id}")])
                keyboard.append([InlineKeyboardButton("📊 Results", callback_data=f"results_{q.id}")])
                keyboard.append([InlineKeyboardButton("🔒 Close", callback_data=f"close_{q.id}")])
            else:  # CLOSED
                keyboard.append([InlineKeyboardButton("📊 Results", callback_data=f"results_{q.id}")])
                keyboard.append([InlineKeyboardButton("📤 Export", callback_data=f"export_{q.id}")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user = update.effective_user
        
        # Admin callbacks
        if data.startswith("admin_"):
            await self.handle_admin_callback(query, data, user)
        elif data.startswith("activate_"):
            await self.handle_activate_questionnaire(query, data, user, context)
        elif data.startswith("close_"):
            await self.handle_close_questionnaire(query, data, user)
        elif data.startswith("results_"):
            await self.handle_view_results_callback(query, data, user)
        elif data.startswith("export_"):
            await self.handle_export_callback(query, data, user, context)
        elif data.startswith("get_link_"):
            await self.handle_get_link_callback(query, data, user, context)
        
        # Creation callbacks
        elif data.startswith("cancel_creation"):
            await self.handle_cancel_creation(query, user)
        elif data.startswith("restart_creation_"):
            await self.handle_restart_creation(query, data, user)
        elif data.startswith("add_question_"):
            await self.handle_add_question(query, data, user)
        elif data.startswith("finish_questionnaire_"):
            await self.handle_finish_questionnaire(query, data, user)
        elif data.startswith("question_type_"):
            await self.handle_question_type_selection(query, data, user)
        elif data.startswith("add_option_"):
            await self.handle_add_option(query, data, user)
        elif data.startswith("finish_options_"):
            await self.handle_finish_options(query, data, user)
        
        # Survey callbacks
        elif data.startswith("restart_survey_"):
            await self.handle_restart_survey(query, data, user)
    
    async def handle_admin_callback(self, query, data, user):
        """Handle admin panel callbacks"""
        if not Config.is_admin(user.id):
            await query.edit_message_text("❌ Access denied. Admin privileges required.")
            return
        
        if data == "admin_create":
            await self.create_questionnaire_start_from_callback(query, user)
        elif data == "admin_list":
            await self.list_my_questionnaires_from_callback(query, user)
        elif data == "admin_results":
            await self.view_results_from_callback(query, user)
        elif data == "admin_export":
            await self.export_results_from_callback(query, user)
    
    async def create_questionnaire_start_from_callback(self, query, user):
        """Start questionnaire creation from callback"""
        self.user_states[user.id] = {
            'action': 'creating_questionnaire',
            'step': 'title',
            'data': {}
        }
        
        keyboard = [[InlineKeyboardButton("🔄 Cancel Creation", callback_data="cancel_creation")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📝 **Create New Questionnaire**\n\n"
            "Step 1: Please enter the questionnaire title:",
            reply_markup=reply_markup
        )
    
    async def handle_cancel_creation(self, query, user):
        """Handle creation cancellation"""
        if user.id in self.user_states:
            del self.user_states[user.id]
        
        await query.edit_message_text("❌ Questionnaire creation cancelled.")
    
    async def handle_restart_creation(self, query, data, user):
        """Handle restarting questionnaire creation"""
        if not Config.is_admin(user.id):
            await query.edit_message_text("❌ Access denied. Admin privileges required.")
            return
        
        questionnaire_id = int(data.split("_")[-1])
        questionnaire = self.db.get_questionnaire(questionnaire_id)
        
        if not questionnaire:
            await query.edit_message_text("❌ Questionnaire not found.")
            return
        
        # Set up state for continuing creation
        self.user_states[user.id] = {
            'action': 'creating_questionnaire',
            'step': 'questions_menu',
            'data': {
                'questionnaire_id': questionnaire_id,
                'title': questionnaire.title,
                'description': questionnaire.description
            }
        }
        
        await self.show_questions_menu(query, questionnaire_id)
    
    async def show_questions_menu(self, query, questionnaire_id):
        """Show the questions management menu"""
        questions = self.db.get_questions(questionnaire_id)
        questionnaire = self.db.get_questionnaire(questionnaire_id)
        
        message = f"📝 **{questionnaire.title}**\n\n"
        message += f"📋 Description: {questionnaire.description}\n\n"
        message += f"❓ Current Questions: {len(questions)}\n\n"
        
        if questions:
            message += "**Questions:**\n"
            for i, q in enumerate(questions):
                type_icon = {"single_choice": "🔘", "multiple_choice": "☑️", "text": "📝"}.get(q.question_type.value, "❓")
                message += f"{i+1}. {type_icon} {q.question_text}\n"
            message += "\n"
        
        keyboard = [
            [InlineKeyboardButton("➕ Add Question", callback_data=f"add_question_{questionnaire_id}")],
            [InlineKeyboardButton("✅ Finish Questionnaire", callback_data=f"finish_questionnaire_{questionnaire_id}")],
            [InlineKeyboardButton("🔄 Cancel", callback_data="cancel_creation")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_add_question(self, query, data, user):
        """Handle adding a new question"""
        if not Config.is_admin(user.id):
            await query.edit_message_text("❌ Access denied. Admin privileges required.")
            return
        
        questionnaire_id = int(data.split("_")[-1])
        
        # Update user state
        if user.id in self.user_states:
            self.user_states[user.id]['step'] = 'question_type'
            self.user_states[user.id]['data']['current_questionnaire_id'] = questionnaire_id
        
        keyboard = [
            [InlineKeyboardButton("🔘 Single Choice", callback_data=f"question_type_single_{questionnaire_id}")],
            [InlineKeyboardButton("☑️ Multiple Choice", callback_data=f"question_type_multiple_{questionnaire_id}")],
            [InlineKeyboardButton("📝 Text Answer", callback_data=f"question_type_text_{questionnaire_id}")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data=f"back_to_menu_{questionnaire_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "❓ **Select Question Type:**\n\n"
            "🔘 **Single Choice** - User selects one option\n"
            "☑️ **Multiple Choice** - User can select multiple options\n"
            "📝 **Text Answer** - User types a free-form answer",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_question_type_selection(self, query, data, user):
        """Handle question type selection"""
        if not Config.is_admin(user.id):
            await query.edit_message_text("❌ Access denied. Admin privileges required.")
            return
        
        parts = data.split("_")
        question_type = parts[2]  # single, multiple, or text
        questionnaire_id = int(parts[3])
        
        # Update user state
        if user.id in self.user_states:
            self.user_states[user.id]['step'] = 'question_text'
            self.user_states[user.id]['data']['current_question_type'] = question_type
            self.user_states[user.id]['data']['current_questionnaire_id'] = questionnaire_id
        
        type_name = {"single": "Single Choice", "multiple": "Multiple Choice", "text": "Text Answer"}[question_type]
        
        keyboard = [
            [InlineKeyboardButton("🔄 Change Type", callback_data=f"add_question_{questionnaire_id}")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data=f"back_to_menu_{questionnaire_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📝 **{type_name} Question**\n\n"
            f"Please type your question text:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages based on user state"""
        user = update.effective_user
        message_text = update.message.text.strip()
        
        if user.id not in self.user_states:
            # No active state - ignore message
            return
        
        state = self.user_states[user.id]
        
        try:
            if state['action'] == 'creating_questionnaire':
                await self.handle_questionnaire_creation(update, context, state, message_text)
            elif state['action'] == 'answering_questionnaire':
                await self.handle_questionnaire_answering(update, context, state, message_text)
        except Exception as e:
            logger.error(f"Error handling text message: {e}")
            await update.message.reply_text("❌ An error occurred. Please try again.")
    
    async def handle_questionnaire_creation(self, update, context, state, message_text):
        """Handle questionnaire creation steps"""
        user = update.effective_user
        
        if state['step'] == 'title':
            state['data']['title'] = message_text
            state['step'] = 'description'
            
            keyboard = [[InlineKeyboardButton("🔄 Cancel Creation", callback_data="cancel_creation")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "📝 **Create New Questionnaire**\n\n"
                "Step 2: Please enter the questionnaire description:",
                reply_markup=reply_markup
            )
            
        elif state['step'] == 'description':
            state['data']['description'] = message_text
            
            # Create questionnaire in database
            questionnaire_id = self.db.create_questionnaire(
                title=state['data']['title'],
                description=state['data']['description'],
                created_by=user.id
            )
            
            state['data']['questionnaire_id'] = questionnaire_id
            state['step'] = 'questions_menu'
            
            await update.message.reply_text(
                f"✅ Questionnaire '{state['data']['title']}' created!\n\n"
                f"Now let's add some questions..."
            )
            
            # Show questions menu
            keyboard = [
                [InlineKeyboardButton("➕ Add Question", callback_data=f"add_question_{questionnaire_id}")],
                [InlineKeyboardButton("✅ Finish Questionnaire", callback_data=f"finish_questionnaire_{questionnaire_id}")],
                [InlineKeyboardButton("🔄 Cancel", callback_data="cancel_creation")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "📋 **Question Management**\n\n"
                "Your questionnaire is ready for questions!\n\n"
                "➕ **Add Question** - Add a new question\n"
                "✅ **Finish** - Complete and save questionnaire",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
        elif state['step'] == 'question_text':
            # Save question text and proceed based on type
            question_type = state['data']['current_question_type']
            questionnaire_id = state['data']['current_questionnaire_id']
            
            state['data']['current_question_text'] = message_text
            
            if question_type in ['single', 'multiple']:
                # Need to collect options
                state['step'] = 'question_options'
                state['data']['current_options'] = []
                
                keyboard = [
                    [InlineKeyboardButton("🔄 Change Question", callback_data=f"add_question_{questionnaire_id}")],
                    [InlineKeyboardButton("🔙 Back to Menu", callback_data=f"back_to_menu_{questionnaire_id}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"📝 **Question:** {message_text}\n\n"
                    f"Now add options for this question.\n"
                    f"Type each option and press Enter.\n"
                    f"When finished, use the button below.",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                # Text question - save directly
                question_type_enum = QuestionType.TEXT
                
                question_id = self.db.add_question(
                    questionnaire_id=questionnaire_id,
                    question_text=message_text,
                    question_type=question_type_enum,
                    options=None,
                    is_required=True
                )
                
                await update.message.reply_text(f"✅ Text question added successfully!")
                
                # Return to questions menu
                await self.show_questions_menu_after_creation(update, questionnaire_id)
        
        elif state['step'] == 'question_options':
            # Add option to current question
            options = state['data']['current_options']
            options.append(message_text)
            
            questionnaire_id = state['data']['current_questionnaire_id']
            
            options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
            
            keyboard = [
                [InlineKeyboardButton("✅ Finish Options", callback_data=f"finish_options_{questionnaire_id}")],
                [InlineKeyboardButton("🔄 Restart Question", callback_data=f"add_question_{questionnaire_id}")],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data=f"back_to_menu_{questionnaire_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"📝 **Question:** {state['data']['current_question_text']}\n\n"
                f"**Options so far:**\n{options_text}\n\n"
                f"➕ Type another option or finish with the button below.\n"
                f"(Minimum 2 options required)",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def show_questions_menu_after_creation(self, update, questionnaire_id):
        """Show questions menu after creating a question"""
        questions = self.db.get_questions(questionnaire_id)
        questionnaire = self.db.get_questionnaire(questionnaire_id)
        
        message = f"📝 **{questionnaire.title}**\n\n"
        message += f"❓ Questions: {len(questions)}\n\n"
        
        if questions:
            message += "**Recent Questions:**\n"
            for i, q in enumerate(questions[-3:]):  # Show last 3
                type_icon = {"single_choice": "🔘", "multiple_choice": "☑️", "text": "📝"}.get(q.question_type.value, "❓")
                message += f"{len(questions)-2+i}. {type_icon} {q.question_text}\n"
            message += "\n"
        
        keyboard = [
            [InlineKeyboardButton("➕ Add Another Question", callback_data=f"add_question_{questionnaire_id}")],
            [InlineKeyboardButton("✅ Finish Questionnaire", callback_data=f"finish_questionnaire_{questionnaire_id}")],
            [InlineKeyboardButton("🔄 Cancel", callback_data="cancel_creation")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_finish_options(self, query, data, user):
        """Handle finishing options for a question"""
        if not Config.is_admin(user.id):
            await query.edit_message_text("❌ Access denied. Admin privileges required.")
            return
        
        questionnaire_id = int(data.split("_")[-1])
        
        if user.id not in self.user_states:
            await query.edit_message_text("❌ No active question creation session.")
            return
        
        state = self.user_states[user.id]
        options = state['data']['current_options']
        
        if len(options) < 2:
            await query.edit_message_text("❌ You need at least 2 options for choice questions.")
            return
        
        # Save the question
        question_type = state['data']['current_question_type']
        question_text = state['data']['current_question_text']
        
        question_type_enum = QuestionType.SINGLE_CHOICE if question_type == 'single' else QuestionType.MULTIPLE_CHOICE
        
        question_id = self.db.add_question(
            questionnaire_id=questionnaire_id,
            question_text=question_text,
            question_type=question_type_enum,
            options=options,
            is_required=True
        )
        
        await query.edit_message_text(f"✅ {question_type_enum.value.replace('_', ' ').title()} question added successfully!")
        
        # Return to questions menu
        await self.show_questions_menu_after_callback(query, questionnaire_id)
    
    async def show_questions_menu_after_callback(self, query, questionnaire_id):
        """Show questions menu after callback action"""
        questions = self.db.get_questions(questionnaire_id)
        questionnaire = self.db.get_questionnaire(questionnaire_id)
        
        message = f"📝 **{questionnaire.title}**\n\n"
        message += f"❓ Questions: {len(questions)}\n\n"
        
        if questions:
            message += "**Questions:**\n"
            for i, q in enumerate(questions):
                type_icon = {"single_choice": "🔘", "multiple_choice": "☑️", "text": "📝"}.get(q.question_type.value, "❓")
                message += f"{i+1}. {type_icon} {q.question_text}\n"
            message += "\n"
        
        keyboard = [
            [InlineKeyboardButton("➕ Add Question", callback_data=f"add_question_{questionnaire_id}")],
            [InlineKeyboardButton("✅ Finish Questionnaire", callback_data=f"finish_questionnaire_{questionnaire_id}")],
            [InlineKeyboardButton("🔄 Cancel", callback_data="cancel_creation")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_finish_questionnaire(self, query, data, user):
        """Handle finishing questionnaire creation"""
        if not Config.is_admin(user.id):
            await query.edit_message_text("❌ Access denied. Admin privileges required.")
            return
        
        questionnaire_id = int(data.split("_")[-1])
        questions = self.db.get_questions(questionnaire_id)
        
        if not questions:
            await query.edit_message_text("❌ You must add at least one question before finishing.")
            return
        
        # Clean up user state
        if user.id in self.user_states:
            del self.user_states[user.id]
        
        questionnaire = self.db.get_questionnaire(questionnaire_id)
        
        await query.edit_message_text(
            f"🎉 **Questionnaire Created Successfully!**\n\n"
            f"📋 **{questionnaire.title}**\n"
            f"❓ Questions: {len(questions)}\n"
            f"📝 Status: Draft\n\n"
            f"Your questionnaire is ready! Use /my_questionnaires to activate it and get the sharing link."
        )
    
    async def handle_activate_questionnaire(self, query, data, user, context):
        """Handle questionnaire activation with link generation"""
        if not Config.is_admin(user.id):
            await query.edit_message_text("❌ Access denied. Admin privileges required.")
            return
        
        questionnaire_id = int(data.split("_")[-1])
        
        # Check if questionnaire has questions
        questions = self.db.get_questions(questionnaire_id)
        if not questions:
            await query.edit_message_text("❌ Cannot activate questionnaire without questions.")
            return
        
        # Get bot username if not cached
        if not self.bot_username:
            bot_info = await context.bot.get_me()
            self.bot_username = bot_info.username
        
        # Activate questionnaire
        self.db.update_questionnaire_status(questionnaire_id, QuestionnaireStatus.ACTIVE)
        questionnaire = self.db.get_questionnaire(questionnaire_id)
        
        # Generate link and QR code
        survey_link = generate_questionnaire_link(self.bot_username, questionnaire_id)
        qr_code_io = generate_qr_code(survey_link)
        
        message = f"✅ **Questionnaire Activated!**\n\n"
        message += f"📋 **{questionnaire.title}**\n"
        message += f"🔗 **Survey Link:**\n`{survey_link}`\n\n"
        message += f"📱 **QR Code:** (attached below)\n\n"
        message += f"Share this link or QR code with participants!"
        
        # Send QR code as photo
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=qr_code_io,
            caption=message,
            parse_mode=ParseMode.MARKDOWN
        )
        
        await query.edit_message_text("🎉 Questionnaire activated! Check the message above for the link and QR code.")
    
    async def handle_get_link_callback(self, query, data, user, context):
        """Handle getting link and QR code for active questionnaire"""
        if not Config.is_admin(user.id):
            await query.edit_message_text("❌ Access denied. Admin privileges required.")
            return
        
        questionnaire_id = int(data.split("_")[-1])
        questionnaire = self.db.get_questionnaire(questionnaire_id)
        
        if questionnaire.status != QuestionnaireStatus.ACTIVE:
            await query.edit_message_text("❌ Only active questionnaires have sharing links.")
            return
        
        # Get bot username if not cached
        if not self.bot_username:
            bot_info = await context.bot.get_me()
            self.bot_username = bot_info.username
        
        # Generate link and QR code
        survey_link = generate_questionnaire_link(self.bot_username, questionnaire_id)
        qr_code_io = generate_qr_code(survey_link)
        
        message = f"🔗 **Survey Link & QR Code**\n\n"
        message += f"📋 **{questionnaire.title}**\n"
        message += f"🔗 **Link:**\n`{survey_link}`\n\n"
        message += f"📱 **QR Code:** (attached below)"
        
        # Send QR code as photo
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=qr_code_io,
            caption=message,
            parse_mode=ParseMode.MARKDOWN
        )
        
        await query.edit_message_text("📤 Link and QR code sent! Check the message above.")
    
    async def handle_questionnaire_answering(self, update, context, state, message_text):
        """Handle questionnaire answering process"""
        user = update.effective_user
        questions = state['questions']
        current_index = state['current_question_index']
        current_question = questions[current_index]
        
        try:
            if current_question.question_type == QuestionType.SINGLE_CHOICE:
                # Single choice validation
                try:
                    selected = int(message_text.strip())
                    if 1 <= selected <= len(current_question.options):
                        selected_option = selected - 1  # Convert to 0-based index
                        
                        self.db.save_response(
                            questionnaire_id=state['questionnaire_id'],
                            user_id=user.id,
                            question_id=current_question.id,
                            selected_option=selected_option
                        )
                    else:
                        raise ValueError("Invalid option")
                except ValueError:
                    keyboard = [[InlineKeyboardButton("🔄 Restart Survey", callback_data=f"restart_survey_{state['questionnaire_id']}")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(
                        f"❌ Invalid option. Please select a number between 1 and {len(current_question.options)}.",
                        reply_markup=reply_markup
                    )
                    return
                    
            elif current_question.question_type == QuestionType.MULTIPLE_CHOICE:
                # Multiple choice validation
                try:
                    # Parse comma-separated numbers
                    selected_numbers = [int(x.strip()) for x in message_text.split(',')]
                    selected_options = []
                    
                    for num in selected_numbers:
                        if 1 <= num <= len(current_question.options):
                            selected_options.append(num - 1)  # Convert to 0-based index
                        else:
                            raise ValueError("Invalid option")
                    
                    if not selected_options:
                        raise ValueError("No valid options")
                    
                    self.db.save_response(
                        questionnaire_id=state['questionnaire_id'],
                        user_id=user.id,
                        question_id=current_question.id,
                        selected_options=selected_options
                    )
                except ValueError:
                    keyboard = [[InlineKeyboardButton("🔄 Restart Survey", callback_data=f"restart_survey_{state['questionnaire_id']}")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(
                        f"❌ Invalid format. Please enter numbers separated by commas (e.g., 1,3,5).\n"
                        f"Valid options: 1-{len(current_question.options)}",
                        reply_markup=reply_markup
                    )
                    return
                    
            else:  # TEXT question
                if not message_text.strip():
                    keyboard = [[InlineKeyboardButton("🔄 Restart Survey", callback_data=f"restart_survey_{state['questionnaire_id']}")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(
                        "❌ Answer cannot be empty. Please provide an answer.",
                        reply_markup=reply_markup
                    )
                    return
                
                self.db.save_response(
                    questionnaire_id=state['questionnaire_id'],
                    user_id=user.id,
                    question_id=current_question.id,
                    answer_text=message_text.strip()
                )
            
            # Move to next question or complete
            next_index = current_index + 1
            
            if next_index >= len(questions):
                # Complete questionnaire
                self.db.complete_questionnaire_response(state['questionnaire_id'], user.id)
                del self.user_states[user.id]
                
                await update.message.reply_text(
                    "🎉 **Survey Completed!**\n\n"
                    "Thank you for your participation! 🙏\n\n"
                    "Your responses have been recorded successfully."
                )
            else:
                # Show next question
                state['current_question_index'] = next_index
                next_question = questions[next_index]
                question_text = self.format_question_for_display(next_question, next_index + 1, len(questions))
                
                keyboard = [[InlineKeyboardButton("🔄 Restart Survey", callback_data=f"restart_survey_{state['questionnaire_id']}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(question_text, reply_markup=reply_markup)
                
        except Exception as e:
            logger.error(f"Error saving response: {e}")
            keyboard = [[InlineKeyboardButton("🔄 Restart Survey", callback_data=f"restart_survey_{state['questionnaire_id']}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "❌ Error saving your answer. Please try again.",
                reply_markup=reply_markup
            )
    
    async def handle_restart_survey(self, query, data, user):
        """Handle survey restart"""
        questionnaire_id = int(data.split("_")[-1])
        
        # Clear any existing state
        if user.id in self.user_states:
            del self.user_states[user.id]
        
        # Restart the survey
        questionnaire = self.db.get_questionnaire(questionnaire_id)
        
        if not questionnaire or questionnaire.status != QuestionnaireStatus.ACTIVE:
            await query.edit_message_text("❌ This survey is not currently available.")
            return
        
        questions = self.db.get_questions(questionnaire_id)
        if not questions:
            await query.edit_message_text("❌ This survey has no questions.")
            return
        
        # Start fresh questionnaire response
        self.db.start_questionnaire_response(questionnaire_id, user.id)
        
        # Set user state for answering questions
        self.user_states[user.id] = {
            'action': 'answering_questionnaire',
            'questionnaire_id': questionnaire_id,
            'current_question_index': 0,
            'questions': questions
        }
        
        # Show first question
        first_question = questions[0]
        question_text = self.format_question_for_display(first_question, 1, len(questions))
        
        keyboard = [[InlineKeyboardButton("🔄 Restart Survey", callback_data=f"restart_survey_{questionnaire_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🔄 Survey Restarted\n\n{question_text}",
            reply_markup=reply_markup
        )
    
    # Additional admin methods (simplified for brevity)
    async def list_my_questionnaires_from_callback(self, query, user):
        """List questionnaires from callback - simplified"""
        if not Config.is_admin(user.id):
            await query.edit_message_text("❌ Access denied. Admin privileges required.")
            return
        
        questionnaires = self.db.get_questionnaires_by_admin(user.id)
        
        if not questionnaires:
            await query.edit_message_text("📋 You haven't created any questionnaires yet.")
            return
        
        message = "📋 **Your Questionnaires:**\n\n"
        for q in questionnaires:
            stats = self.db.get_questionnaire_stats(q.id)
            status_icon = {'draft': '📝', 'active': '✅', 'closed': '🔒'}.get(q.status.value, '❓')
            message += f"{status_icon} {q.title} ({stats['total_completed']} completed)\n"
        
        await query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN)
    
    async def view_results_from_callback(self, query, user):
        """View results from callback - simplified"""
        if not Config.is_admin(user.id):
            await query.edit_message_text("❌ Access denied. Admin privileges required.")
            return
        
        questionnaires = self.db.get_questionnaires_by_admin(user.id)
        
        if not questionnaires:
            await query.edit_message_text("📋 You haven't created any questionnaires yet.")
            return
        
        message = "📊 **Select a questionnaire to view results:**\n\n"
        keyboard = []
        
        for q in questionnaires:
            stats = self.db.get_questionnaire_stats(q.id)
            message += f"📋 {q.title} - {stats['total_completed']} responses\n"
            keyboard.append([InlineKeyboardButton(f"📊 {q.title}", callback_data=f"results_{q.id}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def export_results_from_callback(self, query, user):
        """Export results from callback - simplified"""
        if not Config.is_admin(user.id):
            await query.edit_message_text("❌ Access denied. Admin privileges required.")
            return
        
        questionnaires = self.db.get_questionnaires_by_admin(user.id)
        
        if not questionnaires:
            await query.edit_message_text("📋 You haven't created any questionnaires yet.")
            return
        
        message = "📤 **Select a questionnaire to export:**\n\n"
        keyboard = []
        
        for q in questionnaires:
            stats = self.db.get_questionnaire_stats(q.id)
            message += f"📋 {q.title} - {stats['total_completed']} responses\n"
            keyboard.append([InlineKeyboardButton(f"📤 {q.title}", callback_data=f"export_{q.id}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_close_questionnaire(self, query, data, user):
        """Handle questionnaire closing"""
        if not Config.is_admin(user.id):
            await query.edit_message_text("❌ Access denied. Admin privileges required.")
            return
        
        questionnaire_id = int(data.split("_")[-1])
        self.db.update_questionnaire_status(questionnaire_id, QuestionnaireStatus.CLOSED)
        await query.edit_message_text("🔒 Questionnaire closed successfully!")
    
    async def handle_view_results_callback(self, query, data, user):
        """Handle view results callback"""
        if not Config.is_admin(user.id):
            await query.edit_message_text("❌ Access denied. Admin privileges required.")
            return
        
        questionnaire_id = int(data.split("_")[-1])
        questionnaire = self.db.get_questionnaire(questionnaire_id)
        responses = self.db.get_questionnaire_responses(questionnaire_id)
        
        summary = format_response_summary(responses, questionnaire.title)
        await query.edit_message_text(summary, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_export_callback(self, query, data, user, context):
        """Handle export callback"""
        if not Config.is_admin(user.id):
            await query.edit_message_text("❌ Access denied. Admin privileges required.")
            return
        
        questionnaire_id = int(data.split("_")[-1])
        questionnaire = self.db.get_questionnaire(questionnaire_id)
        questions = self.db.get_questions(questionnaire_id)
        responses = self.db.get_questionnaire_responses(questionnaire_id)
        
        try:
            # Export to Excel
            filepath = export_to_excel(questionnaire.title, responses, questions)
            
            # Send file
            await query.edit_message_text("📤 Preparing export...")
            
            with open(filepath, 'rb') as file:
                await context.bot.send_document(
                    chat_id=query.message.chat_id,
                    document=file,
                    filename=os.path.basename(filepath),
                    caption=f"📊 Export for '{questionnaire.title}'"
                )
            
            await query.edit_message_text("✅ Export completed and sent!")
            
        except Exception as e:
            logger.error(f"Export error: {e}")
            await query.edit_message_text("❌ Error creating export file.")
    
    # Simplified admin commands for direct access
    async def view_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View questionnaire results (admin only)"""
        user = update.effective_user
        
        if not Config.is_admin(user.id):
            await update.message.reply_text("❌ Access denied. Admin privileges required.")
            return
        
        await update.message.reply_text("Use /admin panel for better interface, or see individual questionnaire results in /my_questionnaires")
    
    async def export_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Export questionnaire results (admin only)"""
        user = update.effective_user
        
        if not Config.is_admin(user.id):
            await update.message.reply_text("❌ Access denied. Admin privileges required.")
            return
        
        await update.message.reply_text("Use /admin panel for better interface, or export from /my_questionnaires")
    
    def run(self):
        """Run the bot"""
        logger.info("Starting Questionnaire Bot...")
        self.app.run_polling()

def main():
    """Main function"""
    try:
        bot = QuestionnaireBot()
        bot.run()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        print(f"Error: {e}")
        print("Please check your configuration in config.py")

if __name__ == "__main__":
    main() 