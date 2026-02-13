"use client"

import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog" // Need to ensure shadcn Dialog exists or standard one
import { motion, AnimatePresence } from 'framer-motion'
import { Trophy } from 'lucide-react'

interface NicknameDialogProps {
    open: boolean
    onRegister: (name: string) => void
}

export function NicknameDialog({ open, onRegister }: NicknameDialogProps) {
    const [name, setName] = useState("")

    if (!open) return null

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="w-full max-w-md bg-zinc-900 border border-zinc-800 rounded-2xl shadow-2xl p-6"
            >
                <div className="flex flex-col items-center text-center mb-6">
                    <div className="w-12 h-12 bg-yellow-500/20 rounded-full flex items-center justify-center mb-4 text-yellow-500">
                        <Trophy className="w-6 h-6" />
                    </div>
                    <h2 className="text-2xl font-bold text-white">歡迎來到股市擂台</h2>
                    <p className="text-zinc-400 mt-2">輸入一個響亮的代號，開始建立您的投資組合並與他人一較高下！</p>
                </div>

                <div className="space-y-4">
                    <input
                        type="text"
                        placeholder="例如：少年股神、隔日沖主力..."
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        className="w-full bg-zinc-800 border-zinc-700 text-white placeholder-zinc-500 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-yellow-500/50"
                        autoFocus
                    />
                    <button
                        onClick={() => name && onRegister(name)}
                        disabled={!name}
                        className="w-full bg-yellow-500 hover:bg-yellow-400 text-black font-bold py-3 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        開始挑戰
                    </button>
                </div>
            </motion.div>
        </div>
    )
}
