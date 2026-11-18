from flask import Blueprint, render_template, request, redirect, url_for, flash
import models

feedback_bp = Blueprint('feedback_bp', __name__)

@feedback_bp.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()

        if not name or not email or not message:
            flash('Будь ласка, заповніть усі поля форми.', 'error')
        else:
            models.add_feedback(name, email, message)
            flash('Дякуємо! Ваш відгук успішно збережено у базі даних.', 'success')
            return redirect(url_for('feedback_bp.feedback'))

    # Отримуємо всі відгуки з БД для відображення на сторінці
    feedbacks = models.get_all_feedbacks()
    return render_template('feedback.html', feedbacks=feedbacks)
