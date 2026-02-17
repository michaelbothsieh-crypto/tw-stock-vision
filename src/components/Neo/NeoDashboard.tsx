import React, { useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { StockChart } from './StockChart';
import { fmtNum, fmtPct, trunc2 } from '@/lib/visual-utils';
import { StockData } from './types';
import { MarketOverview } from './modules/MarketOverview';
import { FocusMetrics } from './modules/FocusMetrics';



interface NeoDashboardProps {
    data: StockData[];
    onSelect: (symbol: string) => void;
    currentSymbol: string;
    market: 'TW' | 'US';
    onMarketChange: (m: 'TW' | 'US') => void;
}

type PeriodKey = '1D' | '1M' | '3M' | '6M' | '1Y' | '5Y';

const PERIOD_MAP: Record<PeriodKey, { period: string; interval: string }> = {
    '1D': { period: '1d', interval: '5m' },
    '1M': { period: '1mo', interval: '1d' },
    '3M': { period: '3mo', interval: '1d' },
    '6M': { period: '6mo', interval: '1d' },
    '1Y': { period: '1y', interval: '1d' },
    '5Y': { period: '5y', interval: '1wk' },
};



const HOLIDAYS_2026 = [
    '2026-01-01', // 元旦
    '2026-02-16', '2026-02-17', '2026-02-18', '2026-02-19', '2026-02-20', // 春節
    '2026-02-28', // 228
    '2026-04-03', '2026-04-06', // 清明
    '2026-05-01', // 勞動節
    '2026-06-19', // 端午
    '2026-09-25', // 中秋
    '2026-10-10', // 國慶
];

const getMarketStatus = (market: 'TW' | 'US') => {
    const now = new Date();
    const day = now.getDay(); // 0(Sun) - 6(Sat)
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const date = String(now.getDate()).padStart(2, '0');
    const dateStr = `${year}-${month}-${date}`;

    // 週末非交易日
    if (day === 0 || day === 6) return { label: '週末休市', isOpen: false };

    // 國定假日 (僅適用台股，美股需另外定義但暫時共用邏輯或忽略)
    if (market === 'TW' && HOLIDAYS_2026.includes(dateStr)) {
        return { label: '國定休市', isOpen: false };
    }

    const hour = now.getHours();
    const min = now.getMinutes();
    const timeVal = hour * 100 + min;

    if (market === 'TW') {
        // 台股: 09:00 - 13:30 (開盤), 13:30 - 14:30 (盤後)
        if (timeVal >= 900 && timeVal < 1330) return { label: '交易中', isOpen: true };
        if (timeVal >= 1330 && timeVal < 1430) return { label: '盤後交易', isOpen: false };
        return { label: '已收盤', isOpen: false };
    } else {
        // 美股冬令: 22:30 - 05:00 (+1 day)
        // 22:30 之後 或 05:00 之前
        if (timeVal >= 2230 || timeVal < 500) return { label: '交易中', isOpen: true };
        if (timeVal >= 500 && timeVal < 900) return { label: '盤後交易', isOpen: false };
        return { label: '已收盤', isOpen: false };
    }
};

const TerminalHeader = ({ lastUpdate, market }: { lastUpdate: string; market: 'TW' | 'US' }) => {
    const status = getMarketStatus(market);
    return (
        <div className="flex items-center justify-between border-b border-white/10 bg-black/50 px-4 py-2 font-mono text-xs text-zinc-500 backdrop-blur-md">
            <div className="flex items-center gap-4">
                <span className="flex items-center gap-1.5 text-emerald-500">
                    <span className="relative flex h-2 w-2">
                        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
                        <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
                    </span>
                    系統上線
                </span>
                <span>資料來源: TV / YF</span>
                <span className="flex items-center gap-1.5">
                    市場狀態:
                    <span className={cn("px-1.5 py-0.5 rounded", status.isOpen ? "bg-emerald-500/10 text-emerald-400" : "bg-zinc-800 text-zinc-400")}>
                        {status.label}
                    </span>
                </span>
            </div>
            <div className="flex items-center gap-4">
                <span className="text-zinc-600">v1.2</span>
                <span>最後更新: {lastUpdate}</span>
            </div>
        </div>
    );
};

const ProTicker = ({ data }: { data: StockData[] }) => {
    return (
        <div className="fixed bottom-0 left-0 right-0 z-50 flex h-8 items-center overflow-hidden border-t border-white/10 bg-black text-xs font-mono">
            <motion.div
                className="flex gap-8 whitespace-nowrap px-4"
                animate={{ x: [0, -1000] }}
                transition={{ duration: 30, repeat: Infinity, ease: 'linear' }}
            >
                {[...data, ...data].map((stock, i) => (
                    <div key={`${stock.symbol}-${i}`} className="flex items-center gap-2">
                        <span className="font-bold text-zinc-300">{stock.symbol}</span>
                        <span className={stock.changePercent >= 0 ? 'text-emerald-400' : 'text-rose-500'}>
                            {fmtNum(stock.price)} ({fmtPct(stock.changePercent)})
                        </span>
                    </div>
                ))}
            </motion.div>
        </div>
    );
};









export const NeoDashboard = ({ data, currentSymbol, onSelect, market, onMarketChange }: NeoDashboardProps) => {
    const [time, setTime] = useState('');
    const [chartData, setChartData] = useState<any[]>([]);
    const [detailedName, setDetailedName] = useState<string>('');
    const [loadingChart, setLoadingChart] = useState(false);
    const [detailBySymbol, setDetailBySymbol] = useState<Record<string, Partial<StockData>>>({});
    const [periodKey, setPeriodKey] = useState<PeriodKey>('1Y');
    const [searchTerm, setSearchTerm] = useState('');

    const handleSearch = (term: string) => {
        if (!term) return;
        onSelect(term);
        setSearchTerm('');
    };

    const enrichedData = useMemo(
        () => data.map((item) => ({ ...item, ...(detailBySymbol[item.symbol] || {}) })),
        [data, detailBySymbol]
    );

    const selectedStock = useMemo(
        () => enrichedData.find((s) => s.symbol === currentSymbol) || data.find((s) => s.symbol === currentSymbol) || enrichedData[0],
        [enrichedData, data, currentSymbol]
    );

    useEffect(() => {
        const interval = setInterval(() => {
            setTime(new Date().toLocaleTimeString('zh-TW', { hour12: false }));
        }, 1000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        if (!currentSymbol) return;

        const fetchDetails = async () => {
            setLoadingChart(true);
            setChartData([]);
            setDetailedName('');
            try {
                const cfg = PERIOD_MAP[periodKey];
                const res = await fetch(`/api/stock?symbol=${currentSymbol}&period=${cfg.period}&interval=${cfg.interval}`);
                if (!res.ok) throw new Error('Failed to fetch details');
                const json = await res.json();

                if (Array.isArray(json.history)) {
                    setChartData(json.history);
                }

                const detail = { ...json };
                delete detail.history;
                setDetailBySymbol((prev) => ({ ...prev, [currentSymbol]: detail }));

                if (json.description || json.name) {
                    setDetailedName(json.description || json.name);
                }
            } catch (error) {
                console.error('Chart data error:', error);
            } finally {
                setLoadingChart(false);
            }
        };

        fetchDetails();
    }, [currentSymbol, periodKey]);

    if (!enrichedData.length) {
        return <div className="flex h-screen items-center justify-center font-mono text-zinc-500">系統初始化中 (INITIALIZING)...</div>;
    }

    return (
        <div className="flex min-h-screen flex-col bg-[#050505] text-white selection:bg-emerald-500/30 lg:h-screen lg:overflow-hidden">
            <TerminalHeader lastUpdate={time} market={market} />

            {/* Mobile Search Bar - Sticky Top */}
            <div className="sticky top-0 z-30 block border-b border-white/10 bg-zinc-900/80 p-2 backdrop-blur lg:hidden">
                <div className="relative">
                    <input
                        type="text"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value.toUpperCase())}
                        placeholder="搜尋代號 (如 2330, NVDA)..."
                        className="w-full rounded bg-zinc-950 py-2 pl-9 pr-4 text-sm text-zinc-200 placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-emerald-500/50"
                        onKeyDown={(e) => e.key === 'Enter' && handleSearch(searchTerm)}
                    />
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                </div>
            </div>

            <div className="flex flex-1 flex-col pb-16 lg:grid lg:grid-cols-12 lg:overflow-hidden lg:pb-8">
                {/* Mobile Order: 1. Chart, 2. Metrics, 3. List */}

                {/* 1. Chart Area (Mobile First Order) */}
                <div className="relative order-1 flex min-h-[400px] flex-col items-center justify-center border-b border-white/10 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-zinc-900/50 to-black lg:order-2 lg:col-span-5 lg:h-full lg:border-b-0 lg:border-r">
                    <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:40px_40px]" />

                    <div className="relative z-10 h-full w-full p-4">
                        {loadingChart ? (
                            <div className="absolute inset-0 flex items-center justify-center">
                                <span className="animate-pulse font-mono text-xs text-emerald-500">載入歷史數據中 (FETCHING)...</span>
                            </div>
                        ) : (
                            <div className="h-[300px] w-full lg:h-[calc(100%-40px)]">
                                <StockChart data={chartData} color={selectedStock?.changePercent >= 0 ? '#10b981' : '#f43f5e'} />
                            </div>
                        )}

                        <div className="absolute bottom-4 left-0 right-0 flex justify-center gap-2 overflow-x-auto px-4 pb-2 lg:pb-0">
                            {(Object.keys(PERIOD_MAP) as PeriodKey[]).map((key) => (
                                <button
                                    key={key}
                                    onClick={() => setPeriodKey(key)}
                                    className={cn(
                                        'shrink-0 rounded border border-white/10 px-3 py-1 font-mono text-xs transition-colors',
                                        periodKey === key
                                            ? 'border-white/20 bg-white/10 text-white'
                                            : 'bg-white/5 text-zinc-400 hover:bg-white/10 hover:text-white'
                                    )}
                                >
                                    {key}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                {/* 2. Focus Metrics */}
                <div className="order-2 border-b border-white/10 bg-zinc-950/30 lg:order-1 lg:col-span-4 lg:h-full lg:border-b-0 lg:border-r lg:overflow-y-auto">
                    <FocusMetrics stock={selectedStock} detailedName={detailedName} chartData={chartData} />
                </div>

                {/* 3. Market Overview */}
                <div className="order-3 min-h-[400px] bg-zinc-950/50 lg:order-3 lg:col-span-3 lg:h-full lg:overflow-hidden">
                    <div className="lg:hidden p-4 text-center text-xs text-zinc-500">
                        ↓ 下方為市場總覽列表 ↓
                    </div>
                    <MarketOverview
                        data={enrichedData}
                        onSelect={onSelect}
                        currentSymbol={selectedStock?.symbol}
                        market={market}
                        onMarketChange={onMarketChange}
                        className="lg:h-full"
                    />
                </div>
            </div>

            <div className="hidden lg:block">
                <ProTicker data={enrichedData} />
            </div>
        </div>
    );
};
