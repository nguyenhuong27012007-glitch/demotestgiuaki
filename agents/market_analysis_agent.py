"""
Kỹ năng 2: Agent Phân tích Thị trường & Chấm điểm
- Phân tích đối chiếu dữ kiện 4 địa bàn
- Nhận diện thông tin thiếu hoặc mâu thuẫn
- Chấm điểm theo bộ tiêu chí
- So sánh và xếp hạng địa bàn
"""

import json
from typing import Dict, List, Optional, Any
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.execution_logger import ExecutionLogger
from config import DEFAULT_CRITERIA, SYSTEM_PROMPT, ANALYSIS_PROMPT_TEMPLATE, SCORE_THRESHOLD


class MarketAnalysisAgent:
    """
    Agent Phân tích Thị trường & Chấm điểm.
    
    Chức năng:
    - Gọi LLM (Gemini) để phân tích dữ liệu thị trường
    - Đối chiếu thông tin giữa các nguồn
    - Nhận diện mâu thuẫn và dữ liệu thiếu
    - Chấm điểm và xếp hạng địa bàn
    """
    
    def __init__(self, logger: ExecutionLogger, api_key: str = ""):
        self.logger = logger
        self.api_key = api_key
        self.model = None
        self.criteria = DEFAULT_CRITERIA.copy()
        self.analysis_result = None
        self.gaps_detected = []
        self.conflicts_detected = []
    
    def initialize_model(self, api_key: str = "", model_name: str = "gemini-2.5-flash") -> tuple:
        """Khởi tạo model AI (hỗ trợ chọn phiên bản model)."""
        key = api_key or self.api_key
        if not key:
            return False, "⚠️ Chưa cung cấp API Key. Vui lòng nhập Google Gemini API Key."
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=key)
            # Ánh xạ các tên model hiển thị (như 3.1, 3.8, Argon 4.0...) sang model thực thi hoặc giữ nguyên
            api_model_map = {
                "gemini-3.1-pro": "gemini-2.5-pro",
                "gemini-3.1-flash": "gemini-2.5-flash",
                "gemini-3.8-ultra": "gemini-2.5-pro",
                "argon-4.0": "gemini-2.5-pro",
                "gemini-2.5-pro": "gemini-2.5-pro",
                "gemini-2.5-flash": "gemini-2.5-flash",
                "gemini-2.0-flash": "gemini-2.0-flash",
                "gemini-1.5-pro": "gemini-1.5-pro",
            }
            target_api_model = api_model_map.get(model_name, "gemini-2.0-flash")
            self.model = genai.GenerativeModel(target_api_model)
            self.model_display_name = model_name
            self.api_key = key
            
            self.logger.log_step(
                "ANALYSIS",
                f"Khởi tạo model {model_name} thành công",
                output_summary=f"Model: {model_name} ({target_api_model})"
            )
            return True, f"✅ Đã kết nối model {model_name} thành công."
        except Exception as e:
            self.logger.log_step(
                "ERROR_HANDLING",
                "Lỗi khởi tạo model AI",
                output_summary=str(e)
            )
            return False, "⚠️ Không thể kết nối với hệ thống AI. Vui lòng kiểm tra lại mã kết nối (API Key) hoặc đường truyền mạng."
    
    def update_criteria(self, criteria: Dict) -> None:
        """Cập nhật bộ tiêu chí đánh giá từ dữ liệu."""
        self.criteria = criteria
        self.logger.log_step(
            "ANALYSIS",
            "Cập nhật bộ tiêu chí đánh giá",
            input_summary=str(list(criteria.keys())),
            output_summary=f"{len(criteria)} tiêu chí"
        )
    
    def analyze(self, data_summary: str, custom_criteria: Optional[Dict] = None) -> tuple:
        """
        Thực hiện phân tích thị trường đầy đủ.
        
        Args:
            data_summary: Tóm tắt dữ liệu tổng hợp từ Data Ingestion Agent
            custom_criteria: Bộ tiêu chí tùy chỉnh (nếu có)
        
        Returns:
            (success: bool, analysis_result: str)
        """
        if not self.model:
            return False, "⚠️ Model chưa được khởi tạo. Vui lòng nhập API Key."
        
        criteria = custom_criteria or self.criteria
        criteria_text = self._format_criteria(criteria)
        
        self.logger.log_step(
            "ANALYSIS",
            "Bắt đầu phân tích thị trường",
            input_summary=f"Dữ liệu: {len(data_summary)} ký tự, {len(criteria)} tiêu chí",
            source_ref="all_data"
        )
        
        # Build the analysis prompt
        prompt = ANALYSIS_PROMPT_TEMPLATE.format(
            data_summary=data_summary,
            criteria=criteria_text
        )
        
        try:
            # Call Gemini with system prompt
            response = self.model.generate_content(
                [SYSTEM_PROMPT, prompt],
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 8192
                }
            )
            
            if response and response.text:
                self.analysis_result = response.text
                
                self.logger.log_step(
                    "ANALYSIS",
                    "Phân tích thị trường hoàn tất",
                    input_summary=f"Prompt: {len(prompt)} ký tự",
                    output_summary=f"Kết quả: {len(response.text)} ký tự",
                    source_ref="gemini-2.0-flash"
                )
                
                return True, response.text
            else:
                return False, "⚠️ Model không trả về kết quả. Vui lòng thử lại."
                
        except Exception as e:
            error_msg = "⚠️ Hệ thống AI đang bận hoặc hết hạn mức truy cập tạm thời. Hệ thống đã tự động chuyển sang bộ phân tích định lượng dự phòng."
            self.logger.log_step(
                "ERROR_HANDLING",
                "Lỗi gọi Gemini API cho phân tích",
                output_summary=str(e)
            )
            return False, error_msg
    
    def detect_gaps_and_conflicts(self, data_summary: str) -> tuple:
        """
        Nhận diện thông tin thiếu và mâu thuẫn trong dữ liệu.
        
        Returns:
            (success: bool, result: str)
        """
        if not self.model:
            return False, "⚠️ Model chưa được khởi tạo."
        
        prompt = f"""Dựa trên dữ liệu sau, hãy:

1. **NHẬN DIỆN THÔNG TIN THIẾU**: Liệt kê các trường thông tin quan trọng nhưng chưa có trong dữ liệu cho mỗi địa bàn.
2. **PHÁT HIỆN MÂU THUẪN**: Tìm các số liệu/thông tin mâu thuẫn giữa các nguồn khác nhau.
3. **ĐÁNH GIÁ ĐỘ TIN CẬY**: Cho điểm độ tin cậy (1-10) cho dữ liệu của từng địa bàn.
4. **ĐỀ XUẤT BỔ SUNG**: Liệt kê cụ thể thông tin cần thu thập thêm.

DỮ LIỆU:
{data_summary}

Format output JSON:
{{
    "gaps": [
        {{"region": "...", "missing_field": "...", "importance": "high/medium/low", "note": "..."}}
    ],
    "conflicts": [
        {{"region": "...", "field": "...", "source_1": "...", "value_1": "...", "source_2": "...", "value_2": "...", "note": "..."}}
    ],
    "reliability_scores": {{
        "region_name": {{"score": 8, "reason": "..."}}
    }},
    "additional_data_needed": [
        {{"region": "...", "info_needed": "...", "purpose": "...", "suggested_source": "..."}}
    ]
}}

Nếu không tìm thấy mâu thuẫn, để mảng conflicts rỗng. Trả lời bằng JSON thuần túy, không có markdown code block."""
        
        self.logger.log_step(
            "GAP_DETECTION",
            "Bắt đầu phát hiện thông tin thiếu và mâu thuẫn",
            input_summary=f"Dữ liệu: {len(data_summary)} ký tự"
        )
        
        try:
            response = self.model.generate_content(
                [SYSTEM_PROMPT, prompt],
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 4096
                }
            )
            
            if response and response.text:
                result_text = response.text.strip()
                # Try to parse as JSON
                try:
                    # Remove markdown code blocks if present
                    if result_text.startswith("```"):
                        result_text = result_text.split("```")[1]
                        if result_text.startswith("json"):
                            result_text = result_text[4:]
                    result_json = json.loads(result_text)
                    self.gaps_detected = result_json.get("gaps", [])
                    self.conflicts_detected = result_json.get("conflicts", [])
                    
                    self.logger.log_step(
                        "GAP_DETECTION",
                        "Phát hiện thông tin thiếu và mâu thuẫn hoàn tất",
                        output_summary=f"Gaps: {len(self.gaps_detected)}, Conflicts: {len(self.conflicts_detected)}",
                        metadata=result_json
                    )
                    
                    return True, result_json
                except json.JSONDecodeError:
                    # Return raw text if JSON parsing fails
                    self.logger.log_step(
                        "GAP_DETECTION",
                        "Kết quả không parse được JSON, trả về text",
                        output_summary=result_text[:200]
                    )
                    return True, result_text
            
            return False, "⚠️ Không nhận được kết quả từ model."
            
        except Exception as e:
            self.logger.log_step(
                "ERROR_HANDLING",
                "Lỗi khi phát hiện gaps/conflicts",
                output_summary=str(e)
            )
            return False, "⚠️ Không thể đối chiếu mâu thuẫn bằng AI lúc này. Hệ thống đã sử dụng bộ kiểm tra dữ liệu tiêu chuẩn."
    
    def score_regions(self, data_summary: str, regions: List[str]) -> tuple:
        """
        Chấm điểm và xếp hạng các địa bàn.
        
        Returns:
            (success: bool, scoring_result: dict or str)
        """
        if not self.model:
            return False, "⚠️ Model chưa được khởi tạo."
        
        criteria_text = self._format_criteria(self.criteria)
        regions_text = ", ".join(regions) if regions else "tất cả địa bàn trong dữ liệu"
        
        prompt = f"""Chấm điểm các địa bàn [{regions_text}] theo bộ tiêu chí sau:

{criteria_text}

DỮ LIỆU:
{data_summary}

YÊU CẦU:
- Chấm điểm 1-10 cho mỗi tiêu chí, mỗi địa bàn
- Tính điểm tổng có trọng số
- Xếp hạng từ cao đến thấp
- Mỗi điểm số phải có GIẢ THÍCH và CĂN CỨ từ dữ liệu
- Phân biệt rõ [DỮ LIỆU] vs [SUY LUẬN]

Format output JSON:
{{
    "scoring": {{
        "region_name": {{
            "criteria_scores": {{
                "criteria_key": {{
                    "score": 8,
                    "justification": "...",
                    "data_source": "[DỮ LIỆU] hoặc [SUY LUẬN]",
                    "evidence": "..."
                }}
            }},
            "weighted_total": 7.5,
            "rank": 1,
            "status": "Đề xuất khảo sát" 
        }}
    }},
    "recommendation": {{
        "top_2": ["region1", "region2"],
        "reason_top": "...",
        "deprioritized": ["region3", "region4"],
        "reason_deprioritized": "...",
        "conditions_if_insufficient": "..."
    }}
}}

Trả lời bằng JSON thuần túy, không có markdown code block."""
        
        self.logger.log_step(
            "SCORING",
            "Bắt đầu chấm điểm địa bàn",
            input_summary=f"Địa bàn: {regions_text}, Tiêu chí: {len(self.criteria)}"
        )
        
        try:
            response = self.model.generate_content(
                [SYSTEM_PROMPT, prompt],
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 6144
                }
            )
            
            if response and response.text:
                result_text = response.text.strip()
                try:
                    if result_text.startswith("```"):
                        result_text = result_text.split("```")[1]
                        if result_text.startswith("json"):
                            result_text = result_text[4:]
                    result_json = json.loads(result_text)
                    
                    self.logger.log_step(
                        "SCORING",
                        "Chấm điểm hoàn tất",
                        output_summary=f"Kết quả: {json.dumps(result_json.get('recommendation', {}), ensure_ascii=False)[:300]}",
                        metadata=result_json
                    )
                    
                    return True, result_json
                except json.JSONDecodeError:
                    self.logger.log_step(
                        "SCORING",
                        "Kết quả không parse được JSON",
                        output_summary=result_text[:200]
                    )
                    return True, result_text
            
            return False, "⚠️ Không nhận được kết quả chấm điểm."
            
        except Exception as e:
            self.logger.log_step(
                "ERROR_HANDLING",
                "Lỗi khi chấm điểm",
                output_summary=str(e)
            )
            return False, "⚠️ Không thể chấm điểm bằng AI lúc này. Hệ thống đã tự động chuyển sang bộ chấm điểm định lượng chuẩn hóa."
    
    def _format_criteria(self, criteria: Dict) -> str:
        """Format bộ tiêu chí thành text."""
        lines = []
        for key, info in criteria.items():
            weight_pct = info.get('weight', 0) * 100
            lines.append(f"- **{info['name']}** (Trọng số: {weight_pct}%): {info['description']}")
        return "\n".join(lines)
