export interface StockData {
    symbol: string;
    name?: string;
    description?: string;
    price: number;
    changePercent: number;
    volume: number;
    rsi?: number;
    rvol: number;
    sector: string;
    rating: number;
    peRatio?: number;
    pbRatio?: number;
    yield?: number;
    roe?: number;
    revGrowth?: number;
    netMargin?: number;
    currentRatio?: number;
    quickRatio?: number;
    epsGrowth?: number;
    freeCashFlow?: number;
    history?: Array<{ Date: string; Open: number; High: number; Low: number; Close: number; Volume: number; RSI?: number }>;
}
