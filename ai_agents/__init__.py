from abc import ABC, abstractmethod
import json
import time
from datetime import datetime

class BaseAgent(ABC):
    def __init__(self, name):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.metrics = {}
        self.results = {}
        
    @abstractmethod
    def process(self, input_data):
        """Xử lý chính của agent"""
        pass
    
    @abstractmethod
    def validate_results(self):
        """Kiểm tra kết quả"""
        pass
    
    def start_timer(self):
        self.start_time = time.time()
    
    def end_timer(self):
        self.end_time = time.time()
        
    def get_processing_time(self):
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0
    
    def save_results(self, filepath):
        """Lưu kết quả ra file"""
        output = {
            'agent_name': self.name,
            'timestamp': datetime.now().isoformat(),
            'processing_time': self.get_processing_time(),
            'metrics': self.metrics,
            'results': self.results
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
    
    def log(self, message):
        print(f"[{self.name}] {datetime.now().strftime('%H:%M:%S')} - {message}")

