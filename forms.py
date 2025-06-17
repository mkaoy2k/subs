from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Optional, URL, Length

class ArticleForm(FlaskForm):
    """Form for submitting new articles"""
    title = StringField('Title', validators=[
        DataRequired(message='Title is required'),
        Length(min=5, max=200, message='Title must be between 5 and 200 characters')
    ])
    
    content = TextAreaField('Content', validators=[
        DataRequired(message='Content is required'),
        Length(min=20, message='Content must be at least 20 characters')
    ])
    
    category = SelectField('Category', choices=[
        ('News', 'News'),
        ('Story', 'Story'),
        ('Events', 'Events'),
        ('FAQ', 'FAQ'),
        ('About', 'About')
    ], validators=[DataRequired()])
    
    l10n = SelectField('Language', choices=[
        ('US', 'English'),
        ('繁中', '繁體中文')  
    ], validators=[DataRequired()])

    author = StringField('Your Name', validators=[
        DataRequired(message='Please provide your name')
    ])
    
    source = StringField('Source', validators=[
        DataRequired(message='Please provide the source')
    ])
    
    source_url = StringField('Source URL', validators=[
        Optional(),
        URL(message='Please enter a valid URL (e.g., https://example.com)')
    ])
    
    image_url = StringField('Image URL', validators=[
        Optional(),
        URL(message='Please enter a valid image URL')
    ])
    
    email = StringField('Your Email', validators=[
        DataRequired(message='Email is required and must be a subscriber'),
        Email(message='Please enter a valid email address')
    ])
    
    submit = SubmitField('Submit Article')

    def validate_source_url(self, field):
        """Validate source_url if provided"""
        if field.data and not field.data.startswith(('http://', 'https://')):
            field.data = 'http://' + field.data

    def validate_image_url(self, field):
        """Validate image_url if provided"""
        if field.data and not field.data.startswith(('http://', 'https://')):
            field.data = 'http://' + field.data
