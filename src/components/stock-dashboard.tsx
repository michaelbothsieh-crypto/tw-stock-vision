"use client"

import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import confetti from "canvas-confetti"
import { cn } from "@/lib/utils"
import Typewriter from 'typewriter-effect';
import { AI_RadarChart } from "./ui/radar-chart"
import { Info, PlusCircle, Trophy } from "lucide-react"
import * as Tooltip from '@radix-ui/react-tooltip';
import { toast } from "sonner"
import { useUser } from "@/hooks/use-user"

interface StockData {
    symbol: string
    name?: string
    price: number
    change: number
    changePercent: number
    volume: number
    marketCap?: number
    updatedAt?: string
    // SMC Indicators
    rvol: number
    cmf: number
    vwap: number
    // Ratings
    technicalRating: number
    analystRating: number
    targetPrice: number
    // Daily Vitals
    rsi: number
    atr_p: number
    sma20: number
    sma50: number
    sma200: number
    perf_w: number
    perf_m: number
    perf_ytd: number
    volatility: number
    earningsDate: number
    // AI Data
    smcScore: number
    prediction?: {
        confidence: string
        upper: number
        lower: number
        days: number
    }
    radarData?: any[]
}

interface StockDashboardProps {
    data: StockData | null
    loading: boolean
    error?: string | null
}

// Helper for Tooltip
const InfoTooltip = ({ content }: { content: string }) => (
    <Tooltip.Provider>
        <Tooltip.Root>
            <Tooltip.Trigger asChild>
                <Info className="h-4 w-4 text-muted-foreground/70 hover:text-foreground cursor-help" />
            </Tooltip.Trigger>
            <Tooltip.Portal>
                <Tooltip.Content className="max-w-[200px] bg-popover text-popover-foreground text-xs p-2 rounded shadow-md border animate-in fade-in-0 zoom-in-95" sideOffset={5}>
                    {content}
                    <Tooltip.Arrow className="fill-popover" />
                </Tooltip.Content>
            </Tooltip.Portal>
        </Tooltip.Root>
    </Tooltip.Provider>
)

export function StockDashboard({ data, loading, error }: StockDashboardProps) {
    const [aiCommentString, setAiCommentString] = useState<string>("")

    useEffect(() => {
        if (data) {
            // Trigger confetti if gain > 3%
            if (data.changePercent > 3) {
                const duration = 3 * 1000
                const animationEnd = Date.now() + duration
                const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 0 }

                const randomInRange = (min: number, max: number) => Math.random() * (max - min) + min

                const interval: any = setInterval(function () {
                    const timeLeft = animationEnd - Date.now()

                    if (timeLeft <= 0) {
                        return clearInterval(interval)
                    }

                    const particleCount = 50 * (timeLeft / duration)
                    confetti({
                        ...defaults,
                        particleCount,
                        origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 },
                    })
                    confetti({
                        ...defaults,
                        particleCount,
                        origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 },
                    })
                }, 250)
            }

            // Generate Dynamic AI Comment String (Logic reused)
            const getComment = () => {
                const randomChoice = (arr: string[]) => arr[Math.floor(Math.random() * arr.length)]
                if (data.changePercent > 5) return randomChoice(["飛向宇宙，浩瀚無垠！🚀", "這漲幅... 難道是有內線？🤫", "多軍集結，全面進攻！⚔️"])
                if (data.changePercent < -5) return randomChoice(["這是在特價嗎？還是接刀？🔪", "別怕，這只是技術性調整... 吧？📉", "空軍大獲全勝。🥶"])
                if (data.rsi > 75) return randomChoice(["RSI 過熱！少年股神請冷靜 🔥", "追高小心住套房！⚠️"])
                if (data.rsi < 25) return randomChoice(["RSI 超賣！人棄我取... 嗎？💎", "恐慌殺盤，也許是買點？👀"])
                if (data.rvol > 2.5) return randomChoice(["量能爆棚！主力在搞事？📢", "有人在偷偷吃貨？🧐"])
                if (data.technicalRating > 0.5) return randomChoice(["技術面強勢，趨勢是你的朋友！📈", "均線多頭排列。🌊"])
                if (data.technicalRating < -0.5) return randomChoice(["技術面疲弱，保守為上。🛡️", "型態轉空，現金為王。💰"])
                return randomChoice(["穩健觀察中... ☕", "盤整盤，喝杯咖啡再看吧。💤", "多空交戰，方向未明。⚖️"])
            }
            setAiCommentString(getComment())
        }
    }, [data])

    if (loading) {
        return (
            <div className="flex h-64 items-center justify-center">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            </div>
        )
    }

    if (error) {
        return (
            <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-4 text-destructive">
                錯誤: {error}
            </div>
        )
    }

    if (!data) {
        return (
            <div className="flex h-64 items-center justify-center text-muted-foreground">
                輸入股票代號以查看數據
            </div>
        )
    }

    const isPositive = data.change >= 0

    return (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="grid gap-6">

            {/* 1. Header Card (Overview) */}
            <div className="rounded-3xl border border-border/50 bg-card/50 p-8 shadow-xl backdrop-blur-sm relative overflow-hidden group">
                <div className="absolute top-0 left-0 w-full h-[2px] bg-primary/50 shadow-[0_0_15px_3px_rgba(59,130,246,0.5)] animate-scan opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"></div>
                <div className="absolute top-0 right-0 p-4 opacity-10 text-9xl">{isPositive ? "🐂" : "🐻"}</div>

                <div className="relative z-10 flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                    <div>
                        <div className="flex items-baseline gap-3">
                            <h2 className="text-4xl font-bold tracking-tight text-foreground">{data.symbol}</h2>
                            <span className="rounded-full bg-secondary px-2.5 py-0.5 text-xs font-semibold text-secondary-foreground">
                                {data.symbol.match(/[A-Z]/) ? "US" : "TWSE"}
                            </span>
                        </div>
                        <p className="mt-1 text-2xl font-bold text-primary/90">{data.name || data.symbol}</p>

                        {/* Add to Portfolio Button */}
                        <button
                            onClick={handleAddToPortfolio}
                            disabled={adding || !user}
                            className="mt-4 flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-sm font-bold text-primary-foreground hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <PlusCircle className="h-4 w-4" />
                            {adding ? "加入中..." : "加入追蹤"}
                        </button>
                        {/* Loop Typewriter */}
                        <div className="mt-4 min-h-[40px] inline-flex items-center rounded-2xl bg-primary/10 px-4 py-2 text-primary font-medium border border-primary/20">
                            <span className="mr-2">🤖</span>
                            <Typewriter
                                options={{
                                    strings: [aiCommentString],
                                    autoStart: true,
                                    loop: true,
                                    delay: 50,
                                    deleteSpeed: 30,
                                    cursor: '▋'
                                }}
                            />
                        </div>
                    </div>

                    <div className={cn(
                        "flex flex-col items-end text-right",
                        isPositive ? "text-emerald-400" : "text-rose-400"
                    )}>
                        <h3 className="text-sm font-medium text-muted-foreground mb-1">即時報價</h3>
                        <span className="text-6xl font-bold font-mono tracking-tighter shadow-glow">
                            {data.price.toFixed(2)}
                        </span>
                        <div className="flex items-center gap-2 text-xl font-medium mt-1">
                            <span>{isPositive ? "▲" : "▼"} {Math.abs(data.change).toFixed(2)}</span>
                            <span className="opacity-80">({Math.abs(data.changePercent).toFixed(2)}%)</span>
                        </div>
                    </div>
                </div>

                <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-5">
                    <Stat label="成交量" value={(data.volume || 0).toLocaleString()} />
                    <Stat label="市值" value={data.marketCap ? formatMarketCap(data.marketCap) : "--"} />
                    <Stat label="RVOL (量能)" value={(data.rvol || 0).toFixed(2) + "x"}
                        subtext={(data.rvol || 0) > 1.5 ? "🔥 滾燙" : "冰冷"}
                        color={(data.rvol || 0) > 1.5 ? "text-amber-400" : undefined} />
                    <Stat label="VWAP" value={(data.vwap || 0).toFixed(2)}
                        color={data.price > (data.vwap || 0) ? "text-emerald-400" : "text-rose-400"} />
                    <Stat label="CMF (金流)" value={(data.cmf || 0).toFixed(2)}
                        color={(data.cmf || 0) > 0 ? "text-emerald-400" : "text-rose-400"} />
                </div>
            </div>

            {/* AI Analysis Grid */}
            <div className="grid gap-6 md:grid-cols-2">

                {/* AI Radar Chart */}
                <div className="rounded-3xl border border-border/50 bg-card/30 p-6 shadow-lg backdrop-blur-sm relative overflow-hidden">
                    <h3 className="text-xl font-semibold mb-2 flex items-center gap-2">
                        <span className="text-2xl">🧬</span> AI 戰力分析 (Radar)
                    </h3>
                    <div className="h-[300px]">
                        {data.radarData && <AI_RadarChart data={data.radarData} />}
                    </div>
                </div>

                {/* Prediction Cone & Ratings */}
                <div className="flex flex-col gap-6">
                    {/* Prediction Cone */}
                    <div className="rounded-3xl border border-border/50 bg-gradient-to-br from-blue-900/20 to-cyan-900/20 p-6 shadow-lg backdrop-blur-sm">
                        <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                            <span className="text-2xl">🔮</span> AI 未來視 (Prediction)
                        </h3>
                        {data.prediction ? (
                            <div className="space-y-4">
                                <div className="flex justify-between items-center bg-background/20 p-3 rounded-xl border border-white/5">
                                    <span className="text-sm text-muted-foreground">預測信心指數</span>
                                    <span className="font-bold text-cyan-400">{data.prediction.confidence}</span>
                                </div>
                                <div className="grid grid-cols-3 gap-2 text-center">
                                    <div className="p-2 rounded bg-emerald-500/10 border border-emerald-500/20">
                                        <div className="text-xs text-emerald-400">樂觀 (Bullish)</div>
                                        <div className="font-mono font-bold">{data.prediction.upper.toFixed(2)}</div>
                                    </div>
                                    <div className="p-2 pt-4">
                                        <div className="text-xs text-muted-foreground">當前</div>
                                        <div className="font-mono font-bold text-lg">{data.price.toFixed(2)}</div>
                                    </div>
                                    <div className="p-2 rounded bg-rose-500/10 border border-rose-500/20">
                                        <div className="text-xs text-rose-400">悲觀 (Bearish)</div>
                                        <div className="font-mono font-bold">{data.prediction.lower.toFixed(2)}</div>
                                    </div>
                                </div>
                                <p className="text-[10px] text-center text-muted-foreground opacity-70">
                                    *基於 ATR 波動率推算未來 {data.prediction.days} 日潛在區間 (68% 機率)
                                </p>
                            </div>
                        ) : (
                            <div className="text-center text-muted-foreground py-8">數據不足無法預測</div>
                        )}
                    </div>

                    {/* Ratings */}
                    <div className="flex-1 rounded-3xl border border-border/50 bg-card/30 p-6 shadow-lg backdrop-blur-sm">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-semibold flex items-center gap-2">🎯 目標價與評級</h3>
                            <span className={cn("px-2 py-0.5 rounded text-xs", (data.targetPrice || 0) > data.price ? "bg-emerald-500/20 text-emerald-400" : "bg-zinc-500/20")}>
                                {(((data.targetPrice || 0) - data.price) / data.price * 100).toFixed(1)}% Upside
                            </span>
                        </div>
                        <div className="flex items-center justify-between gap-4">
                            <div className="text-center">
                                <div className="text-sm text-muted-foreground mb-1">目標價</div>
                                <div className="text-2xl font-mono font-bold">{(data.targetPrice || 0).toFixed(2)}</div>
                            </div>
                            <div className="text-center">
                                <div className="text-sm text-muted-foreground mb-1">技術評級</div>
                                <div className="text-lg font-bold" style={{ color: getRatingColor(data.technicalRating) }}>{getRatingText(data.technicalRating)}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="text-center text-xs text-muted-foreground opacity-50 pb-8">
                *SMC 指標與預測僅供參考，不代表投資建議。
            </div>
        </motion.div>
    )
}

function Stat({ label, value, subtext, color }: { label: string; value: string | number, subtext?: string, color?: string }) {
    return (
        <div className="flex flex-col gap-1 p-4 rounded-2xl bg-background/40 border border-border/30 backdrop-blur-md hover:bg-background/50 transition-colors group relative overflow-hidden">
            {/* Scanner Effect Small */}
            <div className="absolute top-0 left-0 w-full h-[1px] bg-white/20 animate-scan opacity-0 group-hover:opacity-100"></div>
            <span className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">{label}</span>
            <span className={cn("text-2xl font-bold font-mono tracking-tight", color || "text-foreground")}>{value}</span>
            {subtext && <span className="text-[10px] text-muted-foreground/80">{subtext}</span>}
        </div>
    )
}

function VitalRow({ label, value, status }: { label: string, value: string, status: "good" | "bad" | "warning" | "neutral" }) {
    const colors = {
        good: "text-emerald-400",
        bad: "text-rose-400",
        warning: "text-amber-400",
        neutral: "text-foreground"
    }
    return (
        <div className="flex justify-between items-center p-3 rounded-xl bg-background/20 hover:bg-background/30 transition-colors">
            <span className="text-sm text-muted-foreground">{label}</span>
            <span className={cn("font-mono font-bold", colors[status])}>{value}</span>
        </div>
    )
}

function Gauge({ value, min, max }: { value: number, min: number, max: number }) {
    const percent = Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100));

    return (
        <div className="relative w-32 h-16 overflow-hidden flex items-end justify-center">
            <div className="absolute top-0 w-32 h-32 rounded-full border-[12px] border-secondary" style={{ clipPath: 'inset(0 0 50% 0)' }}></div>
            <div className="absolute top-0 w-32 h-32 rounded-full border-[12px] border-transparent"
                style={{
                    clipPath: 'inset(0 0 50% 0)',
                    borderTopColor: getRatingColor(value),
                    borderRightColor: getRatingColor(value),
                    transform: `rotate(${percent * 1.8 - 180}deg)`,
                    transition: 'transform 1s ease-out'
                }}>
            </div>
            <div className="mb-0 text-xl font-bold">{percent.toFixed(0)}</div>
        </div>
    )
}

function getRatingColor(val: number) {
    if (val > 0.5) return "#34d399" // Emerald 400
    if (val > 0.1) return "#22c55e" // Green 500
    if (val < -0.5) return "#f43f5e" // Rose 500
    if (val < -0.1) return "#e11d48" // Rose 600
    return "#a1a1aa" // Zinc 400
}

function getRatingText(val: number) {
    if (val > 0.5) return "💪 強力買進"
    if (val > 0.1) return "💰 買進"
    if (val < -0.5) return "📉 強力賣出"
    if (val < -0.1) return "💸 賣出"
    return "😐 觀望 / 中立"
}

function getRsiStatus(val: number): "good" | "bad" | "warning" | "neutral" {
    if (val > 70) return "warning" // Overbought
    if (val < 30) return "good" // Oversold
    return "neutral"
}

function formatMarketCap(value: number): string {
    if (value >= 1e12) return (value / 1e12).toFixed(2) + "兆"
    if (value >= 1e9) return (value / 1e9).toFixed(2) + "0億" // 1B = 10億
    if (value >= 1e6) return (value / 1e6).toFixed(2) + "百萬"
    return value.toLocaleString()
}
