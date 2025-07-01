from enum import Enum
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

class QuestionType(Enum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT = "text"

class QuestionnaireStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"

@dataclass
class User:
    user_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    is_admin: bool
    created_at: datetime

@dataclass
class Questionnaire:
    id: Optional[int]
    title: str
    description: str
    created_by: int
    status: QuestionnaireStatus
    created_at: datetime
    updated_at: datetime

@dataclass
class Question:
    id: Optional[int]
    questionnaire_id: int
    question_text: str
    question_type: QuestionType
    options: Optional[List[str]]  # For multiple choice questions
    is_required: bool
    order_index: int

@dataclass
class Response:
    id: Optional[int]
    questionnaire_id: int
    user_id: int
    question_id: int
    answer_text: Optional[str]
    selected_option: Optional[int]  # Index of selected option for multiple choice
    created_at: datetime

@dataclass
class QuestionnaireResponse:
    questionnaire_id: int
    user_id: int
    started_at: datetime
    completed_at: Optional[datetime]
    is_completed: bool 