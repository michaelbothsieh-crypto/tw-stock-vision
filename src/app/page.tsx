/**
 * page.tsx — ISR Server Component
 *
 * ✅ 改造重點：
 * 1. 移除 'use client' — 改為 Server Component，支援 ISR
 * 2. export const revalidate = 300 — 每 5 分鐘重新生成，無白屏
 * 3. TW trending 資料在 SSR 階段預取，HTML 直接含資料
 * 4. 市場切換（TW/US）保留 client-side 互動（透過 MarketSwitcher）
 */

import { Suspense } from 'react'
import { DashboardClient } from '@/components/Neo/DashboardClient'

// ISR：每 5 分鐘重新生成靜態頁面
export const revalidate = 300

async function getTrendingData(market: 'TW' | 'US') {
    try {
        // 伺服器端直接呼叫 API（Next.js 內部路由）
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000'
        const res = await fetch(`${baseUrl}/api/stock?trending=true&market=${market}`, {
            next: { revalidate: 300 },
        })
        if (!res.ok) return []
        const data = await res.json()
        return Array.isArray(data) ? data : []
    } catch {
        return []
    }
}

export default async function Home() {
    // SSR 預取 TW trending（最常用市場）
    const initialData = await getTrendingData('TW')

    return (
        <main className="min-h-screen bg-[#050505] text-white font-sans lg:fixed lg:inset-0 lg:overflow-hidden">
            {/* Suspense 邊界：SSR 資料已預取，Suspense 只處理 client 互動部分 */}
            <Suspense fallback={
                <div className="flex h-full flex-col items-center justify-center space-y-4 font-mono text-emerald-500">
                    <div className="h-2 w-24 overflow-hidden rounded-full bg-zinc-800">
                        <div className="h-full w-full animate-pulse bg-emerald-500" />
                    </div>
                    <p className="text-sm">市場數據初始化中 (INITIALIZING)...</p>
                </div>
            }>
                <DashboardClient initialData={initialData} initialMarket="TW" />
            </Suspense>
        </main>
    )
}
