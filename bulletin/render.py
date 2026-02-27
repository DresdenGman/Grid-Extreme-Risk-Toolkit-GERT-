from __future__ import annotations

import base64
import io
from datetime import datetime
from typing import Dict, List

import matplotlib

matplotlib.use("Agg")  # Non-interactive backend for server
import matplotlib.pyplot as plt


def render_charts(context: Dict[str, object]) -> Dict[str, str]:
    """
    Rendering step: creates chart images, returns them as base64 strings.
    Kept separate to allow alternate chart backends in the future.
    """
    hours = context["hours"]
    p50 = context["p50"]
    p99 = context["p99"]
    capacity = context["capacity"]
    return {"main_chart_b64": _generate_chart_base64(hours, p50, p99, capacity)}


def _generate_chart_base64(hours: List[int], p50: List[float], p99: List[float], capacity: List[float]) -> str:
    plt.figure(figsize=(10, 4), dpi=100)
    plt.plot(hours, p99, color="#dc2626", label="P99 Extreme Load (Risk)", linewidth=2)
    plt.plot(hours, p50, color="#4f46e5", label="P50 Median Load", linewidth=2, linestyle="--")
    plt.plot(hours, capacity, color="#16a34a", label="Grid Capacity", linewidth=2, linestyle=":")
    plt.fill_between(hours, p50, p99, color="#dc2626", alpha=0.1)

    plt.title("24-Hour Quantile Forecast vs. Capacity", fontsize=12, fontweight="bold")
    plt.xlabel("Hour of Day")
    plt.ylabel("Load (MW)")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(loc="upper left")
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    data = base64.b64encode(buf.read()).decode("utf-8")
    plt.close()
    return data


def render_html(context: Dict[str, object], images: Dict[str, str]) -> str:
    """
    Rendering step: HTML composition only (still pure).
    """
    t = context["templates"]
    risk_level = context["risk_level"]
    risk_color = context["risk_color"]
    issued_at: datetime = context["issued_at"]  # type: ignore[assignment]
    date_str = issued_at.strftime("%Y-%m-%d %H:%00")
    chart_b64 = images["main_chart_b64"]

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>GERT Bulletin</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            @media print {{
                body {{ -webkit-print-color-adjust: exact; }}
                .no-print {{ display: none; }}
            }}
            body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background: white; color: #1f2937; }}
        </style>
    </head>
    <body class="p-8 max-w-4xl mx-auto border-t-8" style="border-color: {risk_color}">
        <div class="flex justify-between items-start mb-8 border-b pb-4">
            <div>
                <h1 class="text-3xl font-bold text-slate-900">{t['title']['en']}</h1>
                <h2 class="text-xl text-slate-600">{t['title']['cn']}</h2>
            </div>
            <div class="text-right">
                <div class="text-sm text-slate-500">ISSUED / 发布时间</div>
                <div class="font-mono font-bold text-lg">{date_str}</div>
                <div class="mt-2 inline-block px-3 py-1 text-white font-bold rounded" style="background-color: {risk_color}">
                    LEVEL: {risk_level}
                </div>
            </div>
        </div>

        <section class="mb-8 bg-slate-50 p-6 rounded-lg border-l-4" style="border-color: {risk_color}">
            <h3 class="text-sm font-bold uppercase text-slate-500 mb-2">{t['headers']['summary']['en']} / {t['headers']['summary']['cn']}</h3>
            <p class="text-lg font-medium mb-2">{t['risk_descriptions'][risk_level]['en']}</p>
            <p class="text-lg font-medium text-slate-600">{t['risk_descriptions'][risk_level]['cn']}</p>
        </section>

        <section class="mb-8">
            <h3 class="text-sm font-bold uppercase text-slate-500 mb-4">{t['headers']['analysis']['en']} / {t['headers']['analysis']['cn']}</h3>
            <div class="border rounded p-2">
                <img src="data:image/png;base64,{chart_b64}" class="w-full" alt="Risk Chart">
            </div>
            <p class="text-xs text-center text-slate-400 mt-2">
                Red Line: P99 Extreme Scenario (1% Probability) | Green Line: Total Available Capacity
            </p>
        </section>

        <div class="grid grid-cols-2 gap-8 mb-8">
            <div>
                <h3 class="text-lg font-bold border-b-2 border-slate-200 pb-2 mb-4">
                    🏢 {t['headers']['advice_public']['en']}<br>
                    <span class="text-sm font-normal text-slate-500">{t['headers']['advice_public']['cn']}</span>
                </h3>
                <ul class="space-y-3">
                    {''.join([f'<li class="flex items-start"><span class="mr-2 text-blue-500">●</span><div><div class="font-medium">{item["en"]}</div><div class="text-sm text-slate-500">{item["cn"]}</div></div></li>' for item in t['advice'][risk_level]['public']])}
                </ul>
            </div>

            <div>
                <h3 class="text-lg font-bold border-b-2 border-slate-200 pb-2 mb-4">
                    ⚡ {t['headers']['advice_grid']['en']}<br>
                    <span class="text-sm font-normal text-slate-500">{t['headers']['advice_grid']['cn']}</span>
                </h3>
                <ul class="space-y-3">
                    {''.join([f'<li class="flex items-start"><span class="mr-2 text-red-500">●</span><div><div class="font-medium">{item["en"]}</div><div class="text-sm text-slate-500">{item["cn"]}</div></div></li>' for item in t['advice'][risk_level]['grid']])}
                </ul>
            </div>
        </div>

        <div class="text-center text-xs text-slate-400 mt-12 pt-4 border-t">
            {t['headers']['footer']['en']}<br>{t['headers']['footer']['cn']}
        </div>

        <div class="no-print mt-6 text-center">
            <button onclick="window.print()" class="bg-indigo-600 text-white px-6 py-2 rounded hover:bg-indigo-700">Print / Save as PDF</button>
        </div>
    </body>
    </html>
    """
    return html

