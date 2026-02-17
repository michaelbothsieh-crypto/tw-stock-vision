
'use client';

import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { Points, PointMaterial, Float, Html, Environment } from '@react-three/drei';
import * as THREE from 'three';

// 墨水個體組件
const InkCell = ({ stock, index, total }: { stock: any, index: number, total: number }) => {
    const meshRef = useRef<THREE.Mesh>(null);

    // 基於產業分配顏色
    const sectorColors: Record<string, string> = {
        'Technology': '#00f2ff',
        'Electronic Technology': '#00bfff',
        'Financial': '#4169e1',
        'Finance': '#4169e1',
        'Healthcare': '#00ff7f',
        'Energy': '#ffd700',
        'Producer Manufacturing': '#ff4500',
        'Consumer Durables': '#ff69b4',
        '-': '#ffffff'
    };

    const baseColor = useMemo(() => {
        return new THREE.Color(sectorColors[stock.sector] || '#ffffff');
    }, [stock.sector]);

    // 物理屬性對應
    const buoyancy = useMemo(() => (stock.changePercent || 0) / 10, [stock.changePercent]);
    const diffusion = useMemo(() => Math.min(1, Math.max(0, (stock.rvol || 1) / 5)), [stock.rvol]);

    useFrame((state) => {
        if (!meshRef.current) return;
        const time = state.clock.getElapsedTime();

        // 升騰與浮動邏輯
        meshRef.current.position.y += Math.sin(time + index) * 0.002 + (buoyancy * 0.001);
        meshRef.current.rotation.z += 0.001 * (1.0 + diffusion);

        // 呼吸律動
        const scale = 1 + Math.sin(time * 2 + index) * 0.05;
        meshRef.current.scale.set(scale, scale, scale);
    });

    // 隨機初始位置 (分群)
    const initialPos = useMemo(() => {
        const angle = (index / total) * Math.PI * 2;
        const radius = 2 + Math.random() * 3;
        return [Math.cos(angle) * radius, Math.sin(angle) * (radius * 0.5), Math.random() * 2];
    }, [index, total]);

    // 產業中文化映射
    const sectorMap: Record<string, string> = {
        'Technology': '科技',
        'Electronic Technology': '電子',
        'Financial': '金融',
        'Finance': '金融',
        'Healthcare': '醫療',
        'Energy': '能源',
        'Producer Manufacturing': '製造',
        'Consumer Durables': '耐久財',
        'Consumer Services': '服務',
        'Process Industries': '加工',
        'Utilities': '公用',
        'Communications': '通訊',
        'Industrial Services': '產服',
        '-': '其他'
    };
    const sectorName = sectorMap[stock.sector] || stock.sector;

    return (
        <Float speed={1.5} rotationIntensity={0.5} floatIntensity={0.5}>
            <mesh ref={meshRef} position={initialPos as any}>
                <sphereGeometry args={[0.2, 32, 32]} />
                <meshStandardMaterial
                    color={baseColor}
                    emissive={baseColor}
                    emissiveIntensity={Math.max(0.5, stock.technicalRating + 1)}
                    transparent
                    opacity={0.8}
                />
                <Html
                    position={[0, 0.4, 0]}
                    center
                    distanceFactor={10}
                    occlude
                >
                    <div className="flex flex-col items-center pointer-events-none select-none">
                        <span className="text-[8px] text-zinc-300 bg-black/50 px-1 rounded mb-0.5 backdrop-blur-[1px]">{sectorName}</span>
                        <div className="flex flex-col items-center bg-black/60 px-2 py-1 rounded backdrop-blur-[2px] border border-white/10">
                            <div className="whitespace-nowrap text-xs font-bold text-white/90 drop-shadow-md">
                                {stock.name}
                            </div>
                            <div className="flex items-center gap-1 mt-0.5">
                                <span className="text-[10px] text-zinc-200 font-mono">${stock.price}</span>
                                <span className={`text-[10px] font-mono font-bold ${stock.changePercent >= 0 ? 'text-red-400' : 'text-green-400'}`}>
                                    {stock.changePercent > 0 ? '+' : ''}{stock.changePercent}%
                                </span>
                            </div>
                        </div>
                    </div>
                </Html>
            </mesh>
        </Float>
    );
};

const FluidWorld = ({ stocks }: { stocks: any[] }) => {
    return (
        <div className="w-full h-screen bg-[#050505]">
            <Canvas camera={{ position: [0, 0, 10], fov: 45 }}>
                <color attach="background" args={['#020202']} />
                <ambientLight intensity={0.5} />
                <pointLight position={[10, 10, 10]} intensity={2} color="#00f2ff" />
                <spotLight position={[-10, 10, 10]} angle={0.15} penumbra={1} intensity={1} color="#ff00ff" />

                {stocks.map((stock, i) => (
                    <InkCell key={stock.symbol} stock={stock} index={i} total={stocks.length} />
                ))}

                <Environment preset="city" />

                {/* 背景粒子模擬介質 */}
                <Particles count={500} />
            </Canvas>
        </div>
    );
};

const Particles = ({ count }: { count: number }) => {
    const points = useMemo(() => {
        const p = new Float32Array(count * 3);
        for (let i = 0; i < count; i++) {
            p[i * 3] = (Math.random() - 0.5) * 20;
            p[i * 3 + 1] = (Math.random() - 0.5) * 10;
            p[i * 3 + 2] = (Math.random() - 0.5) * 10;
        }
        return p;
    }, [count]);

    useFrame((state) => {
        // 這裡可以加入粒子流動模擬
    });

    return (
        <Points positions={points} stride={3} frustumCulled={false}>
            <PointMaterial
                transparent
                color="#333"
                size={0.05}
                sizeAttenuation={true}
                depthWrite={false}
                blending={THREE.AdditiveBlending}
            />
        </Points>
    );
};

export default FluidWorld;
