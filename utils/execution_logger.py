import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict, Any


class ExecutionLogger:
    """Nhật ký thực thi - Ghi lại toàn bộ các bước xử lý của AI Agent để truy vết."""
    
    def __init__(self):
        self.logs: List[Dict[str, Any]] = []
        self.step_counter = 0
    
    def log_step(self, step_type: str, description: str, 
                 input_summary: str = "", output_summary: str = "",
                 source_ref: str = "", metadata: Optional[Dict] = None):
        """
        Ghi lại một bước xử lý của Agent.
        
        Args:
            step_type: Loại bước (DATA_READ, COLUMN_MAPPING, AGGREGATION, ANALYSIS, 
                       SCORING, COMPARISON, GAP_DETECTION, RECOMMENDATION, 
                       ERROR_HANDLING, HUMAN_CHECKPOINT)
            description: Mô tả ngắn gọn bước xử lý
            input_summary: Tóm tắt dữ liệu đầu vào
            output_summary: Tóm tắt kết quả đầu ra
            source_ref: Tham chiếu nguồn dữ liệu (tên file, URL, v.v.)
            metadata: Thông tin bổ sung dạng dict
        
        Returns:
            Dict chứa thông tin bước đã ghi
        """
        self.step_counter += 1
        entry = {
            "step_id": self.step_counter,
            "timestamp": datetime.now().isoformat(),
            "step_type": step_type,
            "description": description,
            "input_summary": input_summary,
            "output_summary": output_summary,
            "source_ref": source_ref,
            "metadata": metadata or {}
        }
        self.logs.append(entry)
        return entry
    
    def get_logs(self) -> List[Dict[str, Any]]:
        """Trả về bản sao danh sách tất cả các bước đã ghi."""
        return self.logs.copy()
    
    def export_dataframe(self) -> pd.DataFrame:
        """Xuất nhật ký thành DataFrame để hiển thị trên Streamlit."""
        if not self.logs:
            return pd.DataFrame(columns=["step_id", "timestamp", "step_type", "description", 
                                         "input_summary", "output_summary", "source_ref"])
        df = pd.DataFrame(self.logs)
        display_cols = ["step_id", "timestamp", "step_type", "description", 
                       "input_summary", "output_summary", "source_ref"]
        return df[[c for c in display_cols if c in df.columns]]
    
    def get_steps_by_type(self, step_type: str) -> List[Dict]:
        """Lọc các bước theo loại step_type."""
        return [log for log in self.logs if log["step_type"] == step_type]
    
    def get_errors(self) -> List[Dict]:
        """Trả về tất cả các bước lỗi đã ghi nhận."""
        return self.get_steps_by_type("ERROR_HANDLING")
    
    def get_human_checkpoints(self) -> List[Dict]:
        """Trả về tất cả các điểm cần con người xác nhận."""
        return self.get_steps_by_type("HUMAN_CHECKPOINT")
    
    def clear(self):
        """Xóa toàn bộ nhật ký và reset bộ đếm."""
        self.logs = []
        self.step_counter = 0
    
    def summary(self) -> Dict[str, Any]:
        """Tạo tóm tắt tổng quan về các bước đã thực thi."""
        return {
            "total_steps": len(self.logs),
            "step_types": {st: len(self.get_steps_by_type(st)) 
                          for st in set(log["step_type"] for log in self.logs)} if self.logs else {},
            "errors_count": len(self.get_errors()),
            "human_checkpoints": len(self.get_human_checkpoints())
        }
