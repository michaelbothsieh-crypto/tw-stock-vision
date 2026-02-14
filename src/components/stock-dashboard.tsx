"use client"

import { useEffect, useState } from "react"
import { Activity, TrendingUp, DollarSign, ShieldCheck, AlertTriangle, Info, PlusCircle } from "lucide-react"
import { motion } from "framer-motion"
import confetti from "canvas-confetti"
import { cn } from "@/lib/utils"
import Typewriter from 'typewriter-effect';
import { AI_RadarChart } from "./ui/radar-chart"
import { toast } from "sonner"
import { useUser } from "@/hooks/use-user"
import { NicknameDialog } from "./nickname-dialog"
import { HealthCheck } from "./health-check"
import { RadarCard } from "./dashboard/radar-card"
import { PredictionCard } from "./dashboard/prediction-card"
import { TechnicalEvidence } from "./dashboard/technical-evidence"
import { StockData } from "./dashboard/types"
import { SECTOR_TRANSLATIONS, EXCHANGE_TRANSLATIONS } from "@/lib/constants"
import { InfoTooltip } from "./dashboard/vitals-grid"
import { STOCK_DEFINITIONS } from "@/lib/tooltips"

interface StockDashboardProps {
    data: StockData | null
    loading: boolean
    error?: string | null
}

export function StockDashboard({ data, loading, error }: StockDashboardProps) {
    const { user, register } = useUser()
    const [adding, setAdding] = useState(false)
    const [aiComments, setAiComments] = useState<string[]>(["分析數據中..."])
    const [showRegister, setShowRegister] = useState(false)

    const performAddToPortfolio = async (userId: string) => {
        if (!data) return
        setAdding(true)
        try {
            const res = await fetch('/api/index', {
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
                window.dispatchEvent(new CustomEvent('refresh-leaderboard'))
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
        if (!user) { setShowRegister(true); return }
        if (adding) return
        performAddToPortfolio(user.id)
    }

    const handleRegister = async (nickname: string) => {
        const newUser = await register(nickname)
        if (newUser) {
            setShowRegister(false)
            toast.success(`歡迎, ${newUser.nickname}! 即將加入追蹤...`)
            performAddToPortfolio(newUser.id)
        } else {
            toast.error("註冊失敗")
        }
    }

    useEffect(() => {
        if (data) {
            if (data.changePercent > 3) {
                const duration = 3 * 1000
                const animationEnd = Date.now() + duration
                const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 0 }
                const randomInRange = (min: number, max: number) => Math.random() * (max - min) + min
                const interval: any = setInterval(function () {
                    const timeLeft = animationEnd - Date.now()
                    if (timeLeft <= 0) return clearInterval(interval)
                    const particleCount = 50 * (timeLeft / duration)
                    confetti({ ...defaults, particleCount, origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 } })
                    confetti({ ...defaults, particleCount, origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 } })
                }, 250)
            }

            const getComments = () => {
                const comments: string[] = []
                const randomChoice = (arr: string[]) => arr[Math.floor(Math.random() * arr.length)]
                if (data.changePercent > 5) comments.push(randomChoice(["飛向宇宙，浩瀚無垠！🚀", "這漲幅... 難道是有內線？🤫", "多軍集結，全面進攻！⚔️"]))
                else if (data.changePercent < -5) comments.push(randomChoice(["這是在特價嗎？還是接刀？🔪", "別怕，這只是技術性調整... 吧？📉"]))
                if (data.rsi > 75) comments.push("RSI 過熱！少年股神請冷靜 🔥")
                else if (data.rsi < 25) comments.push("RSI 超賣！人棄我取... 嗎？💎")
                if (data.rvol > 2.5) comments.push("量能爆棚！主力在搞事？📢")
                const personality = ["SMC 指標顯示主力腳步移動中... 🕵️", "數據正在即時同步，保持關注。📡", "大數據分析完成，請參考雷達圖。📊"]
                const shuffled = [...personality].sort(() => 0.5 - Math.random())
                comments.push(...shuffled.slice(0, 2))
                return comments.length === 0 ? ["穩健觀察中... ☕", "盤整盤，喝杯咖啡再看吧。💤"] : comments
            }
            setAiComments(getComments())
        }
    }, [data])

    if (loading) return <div className="flex h-64 items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>
    if (error) return <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-4 text-destructive">錯誤: {error}</div>
    if (!data) return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="text-center py-12 rounded-3xl border border-dashed border-zinc-800 bg-zinc-900/20">
                <div className="text-5xl mb-4">🔍</div>
                <h3 className="text-xl font-bold mb-2">開始您的數據洞察</h3>
                <p className="text-zinc-500 max-w-sm mx-auto text-sm">在上方輸入代號獲取 AI 驅動分析。</p>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
                {[
                    { emoji: "📊", title: "SMC 籌碼洞察", desc: "偵測異常爆量與資金流向，追蹤機構成本線。", def: "SMC 電腦評分" },
                    { emoji: "🩺", title: "每日健檢", desc: "均線排列趨勢與波動度控管。", def: "RSI" },
                    { emoji: "⚡", title: "AI 戰力評級", desc: "五大維度綜合評等與目標價參考。", def: "技術評級" },
                    { emoji: "💰", title: "財務健康", desc: "毛利率、F-Score 與葛拉漢指數分析。", def: "F-Score" }
                ].map((item, i) => (
                    <div key={i} className="p-6 rounded-3xl bg-zinc-900/50 border border-zinc-800 space-y-3">
                        <div className="flex justify-between items-start">
                            <div className="text-2xl">{item.emoji}</div>
                            <InfoTooltip content={STOCK_DEFINITIONS[item.def]} />
                        </div>
                        <h4 className="font-bold">{item.title}</h4>
                        <p className="text-xs text-zinc-500 leading-relaxed">{item.desc}</p>
                    </div>
                ))}
            </div>
        </div>
    )

    const isPositive = data.change >= 0

    return (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="grid gap-6">
            <NicknameDialog open={showRegister} onRegister={handleRegister} onClose={() => setShowRegister(false)} />
            <div className="rounded-3xl border border-border/50 bg-card/50 p-8 shadow-xl backdrop-blur-sm relative overflow-hidden group">
                <div className="absolute top-0 left-0 w-full h-[2px] bg-primary/50 shadow-[0_0_15px_3px_rgba(59,130,246,0.5)] animate-scan opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"></div>
                <div className="absolute top-0 right-0 p-4 opacity-10 text-9xl">{isPositive ? "🐂" : "🐻"}</div>
                <div className="relative z-10 flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                    <div>
                        <div className="flex flex-wrap items-baseline gap-3">
                            <h2 className="text-4xl font-bold tracking-tight text-foreground">{data.symbol}</h2>
                            <div className="flex flex-wrap items-center gap-2">
                                <span className="px-2.5 py-1 rounded text-xs font-bold bg-zinc-800 text-zinc-300 border border-zinc-700">{EXCHANGE_TRANSLATIONS[data.exchange] || data.exchange}</span>
                                {data.sector && data.sector !== '-' && <span className="px-3 py-1 rounded-full text-xs bg-zinc-800/50 text-zinc-300 border border-zinc-700/50">{SECTOR_TRANSLATIONS[data.sector] || data.sector}</span>}
                            </div>
                        </div>
                        <p className="mt-1 text-2xl font-bold text-primary/90">{data.name || data.symbol}</p>
                        <button onClick={handleAddToPortfolio} disabled={adding} className="mt-4 flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-sm font-bold text-primary-foreground hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20 disabled:opacity-50">
                            {adding ? <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" /> : <PlusCircle className="h-4 w-4" />}
                            {adding ? "加入中..." : "加入追蹤"}
                        </button>
                        <div className="mt-4 min-h-[60px] md:min-h-[48px] flex items-center rounded-2xl bg-primary/10 px-4 py-2 text-primary font-medium border border-primary/20 overflow-hidden">
                            <span className="mr-2 flex-shrink-0">🤖</span>
                            <div className="flex-1 text-sm md:text-base">
                                <Typewriter options={{ strings: aiComments, autoStart: true, loop: true, delay: 50, deleteSpeed: 30, cursor: '▋' }} />
                            </div>
                        </div>
                    </div>
                    <div className={cn("flex flex-col items-end text-right", isPositive ? "text-emerald-400" : "text-rose-400")}>
                        <h3 className="text-xs md:text-sm font-bold text-zinc-400 uppercase tracking-widest mb-1">即時報價</h3>
                        <span className="text-6xl font-black font-mono tracking-tighter shadow-glow leading-none">{(Number(data.price) || 0).toFixed(2)}</span>
                        <div className="flex items-center gap-2 text-xl font-bold mt-2">
                            <span>{isPositive ? "▲" : "▼"} {(Number(data.change) || 0).toFixed(2)}</span>
                            <span className="opacity-80">({(Number(data.changePercent) || 0).toFixed(2)}%)</span>
                        </div>
                    </div>
                </div>
                <TechnicalEvidence volume={data.volume} marketCap={data.marketCap} rvol={data.rvol} vwap={data.vwap} cmf={data.cmf} price={data.price} />
            </div>
            <HealthCheck data={data} />
            <div className="grid gap-6 md:grid-cols-2">
                <RadarCard data={data.radarData || []} />
                <div className="flex flex-col gap-6">
                    <PredictionCard price={data.price} prediction={data.prediction} />
                    <div className="flex-1 rounded-3xl border border-border/50 bg-black/20 p-6 shadow-xl backdrop-blur-sm relative overflow-hidden group/target">
                        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent opacity-0 group-hover/target:opacity-100 transition-opacity duration-500" />

                        <div className="relative z-10">
                            <div className="flex justify-between items-center mb-6">
                                <div className="flex items-center gap-2">
                                    <h3 className="text-xs md:text-sm font-bold text-zinc-400 uppercase tracking-[0.12em] flex items-center gap-2">
                                        <TrendingUp className="h-4 w-4" /> 目標價與評級
                                    </h3>
                                    <InfoTooltip content={STOCK_DEFINITIONS["分析師評語"]} />
                                </div>
                                <div className={cn("px-2.5 py-1 rounded-lg text-xs font-bold border shadow-md transition-colors", (data.targetPrice || 0) > data.price ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-zinc-500/10 text-zinc-400 border-zinc-500/20")}>
                                    {data.targetPrice && data.price ? `${(((data.targetPrice) - data.price) / data.price * 100).toFixed(1)}% Upside` : "- % Upside"}
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-1.5">
                                    <div className="text-xs text-zinc-400 font-bold uppercase tracking-wider">一年預測目標</div>
                                    <div className="text-3xl font-black font-mono text-zinc-100">
                                        {data.targetPrice && data.targetPrice > 0 ? data.targetPrice.toFixed(1) : "--"}
                                    </div>
                                </div>

                                <div className="space-y-3.5">
                                    <div className="flex items-center justify-between">
                                        <div className="text-xs text-zinc-400 font-bold uppercase">分析師評級</div>
                                        <div className="text-xs md:text-sm font-bold text-zinc-200">{getAnalystText(data.analystRating || 3)}</div>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <div className="text-xs text-zinc-400 font-bold uppercase">技術評級</div>
                                        <div className="text-xs md:text-sm font-bold" style={{ color: getRatingColor(data.technicalRating) }}>{getRatingText(data.technicalRating)}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div className="text-center text-xs text-zinc-500 font-medium tracking-wide uppercase mt-6 mb-8 px-4 leading-relaxed">
                * SMC 指標及 AI 預測僅供參考，不構成投資建議。
            </div>
        </motion.div>
    )
}

function getAnalystText(val: number) {
    if (val <= 1.5) return "💎 強力買進"
    if (val <= 2.5) return "✅ 買進"
    if (val <= 3.5) return "⚖️ 中立 / 觀望"
    if (val <= 4.5) return "⚠️ 賣出"
    return "🚫 強力賣出"
}

function getRatingColor(val: number) {
    if (val > 0.5) return "#34d399"
    if (val > 0.1) return "#22c55e"
    if (val < -0.5) return "#f43f5e"
    if (val < -0.1) return "#e11d48"
    return "#a1a1aa"
}

function getRatingText(val: number) {
    if (val > 0.5) return "💪 強力買進"
    if (val > 0.1) return "💰 買進"
    if (val < -0.5) return "📉 強力賣出"
    if (val < -0.1) return "💸 賣出"
    return "😐 觀望 / 中立"
}
