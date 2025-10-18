import os
from datetime import datetime, timedelta

class Config:
    # Website settings
    BASE_URL = "https://thuvienphapluat.vn/chinh-sach-phap-luat-moi/search/?q=giao%20th%C3%B4ng"
    SEARCH_URL = "https://thuvienphapluat.vn/chinh-sach-phap-luat-moi/search/?q=giao%20th%C3%B4ng"
    
    # Crawling settings
    DELAY_BETWEEN_REQUESTS = 2  # seconds   
    MAX_RETRIES = 3
    TIMEOUT = 30
    
    # Data settings
    DATA_DIR = "data"
    RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
    PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
    REPORTS_DIR = "reports"
    
    # Search parameters
    DAYS_BACK = 30  # Lấy văn bản trong 30 ngày gần đây
    MAX_DOCUMENTS = 200 # Tăng lên để hỗ trợ crawl nhiều trang
    DEFAULT_PAGES = 10   # Số trang mặc định
    DEFAULT_DOCS_PER_PAGE = 20  # Số văn bản mặc định mỗi trang
    
    # Crawl all pages settings
    MAX_PAGES_PER_KEYWORD = 200  # Giới hạn an toàn cho mỗi từ khóa
    MAX_EMPTY_PAGES = 3  # Dừng sau 3 trang trống liên tiếp
    TRAFFIC_KEYWORDS = [
        "giao thông",
        "an toàn giao thông", 
        "luật giao thông",
        "nghị định giao thông",
        "phương tiện giao thông",
        "đường bộ"
    ]
    
    # Headers for requests
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    @staticmethod
    def ensure_directories():
        """Tạo các thư mục cần thiết"""
        dirs = [Config.DATA_DIR, Config.RAW_DATA_DIR, 
                Config.PROCESSED_DATA_DIR, Config.REPORTS_DIR]
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
