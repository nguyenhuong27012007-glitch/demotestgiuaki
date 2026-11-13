"""
Kỹ năng 1: Agent Thu thập & Chuẩn hóa Dữ liệu
- Đọc nhiều file dữ liệu (CSV, XLSX, Google Sheet)
- Tự động nhận diện và ánh xạ cột
- Xử lý file lớn, file thiếu dữ liệu, file lỗi
- Chuẩn hóa dữ liệu về format thống nhất
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.file_handler import read_file, read_google_sheet
from utils.column_mapper import map_columns, generate_mapping_report, get_unmapped_columns, COLUMN_SCHEMA
from utils.execution_logger import ExecutionLogger


class DataIngestionAgent:
    """
    Agent Thu thập & Chuẩn hóa Dữ liệu.
    
    Chức năng:
    - Đọc đa nguồn: CSV, XLSX, Google Sheet
    - Tự động ánh xạ cột theo ngữ nghĩa
    - Xử lý file lớn bằng Group By tự động
    - Xử lý file lỗi/rỗng an toàn (Zero-Crash)
    - Ghi nhật ký toàn bộ thao tác
    """
    
    def __init__(self, logger: ExecutionLogger):
        self.logger = logger
        self.raw_dataframes: Dict[str, pd.DataFrame] = {}
        self.file_infos: Dict[str, Dict] = {}
        self.column_mappings: Dict[str, Dict] = {}
        self.errors: List[Dict] = []
        self.warnings: List[str] = []
    
    def ingest_uploaded_file(self, file_content: bytes, filename: str) -> Tuple[bool, str]:
        """
        Đọc và xử lý file được upload.
        
        Returns:
            (success: bool, message: str)
        """
        self.logger.log_step(
            "DATA_READ", 
            f"Bắt đầu đọc file: {filename}",
            input_summary=f"File: {filename}, Size: {len(file_content)} bytes",
            source_ref=filename
        )
        
        try:
            df, file_info, error = read_file(file_content, filename)
            
            if error:
                self.logger.log_step(
                    "ERROR_HANDLING",
                    f"Lỗi khi đọc file: {filename}",
                    input_summary=filename,
                    output_summary=error,
                    source_ref=filename
                )
                self.errors.append({"file": filename, "error": error})
                return False, error
            
            # Store raw data
            self.raw_dataframes[filename] = df
            self.file_infos[filename] = file_info
            
            # Log aggregation if applied
            if file_info.get("was_aggregated"):
                self.logger.log_step(
                    "AGGREGATION",
                    f"File lớn đã được tổng hợp tự động",
                    input_summary=f"File gốc: {filename}",
                    output_summary=file_info["aggregation_note"],
                    source_ref=filename
                )
                self.warnings.append(file_info["aggregation_note"])
            
            # Auto map columns
            mapping = map_columns(list(df.columns))
            self.column_mappings[filename] = mapping
            
            mapped_count = sum(1 for v in mapping.values() if v is not None)
            
            self.logger.log_step(
                "COLUMN_MAPPING",
                f"Ánh xạ cột cho file: {filename}",
                input_summary=f"Cột gốc: {list(df.columns)}",
                output_summary=f"Đã ánh xạ {mapped_count}/{len(COLUMN_SCHEMA)} trường. "
                              f"Mapping: {dict((k,v) for k,v in mapping.items() if v)}",
                source_ref=filename
            )
            
            success_msg = (f"✅ Đã đọc thành công file '{filename}': "
                          f"{file_info['rows']} dòng × {file_info['columns']} cột. "
                          f"Ánh xạ {mapped_count} trường thông tin.")
            
            return True, success_msg
            
        except Exception as e:
            error_msg = f"⚠️ Lỗi không xác định khi xử lý '{filename}': {str(e)}"
            self.logger.log_step(
                "ERROR_HANDLING",
                f"Exception khi đọc file: {filename}",
                input_summary=filename,
                output_summary=str(e),
                source_ref=filename
            )
            self.errors.append({"file": filename, "error": error_msg})
            return False, error_msg
    
    def ingest_google_sheet(self, url: str) -> Tuple[bool, str]:
        """Đọc Google Sheet từ URL công khai."""
        self.logger.log_step(
            "DATA_READ",
            "Bắt đầu đọc Google Sheet",
            input_summary=f"URL: {url}",
            source_ref="Google Sheet"
        )
        
        try:
            df, file_info, error = read_google_sheet(url)
            
            if error:
                self.logger.log_step(
                    "ERROR_HANDLING",
                    "Lỗi khi đọc Google Sheet",
                    input_summary=url,
                    output_summary=error,
                    source_ref="Google Sheet"
                )
                self.errors.append({"file": "Google Sheet", "error": error})
                return False, error
            
            sheet_name = f"GoogleSheet_{len(self.raw_dataframes)+1}"
            self.raw_dataframes[sheet_name] = df
            self.file_infos[sheet_name] = file_info
            
            # Auto map columns
            mapping = map_columns(list(df.columns))
            self.column_mappings[sheet_name] = mapping
            
            mapped_count = sum(1 for v in mapping.values() if v is not None)
            
            self.logger.log_step(
                "COLUMN_MAPPING",
                f"Ánh xạ cột cho Google Sheet",
                input_summary=f"Cột: {list(df.columns)}",
                output_summary=f"Đã ánh xạ {mapped_count}/{len(COLUMN_SCHEMA)} trường",
                source_ref=sheet_name
            )
            
            if file_info.get("was_aggregated"):
                self.warnings.append(file_info["aggregation_note"])
            
            return True, (f"✅ Đã đọc Google Sheet: {file_info['rows']} dòng × "
                         f"{file_info['columns']} cột. Ánh xạ {mapped_count} trường.")
            
        except Exception as e:
            error_msg = f"⚠️ Lỗi khi đọc Google Sheet: {str(e)}"
            self.logger.log_step(
                "ERROR_HANDLING",
                "Exception khi đọc Google Sheet",
                input_summary=url,
                output_summary=str(e),
                source_ref="Google Sheet"
            )
            self.errors.append({"file": "Google Sheet", "error": error_msg})
            return False, error_msg
    
    def get_consolidated_data_summary(self) -> str:
        """
        Tạo tóm tắt tổng hợp từ tất cả dữ liệu đã đọc.
        Đây là đầu vào cho Market Analysis Agent.
        """
        if not self.raw_dataframes:
            return "Chưa có dữ liệu nào được tải lên."
        
        summary_parts = []
        
        for filename, df in self.raw_dataframes.items():
            mapping = self.column_mappings.get(filename, {})
            file_info = self.file_infos.get(filename, {})
            
            part = f"\n--- FILE: {filename} ---\n"
            part += f"Số dòng: {len(df)}, Số cột: {len(df.columns)}\n"
            
            if file_info.get("was_aggregated"):
                part += f"⚠️ {file_info['aggregation_note']}\n"
                if "aggregated_df" in file_info and file_info["aggregated_df"] is not None:
                    part += f"BẢNG TỔNG HỢP GROUP-BY TỪ {len(df):,} DÒNG GỐC:\n{file_info['aggregated_df'].to_string(index=False)}\n\n"
            
            part += f"Cột: {list(df.columns)}\n"
            part += f"Ánh xạ: {dict((k,v) for k,v in mapping.items() if v)}\n\n"
            
            # Add data preview (first 30 rows as string)
            preview = df.head(30).to_string(index=False)
            part += f"DỮ LIỆU MẪU (30 dòng đầu trong tổng số {len(df):,} dòng):\n{preview}\n"
            
            # Add basic statistics for numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                part += f"\nTHỐNG KÊ SỐ:\n{df[numeric_cols].describe().to_string()}\n"
            
            # Identify region column and list unique regions
            region_col = mapping.get("region")
            if region_col and region_col in df.columns:
                regions = df[region_col].dropna().unique().tolist()
                part += f"\nĐỊA BÀN PHÁT HIỆN: {regions}\n"
            
            summary_parts.append(part)
        
        # Add warnings
        if self.warnings:
            summary_parts.append("\n--- CẢNH BÁO ---")
            for w in self.warnings:
                summary_parts.append(f"⚠️ {w}")
        
        # Add errors
        if self.errors:
            summary_parts.append("\n--- LỖI ĐỌC DỮ LIỆU ---")
            for e in self.errors:
                summary_parts.append(f"❌ {e['file']}: {e['error']}")
        
        full_summary = "\n".join(summary_parts)
        
        self.logger.log_step(
            "DATA_READ",
            "Tổng hợp dữ liệu từ tất cả nguồn",
            input_summary=f"{len(self.raw_dataframes)} file(s)",
            output_summary=f"Tóm tắt: {len(full_summary)} ký tự, "
                          f"{sum(len(df) for df in self.raw_dataframes.values())} dòng tổng cộng",
            source_ref="all_files"
        )
        
        return full_summary
    
    def get_regions_detected(self) -> List[str]:
        """Trả về danh sách các địa bàn phát hiện được từ dữ liệu."""
        regions = set()
        for filename, df in self.raw_dataframes.items():
            mapping = self.column_mappings.get(filename, {})
            region_col = mapping.get("region")
            if region_col and region_col in df.columns:
                for val in df[region_col].dropna().unique():
                    regions.add(str(val).strip())
        return sorted(list(regions))
    
    def get_data_completeness_report(self) -> Dict[str, Any]:
        """Báo cáo mức độ đầy đủ dữ liệu cho từng file."""
        report = {}
        for filename in self.raw_dataframes:
            mapping = self.column_mappings.get(filename, {})
            mapped = {k: v for k, v in mapping.items() if v is not None}
            missing = {k: COLUMN_SCHEMA[k]["description"] 
                      for k, v in mapping.items() if v is None}
            report[filename] = {
                "mapped_fields": mapped,
                "missing_fields": missing,
                "completeness": len(mapped) / len(COLUMN_SCHEMA) * 100 if COLUMN_SCHEMA else 0
            }
        return report
    
    def reset(self):
        """Reset agent state."""
        self.raw_dataframes.clear()
        self.file_infos.clear()
        self.column_mappings.clear()
        self.errors.clear()
        self.warnings.clear()
