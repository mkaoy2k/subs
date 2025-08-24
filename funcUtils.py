"""
Function Utilities Module

This module provides various utility functions including:
- Menu loading functionality
- Multi-language localization (L10N) support
- Avatar image processing

Key Features:
- load_menu: Loads menu configurations from JSON files
- load_L10N: Manages multi-language support with JSON-based translations
- create_avatar: Processes and enhances profile pictures with resizing and quality improvements

Dependencies:
- Pillow (PIL): For image processing
- Standard libraries: json, os
"""

import json
from PIL import Image, ImageEnhance
import os
from typing import Dict, List, Any
import traceback
from dotenv import load_dotenv

def get_function_name():
    """取得目前函數名稱"""
    return traceback.extract_stack(None, 2)[0][2]

def load_menu(fn):
    """
    Load menu configuration from a JSON file.
    
    This function reads a JSON file containing menu configurations and returns
    the parsed data as a Python dictionary. The JSON file should contain menu
    items and their corresponding display text for different languages.
    
    Args:
        fn (str): Path to the menu configuration JSON file.
        
    Returns:
        dict: Parsed JSON data containing menu configurations.
        
    Example:
        >>> menu_data = load_menu("menu_config.json")
        >>> print(menu_data['main_menu'])
        [['url1', 'Menu Item 1'], ['url2', 'Menu Item 2']]
        
    Raises:
        FileNotFoundError: If the specified file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    # reading the data from the language-definition file
    with open(fn) as f:
        data = f.read()
        
    # reconstructing languages as a dictionary
    js = json.loads(data)
    
    return js

def load_L10N():
    """
    Load all supported language localization (L10N) dictionaries.
    
    This function loads translation dictionaries for all supported languages from the specified
    configuration file. The configuration file should map language codes to their respective
    translation file paths.
    
    Args:
        f_l10n (str): Path to the L10N configuration file. This file should be a JSON
                    where keys are language codes and values are paths to translation files.
        
    Returns:
        dict: A dictionary where keys are language codes and values are the corresponding
             translation dictionaries.
        
    Example:
        >>> l10n_dicts = load_L10N()
        >>> print(l10n_dicts['US']['welcome_message'])
        'Welcome to our application!'
        
    Note:
        - The configuration file should be in JSON format
        - Each translation file should contain key-value pairs for the translations
        - Language codes should follow standard ISO 639-1 or similar conventions
        
    Raises:
        FileNotFoundError: If the configuration file or any translation file is not found.
        json.JSONDecodeError: If any of the JSON files contain invalid syntax.
    """
    load_dotenv(".env")
    f_l10n = os.getenv("L10N_FILE", "L10N.json")

    # reading the data from the language-definition file
    with open(f_l10n) as f:
        data = f.read()
        
    # reconstructing languages as a dictionary
    js = json.loads(data)
    
    dl10n = {}
    # iterate all supported languages
    for key, fl in js.items():
        # load each language-specific L10N settings
        with open(fl) as f:
            data = f.read()
      
        # reconstructing the data as a dictionary
        d = json.loads(data)
        dl10n[key] = d
  
    return dl10n

def create_avatar(input_path, output_path, size=400, brightness=1.1, contrast=1.1):
    """
    Convert an image to a square avatar with optional image enhancements.
    
    This function processes an input image to create a square avatar with the specified
    dimensions. It performs the following operations:
    1. Converts the image to RGB mode if necessary
    2. Crops the image to a square aspect ratio (centered)
    3. Resizes the image to the specified dimensions
    4. Applies brightness and contrast adjustments
    5. Saves the result as a JPEG file
    
    Args:
        input_path (str): Path to the source image file.
        output_path (str): Path where the processed avatar will be saved.
        size (int, optional): Width and height of the output square image in pixels.
                           Defaults to 400.
        brightness (float, optional): Brightness adjustment factor.
                                   >1.0 increases brightness,
                                   <1.0 decreases brightness.
                                   Defaults to 1.1.
        contrast (float, optional): Contrast adjustment factor.
                                 >1.0 increases contrast,
                                 <1.0 decreases contrast.
                                 Defaults to 1.1.
        
    Returns:
        bool: True if the operation was successful, False otherwise.
        
    Example:
        >>> # Basic usage with default parameters
        >>> success = create_avatar("input.jpg", "avatar.jpg")
        >>> 
        >>> # Custom size and enhancement parameters
        >>> success = create_avatar("input.jpg", "avatar_small.jpg", 
        ...                       size=200, brightness=1.2, contrast=1.3)
        
    Note:
        - Supported input formats include JPEG, PNG, and other formats supported by Pillow.
        - Output is always saved as JPEG with 90% quality.
        - If the output directory doesn't exist, it will be created.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        PIL.UnidentifiedImageError: If the input file is not a valid image.
        OSError: If there are permission issues when writing the output file.
    """
    try:
        # Open image
        with Image.open(input_path) as img:
            # Convert to RGB mode (handles RGBA or P mode)
            if img.mode != 'RGB':
                img = img.convert('RGB')
                
            # Crop to square
            width, height = img.size
            min_dimension = min(width, height)
            left = (width - min_dimension) // 2
            top = (height - min_dimension) // 2
            right = left + min_dimension
            bottom = top + min_dimension
            img = img.crop((left, top, right, bottom))
            
            # Resize
            img = img.resize((size, size), Image.LANCZOS)
            
            # Enhance brightness and contrast
            if brightness != 1.0:
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(brightness)
                
            if contrast != 1.0:
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(contrast)
            
            # Rotate 0 degrees clockwise
            img = img.rotate(0, expand=True)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            # Save image
            img.save(output_path, "JPEG", quality=90)
            return True
            
    except Exception as e:
        print(f"Error creating avatar: {str(e)}")
        return False

def load_page_cat(json_file: str) -> Dict[str, List[str]]:
    """
    Load page category data from a JSON file.
    
    This function reads a JSON file containing page category configurations and returns
    the parsed data as a dictionary. The JSON file should contain page names as keys
    and their corresponding categories as lists of strings.
    
    Args:
        json_file (str): Path to the JSON file containing page categories.
        
    Returns:
        Dict[str, List[str]]: A dictionary where keys are page names and values are 
                            lists of category strings.
        
    Example:
        >>> page_categories = load_page_cat("page_category.json")
        >>> print(page_categories['home'])
        ['News', 'Story', 'Events']
        
    Raises:
        FileNotFoundError: If the specified file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError as e:
        print(f"Error: File not found: {json_file}")
        raise
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in file: {json_file}")
        raise

# Functional testing
if __name__ == '__main__':
    # Test page category loading
    try:
        page_categories = load_page_cat("page_category.json")
        print("Page category loaded successfully:")
        for page, categories in page_categories.items():
            print(f"{page}: {', '.join(categories)}")
    except Exception as e:
        print(f"Test failed: {str(e)}")
    
    # Test multi-language localization (L10N) loading
    # menu = load_menu("ops_menu.json")
    # l_menu = menu['繁中']
    # print(f"l_menu[0] URL={l_menu[0][0]}\n")
    # print(f"l_menu[0] Text={l_menu[0][1]}\n")
    # print(f"l_menu[1] URL={l_menu[1][0]}\n")
    # print(f"l_menu[1] Text={l_menu[1][1]}\n")
    # print(f"l_menu[2] URL={l_menu[2][0]}\n")
    # print(f"l_menu[2] Text={l_menu[2][1]}\n")
    # g_L10N = load_L10N()
    # print(f"g_L10N={g_L10N}\n")
    # g_L10N_options = list(g_L10N.keys())
    # print(f"g_L10N_options={g_L10N_options}")
    
    # Test avatar creation
    # test_input = "test.jpg"  # Replace with your test image path
    # test_output = "test_avatar.jpg"
    # if os.path.exists(test_input):
    #     success = create_avatar(test_input, test_output)
    #     if success:
    #         print(f"Avatar successfully created: {test_output}")
    #     else:
    #         print("Failed to create avatar")
    # else:
    #     print(f"Test image {test_input} does not exist")