import json
from PIL import Image, ImageEnhance
import os

"""
功能工具模組 (Function Utilities Module)

此模組提供多種輔助功能，包括：
- 選單載入功能
- 多國語言本地化(L10N)支援
- 頭像圖片處理

"""

def load_menu(fn):
    """
    從 JSON 檔案載入選單設定
    
    參數:
        fn (str): 選單設定檔的路徑
        
    返回:
        dict: 解析後的 JSON 資料，包含選單設定
        
    範例:
        menu_data = load_menu("menu_config.json")
        print(menu_data['main_menu'])
    """
    # reading the data from the language-definition file
    with open(fn) as f:
        data = f.read()
        
    # reconstructing languages as a dictionary
    js = json.loads(data)
    
    return js

def load_L10N(f_l10n):
    """
    載入多國語言本地化(L10N)字典
    
    從指定的 JSON 設定檔載入所有支援語言的本地化字典。
    
    參數:
        f_l10n (str): 語言設定檔的路徑，該檔案應包含各語言對應的翻譯檔案路徑
        
    返回:
        dict: 以語言名稱為鍵，對應的本地化字典為值的字典
        
    範例:
        l10n_dicts = load_L10N("L10N.json")
        print(l10n_dicts['US']['welcome_message'])
        
    注意:
        - 設定檔應為 JSON 格式，鍵為語言代碼，值為對應的翻譯檔案路徑
        - 每個翻譯檔案也應為 JSON 格式，包含該語言的翻譯鍵值對
    """
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

def create_avatar(input_path, output_path, size=400, brightness=1.1, contrast=1.1):
    """
    將 JPEG 圖片轉換為指定大小的頭像，並進行基本的圖像增強
    
    參數:
        input_path (str): 輸入圖片的路徑
        output_path (str): 輸出頭像的保存路徑
        size (int): 輸出頭像的尺寸（正方形，預設 400x400 像素）
        brightness (float): 亮度增強因子（>1 變亮，<1 變暗，預設 1.1）
        contrast (float): 對比度增強因子（>1 增加對比度，<1 減少對比度，預設 1.1）
        
    返回:
        bool: 轉換成功返回 True，失敗返回 False
        
    範例:
        # 基本使用
        success = create_avatar("input.jpg", "avatar.jpg")
        
        # 自訂尺寸和增強參數
        success = create_avatar("input.jpg", "avatar.jpg", size=300, brightness=1.2, contrast=1.2)
    """
    try:
        # 開啟圖片
        with Image.open(input_path) as img:
            # 轉換為 RGB 模式（處理 RGBA 或 P 模式）
            if img.mode != 'RGB':
                img = img.convert('RGB')
                
            # 裁剪為正方形
            width, height = img.size
            min_dimension = min(width, height)
            left = (width - min_dimension) // 2
            top = (height - min_dimension) // 2
            right = left + min_dimension
            bottom = top + min_dimension
            img = img.crop((left, top, right, bottom))
            
            # 調整大小
            img = img.resize((size, size), Image.LANCZOS)
            
            # 增強亮度和對比度
            if brightness != 1.0:
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(brightness)
                
            if contrast != 1.0:
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(contrast)
            
            # 順時針旋轉 0 度
            img = img.rotate(0, expand=True)
            
            # 確保輸出目錄存在
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            # 儲存圖片
            img.save(output_path, "JPEG", quality=90)
            return True
            
    except Exception as e:
        print(f"建立頭像時發生錯誤: {str(e)}")
        return False

# Functional testing
if __name__ == '__main__':
    # 測試多國語言本地化(L10N)載入
    menu = load_menu("ops_menu.json")
    l_menu = menu['繁中']
    print(f"l_menu[0] URL={l_menu[0][0]}\n")
    print(f"l_menu[0] Text={l_menu[0][1]}\n")
    print(f"l_menu[1] URL={l_menu[1][0]}\n")
    print(f"l_menu[1] Text={l_menu[1][1]}\n")
    print(f"l_menu[2] URL={l_menu[2][0]}\n")
    print(f"l_menu[2] Text={l_menu[2][1]}\n")
    # g_L10N = load_L10N("L10N.json")
    # print(f"g_L10N={g_L10N}\n")
    # g_L10N_options = list(g_L10N.keys())
    # print(f"g_L10N_options={g_L10N_options}")
    
    # 測試頭像建立
    # test_input = "test.jpg"  # 替換為您的測試圖片路徑
    # test_output = "test_avatar.jpg"
    # if os.path.exists(test_input):
    #     success = create_avatar(test_input, test_output)
    #     if success:
    #         print(f"頭像已成功建立: {test_output}")
    #     else:
    #         print("建立頭像失敗")
    # else:
    #     print(f"測試圖片 {test_input} 不存在")