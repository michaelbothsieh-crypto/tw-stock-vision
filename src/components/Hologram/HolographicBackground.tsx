"use client";

import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Points, PointMaterial } from '@react-three/drei';
import * as THREE from 'three';

export function HolographicBackground() {
    return (
        <group>
            <Stars />
            <GridFloors />
        </group>
    );
}

function Stars() {
    const ref = useRef<THREE.Points>(null);
    const sphere = new Float32Array(5000 * 3);
    for (let i = 0; i < 5000; i++) {
        const r = 40 * Math.cbrt(Math.random());
        const theta = Math.random() * 2 * Math.PI;
        const phi = Math.acos(2 * Math.random() - 1);
        const x = r * Math.sin(phi) * Math.cos(theta);
        const y = r * Math.sin(phi) * Math.sin(theta);
        const z = r * Math.cos(phi);
        sphere[i * 3] = x;
        sphere[i * 3 + 1] = y;
        sphere[i * 3 + 2] = z;
    }

    useFrame((state, delta) => {
        if (ref.current) {
            ref.current.rotation.x -= delta / 10;
            ref.current.rotation.y -= delta / 15;
        }
    });

    return (
        <group rotation={[0, 0, Math.PI / 4]}>
            <Points ref={ref} positions={sphere} stride={3} frustumCulled={false}>
                <PointMaterial
                    transparent
                    color="#00aaff"
                    size={0.05}
                    sizeAttenuation={true}
                    depthWrite={false}
                    blending={THREE.AdditiveBlending}
                />
            </Points>
        </group>
    );
}

function GridFloors() {
    return (
        <gridHelper args={[100, 100, 0x111111, 0x050505]} position={[0, -5, 0]} />
    )
}
