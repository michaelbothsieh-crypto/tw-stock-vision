import React from 'react';

interface StockData {
    symbol: string;
    name: string;
    price: number;
    changePercent: number;
    volume?: number;
}

interface LeaderboardProps {
    stocks: StockData[];
    selectedIndex: number;
    onSelect: (index: number) => void;
}

const Leaderboard: React.FC<LeaderboardProps> = ({ stocks, selectedIndex, onSelect }) => {
    return (
        <div className="h-full w-full bg-black/80 border-l border-white/10 flex flex-col backdrop-blur-md">
            <div className="p-4 border-b border-white/10 bg-gradient-to-r from-red-600/20 to-transparent">
                <h2 className="text-xl font-black italic tracking-tighter text-white">
                    RACE POS <span className="text-red-500">///</span>
                </h2>
            </div>

            <div className="flex-1 overflow-y-auto overflow-x-hidden scrollbar-hide">
                <table className="w-full text-left border-collapse">
                    <thead className="text-xs text-zinc-500 font-mono sticky top-0 bg-black/90 z-10 border-b border-white/10">
                        <tr>
                            <th className="p-2 w-10 text-center">#</th>
                            <th className="p-2">DRIVER</th>
                            <th className="p-2 text-right">LAP TIME</th>
                            <th className="p-2 text-right">GAP</th>
                        </tr>
                    </thead>
                    <tbody className="font-mono text-sm">
                        {stocks.map((stock, index) => {
                            const isSelected = index === selectedIndex;
                            const isPositive = stock.changePercent >= 0;

                            return (
                                <tr
                                    key={stock.symbol}
                                    onClick={() => onSelect(index)}
                                    className={`
                                        cursor-pointer transition-colors duration-100 border-b border-white/5
                                        ${isSelected ? 'bg-white text-black font-bold' : 'text-zinc-400 hover:bg-white/10'}
                                    `}
                                >
                                    <td className={`p-2 text-center text-xs ${isSelected ? 'text-black' : 'text-zinc-600'}`}>
                                        {index + 1}
                                    </td>
                                    <td className="p-2">
                                        <div className="flex flex-col leading-none">
                                            <span className="text-xs opacity-70 mb-0.5">{stock.symbol}</span>
                                            <span className="truncate max-w-[100px]">{stock.name}</span>
                                        </div>
                                    </td>
                                    <td className="p-2 text-right">
                                        {stock.price}
                                    </td>
                                    <td className={`p-2 text-right ${!isSelected ? (isPositive ? 'text-red-500' : 'text-green-500') : ''}`}>
                                        {isPositive ? '+' : ''}{stock.changePercent}%
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default Leaderboard;
