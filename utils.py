import pandas as pd
from typing import List, Dict
from datetime import datetime
import os
import qrcode
from io import BytesIO

def export_to_excel(questionnaire_title: str, responses_data: List[dict], 
                   questions_data: List[dict]) -> str:
    """Export questionnaire responses to Excel file"""
    
    # Create filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"questionnaire_{questionnaire_title.replace(' ', '_')}_{timestamp}.xlsx"
    
    # Create directory if it doesn't exist
    if not os.path.exists('exports'):
        os.makedirs('exports')
    
    filepath = f"exports/{filename}"
    
    # Prepare data for Excel
    excel_data = []
    
    for response in responses_data:
        if not response['is_completed']:
            continue  # Skip incomplete responses
            
        user_info = response['user_info']
        row_data = {
            'User ID': user_info['user_id'],
            'Username': user_info['username'] or 'N/A',
            'First Name': user_info['first_name'] or 'N/A',
            'Last Name': user_info['last_name'] or 'N/A',
            'Started At': response['started_at'],
            'Completed At': response['completed_at']
        }
        
        # Add each question's response
        for resp in response['responses']:
            question_text = resp['question_text']
            if resp['question_type'] == 'multiple_choice':
                answer = resp.get('selected_option_text', 'No answer')
            else:
                answer = resp.get('answer_text', 'No answer')
            
            row_data[f"Q: {question_text}"] = answer
        
        excel_data.append(row_data)
    
    # Create DataFrame and save to Excel
    if excel_data:
        df = pd.DataFrame(excel_data)
        df.to_excel(filepath, index=False)
    else:
        # Create empty file with headers if no data
        df = pd.DataFrame(columns=['User ID', 'Username', 'First Name', 'Last Name', 
                                  'Started At', 'Completed At'])
        df.to_excel(filepath, index=False)
    
    return filepath

def format_questionnaire_info(questionnaire, questions_count: int, stats: dict) -> str:
    """Format questionnaire information for display"""
    status_icon = {
        'draft': '📝',
        'active': '✅',
        'closed': '🔒'
    }
    
    return f"""
{status_icon.get(questionnaire.status.value, '❓')} **{questionnaire.title}**

📋 Description: {questionnaire.description or 'No description'}
❓ Questions: {questions_count}
👥 Started: {stats['total_started']}
✅ Completed: {stats['total_completed']}
📅 Created: {questionnaire.created_at.strftime('%Y-%m-%d %H:%M')}
🔄 Status: {questionnaire.status.value.title()}
"""

def format_question_for_display(question, question_number: int) -> str:
    """Format question for display during questionnaire taking"""
    question_text = f"**Question {question_number}:**\n{question.question_text}"
    
    if question.question_type.value == 'multiple_choice' and question.options:
        question_text += "\n\nOptions:"
        for i, option in enumerate(question.options):
            question_text += f"\n{i + 1}. {option}"
        question_text += "\n\nPlease reply with the number of your choice (1-{})".format(len(question.options))
    else:
        question_text += "\n\nPlease type your answer:"
    
    if question.is_required:
        question_text += "\n\n*This question is required."
    
    return question_text

def validate_multiple_choice_answer(answer: str, options_count: int) -> tuple:
    """Validate multiple choice answer and return (is_valid, selected_index)"""
    try:
        selected = int(answer.strip())
        if 1 <= selected <= options_count:
            return True, selected - 1  # Convert to 0-based index
        else:
            return False, None
    except ValueError:
        return False, None

def get_user_display_name(user_info: dict) -> str:
    """Get display name for user"""
    if user_info.get('username'):
        return f"@{user_info['username']}"
    elif user_info.get('first_name') or user_info.get('last_name'):
        name_parts = []
        if user_info.get('first_name'):
            name_parts.append(user_info['first_name'])
        if user_info.get('last_name'):
            name_parts.append(user_info['last_name'])
        return ' '.join(name_parts)
    else:
        return f"User {user_info['user_id']}"

def format_response_summary(responses_data: List[dict], questionnaire_title: str) -> str:
    """Format response summary for admin"""
    if not responses_data:
        return f"📊 **Response Summary for '{questionnaire_title}'**\n\nNo responses yet."
    
    completed_responses = [r for r in responses_data if r['is_completed']]
    
    summary = f"📊 **Response Summary for '{questionnaire_title}'**\n\n"
    summary += f"📈 Total Responses: {len(responses_data)}\n"
    summary += f"✅ Completed: {len(completed_responses)}\n"
    summary += f"⏳ In Progress: {len(responses_data) - len(completed_responses)}\n\n"
    
    if completed_responses:
        summary += "**Recent Completed Responses:**\n"
        for i, response in enumerate(completed_responses[-5:]):  # Show last 5
            user_name = get_user_display_name(response['user_info'])
            completed_at = response['completed_at']
            summary += f"{i+1}. {user_name} - {completed_at}\n"
        
        if len(completed_responses) > 5:
            summary += f"... and {len(completed_responses) - 5} more\n"
    
    return summary

def generate_questionnaire_link(bot_username: str, questionnaire_id: int) -> str:
    """Generate deep link for questionnaire"""
    return f"https://t.me/{bot_username}?start=survey_{questionnaire_id}"

def generate_qr_code(data: str) -> BytesIO:
    """Generate QR code for given data"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    bio = BytesIO()
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio 