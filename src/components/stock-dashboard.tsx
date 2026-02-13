"use client"

import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import confetti from "canvas-confetti"
import { cn } from "@/lib/utils"

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
}

interface StockDashboardProps {
    data: StockData | null
    loading: boolean
    error?: string | null
}

export function StockDashboard({ data, loading, error }: StockDashboardProps) {
    const [aiComment, setAiComment] = useState<string>("")

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

            // Generate Dynamic AI Comment
            const getComment = () => {
                const randomChoice = (arr: string[]) => arr[Math.floor(Math.random() * arr.length)]

                if (data.changePercent > 5) return randomChoice([
                    "飛向宇宙，浩瀚無垠！🚀",
                    "這漲幅... 難道是有內線？🤫",
                    "多軍集結，全面進攻！⚔️",
                    "恭喜持有的股東，今晚加菜！🍗"
                ])
                if (data.changePercent < -5) return randomChoice([
                    "這是在特價嗎？還是接刀？🔪",
                    "別怕，這只是技術性調整... 吧？📉",
                    "該停損還是抄底？這是一個問題。🤔",
                    "空軍大獲全勝，多軍瑟瑟發抖。🥶"
                ])
                if (data.rsi > 75) return randomChoice([
                    "RSI 過熱！少年股神請冷靜 🔥",
                    "追高小心住套房，記得設停損！⚠️",
                    "情緒過於亢奮，隨時可能回檔。🛑"
                ])
                if (data.rsi < 25) return randomChoice([
                    "RSI 超賣！人棄我取... 嗎？💎",
                    "恐慌殺盤，也許是鑽石買點？👀",
                    "跌無可跌，反彈在即？📈"
                ])
                if (data.rvol > 2.5) return randomChoice([
                    "量能爆棚！主力在搞事？📢",
                    "有人在偷偷吃貨，還是在倒貨？🧐",
                    "成交量異常，必有妖孽！👻"
                ])
                if (data.technicalRating > 0.5) return randomChoice([
                    "技術面強勢，趨勢是你的朋友！📈",
                    "均線多頭排列，順勢而為。🌊",
                    "各項指標亮紅燈，衝啊！🚦"
                ])
                if (data.technicalRating < -0.5) return randomChoice([
                    "技術面疲弱，保守為上。🛡️",
                    "型態轉空，現金為王。💰",
                    "不要與趨勢作對，該跑就跑。🏃"
                ])

                return randomChoice([
                    "穩健觀察中... ☕",
                    "盤整盤，喝杯咖啡再看吧。💤",
                    "多空交戰，方向未明。⚖️",
                    "耐心等待出手的時機。🕰️"
                ])
            }

            setAiComment(getComment())
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
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid gap-6"
        >
            {/* Header Card */}
            <div className="rounded-3xl border border-border/50 bg-card/50 p-8 shadow-xl backdrop-blur-sm relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-10 text-9xl">
                    {isPositive ? "🐂" : "🐻"}
                </div>

                <div className="relative z-10 flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                    <div>
                        <div className="flex items-baseline gap-3">
                            <h2 className="text-4xl font-bold tracking-tight text-foreground">{data.symbol}</h2>
                            <span className="rounded-full bg-secondary px-2.5 py-0.5 text-xs font-semibold text-secondary-foreground">
                                {data.symbol.match(/[A-Z]/) ? "US" : "TWSE"}
                            </span>
                        </div>
                        <p className="mt-1 text-2xl font-bold text-primary/90">{data.name || data.symbol}</p>

                        {/* AI Comment Bubble */}
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            transition={{ delay: 0.5 }}
                            className="mt-4 inline-block rounded-2xl bg-primary/10 px-4 py-2 text-primary font-medium border border-primary/20"
                        >
                            🤖 AI 點評: {aiComment}
                        </motion.div>
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
                    <Stat label="相對量能 (RVOL)" value={(data.rvol || 0).toFixed(2) + "x"}
                        subtext={(data.rvol || 0) > 1.5 ? "🔥 交易熱絡" : "正常"}
                        color={(data.rvol || 0) > 1.5 ? "text-amber-400" : undefined} />
                    <Stat label="成交量加權價 (VWAP)" value={(data.vwap || 0).toFixed(2)}
                        subtext={data.price > (data.vwap || 0) ? "多頭強勢 > VWAP" : "空頭弱勢 < VWAP"}
                        color={data.price > (data.vwap || 0) ? "text-emerald-400" : "text-rose-400"} />
                    <Stat label="資金流向 (CMF)" value={(data.cmf || 0).toFixed(2)}
                        color={(data.cmf || 0) > 0 ? "text-emerald-400" : "text-rose-400"} />
                </div>
            </div>

            {/* Smart Money & Ratings Grid */}
            <div className="grid gap-6 md:grid-cols-2">
                {/* Ratings Card */}
                <div className="rounded-3xl border border-border/50 bg-card/30 p-6 shadow-lg backdrop-blur-sm">
                    <h3 className="text-xl font-semibold mb-6 flex items-center gap-2">
                        <span className="text-2xl">⚡</span> 綜合評級 (Ratings)
                    </h3>
                    <div className="grid grid-cols-2 gap-8">
                        {/* Technical Rating */}
                        <div className="flex flex-col items-center">
                            <Gauge value={data.technicalRating || 0} min={-1} max={1} />
                            <span className="mt-2 font-semibold text-lg">
                                {getRatingText(data.technicalRating || 0)}
                            </span>
                            <span className="text-xs text-muted-foreground uppercase tracking-widest mt-1">技術指標</span>
                        </div>
                        {/* Analyst Rating */}
                        <div className="flex flex-col items-center justify-center p-4 bg-background/20 rounded-2xl text-center">
                            <span className="text-sm text-muted-foreground mb-1">分析師目標價</span>

                            {(data.targetPrice || 0) > 0 ? (
                                <>
                                    <span className="text-3xl font-mono font-bold text-foreground">
                                        {(data.targetPrice || 0).toFixed(2)}
                                    </span>
                                    <span className={cn("text-xs font-medium mt-1 px-2 py-0.5 rounded",
                                        (data.targetPrice || 0) > data.price ? "bg-emerald-500/20 text-emerald-400" : "bg-rose-500/20 text-rose-400"
                                    )}>
                                        {(((data.targetPrice || 0) - data.price) / data.price * 100).toFixed(1)}% 潛在空間
                                    </span>
                                </>
                            ) : (
                                <div className="text-muted-foreground">
                                    <span className="text-2xl block mb-1">🤷‍♂️</span>
                                    <span className="text-xs">數據不足或暫無目標價</span>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Daily Vitals Card */}
                <div className="rounded-3xl border border-border/50 bg-card/30 p-6 shadow-lg backdrop-blur-sm">
                    <h3 className="text-xl font-semibold mb-6 flex items-center gap-2">
                        <span className="text-2xl">🩺</span> 每日健檢 (Daily Vitals)
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                        <VitalRow label="RSI (強弱指標)" value={(data.rsi || 50).toFixed(1)} status={getRsiStatus(data.rsi || 50)} />
                        <VitalRow label="ATR 波動率" value={(data.atr_p || 0).toFixed(2) + "%"} status="neutral" />
                        <VitalRow label="月績效" value={(data.perf_m || 0).toFixed(2) + "%"} status={(data.perf_m || 0) > 0 ? "good" : "bad"} />
                        <VitalRow label="今年以來績效" value={(data.perf_ytd || 0).toFixed(2) + "%"} status={(data.perf_ytd || 0) > 0 ? "good" : "bad"} />

                        <div className="col-span-2 mt-2 pt-4 border-t border-border/30">
                            <div className="flex justify-between items-center text-sm mb-2">
                                <span className="text-muted-foreground">均線趨勢對齊 (SMA Trend)</span>
                            </div>
                            <div className="flex gap-1 h-2 w-full rounded-full overflow-hidden bg-secondary">
                                <div className={cn("h-full flex-1 opacity-80", data.price > (data.sma20 || 0) ? "bg-emerald-500" : "bg-rose-500")} title="Price > SMA20" />
                                <div className={cn("h-full flex-1 opacity-80", data.price > (data.sma50 || 0) ? "bg-emerald-500" : "bg-rose-500")} title="Price > SMA50" />
                                <div className={cn("h-full flex-1 opacity-80", data.price > (data.sma200 || 0) ? "bg-emerald-500" : "bg-rose-500")} title="Price > SMA200" />
                            </div>
                            <div className="flex justify-between text-[10px] text-muted-foreground mt-1 px-1">
                                <span>短線 (20MA)</span>
                                <span>中線 (50MA)</span>
                                <span>長線 (200MA)</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="text-center text-xs text-muted-foreground opacity-50 pb-8">
                *SMC 指標 (RVOL, CMF) 基於即時數據快照計算.
            </div>
        </motion.div>
    )
}

function Stat({ label, value, subtext, color }: { label: string; value: string | number, subtext?: string, color?: string }) {
    return (
        <div className="flex flex-col gap-1 p-4 rounded-2xl bg-background/40 border border-border/30 backdrop-blur-md hover:bg-background/50 transition-colors">
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
