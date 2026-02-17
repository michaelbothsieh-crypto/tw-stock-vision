import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

export const BulletMetric = ({ label, value, target, unit = "" }: { label: string; value: number; target: number; unit?: string }) => {
    // 比例邏輯：將 target (產業平均) 固定在 70% 的位置
    // displayPercent = (實際值 / 平均值) * 70%
    // 處理無數據情況 (null, undefined, 0, NaN)
    const isValid = value !== null && value !== undefined && !Number.isNaN(value) && value !== 0;

    // 如果無效，進度條為 0
    // 如果有效，計算百分比，最大不超過 100%
    const displayPercent = isValid
        ? Math.min((value / (target || 1)) * 70, 100)
        : 0;

    return (
        <div className="mb-4">
            <div className="mb-1.5 flex justify-between text-[10px] font-mono">
                <span className="text-zinc-500">{label}</span>
                <span className="text-zinc-200">
                    {isValid ? `${value.toFixed(2)}${unit}` : <span className="text-zinc-600">--</span>}
                    <span className="ml-2 text-[9px] text-zinc-600">Avg: {target}{unit}</span>
                </span>
            </div>
            <div className="relative h-1 w-full rounded-full bg-zinc-900 overflow-hidden">
                {/* 輔助底色 (0-70% 代表低於/等於平均區間) - 僅在有數據時顯示微弱背景，或始終顯示 */}
                <div className="absolute left-0 top-0 h-full bg-white/[0.02]" style={{ width: '70%' }} />

                {/* 實際數值條 */}
                {isValid && (
                    <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${displayPercent}%` }}
                        className={cn(
                            "absolute left-0 top-0 h-full rounded-full transition-all duration-700",
                            displayPercent > 70
                                ? "bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.4)]"
                                : "bg-emerald-500"
                        )}
                    />
                )}

                {/* 產業平均標記線 (固定 70%) */}
                <div
                    className="absolute top-0 h-full w-[1.5px] bg-white/30 z-10"
                    style={{ left: '70%' }}
                />
            </div>
        </div>
    );
};
