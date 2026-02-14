"use client"

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Trophy } from 'lucide-react'
import { useUser } from '@/hooks/use-user'
import { toast } from 'sonner'

interface NicknameDialogProps {
    open: boolean
    onRegister: (name: string) => void
    onClose?: () => void
}

export function NicknameDialog({ open, onRegister, onClose }: NicknameDialogProps) {
    const [name, setName] = useState("")
    const [mode, setMode] = useState<'register' | 'recover'>('register')
    const [recoverId, setRecoverId] = useState("")
    const [existingUsers, setExistingUsers] = useState<{ id: string, nickname: string }[] | null>(null)
    const { user, loginWithId, fetchUsers } = useUser()

    useState(() => {
        if (open) {
            fetchUsers().then(setExistingUsers)
        }
    })

    const handleRecover = async (id?: string) => {
        const targetId = id || recoverId
        if (!targetId) return
        const success = await loginWithId(targetId)
        if (success && onClose) onClose()
    }

    const copyId = () => {
        if (user?.id) {
            navigator.clipboard.writeText(user.id)
            toast.success("ID 已複製到剪貼簿")
        }
    }

    return (
        <AnimatePresence>
            {open && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="absolute inset-0 bg-black/80 backdrop-blur-sm cursor-pointer"
                    />

                    {/* Dialog Content */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        className="relative w-full max-w-sm bg-zinc-900 border border-zinc-800 rounded-2xl shadow-2xl p-6 md:p-8 overflow-hidden"
                    >
                        <div className="flex flex-col items-center text-center mb-6">
                            <button
                                onClick={onClose}
                                className="absolute top-4 right-4 p-2 text-zinc-500 hover:text-white transition-colors"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                            </button>

                            <div className="w-12 h-12 bg-yellow-500/10 rounded-full flex items-center justify-center mb-4 text-yellow-500 ring-1 ring-yellow-500/20">
                                <Trophy className="w-6 h-6" />
                            </div>
                            <h2 className="text-2xl font-bold text-white mb-2">{mode === 'register' ? '歡迎來到股市擂台' : '帳號恢復'}</h2>
                            <p className="text-xs text-zinc-400">
                                {mode === 'register'
                                    ? '輸入一個響亮的代號開始排位賽'
                                    : '請選擇現有使用者或輸入 UUID'}
                            </p>
                        </div>

                        {mode === 'register' ? (
                            <div className="space-y-4">
                                <input
                                    type="text"
                                    placeholder="例如：少年股神..."
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    className="w-full bg-zinc-950/50 border border-zinc-800 text-white placeholder-zinc-600 rounded-xl px-4 py-3 text-lg focus:outline-none focus:ring-2 focus:ring-yellow-500/50 transition-all text-center"
                                    autoFocus
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter' && name) onRegister(name)
                                    }}
                                />
                                <button
                                    onClick={() => name && onRegister(name)}
                                    disabled={!name}
                                    className="w-full bg-yellow-500 hover:bg-yellow-400 text-black font-bold py-3 rounded-xl transition-all disabled:opacity-50 hover:scale-[1.02] active:scale-[0.98]"
                                >
                                    {user ? "儲存名稱" : "開始挑戰"}
                                </button>

                                {existingUsers && !user && existingUsers.length > 0 && (
                                    <div className="space-y-2">
                                        <div className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest text-center">快速切換現有使用者</div>
                                        <div className="flex flex-wrap gap-2 justify-center max-h-32 overflow-y-auto p-1 custom-scrollbar">
                                            {existingUsers.slice(0, 5).map(u => (
                                                <button
                                                    key={u.id}
                                                    onClick={() => handleRecover(u.id)}
                                                    className="px-3 py-1.5 bg-zinc-800/50 hover:bg-zinc-700 text-zinc-300 rounded-lg text-xs transition-colors border border-zinc-700/50"
                                                >
                                                    {u.nickname}
                                                </button>
                                            ))}
                                            <button
                                                onClick={() => setMode('recover')}
                                                className="px-3 py-1.5 bg-zinc-800/20 text-zinc-500 rounded-lg text-xs hover:text-zinc-300 transition-colors"
                                            >
                                                更多...
                                            </button>
                                        </div>
                                    </div>
                                )}

                                {user && (
                                    <div className="pt-4 border-t border-zinc-800">
                                        <div className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest mb-2">您的專屬 ID (請備份以供跨裝置使用)</div>
                                        <div
                                            onClick={copyId}
                                            className="bg-black/40 rounded-lg p-2 text-[10px] font-mono text-zinc-400 break-all cursor-pointer hover:bg-black/60 transition-colors border border-dashed border-zinc-700"
                                        >
                                            {user.id}
                                        </div>
                                    </div>
                                )}

                                {!user && !existingUsers?.length && (
                                    <button
                                        onClick={() => setMode('recover')}
                                        className="w-full text-xs text-zinc-500 hover:text-zinc-300 transition-colors font-medium"
                                    >
                                        已有帳號？點此輸入 ID 恢復
                                    </button>
                                )}
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {existingUsers && existingUsers.length > 0 && (
                                    <div className="space-y-2">
                                        <select
                                            onChange={(e) => handleRecover(e.target.value)}
                                            className="w-full bg-zinc-950/50 border border-zinc-800 text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-yellow-500/50 transition-all appearance-none cursor-pointer"
                                            defaultValue=""
                                        >
                                            <option value="" disabled>點此選擇現有使用者</option>
                                            {existingUsers.map(u => (
                                                <option key={u.id} value={u.id}>{u.nickname}</option>
                                            ))}
                                        </select>
                                        <div className="text-[10px] text-zinc-500 text-center">— 或輸入 UUID 手動恢復 —</div>
                                    </div>
                                )}
                                <input
                                    type="text"
                                    placeholder="輸入 ID (UUID)"
                                    value={recoverId}
                                    onChange={(e) => setRecoverId(e.target.value)}
                                    className="w-full bg-zinc-950/50 border border-zinc-800 text-white placeholder-zinc-600 rounded-xl px-4 py-3 text-[10px] font-mono focus:outline-none focus:ring-2 focus:ring-yellow-500/50 transition-all text-center"
                                    autoFocus
                                />
                                <div className="flex gap-2">
                                    <button
                                        onClick={() => setMode('register')}
                                        className="flex-1 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 font-bold py-3 rounded-xl transition-all"
                                    >
                                        返回
                                    </button>
                                    <button
                                        onClick={() => handleRecover()}
                                        disabled={!recoverId}
                                        className="flex-[2] bg-yellow-500 hover:bg-yellow-400 text-black font-bold py-3 rounded-xl transition-all disabled:opacity-50"
                                    >
                                        恢復帳號
                                    </button>
                                </div>
                            </div>
                        )}
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    )
}
