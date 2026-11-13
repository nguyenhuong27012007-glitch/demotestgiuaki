"""
Bộ công cụ Xuất Báo Cáo & Dashboard Đa Định Dạng (HTML, DOCX, PDF)
- Tạo ảnh biểu đồ phân tích độ phân giải cao (PNG/Base64) từ dữ liệu điểm số
- Tách riêng Báo cáo Đề xuất (có nhúng ảnh biểu đồ phân tích) và Dashboard Tương tác
- Hỗ trợ xuất ra 3 định dạng chuẩn: .html, .docx (Word), .pdf (văn bản Tiếng Việt + biểu đồ)
"""

import io
import re
import base64
import textwrap
from typing import List, Dict, Any
import pandas as pd
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH


# Cấu hình font hỗ trợ đầy đủ Tiếng Việt Unicode trên Windows
plt.rcParams["font.sans-serif"] = ["Segoe UI", "Arial", "Tahoma", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def render_chart_png_bytes(df_scores: pd.DataFrame, chart_type: str = "bar") -> bytes:
    """
    Vẽ biểu đồ chất lượng cao bằng Matplotlib trả về PNG bytes để chèn vào Báo cáo HTML, Word (.docx) và PDF (.pdf).
    chart_type: 'bar' | 'radar' | 'grouped'
    """
    buf = io.BytesIO()

    if chart_type == "bar":
        fig, ax = plt.subplots(figsize=(8.5, 4.5), dpi=160)
        fig.patch.set_facecolor("#ffffff")
        ax.set_facecolor("#fdf2f8")

        regions = df_scores["Địa bàn"].astype(str).tolist()
        scores = df_scores["Điểm tổng hợp"].astype(float).tolist()
        colors = ["#db2777", "#ec4899", "#f472b6", "#f9a8d4", "#fbcfe8"][:len(regions)]

        bars = ax.bar(regions, scores, color=colors, width=0.52, edgecolor="#831843", linewidth=1.0)
        ax.set_ylim(0, 10.8)
        ax.set_ylabel("Điểm Tổng Hợp (Thang 10)", fontsize=11, fontweight="bold", color="#4a154b")
        ax.set_title("Biểu Đồ 1: Xếp Hạng Điểm Tổng Hợp Có Trọng Số Theo Địa Bàn", fontsize=13, fontweight="bold", color="#831843", pad=14)
        ax.grid(axis="y", linestyle="--", alpha=0.45, color="#f472b6")

        for bar, val in zip(bars, scores):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.22,
                f"{val:.2f}",
                ha="center",
                va="bottom",
                fontsize=11,
                fontweight="bold",
                color="#831843"
            )
        plt.tight_layout()
        fig.savefig(buf, format="png", bbox_inches="tight")
        plt.close(fig)

    elif chart_type == "radar":
        categories = ["Quy mô\n(25%)", "Nhu cầu WMS\n(25%)", "Khả thi On-site\n(25%)", "Cạnh tranh\n(15%)", "Tăng trưởng\n(10%)"]
        col_keys = ["Quy mô (25%)", "Nhu cầu WMS (25%)", "Khả thi On-site (25%)", "Cạnh tranh (15%)", "Tăng trưởng (10%)"]
        N = len(categories)
        angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(6.8, 5.5), subplot_kw=dict(polar=True), dpi=160)
        fig.patch.set_facecolor("#ffffff")
        ax.set_facecolor("#fffbfe")

        palette = ["#db2777", "#7c3aed", "#0284c7", "#059669", "#d97706"]
        for idx, row in df_scores.iterrows():
            vals = [float(row.get(k, 0)) for k in col_keys]
            vals += vals[:1]
            c = palette[idx % len(palette)]
            ax.plot(angles, vals, color=c, linewidth=2.2, label=str(row["Địa bàn"]))
            ax.fill(angles, vals, color=c, alpha=0.14)

        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=9.5, fontweight="bold", color="#4a154b")
        ax.set_ylim(0, 10)
        ax.set_title("Biểu Đồ 2: Radar 5 Chiều So Sánh Năng Lực Địa Bàn", fontsize=12.5, fontweight="bold", color="#831843", pad=20)
        ax.legend(loc="upper right", bbox_to_anchor=(1.28, 1.12), fontsize=9.5)
        plt.tight_layout()
        fig.savefig(buf, format="png", bbox_inches="tight")
        plt.close(fig)

    else:  # grouped
        fig, ax = plt.subplots(figsize=(9.5, 4.8), dpi=160)
        fig.patch.set_facecolor("#ffffff")
        ax.set_facecolor("#fdf2f8")

        regions = df_scores["Địa bàn"].astype(str).tolist()
        col_keys = ["Quy mô (25%)", "Nhu cầu WMS (25%)", "Khả thi On-site (25%)", "Cạnh tranh (15%)", "Tăng trưởng (10%)"]
        palette = ["#ec4899", "#8b5cf6", "#3b82f6", "#10b981", "#f59e0b"]

        x = np.arange(len(regions))
        width = 0.15

        for i, (col_k, color) in enumerate(zip(col_keys, palette)):
            vals = df_scores[col_k].astype(float).tolist()
            offset = (i - 2) * width
            ax.bar(x + offset, vals, width, label=col_k, color=color)

        ax.set_xticks(x)
        ax.set_xticklabels(regions, fontsize=11, fontweight="bold", color="#4a154b")
        ax.set_ylim(0, 10.8)
        ax.set_ylabel("Điểm số (1-10)", fontsize=10.5, fontweight="bold", color="#4a154b")
        ax.set_title("Biểu Đồ 3: Phân Tích Chi Tiết 5 Tiêu Chí Theo Từng Địa Bàn", fontsize=13, fontweight="bold", color="#831843", pad=14)
        ax.legend(loc="upper right", fontsize=8.5, ncol=2)
        ax.grid(axis="y", linestyle="--", alpha=0.4, color="#f472b6")
        plt.tight_layout()
        fig.savefig(buf, format="png", bbox_inches="tight")
        plt.close(fig)

    return buf.getvalue()


def _md_to_html_block(md_text: str) -> str:
    """Chuyển đổi văn bản Markdown sang HTML sạch đẹp."""
    lines = md_text.split("\n")
    out = []
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if s.startswith("### "):
            out.append(f"<h3>{s[4:]}</h3>")
        elif s.startswith("## "):
            out.append(f"<h2>{s[3:]}</h2>")
        elif s.startswith("# "):
            out.append(f"<h1>{s[2:]}</h1>")
        elif s.startswith("- "):
            content_li = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", s[2:])
            out.append(f"<li>{content_li}</li>")
        else:
            content_p = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", line)
            out.append(f"<p>{content_p}</p>")
    return "\n".join(out)


def build_standalone_report_html(
    title: str,
    report_md: str,
    plan_md: str,
    df_scores: pd.DataFrame,
    selected_charts: List[str]
) -> str:
    """
    Tạo HTML riêng cho BÁO CÁO ĐỀ XUẤT (có kèm các ảnh biểu đồ mà người dùng tích chọn để minh họa phân tích).
    """
    scores_html_table = df_scores.to_html(index=False, classes="styled-table")
    report_body = _md_to_html_block(report_md)
    plan_body = _md_to_html_block(plan_md)

    charts_html_section = ""
    chart_titles = {
        "bar": "Biểu Đồ 1: Xếp Hạng Điểm Tổng Hợp Có Trọng Số",
        "radar": "Biểu Đồ 2: Radar 5 Chiều So Sánh Năng Lực Địa Bàn",
        "grouped": "Biểu Đồ 3: Phân Tích Chi Tiết 5 Tiêu Chí Theo Địa Bàn"
    }

    if selected_charts:
        charts_items = ""
        for ch_key in selected_charts:
            png_bytes = render_chart_png_bytes(df_scores, ch_key)
            b64_img = base64.b64encode(png_bytes).decode("utf-8")
            c_title = chart_titles.get(ch_key, "Biểu đồ phân tích")
            charts_items += f"""
            <div class="report-chart-card">
                <h4>📊 {c_title}</h4>
                <img src="data:image/png;base64,{b64_img}" alt="{c_title}" />
            </div>
            """
        charts_html_section = f"""
        <h2>📈 HÌNH ẢNH BIỂU ĐỒ MINH HỌA PHÂN TÍCH TRONG BÁO CÁO</h2>
        <div class="report-charts-container">
            {charts_items}
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>{title} - Báo Cáo Đề Xuất</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Plus Jakarta Sans', 'Segoe UI', sans-serif;
            line-height: 1.7;
            color: #1e1b4b;
            background: #fdf6f9;
            padding: 28px;
            margin: 0;
        }}
        .report-paper {{
            max-width: 1050px;
            margin: auto;
            background: #ffffff;
            padding: 44px 52px;
            border-radius: 24px;
            box-shadow: 0 14px 36px rgba(131, 24, 67, 0.1);
            border: 2px solid #fce7f3;
        }}
        .doc-header {{
            border-bottom: 3px solid #f472b6;
            padding-bottom: 20px;
            margin-bottom: 28px;
        }}
        .doc-header h1 {{
            color: #831843;
            margin: 0 0 8px 0;
            font-size: 1.9rem;
        }}
        .doc-header .meta {{
            color: #701a75;
            font-weight: 600;
            font-size: 1rem;
        }}
        h2 {{
            color: #831843;
            border-left: 5px solid #ec4899;
            padding-left: 12px;
            margin-top: 32px;
            font-size: 1.4rem;
        }}
        h3 {{
            color: #4a154b;
            margin-top: 20px;
            font-size: 1.2rem;
        }}
        .styled-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 18px 0 26px 0;
            font-size: 1rem;
        }}
        .styled-table th, .styled-table td {{
            border: 1px solid #f3e8f5;
            padding: 10px 14px;
            text-align: left;
        }}
        .styled-table th {{
            background-color: #fdf2f8;
            color: #831843;
            font-weight: 700;
        }}
        .styled-table tr:nth-child(even) {{
            background-color: #fffbfe;
        }}
        .report-charts-container {{
            display: flex;
            flex-direction: column;
            gap: 24px;
            margin: 22px 0;
        }}
        .report-chart-card {{
            background: #fffafa;
            border: 1.5px solid #fbcfe8;
            border-radius: 18px;
            padding: 18px;
            text-align: center;
        }}
        .report-chart-card h4 {{
            margin: 0 0 12px 0;
            color: #831843;
            font-size: 1.1rem;
        }}
        .report-chart-card img {{
            max-width: 92%;
            height: auto;
            border-radius: 12px;
        }}
        .content-box {{
            background: #fffbfe;
            border: 1px solid #fce7f3;
            border-radius: 16px;
            padding: 22px 28px;
            margin-top: 16px;
            font-size: 1.08rem;
        }}
    </style>
</head>
<body>
    <div class="report-paper">
        <div class="doc-header">
            <h1>📄 {title}</h1>
            <div class="meta">Đơn vị: Công ty Hưng Phát WMS | Tài liệu: Báo Cáo Đề Xuất & Kế Hoạch Khảo Sát Thực Địa</div>
        </div>

        <h2>📋 BẢNG TỔNG HỢP ĐIỂM SỐ & XẾP HẠNG ĐỊA BÀN</h2>
        {scores_html_table}

        {charts_html_section}

        <h2>📑 NỘI DUNG BÁO CÁO PHÂN TÍCH & ĐỀ XUẤT</h2>
        <div class="content-box">
            {report_body}
        </div>

        <h2>📅 KẾ HOẠCH KHẢO SÁT THỰC ĐỊA TIẾP THEO</h2>
        <div class="content-box">
            {plan_body}
        </div>
    </div>
</body>
</html>"""


def build_standalone_dashboard_html(
    title: str,
    df_scores: pd.DataFrame,
    bar_html: str,
    radar_html: str,
    grouped_html: str
) -> str:
    """
    Tạo HTML riêng cho DASHBOARD BIỂU ĐỒ TƯƠNG TÁC (Executive Dashboard).
    """
    top2_list = df_scores["Địa bàn"].head(2).tolist()
    best_region = df_scores.iloc[0]["Địa bàn"] if len(df_scores) > 0 else "N/A"
    best_score = df_scores.iloc[0]["Điểm tổng hợp"] if len(df_scores) > 0 else 0
    avg_score = round(df_scores["Điểm tổng hợp"].mean(), 2) if len(df_scores) > 0 else 0
    scores_html_table = df_scores.to_html(index=False, classes="styled-table")

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>{title} - Interactive Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Plus Jakarta Sans', 'Segoe UI', sans-serif;
            background: linear-gradient(180deg, #fdf4f8 0%, #fae8f0 100%);
            color: #1e1b4b;
            padding: 24px;
            margin: 0;
        }}
        .dash-wrapper {{
            max-width: 1260px;
            margin: auto;
            background: #ffffff;
            padding: 34px 40px;
            border-radius: 26px;
            box-shadow: 0 16px 40px rgba(131, 24, 67, 0.12);
            border: 2px solid #fce7f3;
        }}
        .dash-banner {{
            background: linear-gradient(135deg, #fbcfe8 0%, #fed7aa 50%, #fecdd3 100%);
            padding: 22px 30px;
            border-radius: 20px;
            margin-bottom: 26px;
        }}
        .dash-banner h1 {{
            color: #4a154b;
            margin: 0 0 6px 0;
            font-size: 1.8rem;
        }}
        .dash-banner p {{
            color: #701a75;
            margin: 0;
            font-weight: 600;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 26px;
        }}
        .kpi-card {{
            background: #fdf2f8;
            border: 1.5px solid #fbcfe8;
            border-radius: 18px;
            padding: 16px 18px;
            text-align: center;
        }}
        .kpi-card .label {{
            font-size: 0.9rem;
            color: #64748b;
            font-weight: 700;
            text-transform: uppercase;
        }}
        .kpi-card .val {{
            font-size: 1.65rem;
            color: #831843;
            font-weight: 800;
            margin-top: 6px;
        }}
        .charts-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 22px 0;
        }}
        .chart-box {{
            background: #ffffff;
            border: 1.5px solid #fce7f3;
            border-radius: 20px;
            padding: 14px;
            box-shadow: 0 6px 20px rgba(244, 114, 182, 0.08);
        }}
        .chart-box-full {{
            background: #ffffff;
            border: 1.5px solid #fce7f3;
            border-radius: 20px;
            padding: 14px;
            margin-bottom: 22px;
            box-shadow: 0 6px 20px rgba(244, 114, 182, 0.08);
        }}
        .styled-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 14px 0 22px 0;
            font-size: 1rem;
        }}
        .styled-table th, .styled-table td {{
            border: 1px solid #f3e8f5;
            padding: 10px 14px;
            text-align: left;
        }}
        .styled-table th {{
            background-color: #fdf2f8;
            color: #831843;
            font-weight: 700;
        }}
    </style>
</head>
<body>
    <div class="dash-wrapper">
        <div class="dash-banner">
            <h1>📊 DASHBOARD TRỰC QUAN: {title}</h1>
            <p>Bảng điều khiển chỉ số KPI & Biểu đồ phân tích đa tiêu chí 4 địa bàn</p>
        </div>

        <div class="kpi-grid">
            <div class="kpi-card"><div class="label">🌍 Tổng Địa Bàn</div><div class="val">{len(df_scores)}</div></div>
            <div class="kpi-card"><div class="label">🥇 Dẫn Đầu Điểm Số</div><div class="val">{best_region} ({best_score})</div></div>
            <div class="kpi-card"><div class="label">🎯 Top 2 Đề Xuất</div><div class="val">{", ".join(top2_list)}</div></div>
            <div class="kpi-card"><div class="label">📈 Điểm Trung Bình</div><div class="val">{avg_score} / 10</div></div>
        </div>

        <div class="charts-grid">
            <div class="chart-box">{bar_html}</div>
            <div class="chart-box">{radar_html}</div>
        </div>
        <div class="chart-box-full">{grouped_html}</div>

        <h3 style="color:#831843;">📋 Bảng Dữ Liệu Chấm Điểm Trên Dashboard</h3>
        {scores_html_table}
    </div>
</body>
</html>"""


def build_docx_bytes(
    title: str,
    df_scores: pd.DataFrame,
    report_md: str = "",
    plan_md: str = "",
    chart_keys: List[str] = None,
    mode: str = "report"
) -> bytes:
    """
    Tạo file Word (.docx) chuẩn cho Báo cáo (mode='report') hoặc Dashboard (mode='dashboard').
    Nhúng trực tiếp bảng điểm và các hình ảnh biểu đồ độ phân giải cao.
    """
    doc = Document()

    # Tiêu đề chính
    heading = doc.add_heading(title, level=0)
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER

    sub = doc.add_paragraph("Đơn vị: Công ty Hưng Phát WMS — Hệ thống Đánh giá Thị trường Mở rộng")
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # 1. Bảng điểm tổng hợp
    doc.add_heading("1. Bảng Xếp Hạng & Điểm Số Đa Tiêu Chí", level=1)
    cols = list(df_scores.columns)
    table = doc.add_table(rows=1, cols=len(cols))
    table.style = "Table Grid"
    hdr_cells = table.rows[0].cells
    for i, c_name in enumerate(cols):
        hdr_cells[i].text = str(c_name)

    for _, row in df_scores.iterrows():
        row_cells = table.add_row().cells
        for i, c_name in enumerate(cols):
            row_cells[i].text = str(row[c_name])

    doc.add_paragraph("")

    # 2. Chèn các biểu đồ được chọn
    if chart_keys:
        doc.add_heading("2. Biểu Đồ Phân Tích Trực Quan", level=1)
        chart_titles = {
            "bar": "Biểu Đồ 1: Xếp Hạng Điểm Tổng Hợp Có Trọng Số",
            "radar": "Biểu Đồ 2: Radar 5 Chiều So Sánh Năng Lực Địa Bàn",
            "grouped": "Biểu Đồ 3: Phân Tích Chi Tiết 5 Tiêu Chí Theo Địa Bàn"
        }
        for ch_k in chart_keys:
            p_title = doc.add_paragraph()
            run_t = p_title.add_run(f"📊 {chart_titles.get(ch_k, 'Biểu đồ phân tích')}")
            run_t.bold = True
            png_data = render_chart_png_bytes(df_scores, ch_k)
            doc.add_picture(io.BytesIO(png_data), width=Inches(6.0))
            doc.add_paragraph("")

    # 3. Nếu là chế độ Báo cáo thì thêm nội dung Báo cáo & Kế hoạch khảo sát
    if mode == "report":
        doc.add_heading("3. Nội Dung Báo Cáo Đề Xuất Mở Rộng Thị Trường", level=1)
        for line in report_md.split("\n"):
            s = line.strip()
            if not s:
                continue
            clean_s = s.replace("**", "")
            if s.startswith("### "):
                doc.add_heading(clean_s[4:], level=3)
            elif s.startswith("## "):
                doc.add_heading(clean_s[3:], level=2)
            elif s.startswith("# "):
                doc.add_heading(clean_s[2:], level=1)
            elif s.startswith("- "):
                doc.add_paragraph(clean_s[2:], style="List Bullet")
            else:
                doc.add_paragraph(clean_s)

        doc.add_heading("4. Kế Hoạch Khảo Sát Thực Địa 4 Tuần Tiếp Theo", level=1)
        for line in plan_md.split("\n"):
            s = line.strip()
            if not s:
                continue
            clean_s = s.replace("**", "")
            if s.startswith("### "):
                doc.add_heading(clean_s[4:], level=3)
            elif s.startswith("## "):
                doc.add_heading(clean_s[3:], level=2)
            elif s.startswith("# "):
                doc.add_heading(clean_s[2:], level=1)
            elif s.startswith("- "):
                doc.add_paragraph(clean_s[2:], style="List Bullet")
            else:
                doc.add_paragraph(clean_s)

    out_buf = io.BytesIO()
    doc.save(out_buf)
    return out_buf.getvalue()


def build_pdf_bytes(
    title: str,
    df_scores: pd.DataFrame,
    report_md: str = "",
    plan_md: str = "",
    chart_keys: List[str] = None,
    mode: str = "report"
) -> bytes:
    """
    Tạo file PDF (.pdf) hỗ trợ đầy đủ Tiếng Việt Unicode + Bảng điểm + Biểu đồ phân tích bằng Matplotlib PdfPages.
    """
    pdf_buf = io.BytesIO()

    with PdfPages(pdf_buf) as pdf:
        # TRANG 1: TIÊU ĐỀ + BẢNG ĐIỂM + TÓM TẮT KPI
        fig1, ax1 = plt.subplots(figsize=(8.27, 11.69), dpi=150)
        fig1.patch.set_facecolor("#ffffff")
        ax1.axis("off")

        clean_title = re.sub(r"[^\w\s\-\—\,\.\(\)\/\:]", "", title).strip()
        ax1.text(0.5, 0.94, clean_title, fontsize=14, fontweight="bold", color="#831843", ha="center", va="top", wrap=True)
        ax1.text(0.5, 0.90, "Công ty Hưng Phát WMS — Báo Cáo & Dashboard Đánh Giá Thị Trường", fontsize=10.5, color="#4a154b", ha="center", va="top")

        # Vẽ bảng điểm trên Trang 1
        ax1.text(0.06, 0.84, "1. BẢNG XẾP HẠNG ĐIỂM SỐ ĐA TIÊU CHÍ (CÓ TRỌNG SỐ):", fontsize=11, fontweight="bold", color="#831843")

        table_ax = fig1.add_axes([0.05, 0.62, 0.90, 0.19])
        table_ax.axis("off")
        cell_text = []
        for _, r in df_scores.iterrows():
            cell_text.append([str(r[c]) for c in df_scores.columns])

        mpl_table = table_ax.table(
            cellText=cell_text,
            colLabels=list(df_scores.columns),
            loc="center",
            cellLoc="center"
        )
        mpl_table.auto_set_font_size(False)
        mpl_table.set_fontsize(7.5)
        mpl_table.scale(1.0, 1.45)

        for (row_i, col_i), cell in mpl_table.get_celld().items():
            cell.set_edgecolor("#f3e8f5")
            if row_i == 0:
                cell.set_facecolor("#fdf2f8")
                cell.set_text_props(weight="bold", color="#831843")
            else:
                cell.set_facecolor("#ffffff" if row_i % 2 == 1 else "#fffbfe")

        # Nếu có văn bản báo cáo thì in tiếp ở nửa dưới Trang 1
        if mode == "report":
            full_text = f"{report_md}\n\n{plan_md}"
            clean_lines = []
            for raw_l in full_text.split("\n"):
                s = raw_l.strip().replace("**", "").replace("## ", "").replace("### ", "")
                s = re.sub(r"[^\w\s\-\—\,\.\(\)\/\:\;\+\%\[\]]", "", s)
                if not s:
                    clean_lines.append("")
                else:
                    wrapped = textwrap.wrap(s, width=88)
                    clean_lines.extend(wrapped)

            y_cursor = 0.56
            ax1.text(0.06, 0.59, "2. NỘI DUNG PHÂN TÍCH & KẾ HOẠCH KHẢO SÁT:", fontsize=11, fontweight="bold", color="#831843")
            line_idx = 0
            while line_idx < len(clean_lines) and y_cursor > 0.06:
                ax1.text(0.06, y_cursor, clean_lines[line_idx], fontsize=9.2, color="#1e1b4b")
                y_cursor -= 0.022
                line_idx += 1

            pdf.savefig(fig1)
            plt.close(fig1)

            # Nếu còn dòng văn bản thì sang trang tiếp theo
            while line_idx < len(clean_lines):
                fig_txt, ax_txt = plt.subplots(figsize=(8.27, 11.69), dpi=150)
                fig_txt.patch.set_facecolor("#ffffff")
                ax_txt.axis("off")
                y_cursor = 0.93
                while line_idx < len(clean_lines) and y_cursor > 0.06:
                    ax_txt.text(0.06, y_cursor, clean_lines[line_idx], fontsize=9.2, color="#1e1b4b")
                    y_cursor -= 0.022
                    line_idx += 1
                pdf.savefig(fig_txt)
                plt.close(fig_txt)
        else:
            pdf.savefig(fig1)
            plt.close(fig1)

        # TRANG BIỂU ĐỒ: Vẽ các biểu đồ được chọn vào PDF
        if chart_keys:
            for ch_k in chart_keys:
                png_bytes = render_chart_png_bytes(df_scores, ch_k)
                img = plt.imread(io.BytesIO(png_bytes))
                fig_ch, ax_ch = plt.subplots(figsize=(8.27, 5.8), dpi=150)
                fig_ch.patch.set_facecolor("#ffffff")
                ax_ch.imshow(img)
                ax_ch.axis("off")
                plt.tight_layout()
                pdf.savefig(fig_ch)
                plt.close(fig_ch)

    return pdf_buf.getvalue()

