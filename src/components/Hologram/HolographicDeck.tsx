"use client";

import { useRef, useMemo } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { HolographicCard } from './HolographicCard';
import { useScroll, ScrollControls, DragControls } from '@react-three/drei';
import * as THREE from 'three';

interface HolographicDeckProps {
    stocks: any[];
}

export function HolographicDeck({ stocks }: HolographicDeckProps) {
    const groupRef = useRef<THREE.Group>(null);
    const radius = 6; // Radius of the cylinder

    // Create a cyclic list if few stocks to fill the circle partialy
    const displayStocks = stocks.length > 0 ? stocks : [];

    return (
        <group position={[0, -0.5, -2]}> {/* Push back a bit and center */}
            {displayStocks.map((stock, i) => {
                const count = displayStocks.length;
                // Arrange in a semi-circle or full circle depending on count
                // For a nice HUD feel, let's span about 120-180 degrees if few, or full 360 if many
                const angleStep = (Math.PI * 2) / Math.max(count, 8); // Minimum 8 slots spacing
                const angle = i * angleStep;

                const x = Math.sin(angle) * radius;
                const z = Math.cos(angle) * radius - radius; // Offset z so the first one is at z=0? No, cylinder center is at z-radius

                // Actually, let's place the camera at center (0,0,0) and arrange cards around it.
                // x = sin(a) * r, z = cos(a) * r

                const posX = Math.sin(angle) * radius;
                const posZ = Math.cos(angle) * radius;

                return (
                    <HolographicCard
                        key={stock.symbol || i}
                        stock={stock}
                        position={[posX, 0, posZ]}
                        rotation={[0, angle + Math.PI, 0]} // Face the center
                    />
                );
            })}
        </group>
    );
}

// Wrapper to handle rotation controls
export function DeckController({ children }: { children: React.ReactNode }) {
    const groupRef = useRef<THREE.Group>(null);
    const isDragging = useRef(false);
    const previousMouseX = useRef(0);
    const velocity = useRef(0);

    useFrame(() => {
        if (groupRef.current) {
            // Momentum
            if (!isDragging.current) {
                groupRef.current.rotation.y += velocity.current;
                velocity.current *= 0.95; // Friction
            }
        }
    });

    const onPointerDown = (e: any) => {
        isDragging.current = true;
        previousMouseX.current = e.clientX;
        velocity.current = 0;
    };

    const onPointerUp = () => {
        isDragging.current = false;
    };

    const onPointerMove = (e: any) => {
        if (isDragging.current && groupRef.current) {
            const delta = e.clientX - previousMouseX.current;
            groupRef.current.rotation.y += delta * 0.005;
            velocity.current = delta * 0.005;
            previousMouseX.current = e.clientX;
        }
    };

    return (
        <group
            ref={groupRef}
            onPointerDown={onPointerDown}
            onPointerUp={onPointerUp}
            onPointerLeave={onPointerUp}
            onPointerMove={onPointerMove}
        >
            {children}
        </group>
    );
}
