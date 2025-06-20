from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Optional, URL, Length

class ArticleForm(FlaskForm):
    """Form for submitting new articles"""
    def __init__(self, *args, **kwargs):
        # Get language from kwargs before calling parent's __init__
        lang = kwargs.pop('lang', 'US')
        super().__init__(*args, **kwargs)
        
        # Set default submit text
        submit_text = 'Submit'
        
        try:
            from ops_svr import g_L10N
            # Get the localization dictionary
            current_loc = g_L10N.get(lang, g_L10N.get('US', {}))
            # Get the submit text, fallback to default if not found
            submit_text = current_loc.get('FEEDBACK_SUBMIT', 'Submit')
        except Exception as e:
            # If anything fails, keep the default 'Submit' text
            import logging
            logging.error(f"Error setting form localization: {str(e)}")
        
        # Store the current localization dictionary
        self.current_loc = {
            'title': current_loc.get('FEEDBACK_TITLE', 'Title'),
            'content': current_loc.get('FEEDBACK_CONTENT', 'Content'),
            'author': current_loc.get('FEEDBACK_AUTHOR', 'Author'),
            'source': current_loc.get('FEEDBACK_SOURCE', 'Source'),
            'category': current_loc.get('FEEDBACK_CATEGORY', 'Category'),
            'language': current_loc.get('FEEDBACK_LANGUAGE', 'Language'),
            'source_url': current_loc.get('FEEDBACK_SOURCE_URL', 'Source URL'),
            'image_url': current_loc.get('FEEDBACK_IMAGE_URL', 'Image URL'),
            'email': current_loc.get('FEEDBACK_EMAIL', 'Email'),
            'submit': submit_text
        }
        
        # Update field labels with localized text
        self.title.label.text = self.current_loc['title']
        self.content.label.text = self.current_loc['content']
        self.category.label.text = self.current_loc['category']
        self.l10n.label.text = self.current_loc['language']
        self.author.label.text = self.current_loc['author']
        self.source.label.text = self.current_loc['source']
        self.source_url.label.text = self.current_loc['source_url']
        self.image_url.label.text = self.current_loc['image_url']
        self.email.label.text = self.current_loc['email']
        self.submit.label.text = self.current_loc['submit']
        
    # Form fields defined at class level
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

    author = StringField('Author', validators=[
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
    
    email = StringField('Email', validators=[
        DataRequired(message='Email is required and must be a subscriber'),
        Email(message='Please enter a valid email address')
    ])
    
    submit = SubmitField('Submit')  # Default value, will be updated in __init__

    def validate_source_url(self, field):
        """Validate source_url if provided"""
        if field.data and not field.data.startswith(('http://', 'https://')):
            field.data = 'http://' + field.data

    def validate_image_url(self, field):
        """Validate image_url if provided"""
        if field.data and not field.data.startswith(('http://', 'https://')):
            field.data = 'http://' + field.data
