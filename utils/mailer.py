from flask_mail import Message
from flask import current_app

def send_status_email(mail, to_email, student_name, job_title, company_name, new_status, reset_code=None):
    templates = {
        'SHORTLISTED': {
            'subject': f"You've been shortlisted — {job_title}",
            'body': f"Hi {student_name},\n\nGreat news! You have been shortlisted for the {job_title} position at {company_name}.\n\nThe employer will be in touch shortly regarding next steps.\n\nBest of luck,\nInternBridge Team"
        },
        'INTERVIEW': {
            'subject': f"Interview invitation — {job_title}",
            'body': f"Hi {student_name},\n\nCongratulations! {company_name} has invited you for an interview for the {job_title} role.\n\nPlease log in to your InternBridge dashboard for more details.\n\nBest of luck,\nInternBridge Team"
        },
        'OFFERED': {
            'subject': f"Job offer extended — {job_title}",
            'body': f"Hi {student_name},\n\nExciting news! {company_name} has extended a job offer for the {job_title} position.\n\nPlease log in to your dashboard to review and respond.\n\nCongratulations,\nInternBridge Team"
        },
        'REJECTED': {
            'subject': f"Application update — {job_title}",
            'body': f"Hi {student_name},\n\nThank you for applying to {job_title} at {company_name}.\n\nAfter careful consideration, the employer has decided to move forward with other candidates.\nDon't be discouraged — keep applying on InternBridge!\n\nInternBridge Team"
        },
        # --- FIXED FORGOT PASSWORD TEMPLATE (CODE VERSION) ---
        'RESET_REQUESTED': {
            'subject': "Your Password Reset Code — InternBridge",
            'body': f"Hi {student_name},\n\nYou requested a password reset for your InternBridge account.\n\nYour 6-digit verification code is: {reset_code}\n\nPlease enter this code in the app to reset your password. If you did not request this, please ignore this email.\n\nThank you,\nInternBridge Team"
        }
    }

    if new_status not in templates:
        return

    template = templates[new_status]
    
    if not mail:
        print("Error: Mail instance is None. Check if Flask-Mail is initialized.")
        return

    try:
        msg = Message(
            subject=template['subject'],
            recipients=[to_email],
            body=template['body']
        )
        mail.send(msg)
        print(f"Email sent to {to_email} with code {reset_code}")
    except Exception as e:
        print(f"Email failed: {e}")