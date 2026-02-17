import React, { useState, useEffect } from 'react';
import Gauge from './Gauge';
import Leaderboard from './Leaderboard';

interface CockpitProps {
    stocks: any[];
}

const Cockpit: React.FC<CockpitProps> = ({ stocks }) => {
    const [selectedIndex, setSelectedIndex] = useState(0);

    // Safety check if stocks is empty
    const currentStock = stocks[selectedIndex] || {
        symbol: '---',
        name: 'NO SIGNAL',
        price: 0,
        changePercent: 0,
        volume: 0
    };

    // Auto-select first stock if list changes and index is out of bounds
    useEffect(() => {
        if (selectedIndex >= stocks.length && stocks.length > 0) {
            setSelectedIndex(0);
        }
    }, [stocks, selectedIndex]);

    const isPositive = currentStock.changePercent >= 0;

    return (
        <div className="w-full h-full flex flex-col md:flex-row bg-[#050505] text-white overflow-hidden font-sans">
            {/* Main Instrument Cluster (Left/Center) */}
            <div className="flex-1 relative flex flex-col items-center justify-center p-8">

                {/* Background Grid/Mesh */}
                <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:50px_50px] pointer-events-none" />
                <div className="absolute inset-0 bg-radial-gradient(circle_at_center,transparent_0%,#000000_100%) pointer-events-none" />

                {/* Header Info */}
                <div className="absolute top-8 left-8 z-10">
                    <h1 className="text-4xl font-black italic tracking-tighter text-white/50">
                        {currentStock.symbol} ///
                    </h1>
                    <h2 className="text-2xl text-white font-bold mt-2">
                        {currentStock.name}
                    </h2>
                    <div className="flex gap-2 mt-4 text-xs font-mono text-zinc-500">
                        <span className="border border-zinc-800 px-2 py-1">TRACK_MODE: RACE</span>
                        <span className="border border-zinc-800 px-2 py-1">TC: OFF</span>
                        <span className="border border-zinc-800 px-2 py-1">ABS: OFF</span>
                    </div>
                </div>

                {/* Central Gauge Cluster */}
                <div className="relative z-10 transform scale-100 md:scale-125 transition-transform">
                    {/* The Big Tachometer (Change %) */}
                    <div className="relative">
                        <Gauge
                            value={currentStock.changePercent}
                            min={-10}
                            max={10}
                            label="MOMENTUM %"
                            size={500}
                            warningThreshold={9.5}  // Near limit up
                            criticalThreshold={9.9} // Limit up
                        />

                        {/* Digital Speedometer (Price) Inside */}
                        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 mt-8 text-center bg-black/80 backdrop-blur-xl p-4 rounded-xl border border-white/10 shadow-2xl">
                            <span className="block text-zinc-500 text-xs font-mono mb-1">PRICE (TWD)</span>
                            <span className={`text-6xl font-black tracking-tighter ${isPositive ? 'text-white' : 'text-white'}`}>
                                {currentStock.price}
                            </span>
                            <div className={`mt-2 text-xl font-bold font-mono ${isPositive ? 'text-red-500' : 'text-green-500'}`}>
                                {isPositive ? '▲' : '▼'} {Math.abs(currentStock.changePercent)}%
                            </div>
                        </div>
                    </div>

                    {/* Aux Gauges (Turbo/Volume) */}
                    <div className="absolute -right-24 bottom-10 transform scale-50 origin-bottom-left">
                        <Gauge
                            value={(currentStock.volume || 0) / 1000} // Simplified scaling
                            min={0}
                            max={50}
                            label="VOL (K)"
                            size={300}
                            type="turbo"
                        />
                    </div>
                </div>

                {/* Status Footer */}
                <div className="absolute bottom-8 w-full px-12 flex justify-between text-xs font-mono text-zinc-600">
                    <div>ENGINE_TEMP: PENDING</div>
                    <div>ERS_BATTERY: 100%</div>
                    <div>TIRE_COMP: SOFT</div>
                </div>
            </div>

            {/* Right Side Leaderboard */}
            <div className="w-full md:w-96 h-1/3 md:h-full z-20 shadow-2xl">
                <Leaderboard
                    stocks={stocks}
                    selectedIndex={selectedIndex}
                    onSelect={setSelectedIndex}
                />
            </div>
        </div>
    );
};

export default Cockpit;
