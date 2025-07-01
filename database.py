import sqlite3
import json
from typing import List, Optional, Tuple
from datetime import datetime
from models import *
from config import Config

class Database:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DATABASE_PATH
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Questionnaires table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questionnaires (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                created_by INTEGER NOT NULL,
                status TEXT DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users (user_id)
            )
        ''')
        
        # Questions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                questionnaire_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                question_type TEXT NOT NULL,
                options TEXT,  -- JSON string for multiple choice options
                is_required BOOLEAN DEFAULT TRUE,
                order_index INTEGER NOT NULL,
                FOREIGN KEY (questionnaire_id) REFERENCES questionnaires (id)
            )
        ''')
        
        # Responses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                questionnaire_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                answer_text TEXT,
                selected_option INTEGER,
                selected_options TEXT,  -- JSON string for multiple choice (multiple answers)
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (questionnaire_id) REFERENCES questionnaires (id),
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (question_id) REFERENCES questions (id)
            )
        ''')
        
        # Questionnaire responses table (to track completion status)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questionnaire_responses (
                questionnaire_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                is_completed BOOLEAN DEFAULT FALSE,
                PRIMARY KEY (questionnaire_id, user_id),
                FOREIGN KEY (questionnaire_id) REFERENCES questionnaires (id),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # User operations
    def create_or_update_user(self, user_id: int, username: str = None, 
                             first_name: str = None, last_name: str = None) -> User:
        """Create or update user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        is_admin = Config.is_admin(user_id)
        
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, username, first_name, last_name, is_admin, created_at)
            VALUES (?, ?, ?, ?, ?, COALESCE(
                (SELECT created_at FROM users WHERE user_id = ?), 
                CURRENT_TIMESTAMP
            ))
        ''', (user_id, username, first_name, last_name, is_admin, user_id))
        
        conn.commit()
        conn.close()
        
        return User(user_id, username, first_name, last_name, is_admin, datetime.now())
    
    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return User(
                user_id=row['user_id'],
                username=row['username'],
                first_name=row['first_name'],
                last_name=row['last_name'],
                is_admin=row['is_admin'],
                created_at=datetime.fromisoformat(row['created_at'])
            )
        return None
    
    # Questionnaire operations
    def create_questionnaire(self, title: str, description: str, created_by: int) -> int:
        """Create new questionnaire"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO questionnaires (title, description, created_by)
            VALUES (?, ?, ?)
        ''', (title, description, created_by))
        
        questionnaire_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return questionnaire_id
    
    def get_questionnaire(self, questionnaire_id: int) -> Optional[Questionnaire]:
        """Get questionnaire by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM questionnaires WHERE id = ?', (questionnaire_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Questionnaire(
                id=row['id'],
                title=row['title'],
                description=row['description'],
                created_by=row['created_by'],
                status=QuestionnaireStatus(row['status']),
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            )
        return None
    
    def get_questionnaires_by_admin(self, admin_id: int) -> List[Questionnaire]:
        """Get all questionnaires created by admin"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM questionnaires 
            WHERE created_by = ? 
            ORDER BY created_at DESC
        ''', (admin_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        questionnaires = []
        for row in rows:
            questionnaires.append(Questionnaire(
                id=row['id'],
                title=row['title'],
                description=row['description'],
                created_by=row['created_by'],
                status=QuestionnaireStatus(row['status']),
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            ))
        
        return questionnaires
    
    def get_active_questionnaires(self) -> List[Questionnaire]:
        """Get all active questionnaires"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM questionnaires 
            WHERE status = 'active' 
            ORDER BY created_at DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        questionnaires = []
        for row in rows:
            questionnaires.append(Questionnaire(
                id=row['id'],
                title=row['title'],
                description=row['description'],
                created_by=row['created_by'],
                status=QuestionnaireStatus(row['status']),
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            ))
        
        return questionnaires
    
    def update_questionnaire_status(self, questionnaire_id: int, status: QuestionnaireStatus):
        """Update questionnaire status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE questionnaires 
            SET status = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (status.value, questionnaire_id))
        
        conn.commit()
        conn.close()
    
    # Question operations
    def add_question(self, questionnaire_id: int, question_text: str, 
                    question_type: QuestionType, options: List[str] = None, 
                    is_required: bool = True) -> int:
        """Add question to questionnaire"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get next order index
        cursor.execute('''
            SELECT COALESCE(MAX(order_index), 0) + 1 
            FROM questions 
            WHERE questionnaire_id = ?
        ''', (questionnaire_id,))
        order_index = cursor.fetchone()[0]
        
        options_json = json.dumps(options) if options else None
        
        cursor.execute('''
            INSERT INTO questions 
            (questionnaire_id, question_text, question_type, options, is_required, order_index)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (questionnaire_id, question_text, question_type.value, options_json, is_required, order_index))
        
        question_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return question_id
    
    def get_questions(self, questionnaire_id: int) -> List[Question]:
        """Get all questions for questionnaire"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM questions 
            WHERE questionnaire_id = ? 
            ORDER BY order_index
        ''', (questionnaire_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        questions = []
        for row in rows:
            options = json.loads(row['options']) if row['options'] else None
            questions.append(Question(
                id=row['id'],
                questionnaire_id=row['questionnaire_id'],
                question_text=row['question_text'],
                question_type=QuestionType(row['question_type']),
                options=options,
                is_required=row['is_required'],
                order_index=row['order_index']
            ))
        
        return questions
    
    # Response operations
    def start_questionnaire_response(self, questionnaire_id: int, user_id: int):
        """Start questionnaire response"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO questionnaire_responses 
            (questionnaire_id, user_id, started_at, is_completed)
            VALUES (?, ?, CURRENT_TIMESTAMP, FALSE)
        ''', (questionnaire_id, user_id))
        
        conn.commit()
        conn.close()
    
    def save_response(self, questionnaire_id: int, user_id: int, question_id: int,
                     answer_text: str = None, selected_option: int = None, 
                     selected_options: List[int] = None):
        """Save response to question"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        selected_options_json = json.dumps(selected_options) if selected_options else None
        
        cursor.execute('''
            INSERT OR REPLACE INTO responses 
            (questionnaire_id, user_id, question_id, answer_text, selected_option, selected_options)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (questionnaire_id, user_id, question_id, answer_text, selected_option, selected_options_json))
        
        conn.commit()
        conn.close()
    
    def complete_questionnaire_response(self, questionnaire_id: int, user_id: int):
        """Mark questionnaire response as completed"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE questionnaire_responses 
            SET completed_at = CURRENT_TIMESTAMP, is_completed = TRUE
            WHERE questionnaire_id = ? AND user_id = ?
        ''', (questionnaire_id, user_id))
        
        conn.commit()
        conn.close()
    
    def get_questionnaire_stats(self, questionnaire_id: int) -> dict:
        """Get questionnaire statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get total responses
        cursor.execute('''
            SELECT COUNT(*) as total_started,
                   COUNT(CASE WHEN is_completed = 1 THEN 1 END) as total_completed
            FROM questionnaire_responses 
            WHERE questionnaire_id = ?
        ''', (questionnaire_id,))
        
        stats = cursor.fetchone()
        conn.close()
        
        return {
            'total_started': stats['total_started'],
            'total_completed': stats['total_completed']
        }
    
    def get_questionnaire_responses(self, questionnaire_id: int) -> List[dict]:
        """Get all responses for questionnaire"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT qr.user_id, u.username, u.first_name, u.last_name,
                   qr.started_at, qr.completed_at, qr.is_completed,
                   q.id as question_id, q.question_text, q.question_type, q.options,
                   r.answer_text, r.selected_option
            FROM questionnaire_responses qr
            JOIN users u ON qr.user_id = u.user_id
            LEFT JOIN questions q ON q.questionnaire_id = qr.questionnaire_id
            LEFT JOIN responses r ON r.questionnaire_id = qr.questionnaire_id 
                                  AND r.user_id = qr.user_id 
                                  AND r.question_id = q.id
            WHERE qr.questionnaire_id = ?
            ORDER BY qr.user_id, q.order_index
        ''', (questionnaire_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Group responses by user
        user_responses = {}
        for row in rows:
            user_id = row['user_id']
            if user_id not in user_responses:
                user_responses[user_id] = {
                    'user_info': {
                        'user_id': user_id,
                        'username': row['username'],
                        'first_name': row['first_name'],
                        'last_name': row['last_name']
                    },
                    'started_at': row['started_at'],
                    'completed_at': row['completed_at'],
                    'is_completed': row['is_completed'],
                    'responses': []
                }
            
            if row['question_id']:  # Only add if question exists
                response_data = {
                    'question_id': row['question_id'],
                    'question_text': row['question_text'],
                    'question_type': row['question_type'],
                    'answer_text': row['answer_text'],
                    'selected_option': row['selected_option']
                }
                
                if row['options']:
                    options = json.loads(row['options'])
                    response_data['options'] = options
                    if row['selected_option'] is not None:
                        response_data['selected_option_text'] = options[row['selected_option']]
                
                user_responses[user_id]['responses'].append(response_data)
        
        return list(user_responses.values()) 