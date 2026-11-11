"""
Academic Report to PDF Compiler
================================
Converts Final_Report.md into a publication-grade, IEEE/ACM-styled PDF
complete with embedded figures, tables, authors card, and academic typography.
Uses Chrome / Edge headless printing for pixel-perfect PDF rendering.
"""

import os
import sys
import base64
import subprocess
import markdown


def image_to_base64(img_path: str) -> str:
    """Encodes an image file to base64 data URI."""
    if not os.path.exists(img_path):
        return ""
    with open(img_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    ext = os.path.splitext(img_path)[1].replace(".", "").lower()
    return f"data:image/{ext};base64,{encoded}"


def build_academic_html(md_content: str, figures_dir: str) -> str:
    """Converts markdown to full HTML document with academic stylesheet."""
    # Convert markdown tables, fenced code, and attrs
    md_parser = markdown.Markdown(extensions=["tables", "fenced_code", "attr_list"])
    html_body = md_parser.convert(md_content)

    # Embed figures directly via Base64 data URIs
    fig1_b64 = image_to_base64(os.path.join(figures_dir, "fig1_energy_per_operation_by_algorithm.png"))
    fig2_b64 = image_to_base64(os.path.join(figures_dir, "fig2_21day_power_and_thermal_trend.png"))
    fig3_b64 = image_to_base64(os.path.join(figures_dir, "fig3_regression_model_energy_scaling.png"))

    html_body = html_body.replace('src="figures/fig1_energy_per_operation_by_algorithm.png"', f'src="{fig1_b64}"')
    html_body = html_body.replace('src="figures/fig2_21day_power_and_thermal_trend.png"', f'src="{fig2_b64}"')
    html_body = html_body.replace('src="figures/fig3_regression_model_energy_scaling.png"', f'src="{fig3_b64}"')

    # Full styled HTML document
    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Final Report: Energy-per-Computation Benchmarking Tool for Software</title>
<style>
    @page {{
        size: A4;
        margin: 14mm 13mm 14mm 13mm;
        @bottom-right {{
            content: "Page " counter(page);
            font-size: 8pt;
            color: #666;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        @bottom-left {{
            content: "SRM Institute of Science and Technology | SEE Course Project";
            font-size: 8pt;
            color: #666;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
    }}

    body {{
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
        font-size: 8.9pt;
        line-height: 1.36;
        color: #212529;
        background-color: #ffffff;
        margin: 0;
        padding: 0;
    }}

    /* Header & Institutional Branding */
    .report-header {{
        border-bottom: 2px solid #1565C0;
        padding-bottom: 8px;
        margin-bottom: 10px;
    }}
    .institution-title {{
        font-size: 13pt;
        font-weight: bold;
        color: #0D47A1;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 2px;
    }}
    .department-title {{
        font-size: 9.8pt;
        font-weight: 600;
        color: #37474F;
        margin-bottom: 6px;
    }}
    h1 {{
        font-size: 14.5pt;
        font-weight: 700;
        color: #0D47A1;
        line-height: 1.22;
        margin-top: 6px;
        margin-bottom: 8px;
    }}

    /* Authors Badge Card */
    .authors-card {{
        background-color: #F8F9FA;
        border: 1px solid #CFD8DC;
        border-left: 3.5px solid #1E88E5;
        border-radius: 4px;
        padding: 7px 12px;
        margin-bottom: 10px;
        display: flex;
        flex-wrap: wrap;
        gap: 10px 20px;
    }}
    .author-item {{
        font-size: 8.8pt;
    }}
    .author-name {{
        font-weight: 700;
        color: #1A237E;
    }}
    .author-reg {{
        font-family: 'Consolas', 'Courier New', monospace;
        color: #455A64;
        font-weight: 600;
    }}

    /* Headings */
    h2 {{
        font-size: 11.2pt;
        font-weight: 700;
        color: #1565C0;
        border-bottom: 1px solid #E0E0E0;
        padding-bottom: 3px;
        margin-top: 14px;
        margin-bottom: 6px;
        page-break-after: avoid;
    }}
    h3 {{
        font-size: 9.8pt;
        font-weight: 700;
        color: #2E7D32;
        margin-top: 10px;
        margin-bottom: 4px;
        page-break-after: avoid;
    }}
    h4 {{
        font-size: 9.2pt;
        font-weight: 600;
        color: #C62828;
        margin-top: 8px;
        margin-bottom: 3px;
        page-break-after: avoid;
    }}

    p {{
        margin-top: 0;
        margin-bottom: 6px;
        text-align: justify;
    }}

    /* Tables */
    table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 6px;
        margin-bottom: 8px;
        font-size: 8.0pt;
        page-break-inside: avoid;
    }}
    th {{
        background-color: #ECEFF1;
        color: #263238;
        font-weight: 700;
        text-align: left;
        padding: 3.5px 5px;
        border: 1px solid #B0BEC5;
    }}
    td {{
        padding: 3px 5px;
        border: 1px solid #CFD8DC;
        vertical-align: middle;
    }}
    tr:nth-child(even) td {{
        background-color: #F8F9FA;
    }}

    /* Blockquotes / Callout Boxes */
    blockquote {{
        background-color: #E8F5E9;
        border-left: 3.5px solid #2E7D32;
        margin: 6px 0;
        padding: 5px 10px;
        font-size: 8.6pt;
        color: #1B5E20;
        border-radius: 0 4px 4px 0;
    }}
    blockquote p {{
        margin: 0;
    }}

    /* Figures */
    img {{
        max-width: 82%;
        height: auto;
        display: block;
        margin: 5px auto;
        border: 1px solid #E0E0E0;
        border-radius: 4px;
        page-break-inside: avoid;
    }}
    em {{
        display: block;
        text-align: center;
        font-size: 8.0pt;
        color: #546E7A;
        margin-top: 2px;
        margin-bottom: 8px;
    }}

    /* Code & Formulas */
    code {{
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 8.2pt;
        background-color: #ECEFF1;
        padding: 1px 3px;
        border-radius: 3px;
        color: #C2185B;
    }}
    pre {{
        background-color: #263238;
        color: #ECEFF1;
        padding: 6px 10px;
        border-radius: 4px;
        font-size: 7.8pt;
        overflow-x: auto;
        margin: 6px 0;
    }}
    pre code {{
        background-color: transparent;
        color: #80CBC4;
        padding: 0;
    }}

    hr {{
        border: none;
        border-top: 1px solid #ECEFF1;
        margin: 10px 0;
    }}

    /* Clean Page Breaks */
    .page-break {{
        page-break-before: always;
    }}
</style>
</head>
<body>

<div class="report-header">
    <div class="institution-title">SRM Institute of Science and Technology</div>
    <div class="department-title">Department of Computer Science & Engineering | Course: Sustainable Energy Engineering (SEE)</div>
    <h1>Energy-per-Computation Benchmarking Tool for Software & Green Coding Guidelines</h1>
    <div class="authors-card">
        <div class="author-item">
            <span class="author-name">Sathvik S Rao</span><br>
            <span class="author-reg">RA2311003050063</span>
        </div>
        <div class="author-item">
            <span class="author-name">Shayantan Bose</span><br>
            <span class="author-reg">RA2311003050062</span>
        </div>
        <div class="author-item">
            <span class="author-name">Ansh Baiju</span><br>
            <span class="author-reg">RA2311003050041</span>
        </div>
        <div class="author-item" style="margin-left: auto;">
            <strong>Academic Term:</strong> 2026–2027<br>
            <strong>Testbed Host:</strong> 12th Gen Intel Core i7-12700H (45W TDP)
        </div>
    </div>
</div>

{html_body}

</body>
</html>"""
    return html_doc


def find_browser_executable() -> str:
    """Finds path to Google Chrome or Microsoft Edge executable."""
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("Neither Google Chrome nor Microsoft Edge was found on system.")


def convert_to_pdf(html_path: str, pdf_path: str):
    """Executes browser headless printing to PDF."""
    browser_path = find_browser_executable()
    print(f"[*] Compiling PDF using browser engine: {browser_path}")

    # Use file:// URI for local HTML
    file_uri = f"file:///{os.path.abspath(html_path).replace(os.sep, '/')}"

    cmd = [
        browser_path,
        "--headless=new",
        "--disable-gpu",
        "--allow-file-access-from-files",
        "--run-all-compositor-stages-before-draw",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        file_uri,
    ]

    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f"[+] Final Report PDF generated successfully: {pdf_path}")


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    md_path = os.path.join(base_dir, "Final_Report.md")
    figures_dir = os.path.join(base_dir, "figures")
    html_out = os.path.join(base_dir, "Final_Report.html")
    pdf_out = os.path.join(base_dir, "Final_Report.pdf")

    if not os.path.exists(md_path):
        print(f"[!] Final_Report.md not found at: {md_path}")
        return

    print(f"[*] Reading markdown report: {md_path}")
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    print("[*] Generating academic styled HTML document...")
    html_content = build_academic_html(md_text, figures_dir)

    with open(html_out, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[+] Intermediate HTML created: {html_out}")

    print("[*] Rendering high-resolution PDF...")
    convert_to_pdf(html_out, pdf_out)

    if os.path.exists(pdf_out):
        size_kb = os.path.getsize(pdf_out) / 1024.0
        print(f"[+] Final Report PDF Ready: {pdf_out} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
