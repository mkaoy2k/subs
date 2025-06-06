
import json

def load_menu(fn):

    # reading the data from the language-definition file
    with open(fn) as f:
        data = f.read()
        
    # reconstructing languages as a dictionary
    js = json.loads(data)
    
    return js

# --- Load supported L10N dictionaries ---
def load_L10N(f_l10n):
    # Build and return a dictionary for all supported languages, 
    # with key of language name and associated L10N dictionaries.
    # Load the environment variables from file
    
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

# Functional testing
if __name__ == '__main__':
    g_L10N = load_L10N("L10N.json")
    print(f"g_L10N={g_L10N}\n")
    g_L10N_options = list(g_L10N.keys())
    print(f"g_L10N_options={g_L10N_options}")