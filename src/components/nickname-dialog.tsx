"use client"

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Trophy } from 'lucide-react'

interface NicknameDialogProps {
    open: boolean
    onRegister: (name: string) => void
}

export function NicknameDialog({ open, onRegister }: NicknameDialogProps) {
    const [name, setName] = useState("")

    return (
        <AnimatePresence>
            {open && (
                <div className="fixed inset-0 z-50 flex items-center justify-center">
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="absolute inset-0 bg-black/80 backdrop-blur-sm"
                    />

                    {/* Dialog Content */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        className="relative w-full max-w-md bg-zinc-900 border border-zinc-800 rounded-2xl shadow-2xl p-8 mx-4"
                    >
                        <div className="flex flex-col items-center text-center mb-8">
                            <div className="w-16 h-16 bg-yellow-500/10 rounded-full flex items-center justify-center mb-6 text-yellow-500 ring-1 ring-yellow-500/20">
                                <Trophy className="w-8 h-8" />
                            </div>
                            <h2 className="text-3xl font-bold text-white mb-2">歡迎來到股市擂台</h2>
                            <p className="text-zinc-400">輸入一個響亮的代號<br />開始建立您的投資組合並與他人一較高下！</p>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <input
                                    type="text"
                                    placeholder="例如：少年股神、隔日沖主力..."
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    className="w-full bg-zinc-950/50 border border-zinc-800 text-white placeholder-zinc-600 rounded-xl px-4 py-4 text-lg focus:outline-none focus:ring-2 focus:ring-yellow-500/50 transition-all text-center"
                                    autoFocus
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter' && name) onRegister(name)
                                    }}
                                />
                            </div>
                            <button
                                onClick={() => name && onRegister(name)}
                                disabled={!name}
                                className="w-full bg-yellow-500 hover:bg-yellow-400 text-black font-bold text-lg py-4 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:scale-[1.02] active:scale-[0.98]"
                            >
                                開始挑戰
                            </button>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    )
}
