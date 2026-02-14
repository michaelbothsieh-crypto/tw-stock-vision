import { motion } from "framer-motion"
import { Activity, TrendingUp, DollarSign, ShieldCheck, AlertTriangle, Info } from "lucide-react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"

interface HealthCheckProps {
    data: {
        fScore: number | string
        zScore: number | string
        grossMargin: number | string
        netMargin: number | string
        operatingMargin: number | string
        epsGrowth: number | string
        revGrowth: number | string
        peRatio: number | string
        pegRatio: number | string
        grahamNumber: number | string
        price: number
        sma20?: number
        sma50?: number
        sma200?: number
        rsi?: number
        atr_p?: number
    }
}

export function HealthCheck({ data }: HealthCheckProps) {
    // Helper to determine score color
    const getScoreColor = (score: number, max: number) => {
        const percentage = score / max
        if (percentage >= 0.7) return "text-emerald-400"
        if (percentage >= 0.4) return "text-yellow-400"
        return "text-rose-400"
    }

    const getZScoreColor = (score: number) => {
        if (score > 2.99) return "text-emerald-400" // Safe
        if (score > 1.81) return "text-yellow-400" // Grey
        return "text-rose-400" // Distress
    }

    // Safe value conversion
    const getNum = (val: any): number => {
        if (typeof val === 'number') return val;
        const n = parseFloat(String(val));
        return isNaN(n) ? 0 : n;
    }

    const zScore = getNum(data.zScore)
    const grahamNumber = getNum(data.grahamNumber)
    const grossMargin = getNum(data.grossMargin)
    const operatingMargin = getNum(data.operatingMargin)
    const netMargin = getNum(data.netMargin)
    const peRatio = getNum(data.peRatio)
    const pegRatio = getNum(data.pegRatio)
    const fScore = getNum(data.fScore)

    const getValuationStatus = () => {
        if (grahamNumber === 0) return { text: "無法估算", color: "text-zinc-500" }
        const difference = (data.price - grahamNumber) / grahamNumber
        if (difference < -0.2) return { text: "被低估", color: "text-emerald-400" }
        if (difference > 0.2) return { text: "被高估", color: "text-rose-400" }
        return { text: "合理", color: "text-yellow-400" }
    }

    const valuation = getValuationStatus()

    // Calculate SMA Trend Score
    const getSmaScore = () => {
        let score = 0
        if (data.price > (data.sma20 || 0)) score += 33
        if (data.price > (data.sma50 || 0)) score += 33
        if (data.price > (data.sma200 || 0)) score += 34
        return score
    }
    const smaScore = getSmaScore()

    return (
        <div className="rounded-[2rem] border border-zinc-800 bg-zinc-900/40 p-5 md:p-8 backdrop-blur-md shadow-2xl overflow-hidden relative group/hero">
            <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent opacity-50 group-hover/hero:opacity-100 transition-opacity duration-700" />

            <h3 className="text-lg md:text-xl font-bold flex items-center gap-3 mb-8 text-zinc-100 relative z-10">
                <div className="p-2 rounded-xl bg-primary/10 border border-primary/20">
                    <Activity className="h-5 w-5 text-primary" />
                </div>
                AI 數據健檢
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative z-10">

                {/* 1. Daily Vitals (SMA/RSI/ATR) */}
                <div className="space-y-4 p-5 rounded-2xl bg-black/20 border border-white/5">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-[0.65rem] font-bold text-zinc-500 uppercase tracking-[0.15em] flex items-center gap-2">
                            <TrendingUp className="h-3 w-3" /> 每日健檢 Vitals
                        </span>
                    </div>

                    <div className="space-y-4">
                        <div className="p-4 rounded-2xl bg-zinc-900/60 border border-white/5 hover:border-white/10 transition-colors">
                            <div className="flex items-center justify-between mb-3">
                                <span className="text-xs text-zinc-500 font-medium tracking-tight">SMA 趨勢儀</span>
                                <span className={cn("text-xs font-bold px-2 py-0.5 rounded-full bg-black/40 border", smaScore > 60 ? "text-emerald-400 border-emerald-500/20" : smaScore > 30 ? "text-yellow-400 border-yellow-500/20" : "text-rose-400 border-rose-500/20")}>
                                    {smaScore > 60 ? "偏多" : smaScore > 30 ? "中性" : "偏空"}
                                </span>
                            </div>
                            <div className="h-2 w-full bg-zinc-800/50 rounded-full overflow-hidden shadow-inner">
                                <div className={cn("h-full transition-all duration-1000 shadow-[0_0_12px_rgba(0,0,0,0.5)]", smaScore > 60 ? "bg-emerald-500" : smaScore > 30 ? "bg-yellow-500" : "bg-rose-500")} style={{ width: `${smaScore}%` }} />
                            </div>
                            <p className="text-[0.65rem] text-zinc-600 mt-3 leading-relaxed">分析 20/50/200MA 多頭排列狀況。</p>
                        </div>

                        <div className="grid grid-cols-2 gap-3">
                            <div className="p-3 rounded-xl bg-zinc-900/40 border border-white/5">
                                <span className="text-[10px] text-zinc-500 block mb-1">RSI 強弱</span>
                                <span className={cn("text-sm font-bold", (data.rsi || 50) > 70 ? "text-rose-400" : (data.rsi || 50) < 30 ? "text-emerald-400" : "text-zinc-300")}>
                                    {data.rsi?.toFixed(1) || "-"}
                                </span>
                                <p className="text-[8px] text-zinc-600 mt-1">過熱(&gt;70)或超賣(&lt;30)。</p>
                            </div>
                            <div className="p-3 rounded-xl bg-zinc-900/40 border border-white/5">
                                <span className="text-[10px] text-zinc-500 block mb-1">ATR 波動</span>
                                <span className="text-sm font-bold text-zinc-300">
                                    ±{data.atr_p?.toFixed(2) || "-"}
                                </span>
                                <p className="text-[8px] text-zinc-600 mt-1">預估當日波動範圍。</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* 2. Financial Strength */}
                <div className="space-y-4 p-5 rounded-2xl bg-black/20 border border-white/5 flex flex-col justify-between">
                    <div className="space-y-6">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-[0.65rem] font-bold text-zinc-500 uppercase tracking-[0.15em] flex items-center gap-2">
                                <ShieldCheck className="h-3.5 w-3.5" /> 財務強度
                            </span>
                        </div>

                        <div className="space-y-5">
                            <div>
                                <div className="flex justify-between items-center mb-1.5">
                                    <div className="flex items-center gap-1.5">
                                        <span className="text-xs text-zinc-400 font-medium">F-SCORE</span>
                                        <TooltipProvider delayDuration={0}>
                                            <Tooltip>
                                                <TooltipTrigger asChild>
                                                    <button className="cursor-help outline-none">
                                                        <Info className="h-3.5 w-3.5 text-zinc-600 hover:text-primary transition-colors" />
                                                    </button>
                                                </TooltipTrigger>
                                                <TooltipContent className="max-w-[200px] text-[10px] bg-zinc-900 border-zinc-800 text-zinc-300">
                                                    Piotroski F-Score：衡量獲利能力、營運效率及財務槓桿，最高 9 分。
                                                </TooltipContent>
                                            </Tooltip>
                                        </TooltipProvider>
                                    </div>
                                    <span className={cn("font-mono font-bold text-2xl tracking-tighter", data.fScore !== undefined && data.fScore !== null ? getScoreColor(getNum(data.fScore), 9) : "text-zinc-500")}>
                                        {data.fScore !== undefined && data.fScore !== null ? getNum(data.fScore) : "-"} <span className="text-sm font-normal text-zinc-600 ml-0.5">/ 9</span>
                                    </span>
                                </div>
                                <div className="w-full bg-zinc-800/50 h-1.5 rounded-full overflow-hidden shadow-inner">
                                    <div className={cn("h-full rounded-full transition-all duration-1000", (data.fScore !== undefined && data.fScore !== null ? getScoreColor(getNum(data.fScore), 9) : "bg-zinc-700").replace('text-', 'bg-'))} style={{ width: `${(getNum(data.fScore) / 9) * 100}%` }} />
                                </div>
                            </div>

                            <div>
                                <div className="flex justify-between items-center mb-1.5">
                                    <div className="flex items-center gap-1.5">
                                        <span className="text-xs text-zinc-400 font-medium">Z-SCORE</span>
                                        <TooltipProvider delayDuration={0}>
                                            <Tooltip>
                                                <TooltipTrigger asChild>
                                                    <button className="cursor-help outline-none">
                                                        <Info className="h-3.5 w-3.5 text-zinc-600 hover:text-primary transition-colors" />
                                                    </button>
                                                </TooltipTrigger>
                                                <TooltipContent className="max-w-[200px] text-[10px] bg-zinc-900 border-zinc-800 text-zinc-300">
                                                    Altman Z-Score：破產預警指標。&gt; 2.99 為安全。
                                                </TooltipContent>
                                            </Tooltip>
                                        </TooltipProvider>
                                    </div>
                                    <span className={cn("font-mono font-bold text-2xl tracking-tighter", getZScoreColor(zScore))}>
                                        {data.zScore !== undefined && data.zScore !== null && zScore !== 0 ? zScore.toFixed(2) : "-"}
                                    </span>
                                </div>
                                <p className="text-[10px] text-zinc-500 text-right italic font-medium">
                                    {data.zScore !== undefined && data.zScore !== null && zScore !== 0 ? (zScore > 2.99 ? "財務安全" : zScore > 1.81 ? "灰色地帶" : "財務預警") : "數據缺失"}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* 3. Valuation & Margins */}
                <div className="space-y-4 p-5 rounded-2xl bg-black/20 border border-white/5 flex flex-col justify-between relative overflow-hidden group/valuation">
                    <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 via-transparent to-transparent opacity-0 group-hover/valuation:opacity-100 transition-opacity duration-500" />
                    <div className="relative z-10 w-full">
                        <div className="flex items-center justify-between mb-4">
                            <span className="text-[0.65rem] font-bold text-zinc-500 uppercase tracking-[0.15em] flex items-center gap-2">
                                <DollarSign className="h-3.5 w-3.5" /> 價值與獲利
                            </span>
                        </div>

                        <div className="space-y-4">
                            <div className="text-center py-4 rounded-2xl bg-zinc-900/60 border border-white/5 shadow-inner">
                                <div className={cn("text-2xl font-black mb-1 tracking-tight drop-shadow-sm", valuation.color)}>
                                    {valuation.text}
                                </div>
                                <div className="text-[0.65rem] text-zinc-500 uppercase font-bold tracking-[0.1em]">
                                    合理價 <span className="font-mono text-zinc-300 ml-1">{data.grahamNumber !== undefined && data.grahamNumber !== null && grahamNumber > 0.1 ? `$${grahamNumber.toLocaleString(undefined, { maximumFractionDigits: 1 })}` : "N/A"}</span>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-3">
                                <div className="p-3 rounded-xl bg-zinc-900/40 border border-white/5 text-center group/card transition-all hover:bg-zinc-900/60 shadow-sm">
                                    <div className="text-[0.65rem] text-zinc-500 font-bold uppercase mb-1 group-hover/card:text-zinc-400 transition-colors">毛利率</div>
                                    <div className="font-mono font-bold text-sm text-zinc-200">{grossMargin !== 0 ? grossMargin.toFixed(1) + "%" : "-"}</div>
                                </div>
                                <div className="p-3 rounded-xl bg-zinc-900/40 border border-white/5 text-center group/card transition-all hover:bg-zinc-900/60 shadow-sm">
                                    <div className="text-[0.65rem] text-zinc-500 font-bold uppercase mb-1 group-hover/card:text-zinc-400 transition-colors">淨利率</div>
                                    <div className={cn("font-mono font-bold text-sm", netMargin > 0 ? "text-emerald-400" : "text-rose-400")}>
                                        {netMargin !== 0 ? netMargin.toFixed(1) + "%" : "-"}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    )
}
