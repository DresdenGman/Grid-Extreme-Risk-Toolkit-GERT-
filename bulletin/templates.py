from __future__ import annotations

TEMPLATES = {
    "title": {"en": "GERT Extreme Risk Bulletin", "cn": "GERT 极端风险通报"},
    "headers": {
        "summary": {"en": "Executive Summary", "cn": "执行摘要"},
        "analysis": {"en": "Load & Risk Analysis (Next 24h)", "cn": "负载与风险分析 (未来24小时)"},
        "advice_public": {"en": "Action Plan: Public", "cn": "行动建议：公众"},
        "advice_grid": {"en": "Action Plan: Grid Operators", "cn": "行动建议：电网运营机构"},
        "footer": {
            "en": "Rendered by GERT from the current risk snapshot. Not for official regulatory use.",
            "cn": "由 GERT 根据当前风险快照生成。仅供参考，非官方监管文件。",
        },
    },
    "risk_descriptions": {
        "LOW": {"en": "Grid conditions are stable. Standard operations.", "cn": "电网运行平稳。维持标准作业程序。"},
        "MODERATE": {"en": "Elevated load expected. Monitor reserves closely.", "cn": "预计负载升高。需密切监控备用容量。"},
        "HIGH": {
            "en": "Reserves may fall below safety margins. Voluntary conservation requested.",
            "cn": "备用容量可能跌破安全边际。建议实行自愿节能。",
        },
        "EXTREME": {
            "en": "CRITICAL EMERGENCY. Rolling blackouts probable. Immediate load shedding required.",
            "cn": "极度紧急状态。极有可能发生轮流停电。必须立即执行负荷削减。",
        },
    },
    "advice": {
        "LOW": {
            "public": [
                {"en": "No specific action required.", "cn": "无需采取特殊行动。"},
                {"en": "Monitor local news for weather updates.", "cn": "留意当地气象新闻更新。"},
            ],
            "grid": [
                {"en": "Perform routine maintenance.", "cn": "执行例行维护。"},
                {"en": "Validate forecast models.", "cn": "校准预测模型。"},
            ],
        },
        "MODERATE": {
            "public": [
                {"en": "Shift heavy appliance use to off-peak hours.", "cn": "将大功率电器使用移至非高峰时段。"},
                {"en": "Check insulation on windows/doors.", "cn": "检查门窗隔热密封情况。"},
            ],
            "grid": [
                {"en": "Cancel scheduled maintenance outages.", "cn": "取消计划内的维护停机。"},
                {"en": "Pre-warm auxiliary boilers.", "cn": "预热辅助锅炉。"},
            ],
        },
        "HIGH": {
            "public": [
                {"en": "Set thermostat to 68°F (20°C) or lower.", "cn": "将恒温器设定在 20°C 或更低。"},
                {"en": "Avoid using washing machines/dryers.", "cn": "避免使用洗衣机/烘干机。"},
                {"en": "Charge mobile devices and battery packs.", "cn": "为移动设备和充电宝充满电。"},
            ],
            "grid": [
                {"en": "Activate Demand Response (DR) programs.", "cn": "启动需求响应 (DR) 计划。"},
                {"en": "Import max available power from neighbors.", "cn": "从邻近电网最大化进口电力。"},
                {"en": "Issue public conservation alerts.", "cn": "发布公众节能预警。"},
            ],
        },
        "EXTREME": {
            "public": [
                {"en": "Prepare emergency kit (flashlights, water, food).", "cn": "准备应急包（手电筒、水、食物）。"},
                {"en": "Unplug sensitive electronics to prevent surge damage.", "cn": "拔掉敏感电子设备以防浪涌损坏。"},
                {"en": "If power is lost, keep fridge closed.", "cn": "如果停电，请保持冰箱关闭。"},
                {"en": "DO NOT use gas stoves for heating.", "cn": "严禁使用燃气灶取暖（防止一氧化碳中毒）。"},
            ],
            "grid": [
                {"en": "INITIATE TIER 3 LOAD SHEDDING.", "cn": "启动三级负荷削减（轮流停电）。"},
                {"en": "Secure critical infrastructure (hospitals, fire stations).", "cn": "保障关键基础设施（医院、消防）供电。"},
                {"en": "Deploy black-start units for contingency.", "cn": "部署黑启动机组以防万一。"},
            ],
        },
    },
}
