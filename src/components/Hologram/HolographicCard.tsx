"use client";

import { useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html, MeshTransmissionMaterial, RoundedBox } from '@react-three/drei';
import * as THREE from 'three';

interface HolographicCardProps {
    stock: {
        symbol: string;
        name: string;
        price: number;
        changePercent: number;
        sector: string;
    };
    position: [number, number, number];
    rotation: [number, number, number];
}

export function HolographicCard({ stock, position, rotation }: HolographicCardProps) {
    const meshRef = useRef<THREE.Mesh>(null);
    const [hovered, setHover] = useState(false);

    // Animation for hover effect
    useFrame((state, delta) => {
        if (meshRef.current) {
            // Gentle float
            meshRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime + position[0]) * 0.1;

            // Hover scale and emission
            const targetScale = hovered ? 1.1 : 1;
            meshRef.current.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), delta * 5);
        }
    });

    const isPositive = stock.changePercent >= 0;
    const color = isPositive ? '#ef4444' : '#22c55e'; // Red for up, Green for down

    return (
        <group position={position} rotation={rotation}>
            <mesh
                ref={meshRef}
                onPointerOver={() => setHover(true)}
                onPointerOut={() => setHover(false)}
            >
                <RoundedBox args={[3, 4.5, 0.1]} radius={0.1} smoothness={4}>
                    {/* Glass Material */}
                    <MeshTransmissionMaterial
                        backside
                        samples={16}
                        resolution={512}
                        transmission={1}
                        roughness={0.2}
                        clearcoat={1}
                        clearcoatRoughness={0.1}
                        thickness={0.2}
                        ior={1.5}
                        chromaticAberration={0.06}
                        anisotropy={0.1}
                        distortion={0.1}
                        distortionScale={0.3}
                        temporalDistortion={0.5}
                        attenuationDistance={0.5}
                        attenuationColor="#ffffff"
                        color={hovered ? '#e0f2fe' : '#ffffff'}
                        background={new THREE.Color('#000000')}
                    />
                </RoundedBox>

                {/* Content Overlay */}
                <Html
                    transform
                    occlude="blending"
                    position={[0, 0, 0.06]} // Slightly in front of the glass
                    style={{
                        width: '280px',
                        height: '420px',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'space-between',
                        padding: '24px',
                        background: 'transparent',
                        color: 'white',
                        fontFamily: "'Noto Sans TC', sans-serif",
                        pointerEvents: 'none', // Allow clicks to pass through to mesh
                        userSelect: 'none',
                    }}
                >
                    {/* Header */}
                    <div className="flex justify-between items-start">
                        <div>
                            <div className="text-xs text-blue-300 font-mono tracking-widest uppercase mb-1">{stock.symbol}</div>
                            <div className="text-lg font-bold leading-tight">{stock.name}</div>
                        </div>
                        <div className="text-[10px] bg-white/10 px-1.5 py-0.5 rounded text-zinc-300 backdrop-blur-md border border-white/5">
                            {stock.sector || 'ETF'}
                        </div>
                    </div>

                    {/* Sparkline Placeholder (Can be real SVG line later) */}
                    <div className="flex-1 flex items-center justify-center opacity-30">
                        {/* Simple CSS waveform for now */}
                        <div className="w-full h-16 border-b border-dashed border-white/20 relative">
                            <div className={`absolute bottom-0 left-0 w-full h-full bg-gradient-to-t ${isPositive ? 'from-red-500/20' : 'from-green-500/20'} to-transparent`} style={{ maskImage: 'linear-gradient(to right, transparent, black)' }}></div>
                        </div>
                    </div>

                    {/* Footer Data */}
                    <div>
                        <div className="flex items-baseline gap-1">
                            <span className="text-4xl font-black tracking-tighter drop-shadow-[0_0_10px_rgba(255,255,255,0.3)]">
                                {stock.price}
                            </span>
                            <span className="text-xs text-zinc-400">TWD</span>
                        </div>

                        <div className={`text-sm font-bold font-mono mt-1 ${isPositive ? 'text-red-400 drop-shadow-[0_0_8px_rgba(239,68,68,0.6)]' : 'text-green-400 drop-shadow-[0_0_8px_rgba(34,197,94,0.6)]'}`}>
                            {isPositive ? '▲' : '▼'} {stock.changePercent > 0 ? '+' : ''}{stock.changePercent}%
                        </div>
                    </div>
                </Html>
            </mesh>
        </group>
    );
}
