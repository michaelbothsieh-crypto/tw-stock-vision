"use client"

import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import confetti from "canvas-confetti"
import { cn } from "@/lib/utils"
import Typewriter from 'typewriter-effect';
import { AI_RadarChart } from "./ui/radar-chart"
import { Info, PlusCircle, Trophy } from "lucide-react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { toast } from "sonner"
import { useUser } from "@/hooks/use-user"
import { NicknameDialog } from "./nickname-dialog"
import { HealthCheck } from "./health-check"
import { RadarCard } from "./dashboard/radar-card"
import { PredictionCard } from "./dashboard/prediction-card"
import { TechnicalEvidence } from "./dashboard/technical-evidence"
import { StockData } from "./dashboard/types"
const SECTOR_TRANSLATIONS: Record<string, string> = {
    "Electronic Technology": "電子科技",
    "Semiconductors": "半導體",
    "Finance": "金融服務",
    "Health Technology": "健康醫療",
    "Technology Services": "科技服務",
    "Consumer Durables": "耐用消費品",
    "Consumer Non-Durables": "非耐用消費品",
    "Producer Manufacturing": "生產製造",
    "Energy Minerals": "能源礦產",
    "Process Industries": "加工工業",
    "Communications": "通訊通訊",
    "Utilities": "公用事業",
    "Distribution Services": "流通服務",
    "Retail Trade": "零售貿易",
    "Commercial Services": "商業服務",
    "Transportation": "運輸物流",
    "Technology": "科技",
    "Electronic": "電子",
    "Financial": "金融",
    "Basic Materials": "基礎材料",
    "Capital Goods": "資本財",
    "Consumer Cyclical": "週期性消費",
    "Consumer Defensive": "防禦性消費",
    "Healthcare": "健康醫療"
}

const EXCHANGE_TRANSLATIONS: Record<string, string> = {
    "TWSE": "證交所",
    "OTC": "櫃買中心",
    "NASDAQ": "那斯達克",
    "NYSE": "紐約證交所",
    "AMEX": "美交所"
}


interface StockDashboardProps {
    data: StockData | null
    loading: boolean
    error?: string | null
}

// Helper for Tooltip
const InfoTooltip = ({ content }: { content: string }) => (
    <TooltipProvider>
        <Tooltip>
            <TooltipTrigger asChild>
                <Info className="h-4 w-4 text-muted-foreground/70 hover:text-foreground cursor-help" />
            </TooltipTrigger>
            <TooltipContent className="max-w-[200px]" sideOffset={5}>
                {content}
            </TooltipContent>
        </Tooltip>
    </TooltipProvider>
)

export function StockDashboard({ data, loading, error }: StockDashboardProps) {
    const { user, register } = useUser()
    const [adding, setAdding] = useState(false)
    const [aiComments, setAiComments] = useState<string[]>(["分析數據中..."])
    const [showRegister, setShowRegister] = useState(false)

    // Helper to perform the actual API call
    const performAddToPortfolio = async (userId: string) => {
        if (!data) return
        setAdding(true)
        try {
            const res = await fetch('http://127.0.0.1:8000', {
                method: 'POST',
                body: JSON.stringify({
                    action: 'add_portfolio',
                    user_id: userId,
                    symbol: data.symbol,
                    price: data.price
                })
            })
            const result = await res.json()
            if (result.status === 'success') {
                toast.success(`已將 ${data.symbol} 加入投資組合！`)
            } else {
                toast.error("加入失敗: " + (result.error || "未知錯誤"))
            }
        } catch (e) {
            toast.error("連線錯誤")
        } finally {
            setAdding(false)
        }
    }

    const handleAddToPortfolio = async () => {
        if (!data) return

        if (!user) {
            setShowRegister(true)
            return
        }

        if (adding) return // Prevent double clicks while adding

        performAddToPortfolio(user.id)
    }

    const handleRegister = async (nickname: string) => {
        const newUser = await register(nickname)
        if (newUser) {
            setShowRegister(false)
            toast.success(`歡迎, ${newUser.nickname}! 即將加入追蹤...`)
            // Short delay to ensure state updates? Not needed usually, but safe.
            performAddToPortfolio(newUser.id)
        } else {
            toast.error("註冊失敗")
        }
    }

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

            // Generate Dynamic AI Comment List
            const getComments = () => {
                const comments: string[] = []
                const randomChoice = (arr: string[]) => arr[Math.floor(Math.random() * arr.length)]

                // 1. Condition-based comments
                if (data.changePercent > 5) comments.push(randomChoice(["飛向宇宙，浩瀚無垠！🚀", "這漲幅... 難道是有內線？🤫", "多軍集結，全面進攻！⚔️"]))
                else if (data.changePercent < -5) comments.push(randomChoice(["這是在特價嗎？還是接刀？🔪", "別怕，這只是技術性調整... 吧？📉", "空軍大獲全勝。🥶"]))

                if (data.rsi > 75) comments.push(randomChoice(["RSI 過熱！少年股神請冷靜 🔥", "追高小心住套房！⚠️"]))
                else if (data.rsi < 25) comments.push(randomChoice(["RSI 超賣！人棄我取... 嗎？💎", "恐慌殺盤，也許是買點？👀"]))

                if (data.rvol > 2.5) comments.push(randomChoice(["量能爆棚！主力在搞事？📢", "有人在偷偷吃貨？🧐"]))

                if (data.technicalRating > 0.5) comments.push(randomChoice(["技術面強勢，趨勢是你的朋友！📈", "均線多頭排列。🌊"]))
                else if (data.technicalRating < -0.5) comments.push(randomChoice(["技術面疲弱，保守為上。🛡️", "型態轉空，現金為王。💰"]))

                // 2. Personality/Default comments to ensure variety
                const personality = [
                    "SMC 指標顯示主力腳步移動中... 🕵️",
                    "數據正在即時同步，保持關注。📡",
                    "大數據分析完成，請參考雷達圖。📊",
                    "盤勢千變萬化，紀律才是核心。🧘"
                ]

                // Shuffle and take 2 random ones to mix with specific data comments
                const shuffled = [...personality].sort(() => 0.5 - Math.random())
                comments.push(...shuffled.slice(0, 2))

                // Fallback if empty
                if (comments.length === 0) return ["穩健觀察中... ☕", "盤整盤，喝杯咖啡再看吧。💤"]

                return comments
            }
            setAiComments(getComments())
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
            <NicknameDialog
                open={showRegister}
                onRegister={handleRegister}
                onClose={() => setShowRegister(false)}
            />

            {/* 1. Header Card (Overview) */}
            <div className="rounded-3xl border border-border/50 bg-card/50 p-8 shadow-xl backdrop-blur-sm relative overflow-hidden group">
                <div className="absolute top-0 left-0 w-full h-[2px] bg-primary/50 shadow-[0_0_15px_3px_rgba(59,130,246,0.5)] animate-scan opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"></div>
                <div className="absolute top-0 right-0 p-4 opacity-10 text-9xl">{isPositive ? "🐂" : "🐻"}</div>

                <div className="relative z-10 flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                    <div>
                        <div className="flex flex-wrap items-baseline gap-3">
                            <h2 className="text-4xl font-bold tracking-tight text-foreground">{data.symbol}</h2>
                            <div className="flex flex-wrap items-center gap-2">
                                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-zinc-800 text-zinc-400 border border-zinc-700">
                                    {EXCHANGE_TRANSLATIONS[data.exchange] || data.exchange}
                                </span>
                                {data.sector && data.sector !== '-' && (
                                    <span className="px-3 py-0.5 rounded-full text-xs bg-zinc-800/50 text-zinc-400 border border-zinc-700/50">
                                        {SECTOR_TRANSLATIONS[data.sector] || data.sector}
                                    </span>
                                )}
                            </div>
                        </div>
                        <p className="mt-1 text-2xl font-bold text-primary/90">{data.name || data.symbol}</p>

                        {/* Add to Portfolio Button */}
                        <button
                            onClick={handleAddToPortfolio}
                            disabled={adding}
                            className="mt-4 flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-sm font-bold text-primary-foreground hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {adding ? <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" /> : <PlusCircle className="h-4 w-4" />}
                            {adding ? "加入中..." : "加入追蹤"}
                        </button>
                        {/* Loop Typewriter */}
                        <div className="mt-4 min-h-[40px] inline-flex items-center rounded-2xl bg-primary/10 px-4 py-2 text-primary font-medium border border-primary/20">
                            <span className="mr-2">🤖</span>
                            <Typewriter
                                options={{
                                    strings: aiComments,
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

                <TechnicalEvidence
                    volume={data.volume}
                    marketCap={data.marketCap}
                    rvol={data.rvol}
                    vwap={data.vwap}
                    cmf={data.cmf}
                    price={data.price}
                />
            </div>

            {/* 3. Fundamental Health Check */}
            <HealthCheck data={data} />

            {/* 4. AI Analysis Grid */}
            <div className="grid gap-6 md:grid-cols-2">
                {/* AI Radar Chart */}
                <RadarCard data={data.radarData || []} />

                {/* Prediction Cone & Ratings */}
                <div className="flex flex-col gap-6">
                    <PredictionCard price={data.price} prediction={data.prediction} />

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

