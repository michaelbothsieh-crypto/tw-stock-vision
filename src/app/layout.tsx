import { Inter, JetBrains_Mono, Noto_Sans_TC } from 'next/font/google'
import "./globals.css"
import { Toaster } from "sonner";

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',    // ✅ 先用系統字體，載入後替換，不阻塞 FCP
})
const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-jetbrains-mono',
  display: 'swap',
  preload: false,     // ✅ 非關鍵字體，不預載
})
const notoSansTC = Noto_Sans_TC({
  subsets: ['latin'],
  variable: '--font-noto-sans-tc',
  display: 'swap',
  weight: ['400', '700'],  // ✅ 只載入必要字重（移除 500, 900，節省 ~40KB）
})

export const metadata = {
  title: 'TwStockVision | 台股視覺化',
  description: '即時台灣股市視覺化洞察',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-Hant" className="dark">
      <body className={`${inter.variable} ${jetbrainsMono.variable} ${notoSansTC.variable} font-sans bg-background text-foreground antialiased`}>{children}<Toaster /></body>
    </html>
  )
}
