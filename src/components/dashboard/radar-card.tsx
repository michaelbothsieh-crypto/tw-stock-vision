"use client"

import { AI_RadarChart } from "../ui/radar-chart"

interface RadarCardProps {
    data: any[]
}

export function RadarCard({ data }: RadarCardProps) {
    return (
        <div className="rounded-3xl border border-border/50 bg-card/30 p-6 shadow-lg backdrop-blur-sm relative overflow-hidden flex flex-col">
            <h3 className="text-xl font-semibold mb-2 flex items-center gap-2">
                <span className="text-2xl">🧬</span> AI 戰力分析 (Radar)
            </h3>
            <div className="h-[280px] w-full">
                <AI_RadarChart data={data} />
            </div>

            <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 gap-2">
                {data.map((item: any) => (
                    <div key={item.subject} className="bg-background/40 p-2 rounded-xl border border-white/5">
                        <div className="flex justify-between items-center mb-1">
                            <span className="text-[10px] text-muted-foreground">{item.subject}</span>
                            <span className="text-xs font-mono font-bold text-primary">{Math.round(item.A)}</span>
                        </div>
                        <div className="text-[10px] text-zinc-400 leading-tight">
                            {item.desc || "數據收集中"}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}
