'use client'

import { Suspense, useRef } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import * as THREE from 'three'
import { TVModel } from './TVModel'

export default function TVScene() {
  const gifRef = useRef(null)

  return (
    <div style={{ width: '100vw', height: '100vh', background: '#0a0a0a' }}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        ref={gifRef}
        src="/chase.gif"
        alt=""
        style={{ display: 'none' }}
        crossOrigin="anonymous"
      />
      <Canvas
        camera={{ position: [0, 0.5, 5], fov: 45 }}
        shadows
        gl={{
          antialias: true,
          toneMapping: THREE.ACESFilmicToneMapping,
          toneMappingExposure: 1.0,
        }}
      >
        <ambientLight intensity={0.4} />
        <directionalLight position={[-2, 4, 3]} intensity={1.2} castShadow />
        <spotLight position={[0, 6, 6]} intensity={0.6} angle={0.4} penumbra={0.8} />
        <Suspense fallback={null}>
          <TVModel gifRef={gifRef} />
        </Suspense>
        <OrbitControls
          enableZoom
          enablePan={false}
          minPolarAngle={Math.PI / 4}
          maxPolarAngle={Math.PI / 1.6}
          minDistance={2}
          maxDistance={20}
        />
      </Canvas>
    </div>
  )
}