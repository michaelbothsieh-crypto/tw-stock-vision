"use client"

import { useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Brain, Zap, History, ChevronRight, Activity, Target, HelpCircle, X } from "lucide-react"
import { AI_RadarChart } from "./ui/radar-chart"
import { cn } from "@/lib/utils"

interface PerformanceTracking {
    total_predictions: number
    resolved: number
    pending: number
    accuracy_stats: {
        accuracy: number | null
        sample_size: number
        avg_return: number | null
        message?: string
    }
}

interface EvolutionState {
    version: string
    last_updated: string
    strategies: {
        [key: string]: {
            name: string
            description: string
            weights: { [key: string]: number }
            performance_history: any[]
        }
    }
    performance_tracking?: PerformanceTracking
    market_regime?: string
    strategy_config?: {
        strategies: {
            [key: string]: {
                name?: string
                rsi_threshold?: number
                f_score_min?: number
                weights?: { [key: string]: number }
            }
        }
    }
}

export function EvolutionDashboard() {
    const [state, setState] = useState<EvolutionState | null>(null)
    const [loading, setLoading] = useState(true)
    const [showHelp, setShowHelp] = useState(false)

    useEffect(() => {
        const fetchState = async () => {
            try {
                const res = await fetch('/api/evolution')
                const data = await res.json()
                setState(data)
            } catch (e) {
                console.error("Failed to fetch evolution state", e)
            } finally {
                setLoading(false)
            }
        }
        fetchState()
        const interval = setInterval(fetchState, 30000) // 30s auto-refresh
        return () => clearInterval(interval)
    }, [])

    if (loading) return null

    const mainStrategy = state?.strategies?.growth_value
    if (!mainStrategy) return null

    // Transform weights for radar chart to match RadarDataPoint interface
    const radarData = Object.entries(mainStrategy.weights).map(([key, value]) => ({
        subject: key.replace('_', ' ').toUpperCase(),
        A: value * 100,
        fullMark: 100
    }))

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="grid gap-6 lg:grid-cols-2"
        >
            {/* 1. Evolution Core: Strategy Radar */}
            <div className="rounded-[2rem] border border-primary/20 bg-zinc-900/40 p-8 backdrop-blur-xl shadow-2xl relative overflow-hidden group">
                <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-transparent opacity-50 group-hover:opacity-100 transition-opacity duration-700" />

                <div className="flex items-center justify-between mb-8 relative z-10">
                    <div className="flex items-center gap-4">
                        <div className="p-3 rounded-2xl bg-primary/20 border border-primary/30 shadow-[0_0_15px_rgba(59,130,246,0.3)]">
                            <Brain className="h-6 w-6 text-primary animate-pulse" />
                        </div>
                        <div>
                            <h3 className="text-xl font-bold text-zinc-100">AI 自進化核心</h3>
                            <p className="text-xs text-zinc-500 font-medium uppercase tracking-widest mt-0.5">Strategy Version {state.version}</p>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        {state.market_regime && (
                            <div className={cn(
                                "px-3 py-1 rounded-full border text-[10px] font-bold flex items-center gap-1.5 uppercase",
                                state.market_regime === 'bull' ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400" :
                                    state.market_regime === 'bear' ? "bg-rose-500/10 border-rose-500/20 text-rose-400" :
                                        "bg-zinc-500/10 border-zinc-500/20 text-zinc-400"
                            )}>
                                <Activity className="h-3 w-3" /> {state.market_regime} MARKET
                            </div>
                        )}
                        <div className="px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-[10px] font-bold flex items-center gap-1.5 animate-pulse">
                            <Zap className="h-3 w-3" /> LIVE
                        </div>
                        <button
                            onClick={() => setShowHelp(true)}
                            className="p-1.5 rounded-full hover:bg-white/10 text-zinc-500 hover:text-white transition-colors"
                            title="AI 運作說明"
                        >
                            <HelpCircle className="h-4 w-4" />
                        </button>
                    </div>
                </div>

                <AnimatePresence>
                    {showHelp && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
                            onClick={() => setShowHelp(false)}
                        >
                            <motion.div
                                initial={{ scale: 0.95, opacity: 0 }}
                                animate={{ scale: 1, opacity: 1 }}
                                exit={{ scale: 0.95, opacity: 0 }}
                                className="w-full max-w-2xl overflow-hidden rounded-xl border border-white/10 bg-zinc-900 shadow-2xl"
                                onClick={e => e.stopPropagation()}
                            >
                                <div className="flex items-center justify-between border-b border-white/10 bg-white/5 px-6 py-4">
                                    <h3 className="flex items-center gap-2 font-mono text-lg font-bold text-white">
                                        <Brain className="h-5 w-5 text-emerald-500" />
                                        AI 核心架構說明
                                    </h3>
                                    <button onClick={() => setShowHelp(false)} className="text-zinc-500 hover:text-white">
                                        <X className="h-5 w-5" />
                                    </button>
                                </div>

                                <div className="max-h-[70vh] overflow-y-auto p-6 space-y-8">
                                    <section className="space-y-3">
                                        <h4 className="flex items-center gap-2 text-sm font-bold text-emerald-400 uppercase tracking-wider">
                                            <Activity className="h-4 w-4" /> 運作循環 (Evolution Loop)
                                        </h4>
                                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
                                            <div className="bg-zinc-950/50 p-3 rounded border border-white/5 space-y-1">
                                                <div className="font-bold text-zinc-300">1. 觀察 (Observe)</div>
                                                <div className="text-zinc-500">掃描全市場，收集技術指標 (RSI, MA) 與基本面數據 (F-Score)。</div>
                                            </div>
                                            <div className="bg-zinc-950/50 p-3 rounded border border-white/5 space-y-1">
                                                <div className="font-bold text-zinc-300">2. 預測 (Predict)</div>
                                                <div className="text-zinc-500">基於當前策略參數計算評分 (0-10)，高分者推薦。</div>
                                            </div>
                                            <div className="bg-zinc-950/50 p-3 rounded border border-white/5 space-y-1">
                                                <div className="font-bold text-zinc-300">3. 追蹤 (Track)</div>
                                                <div className="text-zinc-500">紀錄預測當下的價格，並持續追蹤後續 24 小時漲跌幅。</div>
                                            </div>
                                            <div className="bg-zinc-950/50 p-3 rounded border border-white/5 space-y-1">
                                                <div className="font-bold text-zinc-300">4. 進化 (Mutate)</div>
                                                <div className="text-zinc-500">若準確率低於 40%，自動觸發「反思引擎」調整策略參數。</div>
                                            </div>
                                        </div>
                                    </section>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                        <section className="space-y-3">
                                            <h4 className="flex items-center gap-2 text-sm font-bold text-emerald-400 uppercase tracking-wider">
                                                <Activity className="h-4 w-4" /> 市場狀態 (Market Regime)
                                            </h4>
                                            <ul className="space-y-2 text-xs text-zinc-400">
                                                <li className="flex gap-2">
                                                    <span className="font-bold text-emerald-400 min-w-[3rem]">BULL</span>
                                                    <span>牛市：大盤 200MA 之上。AI 策略偏向積極，容許較高 RSI。</span>
                                                </li>
                                                <li className="flex gap-2">
                                                    <span className="font-bold text-rose-400 min-w-[3rem]">BEAR</span>
                                                    <span>熊市：大盤 200MA 之下。AI 策略轉為防禦，嚴格過濾高風險股。</span>
                                                </li>
                                                <li className="flex gap-2">
                                                    <span className="font-bold text-zinc-400 min-w-[3rem]">SIDE</span>
                                                    <span>盤整：大盤無明顯趨勢。AI 側重區間操作與高防禦性標的。</span>
                                                </li>
                                            </ul>
                                        </section>

                                        <section className="space-y-3">
                                            <h4 className="flex items-center gap-2 text-sm font-bold text-emerald-400 uppercase tracking-wider">
                                                <Zap className="h-4 w-4" /> 關鍵參數 (Parameters)
                                            </h4>
                                            <ul className="space-y-2 text-xs text-zinc-400">
                                                <li className="flex gap-2">
                                                    <span className="font-bold text-zinc-300 min-w-[6rem]">RSI Threshold</span>
                                                    <span>相對強弱指標上限。熊市時此數值會自動降低以減少追高風險。</span>
                                                </li>
                                                <li className="flex gap-2">
                                                    <span className="font-bold text-zinc-300 min-w-[6rem]">F-Score Min</span>
                                                    <span>Piotroski F-Score 財務評分下限 (0-9)。確保選股基本面體質。</span>
                                                </li>
                                                <li className="flex gap-2">
                                                    <span className="font-bold text-zinc-300 min-w-[6rem]">Accuracy</span>
                                                    <span>AI 預測準確率 (勝率)。綠燈 &gt; 60%，紅燈 &lt; 40%。</span>
                                                </li>
                                            </ul>
                                        </section>
                                    </div>
                                </div>

                                <div className="bg-white/5 px-6 py-4 text-center">
                                    <button
                                        onClick={() => setShowHelp(false)}
                                        className="w-full rounded bg-emerald-500 py-2 text-sm font-bold text-black hover:bg-emerald-400 transition-colors"
                                    >
                                        了解
                                    </button>
                                </div>
                            </motion.div>
                        </motion.div>
                    )}
                </AnimatePresence>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center relative z-10">
                    <div className="h-64">
                        <AI_RadarChart data={radarData} />
                    </div>
                    <div className="space-y-4">
                        <div className="p-4 rounded-2xl bg-black/40 border border-white/5">
                            <span className="text-[10px] text-zinc-500 font-bold uppercase block mb-1">當前模型</span>
                            <div className="text-lg font-bold text-primary">{mainStrategy.name}</div>
                            <p className="text-xs text-zinc-400 mt-1 leading-relaxed">{mainStrategy.description}</p>

                            {/* Dynamic Parameters Display */}
                            {state.strategy_config?.strategies?.growth_value && (
                                <div className="mt-3 pt-3 border-t border-white/5 grid grid-cols-2 gap-2">
                                    <div>
                                        <span className="text-[9px] text-zinc-600 block">RSI THRESHOLD</span>
                                        <span className="text-xs font-mono text-zinc-300">
                                            &lt; {state.strategy_config.strategies.growth_value.rsi_threshold || 70}
                                        </span>
                                    </div>
                                    <div>
                                        <span className="text-[9px] text-zinc-600 block">F-SCORE MIN</span>
                                        <span className="text-xs font-mono text-zinc-300">
                                            &gt;= {state.strategy_config.strategies.growth_value.f_score_min || 5}
                                        </span>
                                    </div>
                                </div>
                            )}
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                            {Object.entries(mainStrategy.weights).map(([key, val]) => (
                                <div key={key} className="p-3 rounded-xl bg-zinc-900/60 border border-white/5">
                                    <span className="text-[9px] text-zinc-500 font-bold block truncate">{key.toUpperCase()}</span>
                                    <span className="text-sm font-mono font-bold text-zinc-200">{(val * 100).toFixed(1)}%</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* 3. Performance Tracking — 進化閃環觀察資料 */}
            {state?.performance_tracking && (
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="col-span-2 rounded-[2rem] border border-zinc-800 bg-zinc-900/40 p-6 backdrop-blur-xl"
                >
                    <h3 className="text-sm font-bold flex items-center gap-2 mb-4 text-zinc-300">
                        <Target className="h-4 w-4 text-primary" />
                        進化閃環—預測準確率追蹤
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="p-4 rounded-2xl bg-black/30 border border-white/5">
                            <span className="text-[10px] text-zinc-500 font-bold block mb-1">TOTAL PREDICTIONS</span>
                            <span className="text-2xl font-mono font-bold text-zinc-200">
                                {state.performance_tracking.total_predictions}
                            </span>
                        </div>
                        <div className="p-4 rounded-2xl bg-black/30 border border-white/5">
                            <span className="text-[10px] text-zinc-500 font-bold block mb-1">RESOLVED</span>
                            <span className="text-2xl font-mono font-bold text-zinc-200">
                                {state.performance_tracking.resolved}
                            </span>
                        </div>
                        <div className="p-4 rounded-2xl bg-black/30 border border-white/5">
                            <span className="text-[10px] text-zinc-500 font-bold block mb-1">ACCURACY</span>
                            {state.performance_tracking.accuracy_stats.accuracy !== null ? (
                                <span className={cn(
                                    "text-2xl font-mono font-bold",
                                    state.performance_tracking.accuracy_stats.accuracy >= 0.6
                                        ? "text-emerald-400"
                                        : state.performance_tracking.accuracy_stats.accuracy >= 0.4
                                            ? "text-amber-400"
                                            : "text-rose-400"
                                )}>
                                    {(state.performance_tracking.accuracy_stats.accuracy * 100).toFixed(1)}%
                                </span>
                            ) : (
                                <span className="text-sm text-zinc-600 font-mono">
                                    {state.performance_tracking.accuracy_stats.message || '樣本不足'}
                                </span>
                            )}
                        </div>
                        <div className="p-4 rounded-2xl bg-black/30 border border-white/5">
                            <span className="text-[10px] text-zinc-500 font-bold block mb-1">AVG RETURN</span>
                            {state.performance_tracking.accuracy_stats.avg_return !== null ? (
                                <span className={cn(
                                    "text-2xl font-mono font-bold",
                                    (state.performance_tracking.accuracy_stats.avg_return ?? 0) >= 0
                                        ? "text-emerald-400"
                                        : "text-rose-400"
                                )}>
                                    {(state.performance_tracking.accuracy_stats.avg_return ?? 0) >= 0 ? '+' : ''}
                                    {state.performance_tracking.accuracy_stats.avg_return?.toFixed(2)}%
                                </span>
                            ) : (
                                <span className="text-sm text-zinc-600 font-mono">—</span>
                            )}
                        </div>
                    </div>
                </motion.div>
            )}

            {/* 2. Evolution Logs */}
            <div className="rounded-[2rem] border border-zinc-800 bg-zinc-900/40 p-8 backdrop-blur-xl shadow-2xl relative overflow-hidden flex flex-col">
                <h3 className="text-lg font-bold flex items-center gap-3 mb-6 relative z-10 text-zinc-100">
                    <History className="h-5 w-5 text-zinc-400" /> 近期進化日誌
                </h3>

                <div className="flex-1 space-y-4 overflow-y-auto max-h-[300px] pr-2 custom-scrollbar relative z-10">
                    <AnimatePresence mode="popLayout">
                        {mainStrategy.performance_history.length > 0 ? (
                            mainStrategy.performance_history.map((log: any, i: number) => (
                                <motion.div
                                    key={i}
                                    initial={{ x: -10, opacity: 0 }}
                                    animate={{ x: 0, opacity: 1 }}
                                    transition={{ delay: i * 0.1 }}
                                    className="p-4 rounded-2xl bg-black/20 border border-white/5 hover:border-primary/20 transition-colors group/item"
                                >
                                    <div className="flex justify-between items-start mb-2">
                                        <span className="text-[10px] font-mono text-zinc-500">{new Date(log.date).toLocaleDateString()}</span>
                                        <span className={cn("text-[10px] font-bold px-1.5 py-0.5 rounded-md", log.performance.avg_return >= 0 ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400")}>
                                            {log.performance.avg_return >= 0 ? "+" : ""}{(log.performance.avg_return * 100).toFixed(1)}% Return
                                        </span>
                                    </div>
                                    {log.reflections.map((ref: string, j: number) => (
                                        <div key={j} className="flex gap-2 text-xs text-zinc-300 mt-1">
                                            <ChevronRight className="h-3 w-3 mt-0.5 text-primary flex-shrink-0" />
                                            {ref}
                                        </div>
                                    ))}
                                </motion.div>
                            ))
                        ) : (
                            <div className="flex flex-col items-center justify-center py-12 text-zinc-600 grayscale opacity-50">
                                <Zap className="h-12 w-12 mb-4 animate-pulse" />
                                <p className="text-sm font-medium">等待首個 14:30 反思週期...</p>
                                <p className="text-[10px] uppercase mt-1 tracking-widest">Self-Healing Active</p>
                            </div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </motion.div>
    )
}
