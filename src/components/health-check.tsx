import { motion } from "framer-motion"
import { Activity, TrendingUp, DollarSign, ShieldCheck, AlertTriangle } from "lucide-react"
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
                <div className="space-y-4 p-4 rounded-2xl bg-black/20 border border-white/5">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-zinc-400 flex items-center gap-1">
                            <ShieldCheck className="h-4 w-4" /> 財務強度
                        </span>
                    </div>

                    <div className="flex justify-between items-center">
                        <span className="text-sm">Piotroski F-Score</span>
                        <span className={cn("font-mono font-bold text-lg", getScoreColor(data.fScore, 9))}>
                            {data.fScore} / 9
                        </span>
                    </div>
                    <div className="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                        <div className={cn("h-full rounded-full", getScoreColor(data.fScore, 9).replace('text-', 'bg-'))} style={{ width: `${(data.fScore / 9) * 100}%` }} />
                    </div>

                    <div className="flex justify-between items-center mt-2">
                        <span className="text-sm">Altman Z-Score</span>
                        <span className={cn("font-mono font-bold text-lg", getZScoreColor(data.zScore))}>
                            {data.zScore.toFixed(2)}
                        </span>
                    </div>
                    <p className="text-xs text-zinc-500 text-right">
                        {data.zScore > 2.99 ? "財務安全" : data.zScore > 1.81 ? "灰色地帶" : "財務預警"}
                    </p>
                </div>

                {/* 2. Profitability (Margins) */}
                <div className="space-y-4 p-4 rounded-2xl bg-black/20 border border-white/5">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-zinc-400 flex items-center gap-1">
                            <TrendingUp className="h-4 w-4" /> 獲利能力 (TTM)
                        </span>
                    </div>

                    <div className="space-y-3">
                        <div className="flex justify-between text-sm">
                            <span className="text-zinc-400">毛利率 (Gross)</span>
                            <span className="font-mono font-bold">{data.grossMargin.toFixed(1)}%</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span className="text-zinc-400">營益率 (Operating)</span>
                            <span className="font-mono font-bold">{data.operatingMargin.toFixed(1)}%</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span className="text-zinc-400">淨利率 (Net)</span>
                            <span className={cn("font-mono font-bold", data.netMargin > 0 ? "text-emerald-400" : "text-rose-400")}>
                                {data.netMargin.toFixed(1)}%
                            </span>
                        </div>
                    </div>
                </div>

                {/* 3. Valuation (Graham & PEG) */}
                <div className="space-y-4 p-4 rounded-2xl bg-black/20 border border-white/5">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-zinc-400 flex items-center gap-1">
                            <DollarSign className="h-4 w-4" /> 價值評估
                        </span>
                    </div>

                    <div className="text-center py-2">
                        <div className={cn("text-2xl font-bold mb-1", valuation.color)}>
                            {valuation.text}
                        </div>
                        <div className="text-xs text-zinc-500">
                            目前股價 vs 葛拉漢合理價 <span className="font-mono ml-1">${data.grahamNumber > 0 ? data.grahamNumber.toFixed(1) : "N/A"}</span>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-center border-t border-white/5 pt-2">
                        <div>
                            <div className="text-xs text-zinc-500">P/E Ratio</div>
                            <div className="font-mono font-bold text-sm text-zinc-300">{data.peRatio > 0 ? data.peRatio.toFixed(1) : "N/A"}</div>
                        </div>
                        <div>
                            <div className="text-xs text-zinc-500">PEG Ratio</div>
                            <div className={cn("font-mono font-bold text-sm",
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
