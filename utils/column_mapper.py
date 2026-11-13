import re
from typing import Dict, List, Optional, Tuple

# Schema chuẩn các loại cột và từ khóa nhận diện (tiếng Việt + tiếng Anh)
COLUMN_SCHEMA = {
    "region": {
        "description": "Địa bàn / Tỉnh thành / Khu vực",
        "keywords": ["tỉnh", "thành", "thành phố", "city", "region", "province", 
                     "địa bàn", "khu vực", "area", "location", "địa_bàn", "tinh_thanh",
                     "dia_ban", "vùng", "miền", "territory", "market", "thị trường"],
        "priority": 1
    },
    "market_size": {
        "description": "Quy mô thị trường (số cửa hàng, đơn hàng, doanh số)",
        "keywords": ["quy mô", "size", "stores", "cửa hàng", "doanh số", "revenue",
                     "doanh thu", "orders", "đơn hàng", "sales", "bán hàng", "turnover",
                     "market_size", "số lượng ch", "retail", "bán lẻ", "scale"],
        "priority": 2
    },
    "growth_rate": {
        "description": "Tốc độ tăng trưởng",
        "keywords": ["tăng trưởng", "growth", "tốc độ", "rate", "yoy", "cagr",
                     "trend", "xu hướng", "phát triển", "expansion", "mở rộng"],
        "priority": 3
    },
    "wms_demand": {
        "description": "Nhu cầu tính năng kho / WMS",
        "keywords": ["wms", "kho", "warehouse", "quản lý kho", "inventory", "tồn kho",
                     "tính năng", "feature", "category", "mô tả", "nhu cầu", "demand",
                     "requirement", "yêu cầu", "giải pháp", "solution", "logistics",
                     "supply chain", "chuỗi cung ứng", "fulfillment"],
        "priority": 4
    },
    "technical_barrier": {
        "description": "Rào cản kỹ thuật / Yêu cầu hỗ trợ tại chỗ",
        "keywords": ["rào cản", "barrier", "sla", "hỗ trợ", "support", "on-site",
                     "tại chỗ", "shipping", "vận chuyển", "kỹ thuật", "technical",
                     "triển khai", "deployment", "implementation", "khó khăn",
                     "challenge", "constraint", "hạn chế", "risk", "rủi ro"],
        "priority": 5
    },
    "competitor": {
        "description": "Đối thủ cạnh tranh",
        "keywords": ["đối thủ", "competitor", "cạnh tranh", "competition", "rival",
                     "vendor", "nhà cung cấp", "provider", "market share", "thị phần"],
        "priority": 6
    },
    "customer_feedback": {
        "description": "Phản hồi khách hàng",
        "keywords": ["phản hồi", "feedback", "khách hàng", "customer", "client",
                     "đánh giá", "review", "satisfaction", "hài lòng", "nps",
                     "complaint", "khiếu nại", "opinion", "ý kiến", "survey"],
        "priority": 7
    },
    "time_source": {
        "description": "Thời gian / Nguồn dữ liệu",
        "keywords": ["thời gian", "time", "date", "ngày", "tháng", "năm", "year",
                     "quarter", "quý", "period", "kỳ", "nguồn", "source", "báo cáo",
                     "report", "reference", "tham chiếu", "published", "xuất bản"],
        "priority": 8
    },
    "ecommerce": {
        "description": "Thương mại điện tử / TMĐT",
        "keywords": ["tmđt", "ecommerce", "e-commerce", "thương mại điện tử", "online",
                     "trực tuyến", "digital", "số hóa", "marketplace", "sàn"],
        "priority": 9
    },
    "return_rate": {
        "description": "Tỷ lệ trả hàng / Hoàn trả",
        "keywords": ["trả hàng", "return", "hoàn trả", "refund", "đổi trả",
                     "return rate", "tỷ lệ trả", "reverse logistics"],
        "priority": 10
    }
}


def map_columns(columns: List[str]) -> Dict[str, Optional[str]]:
    """
    Ánh xạ tên cột từ file dữ liệu sang schema chuẩn.
    Sử dụng keyword matching để nhận diện ngữ nghĩa cột.
    
    Args:
        columns: Danh sách tên cột từ DataFrame
    
    Returns:
        Dict mapping schema_key -> actual_column_name (hoặc None nếu không tìm thấy)
    """
    mapping = {}
    used_columns = set()
    
    # Chuẩn hóa tên cột để so khớp
    normalized = {col: _normalize(col) for col in columns}
    
    # Sắp xếp schema theo ưu tiên (cột quan trọng hơn được ánh xạ trước)
    sorted_schema = sorted(COLUMN_SCHEMA.items(), key=lambda x: x[1]["priority"])
    
    for schema_key, schema_info in sorted_schema:
        best_match = None
        best_score = 0
        
        for col in columns:
            if col in used_columns:
                continue
            
            score = _match_score(normalized[col], schema_info["keywords"])
            if score > best_score:
                best_score = score
                best_match = col
        
        if best_match and best_score > 0:
            mapping[schema_key] = best_match
            used_columns.add(best_match)
        else:
            mapping[schema_key] = None
    
    return mapping


def _normalize(text: str) -> str:
    """Chuẩn hóa tên cột: lowercase, bỏ ký tự đặc biệt, giữ tiếng Việt."""
    text = str(text).lower().strip()
    # Bỏ ký tự đặc biệt nhưng giữ tiếng Việt
    text = re.sub(r'[_\-\.\/\\()]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text


def _match_score(normalized_col: str, keywords: List[str]) -> int:
    """
    Tính điểm khớp giữa tên cột đã chuẩn hóa và danh sách keyword.
    
    Quy tắc tính điểm:
    - Khớp chính xác: +10 điểm
    - Keyword là substring của tên cột: +5 điểm
    - Tên cột là substring của keyword: +3 điểm
    - Khớp ở mức từ (word-level): +2 điểm mỗi từ chung
    """
    score = 0
    for keyword in keywords:
        keyword_lower = keyword.lower()
        if keyword_lower == normalized_col:
            score += 10  # Khớp chính xác
        elif keyword_lower in normalized_col:
            score += 5   # Substring match
        elif normalized_col in keyword_lower and len(normalized_col) > 2:
            score += 3   # Reverse substring
        else:
            # Khớp ở mức từ
            col_words = set(normalized_col.split())
            kw_words = set(keyword_lower.split())
            common = col_words & kw_words
            if common:
                score += 2 * len(common)
    return score


def get_unmapped_columns(columns: List[str], mapping: Dict[str, Optional[str]]) -> List[str]:
    """Trả về các cột chưa được ánh xạ vào schema nào."""
    mapped_cols = set(v for v in mapping.values() if v is not None)
    return [col for col in columns if col not in mapped_cols]


def generate_mapping_report(columns: List[str], mapping: Dict[str, Optional[str]]) -> str:
    """
    Tạo báo cáo ánh xạ cột để hiển thị cho người dùng.
    
    Args:
        columns: Danh sách tên cột gốc
        mapping: Kết quả ánh xạ từ map_columns()
    
    Returns:
        Chuỗi markdown mô tả kết quả ánh xạ
    """
    report_lines = ["### 📋 Kết quả ánh xạ cột dữ liệu\n"]
    
    mapped_count = sum(1 for v in mapping.values() if v is not None)
    total = len(COLUMN_SCHEMA)
    
    report_lines.append(f"**Đã ánh xạ:** {mapped_count}/{total} trường thông tin\n")
    
    for schema_key, actual_col in mapping.items():
        schema_desc = COLUMN_SCHEMA[schema_key]["description"]
        if actual_col:
            report_lines.append(f"✅ **{schema_desc}** → `{actual_col}`")
        else:
            report_lines.append(f"❌ **{schema_desc}** → _Chưa có dữ liệu_")
    
    unmapped = get_unmapped_columns(columns, mapping)
    if unmapped:
        report_lines.append(f"\n**Cột chưa phân loại:** {', '.join(f'`{c}`' for c in unmapped)}")
    
    return "\n".join(report_lines)
