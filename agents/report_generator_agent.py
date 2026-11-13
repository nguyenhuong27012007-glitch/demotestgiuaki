"""
Kỹ năng 3: Agent Tạo Báo cáo & Kế hoạch Khảo sát
- Tạo báo cáo đề xuất cho Trưởng phòng PTKD
- Tạo bảng so sánh có căn cứ
- Lập kế hoạch khảo sát tiếp theo
- Xác định điểm cần con người xử lý
"""

import json
from typing import Dict, Optional, Any
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.execution_logger import ExecutionLogger
from config import SYSTEM_PROMPT, REPORT_PROMPT_TEMPLATE, COMPANY_NAME


class ReportGeneratorAgent:
    """
    Agent Tạo Báo cáo Đề xuất & Kế hoạch Khảo sát.
    
    Chức năng:
    - Tổng hợp kết quả phân tích thành báo cáo
    - Tạo bảng so sánh có căn cứ tài liệu nguồn
    - Đề xuất 2 địa bàn ưu tiên + giải thích
    - Lập kế hoạch khảo sát: nhóm khách, thông tin xác minh, người phụ trách
    - Xác định điểm Human Checkpoint
    """
    
    def __init__(self, logger: ExecutionLogger, model=None):
        self.logger = logger
        self.model = model
        self.report = None
        self.survey_plan = None
    
    def set_model(self, model):
        """Set the Gemini model instance."""
        self.model = model
    
    def generate_full_report(self, analysis_result: str, 
                              scoring_result: Any = None,
                              gaps_result: Any = None) -> tuple:
        """
        Tạo báo cáo đề xuất đầy đủ.
        
        Args:
            analysis_result: Kết quả phân tích từ MarketAnalysisAgent
            scoring_result: Kết quả chấm điểm (dict hoặc text)
            gaps_result: Kết quả phát hiện gaps/conflicts (dict hoặc text)
        
        Returns:
            (success: bool, report: str)
        """
        if not self.model:
            return False, "⚠️ Model chưa được khởi tạo."
        
        # Combine all analysis results
        combined = f"=== KẾT QUẢ PHÂN TÍCH THỊ TRƯỜNG ===\n{analysis_result}\n\n"
        
        if scoring_result:
            if isinstance(scoring_result, dict):
                combined += f"=== KẾT QUẢ CHẤM ĐIỂM ===\n{json.dumps(scoring_result, ensure_ascii=False, indent=2)}\n\n"
            else:
                combined += f"=== KẾT QUẢ CHẤM ĐIỂM ===\n{scoring_result}\n\n"
        
        if gaps_result:
            if isinstance(gaps_result, dict):
                combined += f"=== THÔNG TIN THIẾU & MÂU THUẪN ===\n{json.dumps(gaps_result, ensure_ascii=False, indent=2)}\n\n"
            else:
                combined += f"=== THÔNG TIN THIẾU & MÂU THUẪN ===\n{gaps_result}\n\n"
        
        prompt = REPORT_PROMPT_TEMPLATE.format(analysis_result=combined)
        
        self.logger.log_step(
            "RECOMMENDATION",
            "Bắt đầu tạo báo cáo đề xuất",
            input_summary=f"Dữ liệu phân tích: {len(combined)} ký tự"
        )
        
        try:
            response = self.model.generate_content(
                [SYSTEM_PROMPT, prompt],
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 8192
                }
            )
            
            if response and response.text:
                self.report = response.text
                
                self.logger.log_step(
                    "RECOMMENDATION",
                    "Báo cáo đề xuất đã được tạo",
                    output_summary=f"Báo cáo: {len(response.text)} ký tự",
                    source_ref="gemini-2.0-flash"
                )
                
                # Log human checkpoint
                self.logger.log_step(
                    "HUMAN_CHECKPOINT",
                    "⚠️ CẦN KIỂM TRA: Trưởng phòng PTKD cần xem xét và thẩm định báo cáo đề xuất",
                    input_summary="Báo cáo đề xuất 2 địa bàn ưu tiên",
                    output_summary="Trưởng phòng PTKD xác nhận hoặc điều chỉnh trước khi trình Ban Giám đốc"
                )
                
                return True, response.text
            
            return False, "⚠️ Không tạo được báo cáo."
            
        except Exception as e:
            self.logger.log_step(
                "ERROR_HANDLING",
                "Lỗi khi tạo báo cáo",
                output_summary=str(e)
            )
            return False, "⚠️ Không thể tạo báo cáo qua AI lúc này. Hệ thống đã tự động sử dụng mẫu báo cáo phân tích định lượng chuẩn hóa."
    
    def generate_survey_plan(self, analysis_result: str, 
                              recommended_regions: list = None) -> tuple:
        """
        Tạo kế hoạch khảo sát tiếp theo.
        
        Returns:
            (success: bool, plan: str)
        """
        if not self.model:
            return False, "⚠️ Model chưa được khởi tạo."
        
        regions_text = ", ".join(recommended_regions) if recommended_regions else "2 địa bàn được đề xuất"
        
        prompt = f"""Dựa trên kết quả phân tích, tạo KẾ HOẠCH KHẢO SÁT CHI TIẾT cho {regions_text}:

=== KẾT QUẢ PHÂN TÍCH ===
{analysis_result}

=== YÊU CẦU KẾ HOẠCH ===

### 1. NHÓM KHÁCH CẦN TIẾP CẬN
Cho mỗi địa bàn, xác định:
- Loại khách hàng mục tiêu (chuỗi bán lẻ lớn, SME, startup...)
- Ước tính số lượng khách cần tiếp cận
- Kênh tiếp cận phù hợp
- Thông tin cần thu thập từ khách

### 2. THÔNG TIN CẦN XÁC MINH
- Dữ liệu nào từ báo cáo thị trường cần kiểm chứng thực tế
- Thông tin đối thủ cần cập nhật
- Yêu cầu kỹ thuật cần khảo sát tại chỗ

### 3. PHÂN CÔNG TRÁCH NHIỆM
- Ai thực hiện khảo sát (vai trò, bộ phận)
- Timeline dự kiến
- KPI đánh giá khảo sát

### 4. ĐIỂM CON NGƯỜI CẦN QUYẾT ĐỊNH
- Các quyết định mà AI không thể thay thế con người
- Điều kiện chuyển xử lý giữa AI và con người
- Cách phát hiện kết quả sai / bias

Trả lời bằng tiếng Việt, cấu trúc rõ ràng, phân biệt [DỮ LIỆU] vs [SUY LUẬN]."""
        
        self.logger.log_step(
            "RECOMMENDATION",
            "Bắt đầu tạo kế hoạch khảo sát",
            input_summary=f"Địa bàn: {regions_text}"
        )
        
        try:
            response = self.model.generate_content(
                [SYSTEM_PROMPT, prompt],
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 6144
                }
            )
            
            if response and response.text:
                self.survey_plan = response.text
                
                self.logger.log_step(
                    "RECOMMENDATION",
                    "Kế hoạch khảo sát đã được tạo",
                    output_summary=f"Kế hoạch: {len(response.text)} ký tự"
                )
                
                self.logger.log_step(
                    "HUMAN_CHECKPOINT",
                    "⚠️ CẦN KIỂM TRA: Trưởng phòng PTKD phê duyệt kế hoạch khảo sát trước khi triển khai",
                    input_summary="Kế hoạch khảo sát 2 địa bàn",
                    output_summary="Cần xác nhận: nhóm khách, ngân sách, timeline, nhân sự"
                )
                
                return True, response.text
            
            return False, "⚠️ Không tạo được kế hoạch khảo sát."
            
        except Exception as e:
            self.logger.log_step(
                "ERROR_HANDLING",
                "Lỗi khi tạo kế hoạch khảo sát",
                output_summary=str(e)
            )
            return False, "⚠️ Không thể tạo kế hoạch khảo sát qua AI lúc này. Hệ thống đã tự động sử dụng mẫu kế hoạch khảo sát 4 tuần tiêu chuẩn."
