"""报告生成器 - HTML / PDF"""
import os
import sys
import json
from datetime import datetime
from typing import Optional


class ReportGenerator:
    """报告生成"""

    def __init__(self, output_dir: str = None, base_url: str = 'http://allenqian.online'):
        self.output_dir = output_dir or '/home/admin/sites/allenqian.online/reports'
        self.base_url = base_url
        os.makedirs(self.output_dir, exist_ok=True)

    def create_html(self, title: str, sections: list, kpis: list = None,
                    chart: str = None) -> str:
        """
        生成HTML报告

        Args:
            title: 报告标题
            sections: [{title, content, type}] 内容块
            kpis: [{label, value, trend}]
            chart: SVG 图表字符串
        """
        kpi_html = ''
        if kpis:
            kpi_cards = ''
            for k in kpis:
                trend_cls = ''
                if k.get('trend') == 'up':
                    trend_cls = 'good'
                elif k.get('trend') == 'down':
                    trend_cls = 'warn'
                kpi_cards += f'''
                <div class="kpi-card {trend_cls}">
                    <div class="label">{k['label']}</div>
                    <div class="value">{k['value']}</div>
                    <div class="sub">{k.get('sub', '')}</div>
                </div>'''
            kpi_html = f'<div class="kpi-grid">{kpi_cards}</div>'

        sections_html = ''
        for s in sections:
            sections_html += f'''
            <div class="section">
                <h2>{s['title']}</h2>
                <div class="content">{s.get('content', '')}</div>
            </div>'''

        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0d1117;color:#c9d1d9;font-family:-apple-system,BlinkMacSystemFont,"Microsoft YaHei",sans-serif;line-height:1.6}}
.container{{max-width:1000px;margin:0 auto;padding:30px 20px}}
h1{{font-size:28px;color:#f0f6fc;margin-bottom:24px}}
.kpi-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin-bottom:28px}}
.kpi-card{{background:#161b22;border:1px solid #21262d;border-radius:10px;padding:18px}}
.kpi-card .label{{font-size:11px;color:#8b949e;text-transform:uppercase;margin-bottom:6px}}
.kpi-card .value{{font-size:26px;font-weight:700;color:#f0f6fc}}
.kpi-card .sub{{font-size:12px;color:#8b949e;margin-top:4px}}
.kpi-card.warn .value{{color:#FF6B6B}}
.kpi-card.good .value{{color:#51CF66}}
.section{{background:#161b22;border:1px solid #21262d;border-radius:10px;padding:24px;margin-bottom:20px}}
.section h2{{font-size:18px;color:#e6edf3;margin-bottom:14px;padding-bottom:10px;border-bottom:1px solid #21262d}}
.content{{font-size:14px;color:#c9d1d9}}
.content table{{width:100%;border-collapse:collapse;margin:12px 0}}
.content th{{background:#21262d;color:#8b949e;text-align:left;padding:8px 12px;font-size:11px}}
.content td{{padding:8px 12px;border-bottom:1px solid #21262d}}
.footer{{text-align:center;color:#484f58;font-size:11px;margin-top:40px;padding-top:20px;border-top:1px solid #21262d}}
</style></head>
<body>
<div class="container">
<h1>{title}</h1>
{kpi_html}
{sections_html}
<div class="footer">AllenTrader v2 · Generated {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
</div>
</body></html>'''

        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        path = os.path.join(self.output_dir, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
        return f"{self.base_url}/{filename}"

    def save_to_site(self, content: str, filename: str):
        """保存文件到站点目录"""
        path = os.path.join(self.output_dir, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"{self.base_url}/{filename}"
