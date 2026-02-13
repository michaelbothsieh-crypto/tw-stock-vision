"use client"

import { cn } from "@/lib/utils"

interface PredictionCardProps {
    price: number
    prediction?: {
        confidence: string
        upper: number
        lower: number
        days: number
    }
}

export function PredictionCard({ price, prediction }: PredictionCardProps) {
    if (!prediction) {
        return (
            <div className="rounded-3xl border border-border/50 bg-gradient-to-br from-blue-900/20 to-cyan-900/20 p-6 shadow-lg backdrop-blur-sm">
                <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                    <span className="text-2xl">🔮</span> AI 未來視 (Prediction)
                </h3>
                <div className="text-center text-muted-foreground py-8">數據不足無法預測</div>
            </div>
        )
    }

    return (
        <div className="rounded-3xl border border-border/50 bg-gradient-to-br from-blue-900/20 to-cyan-900/20 p-6 shadow-lg backdrop-blur-sm">
            <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <span className="text-2xl">🔮</span> AI 未來視 (Prediction)
            </h3>
            <div className="space-y-4">
                <div className="flex justify-between items-center bg-background/20 p-3 rounded-xl border border-white/5">
                    <span className="text-sm text-muted-foreground">預測信心指數</span>
                    <span className="font-bold text-cyan-400">{prediction.confidence}</span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="p-2 rounded bg-emerald-500/10 border border-emerald-500/20">
                        <div className="text-xs text-emerald-400">樂觀 (Bullish)</div>
                        <div className="font-mono font-bold">{prediction.upper.toFixed(2)}</div>
                    </div>
                    <div className="p-2 pt-4">
                        <div className="text-xs text-muted-foreground">當前</div>
                        <div className="font-mono font-bold text-lg">{price.toFixed(2)}</div>
                    </div>
                    <div className="p-2 rounded bg-rose-500/10 border border-rose-500/20">
                        <div className="text-xs text-rose-400">悲觀 (Bearish)</div>
                        <div className="font-mono font-bold">{prediction.lower.toFixed(2)}</div>
                    </div>
                </div>
                <p className="text-[10px] text-center text-muted-foreground opacity-70">
                    *基於 ATR 波動率推算未來 {prediction.days} 日潛在區間 (68% 機率)
                </p>
            </div>
        </div>
    )
}
