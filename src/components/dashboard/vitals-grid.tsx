"use client"

import { cn } from "@/lib/utils"
import { Info } from "lucide-react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { STOCK_DEFINITIONS } from "@/lib/tooltips"

export const InfoTooltip = ({ content }: { content: string }) => (
    <TooltipProvider>
        <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
                <div className="p-1 hover:bg-white/10 rounded-full transition-colors cursor-help group/info">
                    <Info className="h-3.5 w-3.5 text-zinc-500 group-hover/info:text-zinc-300 transition-colors" />
                </div>
            </TooltipTrigger>
            <TooltipContent className="max-w-[240px] bg-zinc-900 border-zinc-800 text-zinc-200 text-xs leading-relaxed shadow-xl p-3" sideOffset={5}>
                {content}
            </TooltipContent>
        </Tooltip>
    </TooltipProvider>
)

export function VitalRow({ label, value, status }: { label: string, value: string, status: "good" | "bad" | "warning" | "neutral" }) {
    const colors = {
        good: "text-emerald-400 bg-emerald-400/10 border-emerald-400/20",
        bad: "text-rose-400 bg-rose-400/10 border-rose-400/20",
        warning: "text-amber-400 bg-amber-400/10 border-amber-400/20",
        neutral: "text-zinc-400 bg-zinc-400/10 border-zinc-400/20"
    }

    const definition = STOCK_DEFINITIONS[label] || STOCK_DEFINITIONS[label.replace(" (TTM)", "")] || STOCK_DEFINITIONS[label.split(' ')[0]];

    return (
        <div className="flex items-center justify-between p-3 rounded-xl border border-white/5 bg-white/5 group hover:bg-white/10 transition-colors">
            <div className="flex items-center gap-1.5">
                <span className="text-xs font-bold text-zinc-500 uppercase tracking-tighter">{label}</span>
                {definition && <InfoTooltip content={definition} />}
            </div>
            <span className={cn("text-sm font-mono font-bold px-2 py-0.5 rounded border", colors[status])}>
                {value}
            </span>
        </div>
    )
}

export function Gauge({ value, min, max }: { value: number, min: number, max: number }) {
    const percentage = Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100))
    const color = percentage > 70 ? "bg-emerald-500" : percentage > 40 ? "bg-amber-500" : "bg-zinc-500"

    return (
        <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
            <div
                className={cn("h-full transition-all duration-1000 ease-out", color)}
                style={{ width: `${percentage}%` }}
            />
        </div>
    )
}
