/**
 * 視覺化數據工具函數
 * 用於處理雷達圖與儀表板的數值映射與標準化
 */

/**
 * 將數值標準化為 0-100 區間
 * @param value 原始數值
 * @param min 最小值
 * @param max 最大值
 * @param reverse 是否反轉 (如 PE，小數字代表更強)
 */
export const normalize = (value: number | undefined | null, min: number, max: number, reverse = false): number => {
    if (value === undefined || value === null || Number.isNaN(Number(value)) || value <= 0) {
        // 對於本益比等指標，0 或負數通常代表虧損或無數據，給予最低分
        return 0;
    }
    const v = Number(value);

    // 箝位元處理
    const clamped = Math.min(Math.max(v, min), max);
    let normalized = ((clamped - min) / (max - min)) * 100;

    if (reverse) {
        normalized = 100 - normalized;
    }

    return Math.max(0, normalized);
};

/**
 * 定義五維度雷達圖的數據源映射
 */
export const getRadarData = (stock: any) => {
    return [
        { subject: '價值 (Value)', A: normalize(stock.peRatio, 0, 50, true), fullMark: 100 },
        { subject: '獲利 (Profit)', A: normalize(stock.roe, 0, 30), fullMark: 100 },
        { subject: '增長 (Growth)', A: normalize(stock.epsGrowth, 0, 50), fullMark: 100 },
        { subject: '回饋 (Return)', A: normalize(stock.yield, 0, 8), fullMark: 100 },
        { subject: '安全 (Safety)', A: normalize(stock.currentRatio, 100, 300), fullMark: 100 },
    ];
};

/**
 * 根據數值獲取狀態色彩
 */
export const getStatusColor = (value: number, type: 'RVOL' | 'RSI') => {
    if (type === 'RVOL') {
        if (value >= 2.0) return '#f43f5e'; // 爆量紅
        if (value >= 1.2) return '#22d3ee'; // 溫和藍
        return '#71717a'; // 量縮灰
    }
    if (type === 'RSI') {
        if (value > 70) return '#00ffbb'; // 超買螢光綠
        if (value < 30) return '#64748b'; // 超賣灰藍
        return '#10b981'; // 常態綠
    }
    return '#10b981';
};

/**
 * 數值截斷 (無條件捨去至小數第 2 位)
 */
export const trunc2 = (value: number | undefined | null) => {
    if (value === undefined || value === null || Number.isNaN(Number(value))) return 0;
    return Math.trunc(Number(value) * 100) / 100;
};

/**
 * 格式化數值 (帶截斷邏輯)
 */
export const fmtNum = (value: number | undefined | null, digits = 2) => {
    if (value === undefined || value === null || Number.isNaN(Number(value))) return '--';
    const v = Number(value);
    if (v <= 0) return '--';
    const factor = Math.pow(10, digits);
    return (Math.trunc(v * factor) / factor).toFixed(digits);
};

/**
 * 格式化百分比 (帶正負號與顏色邏輯所需數值)
 */
export const fmtPct = (value: number | undefined | null, withSign = true) => {
    const v = trunc2(value);
    const sign = withSign && v > 0 ? '+' : '';
    return `${sign}${v.toFixed(2)}%`;
};
