"use client";

import { Canvas } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Environment } from '@react-three/drei';
import { HolographicDeck, DeckController } from './HolographicDeck';
import { HolographicBackground } from './HolographicBackground';
import { Suspense } from 'react';
import * as THREE from 'three';

interface HolographicWorldProps {
    stocks: any[];
}

export default function HolographicWorld({ stocks }: HolographicWorldProps) {
    return (
        <div className="w-full h-full relative">
            <Canvas
                dpr={[1, 2]}
                gl={{
                    antialias: true,
                    alpha: false,
                    toneMapping: THREE.ACESFilmicToneMapping,
                    toneMappingExposure: 1.2
                }}
            >
                <color attach="background" args={['#050505']} />

                {/* Camera */}
                <PerspectiveCamera makeDefault position={[0, 2, 14]} fov={35} />

                {/* Controls: Allow orbit but restrict angles to keep user focused */}
                <OrbitControls
                    enableZoom={true}
                    minDistance={8}
                    maxDistance={25}
                    enablePan={false}
                    maxPolarAngle={Math.PI / 2 + 0.2} // Don't go too low
                    minPolarAngle={Math.PI / 3} // Don't go too high
                />

                {/* Lighting */}
                <ambientLight intensity={0.2} />
                <spotLight position={[10, 10, 10]} angle={0.15} penumbra={1} intensity={1} castShadow />
                <pointLight position={[-10, -5, -10]} intensity={0.5} color="#0040ff" />

                {/* Content */}
                <Suspense fallback={null}>
                    {/* Environment is key for Glass Material reflections */}
                    <Environment preset="city" background={false} />

                    <HolographicBackground />

                    <DeckController>
                        <HolographicDeck stocks={stocks} />
                    </DeckController>
                </Suspense>
            </Canvas>
        </div>
    );
}
