"use client"

import { AI_RadarChart } from "../ui/radar-chart"

interface RadarCardProps {
    data: any[]
}

export function RadarCard({ data }: RadarCardProps) {
    return (
        <div className="rounded-3xl border border-border/50 bg-card/30 p-6 shadow-lg backdrop-blur-sm relative overflow-hidden">
            <h3 className="text-xl font-semibold mb-2 flex items-center gap-2">
                <span className="text-2xl">🧬</span> AI 戰力分析 (Radar)
            </h3>
            <div className="h-[300px]">
                <AI_RadarChart data={data} />
            </div>
        </div>
    )
}
