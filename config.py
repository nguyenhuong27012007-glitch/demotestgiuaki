"""
Cấu hình hệ thống AI Agent - Đánh giá thị trường mở rộng kinh doanh
Công ty Hưng Phát - Giải pháp quản lý kho cho chuỗi bán lẻ
"""
import os

# === API Key mặc định ===
DEFAULT_GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6KsCpm9zXcKbUaS1X2tSeFhNY6TbYwDXh_C2OMCEB90Aw")

# === Thông tin công ty ===
COMPANY_NAME = "Hưng Phát"
COMPANY_DESCRIPTION = "Cung cấp giải pháp quản lý kho (WMS) cho chuỗi bán lẻ"
EXPANSION_SLOTS = 2  # Số địa bàn được chọn để khảo sát tiếp
TOTAL_REGIONS = 4    # Tổng số địa bàn ứng viên

# === Bộ tiêu chí đánh giá địa bàn (mặc định, có thể cập nhật từ dữ liệu) ===
DEFAULT_CRITERIA = {
    "market_size": {
        "name": "Quy mô thị trường",
        "weight": 0.25,
        "description": "Số lượng chuỗi bán lẻ, cửa hàng, quy mô doanh số"
    },
    "wms_demand_fit": {
        "name": "Mức độ phù hợp nhu cầu WMS",
        "weight": 0.25,
        "description": "Nhu cầu quản lý kho có khớp với giải pháp công ty không"
    },
    "deployment_feasibility": {
        "name": "Khả năng triển khai",
        "weight": 0.25,
        "description": "Yêu cầu hỗ trợ tại chỗ, SLA, rào cản kỹ thuật so với năng lực hiện tại"
    },
    "competitive_landscape": {
        "name": "Cạnh tranh",
        "weight": 0.15,
        "description": "Mức độ cạnh tranh từ đối thủ, thị phần còn trống"
    },
    "growth_potential": {
        "name": "Tiềm năng tăng trưởng",
        "weight": 0.10,
        "description": "Xu hướng tăng trưởng, tiềm năng mở rộng trong tương lai"
    }
}

# === Ngưỡng quyết định ===
SCORE_THRESHOLD = {
    "recommend": 7.0,      # Điểm tối thiểu để đề xuất khảo sát
    "caution": 5.0,         # Điểm cần xem xét thêm
    "not_recommend": 3.0    # Điểm dưới ngưỡng khuyến nghị
}

# === Cấu hình xử lý dữ liệu ===
MAX_ROWS_BEFORE_AGGREGATION = 5000  # Số dòng tối đa trước khi tự động tổng hợp
SUPPORTED_FILE_TYPES = [".csv", ".xlsx", ".xls"]

# === Labels trạng thái ===
STATUS_LABELS = {
    "sufficient": "✅ Đủ dữ liệu",
    "partial": "⚠️ Thiếu một phần",
    "insufficient": "❌ Cần bổ sung dữ liệu",
    "conflict": "🔄 Có mâu thuẫn"
}

# === Template prompt cho Gemini ===
SYSTEM_PROMPT = """Bạn là AI Agent chuyên phân tích thị trường cho công ty {company_name} - {company_desc}.

NHIỆM VỤ: Đánh giá {total_regions} địa bàn tiềm năng và đề xuất {expansion_slots} địa bàn ưu tiên để khảo sát mở rộng kinh doanh.

QUY TẮC BẮT BUỘC:
1. Chỉ sử dụng dữ liệu được cung cấp - KHÔNG tự bổ sung thông tin thị trường ngoài gói dữ liệu.
2. Phân biệt rõ: [DỮ LIỆU] = số liệu từ tài liệu nguồn vs [SUY LUẬN] = nhận định của Agent.
3. Nếu thiếu dữ liệu, ghi rõ "Chưa có dữ liệu" và nêu điều kiện cần bổ sung.
4. Đánh giá dựa trên bộ tiêu chí: Quy mô thị trường, Mức độ phù hợp WMS, Khả năng triển khai, Cạnh tranh, Tiềm năng tăng trưởng.
5. Mỗi nhận định phải có căn cứ tới tài liệu nguồn (tên file, cột, giá trị).

FORMAT OUTPUT: Trả lời bằng tiếng Việt, cấu trúc rõ ràng với heading và bullet points.
""".format(
    company_name=COMPANY_NAME,
    company_desc=COMPANY_DESCRIPTION, 
    total_regions=TOTAL_REGIONS,
    expansion_slots=EXPANSION_SLOTS
)

ANALYSIS_PROMPT_TEMPLATE = """Dựa trên dữ liệu sau đây, hãy phân tích và so sánh các địa bàn:

=== DỮ LIỆU ĐẦU VÀO ===
{data_summary}

=== BỘ TIÊU CHÍ ĐÁNH GIÁ ===
{criteria}

=== YÊU CẦU PHÂN TÍCH ===
1. **Tổng hợp dữ kiện** từng địa bàn theo 5 tiêu chí
2. **Nhận diện thông tin thiếu hoặc mâu thuẫn** giữa các nguồn
3. **Chấm điểm** mỗi địa bàn theo thang 1-10 cho từng tiêu chí (có giải thích)
4. **Xếp hạng** và đề xuất 2 địa bàn ưu tiên
5. **Giải thích** vì sao chưa ưu tiên các địa bàn còn lại
6. Nếu chưa đủ căn cứ, nêu rõ **điều kiện cần bổ sung**

Phân biệt rõ [DỮ LIỆU] vs [SUY LUẬN] trong mọi nhận định.
"""

REPORT_PROMPT_TEMPLATE = """Dựa trên kết quả phân tích sau, hãy tạo BÁO CÁO ĐỀ XUẤT cho Trưởng phòng Phát triển Kinh doanh:

=== KẾT QUẢ PHÂN TÍCH ===
{analysis_result}

=== YÊU CẦU BÁO CÁO ===
Tạo báo cáo gồm:
1. **TÓM TẮT ĐIỀU HÀNH** (Executive Summary)
2. **BẢNG SO SÁNH** 4 địa bàn theo các tiêu chí (có điểm số và căn cứ)
3. **ĐỀ XUẤT**: 2 địa bàn ưu tiên khảo sát + lý do
4. **GIẢI THÍCH** vì sao chưa ưu tiên địa bàn còn lại
5. **THÔNG TIN CHƯA XÁC ĐỊNH** cần bổ sung
6. **KẾ HOẠCH KHẢO SÁT TIẾP THEO**:
   - Nhóm khách cần tiếp cận
   - Thông tin cần xác minh
   - Người/bộ phận phụ trách
7. **ĐIỂM CẦN CON NGƯỜI XỬ LÝ** (Human Checkpoints)

Phân biệt rõ [DỮ LIỆU] vs [SUY LUẬN]. Không thêm thông tin thị trường ngoài dữ liệu đã cung cấp.
"""
