export const SECTOR_TRANSLATIONS: Record<string, string> = {
    "Electronic Technology": "電子科技",
    "Semiconductors": "半導體",
    "Finance": "金融服務",
    "Health Technology": "健康醫療",
    "Technology Services": "科技服務",
    "Consumer Services": "消費者服務",
    "Process Industries": "製程工業",
    "Producer Manufacturing": "生產製造",
    "Retail Trade": "零售貿易",
    "Transportation": "運輸業",
    "Commercial Services": "商業服務",
    "Utilities": "公用事業",
    "Energy Minerals": "能源礦產",
    "Consumer Non-Durables": "消費性耐久財",
    "Non-Energy Minerals": "非能源礦產",
    "Distribution Services": "分銷服務",
    "Communications": "通訊業",
    "Consumer Durables": "消費性耐用品",
    "Health Services": "醫療服務",
    "Healthcare": "健康醫療"
}

export const EXCHANGE_TRANSLATIONS: Record<string, string> = {
    "TWSE": "證交所",
    "OTC": "櫃買中心",
    "NASDAQ": "那斯達克",
    "NYSE": "紐約證交所",
    "AMEX": "美交所"
}

export const getRadarDesc = (subject: string, score: number) => {
    if (subject === "動能") {
        if (score > 70) return "多頭動能強勁"
        if (score < 30) return "動能低迷"
        return "動能中性"
    }
    if (subject === "趨勢") {
        if (score > 70) return "趨勢向上"
        if (score < 30) return "趨勢偏空"
        return "盤整格局"
    }
    if (subject === "關注") {
        if (score > 60) return "主力介入明顯"
        return "量能平淡"
    }
    if (subject === "安全") {
        if (score > 70) return "波段波動可控"
        return "波動劇烈"
    }
    if (subject === "價值") {
        if (score > 60) return "評價具有吸引力"
        return "評價稍高"
    }
    return ""
}
