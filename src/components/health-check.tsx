import { motion } from "framer-motion"
import { Activity, TrendingUp, DollarSign, ShieldCheck, AlertTriangle, Info } from "lucide-react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"

interface HealthCheckProps {
    data: {
        fScore: number
        zScore: number
        grossMargin: number
        netMargin: number
        operatingMargin: number
        epsGrowth: number
        revGrowth: number
        peRatio: number
        pegRatio: number
        grahamNumber: number
        price: number
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

    const getValuationStatus = () => {
        if (data.grahamNumber === 0) return { text: "無法估算", color: "text-zinc-500" }
        const difference = (data.price - data.grahamNumber) / data.grahamNumber
        if (difference < -0.2) return { text: "被低估", color: "text-emerald-400" }
        if (difference > 0.2) return { text: "被高估", color: "text-rose-400" }
        return { text: "合理", color: "text-yellow-400" }
    }

    const valuation = getValuationStatus()

    return (
        <div className="rounded-3xl border border-zinc-800 bg-zinc-900/50 p-6 backdrop-blur-sm">
            <h3 className="text-xl font-bold flex items-center gap-2 mb-6 text-zinc-300">
                <Activity className="h-5 w-5 text-primary" />
                AI 體質健檢
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

                {/* 1. Financial Health (Scores) */}
                <div className="space-y-4 p-5 rounded-2xl bg-black/20 border border-white/5 flex flex-col justify-between">
                    <div>
                        <div className="flex items-center justify-between mb-4">
                            <span className="text-sm font-medium text-zinc-400 flex items-center gap-1">
                                <ShieldCheck className="h-4 w-4" /> 財務強度
                            </span>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <div className="flex justify-between items-center mb-1">
                                    <div className="flex items-center gap-1">
                                        <span className="text-xs text-zinc-500 uppercase">F-Score</span>
                                        <TooltipProvider>
                                            <Tooltip>
                                                <TooltipTrigger><Info className="h-3 w-3 text-zinc-600" /></TooltipTrigger>
                                                <TooltipContent className="max-w-[200px] text-[10px]">
                                                    Piotroski F-Score：衡量獲利能力、營運效率及財務槓桿，最高 9 分，越高代表體質越強。
                                                </TooltipContent>
                                            </Tooltip>
                                        </TooltipProvider>
                                    </div>
                                    <span className={cn("font-mono font-bold text-xl", getScoreColor(data.fScore, 9))}>
                                        {data.fScore} <span className="text-xs font-normal text-zinc-600">/ 9</span>
                                    </span>
                                </div>
                                <div className="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                                    <div className={cn("h-full rounded-full transition-all duration-1000", getScoreColor(data.fScore, 9).replace('text-', 'bg-'))} style={{ width: `${(data.fScore / 9) * 100}%` }} />
                                </div>
                            </div>

                            <div>
                                <div className="flex justify-between items-center mb-1">
                                    <div className="flex items-center gap-1">
                                        <span className="text-xs text-zinc-500 uppercase">Z-Score</span>
                                        <TooltipProvider>
                                            <Tooltip>
                                                <TooltipTrigger><Info className="h-3 w-3 text-zinc-600" /></TooltipTrigger>
                                                <TooltipContent className="max-w-[200px] text-[10px]">
                                                    Altman Z-Score：破產預警指標。&gt; 2.99 為安全，&lt; 1.81 為財務困窘區。
                                                </TooltipContent>
                                            </Tooltip>
                                        </TooltipProvider>
                                    </div>
                                    <span className={cn("font-mono font-bold text-xl", getZScoreColor(data.zScore))}>
                                        {data.zScore > 0 ? data.zScore.toFixed(2) : "N/A"}
                                    </span>
                                </div>
                                <p className="text-[10px] text-zinc-500 text-right italic">
                                    {data.zScore > 2.99 ? "財務安全" : data.zScore > 1.81 ? "灰色地帶" : data.zScore > 0 ? "財務預警" : "數據缺失"}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* 2. Profitability (Margins) */}
                <div className="space-y-4 p-5 rounded-2xl bg-black/20 border border-white/5">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-zinc-400 flex items-center gap-1">
                            <TrendingUp className="h-4 w-4" /> 獲利能力 (TTM)
                        </span>
                    </div>

                    <div className="space-y-4 py-2">
                        <div className="flex justify-between items-center border-b border-white/5 pb-2">
                            <span className="text-sm text-zinc-400">毛利率 (Gross)</span>
                            <span className="font-mono font-bold text-lg">{data.grossMargin !== undefined && data.grossMargin !== null ? data.grossMargin.toFixed(1) + "%" : "N/A"}</span>
                        </div>
                        <div className="flex justify-between items-center border-b border-white/5 pb-2">
                            <span className="text-sm text-zinc-400">營益率 (Operating)</span>
                            <span className="font-mono font-bold text-lg">{data.operatingMargin !== undefined && data.operatingMargin !== null ? data.operatingMargin.toFixed(1) + "%" : "N/A"}</span>
                        </div>
                        <div className="flex justify-between items-center pb-2">
                            <span className="text-sm text-zinc-400">淨利率 (Net)</span>
                            <span className={cn("font-mono font-bold text-lg", (data.netMargin || 0) > 0 ? "text-emerald-400" : "text-rose-400")}>
                                {data.netMargin !== undefined && data.netMargin !== null ? data.netMargin.toFixed(1) + "%" : "N/A"}
                            </span>
                        </div>
                    </div>
                </div>

                {/* 3. Valuation (Graham & PEG) */}
                <div className="space-y-4 p-5 rounded-2xl bg-black/20 border border-white/5">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-zinc-400 flex items-center gap-1">
                            <DollarSign className="h-4 w-4" /> 價值評估
                        </span>
                    </div>

                    <div className="text-center py-4">
                        <div className={cn("text-3xl font-bold mb-2 tracking-tight", valuation.color)}>
                            {valuation.text}
                        </div>
                        <div className="text-[10px] text-zinc-500 uppercase leading-relaxed text-balance px-2">
                            目前股價 vs 葛拉漢合理價 <br />
                            <span className="font-mono text-zinc-400 text-xs">{data.grahamNumber > 0 ? `$${data.grahamNumber.toFixed(1)}` : "數據暫缺"}</span>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-center border-t border-white/5 pt-4">
                        <div>
                            <div className="text-[10px] text-zinc-500 uppercase mb-1">P/E Ratio</div>
                            <div className="font-mono font-bold text-base text-zinc-300">{data.peRatio > 0 ? data.peRatio.toFixed(1) : "N/A"}</div>
                        </div>
                        <div>
                            <div className="text-[10px] text-zinc-500 uppercase mb-1">PEG Ratio</div>
                            <div className={cn("font-mono font-bold text-base",
                                data.pegRatio > 0 && data.pegRatio < 1 ? "text-emerald-400" :
                                    data.pegRatio > 1.5 ? "text-rose-400" : "text-zinc-300"
                            )}>{data.pegRatio > 0 ? data.pegRatio.toFixed(2) : "N/A"}</div>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    )
}
