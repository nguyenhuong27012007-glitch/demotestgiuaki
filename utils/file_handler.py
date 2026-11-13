import pandas as pd
import io
import os
from typing import Tuple, Optional, Dict, Any


def read_file(file_content: bytes, filename: str) -> Tuple[Optional[pd.DataFrame], Dict[str, Any], Optional[str]]:
    """
    Đọc file CSV hoặc XLSX với xử lý lỗi an toàn.
    
    Args:
        file_content: Nội dung file dạng bytes
        filename: Tên file gốc (dùng để xác định định dạng)
    
    Returns:
        (DataFrame hoặc None, thông tin file, thông báo lỗi hoặc None)
    """
    file_info = {
        "filename": filename,
        "size_bytes": len(file_content) if file_content else 0,
        "format": os.path.splitext(filename)[1].lower() if filename else "unknown",
        "rows": 0,
        "columns": 0,
        "column_names": [],
        "was_aggregated": False,
        "aggregation_note": ""
    }
    
    if not file_content or len(file_content) == 0:
        return None, file_info, "⚠️ File rỗng. Vui lòng tải lên file có dữ liệu."
    
    try:
        ext = file_info["format"]
        
        if ext == ".csv":
            df = _read_csv(file_content)
        elif ext in [".xlsx", ".xls"]:
            df = _read_xlsx(file_content)
        else:
            return None, file_info, f"⚠️ Định dạng file '{ext}' không được hỗ trợ. Vui lòng sử dụng .csv hoặc .xlsx"
        
        if df is None or df.empty:
            return None, file_info, "⚠️ File không chứa dữ liệu. Vui lòng kiểm tra lại nội dung file."
        
        # Xóa các dòng và cột hoàn toàn trống
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        if df.empty:
            return None, file_info, "⚠️ File chỉ chứa các ô trống. Vui lòng kiểm tra lại."
        
        file_info["rows"] = len(df)
        file_info["original_rows"] = len(df)
        file_info["columns"] = len(df.columns)
        file_info["column_names"] = list(df.columns)
        
        # Giữ nguyên toàn bộ 20.000+ dòng gốc để người dùng xem/sửa trên web,
        # đồng thời tạo sẵn bản tóm tắt Group-By cho AI Agent nếu file lớn (> 1.000 dòng)
        if len(df) > 1000:
            agg_df, agg_note = _auto_aggregate(df, filename)
            file_info["was_aggregated"] = True
            file_info["aggregation_note"] = agg_note
            file_info["aggregated_df"] = agg_df
        
        return df, file_info, None
        
    except Exception:
        return None, file_info, f"⚠️ Không thể đọc tệp '{filename}'. Vui lòng kiểm tra định dạng tệp (.csv, .xlsx) không bị hỏng và thử lại."


def _read_csv(content: bytes) -> Optional[pd.DataFrame]:
    """Đọc CSV với tự động phát hiện encoding và separator."""
    encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    separators = [',', ';', '\t', '|']
    
    for encoding in encodings:
        for sep in separators:
            try:
                df = pd.read_csv(io.BytesIO(content), encoding=encoding, sep=sep, 
                                on_bad_lines='skip', dtype=str)
                if len(df.columns) > 1 or (len(df.columns) == 1 and len(df) > 0):
                    # Chuyển đổi các cột có dạng số (tương thích Pandas 2.2+)
                    for col in df.columns:
                        try:
                            df[col] = pd.to_numeric(df[col].str.replace(',', ''))
                        except Exception:
                            pass
                    return df
            except:
                continue
    return None


def _read_xlsx(content: bytes) -> Optional[pd.DataFrame]:
    """Đọc XLSX file tốc độ cao, hỗ trợ nhiều sheet và file 20.000+ dòng."""
    try:
        xls = pd.ExcelFile(io.BytesIO(content), engine='openpyxl')
        sheets = xls.sheet_names
        
        if len(sheets) == 1:
            df = pd.read_excel(xls, sheet_name=sheets[0])
            return df
        else:
            # Nhiều sheet - nối tất cả lại với cột đánh dấu nguồn
            dfs = []
            for sheet in sheets:
                try:
                    df_sheet = pd.read_excel(xls, sheet_name=sheet)
                    if not df_sheet.empty:
                        df_sheet['_source_sheet'] = sheet
                        dfs.append(df_sheet)
                except:
                    continue
            if dfs:
                return pd.concat(dfs, ignore_index=True)
    except:
        pass
    return None


def _auto_aggregate(df: pd.DataFrame, filename: str) -> Tuple[pd.DataFrame, str]:
    """
    Tự động tổng hợp file lớn theo cột địa bàn/tỉnh thành.
    Áp dụng cho file nhật ký giao dịch (Transaction Log) có hàng nghìn dòng.
    """
    # Tìm cột chứa thông tin địa bàn/tỉnh thành
    region_keywords = ['tỉnh', 'thành', 'thành phố', 'city', 'region', 'province', 
                       'địa bàn', 'khu vực', 'area', 'location', 'địa_bàn', 'tinh_thanh',
                       'dia_ban', 'district', 'state']
    
    region_col = None
    for col in df.columns:
        col_lower = str(col).lower().strip()
        for keyword in region_keywords:
            if keyword in col_lower:
                region_col = col
                break
        if region_col:
            break
    
    if region_col is None:
        # Dùng cột chuỗi đầu tiên làm key nhóm
        str_cols = df.select_dtypes(include=['object']).columns
        if len(str_cols) > 0:
            region_col = str_cols[0]
        else:
            # Không thể tổng hợp - lấy mẫu thay thế
            sampled = df.head(500)
            return sampled, f"File '{filename}' có {len(df)} dòng. Đã lấy mẫu 500 dòng đầu tiên do không tìm được cột nhóm phù hợp."
    
    # Tổng hợp các cột số
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    str_cols = [c for c in df.columns if c != region_col and c not in numeric_cols]
    
    agg_dict = {}
    for col in numeric_cols:
        agg_dict[col] = ['sum', 'mean', 'count']
    for col in str_cols[:5]:  # Giới hạn cột chuỗi
        agg_dict[col] = 'first'
    
    if not agg_dict:
        grouped = df.groupby(region_col).size().reset_index(name='count')
    else:
        try:
            grouped = df.groupby(region_col).agg(agg_dict).reset_index()
            # Làm phẳng cột đa cấp
            grouped.columns = ['_'.join(col).strip('_') if isinstance(col, tuple) else col 
                              for col in grouped.columns]
        except:
            grouped = df.groupby(region_col).size().reset_index(name='count')
    
    note = (f"⚠️ File '{filename}' có {len(df)} dòng (file nhật ký giao dịch lớn). "
            f"Đã tự động tổng hợp (Group By) theo '{region_col}' thành {len(grouped)} nhóm "
            f"để tránh tràn bộ nhớ. Các chỉ số: tổng, trung bình, số lượng.")
    
    return grouped, note


def read_google_sheet(url: str) -> Tuple[Optional[pd.DataFrame], Dict[str, Any], Optional[str]]:
    """
    Đọc Google Sheet từ URL công khai.
    Chuyển đổi URL sang định dạng CSV export.
    
    Args:
        url: URL Google Sheet (công khai hoặc có quyền xem)
    
    Returns:
        (DataFrame hoặc None, thông tin file, thông báo lỗi hoặc None)
    """
    file_info = {
        "filename": "Google Sheet",
        "source_url": url,
        "format": "google_sheet",
        "rows": 0,
        "columns": 0,
        "column_names": [],
        "was_aggregated": False,
        "aggregation_note": ""
    }
    
    try:
        # Chuyển đổi URL Google Sheet sang URL xuất CSV
        if '/edit' in url:
            csv_url = url.split('/edit')[0] + '/export?format=csv'
        elif '/pubhtml' in url:
            csv_url = url.split('/pubhtml')[0] + '/export?format=csv'
        elif 'export?format=csv' in url:
            csv_url = url
        elif '/d/' in url:
            # Trích xuất Sheet ID từ URL
            parts = url.split('/d/')
            if len(parts) > 1:
                sheet_id = parts[1].split('/')[0]
                csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
            else:
                return None, file_info, "⚠️ Không thể phân tích URL Google Sheet. Vui lòng kiểm tra lại link."
        else:
            return None, file_info, "⚠️ URL không đúng định dạng Google Sheet. Vui lòng dán link chia sẻ công khai."
        
        # Xử lý tham số gid cho sheet cụ thể
        if 'gid=' in url:
            gid = url.split('gid=')[1].split('&')[0].split('#')[0]
            csv_url += f'&gid={gid}'
        
        df = pd.read_csv(csv_url, dtype=str)
        
        if df is None or df.empty:
            return None, file_info, "⚠️ Google Sheet rỗng hoặc không thể truy cập. Kiểm tra quyền chia sẻ (công khai)."
        
        # Dọn dẹp dữ liệu
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # Chuyển đổi cột số (tương thích Pandas 2.2+)
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col].str.replace(',', ''))
            except Exception:
                pass
        
        file_info["rows"] = len(df)
        file_info["columns"] = len(df.columns)
        file_info["column_names"] = list(df.columns)
        
        # Xử lý Google Sheet quá lớn
        if len(df) > 5000:
            df, agg_note = _auto_aggregate(df, "Google Sheet")
            file_info["was_aggregated"] = True
            file_info["aggregation_note"] = agg_note
            file_info["rows"] = len(df)
        
        return df, file_info, None
        
    except pd.errors.ParserError:
        return None, file_info, "⚠️ Không thể phân tích cấu trúc bảng từ Google Sheet. Vui lòng kiểm tra lại định dạng các dòng và cột trong trang tính."
    except Exception as e:
        error_str = str(e)
        if "HTTP Error 404" in error_str or "404" in error_str:
            return None, file_info, "⚠️ Không tìm thấy Google Sheet. Kiểm tra URL và quyền chia sẻ công khai."
        elif "HTTP Error 403" in error_str or "403" in error_str:
            return None, file_info, "⚠️ Không có quyền truy cập Google Sheet. Hãy đặt quyền chia sẻ là 'Mọi người có link'."
        else:
            return None, file_info, "⚠️ Không thể kết nối tới Google Sheet. Vui lòng kiểm tra lại đường dẫn chia sẻ công khai hoặc kết nối mạng."
