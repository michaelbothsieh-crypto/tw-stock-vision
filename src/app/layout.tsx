import { Inter, JetBrains_Mono } from 'next/font/google'
import "./globals.css"
import { Toaster } from "sonner";

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })
const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-jetbrains-mono' })

export const metadata = {
  title: 'TwStockVision',
  description: 'Real-time Taiwan stock market insights',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} ${jetbrainsMono.variable} font-sans bg-background text-foreground antialiased`}>{children}<Toaster /></body>
    </html>
  )
}
