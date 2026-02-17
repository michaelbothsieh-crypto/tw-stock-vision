import { Inter, JetBrains_Mono, Noto_Sans_TC } from 'next/font/google'
import "./globals.css"
import { Toaster } from "sonner";

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })
const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-jetbrains-mono' })
const notoSansTC = Noto_Sans_TC({ subsets: ['latin'], variable: '--font-noto-sans-tc', weight: ['400', '500', '700', '900'] })

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
