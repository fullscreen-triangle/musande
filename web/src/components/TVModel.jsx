'use client'

import { useRef, useEffect } from 'react'
import { useGLTF, useAnimations } from '@react-three/drei'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'

useGLTF.preload('/deep_impact_tv_from_the_matrix.glb')

export function TVModel({ gifRef }) {
  const group = useRef()
  const { nodes, materials, animations } = useGLTF('/deep_impact_tv_from_the_matrix.glb')
  const { actions } = useAnimations(animations, group)
  const screenMeshRef = useRef()
  const textureRef = useRef()

  useEffect(() => {
    const img = gifRef.current
    if (!img || !screenMeshRef.current) return

    const texture = new THREE.Texture(img)
    texture.minFilter = THREE.LinearFilter
    texture.magFilter = THREE.LinearFilter
    texture.flipY = false
    textureRef.current = texture

    screenMeshRef.current.material = new THREE.MeshBasicMaterial({
      map: texture,
      toneMapped: false,
    })

    return () => {
      texture.dispose()
      screenMeshRef.current?.material?.dispose()
    }
  }, [gifRef])

  // Mark texture as needing update every frame so the gif animates
  useFrame(() => {
    if (textureRef.current) {
      textureRef.current.needsUpdate = true
    }
  })

  return (
    <group ref={group} dispose={null}>
      <group name="Sketchfab_Scene">
        <group name="Sketchfab_model" rotation={[-Math.PI / 2, 0, 0]}>
          <group name="deep_impact_tvfbx" rotation={[Math.PI / 2, 0, 0]}>
            <group name="Object_2">
              <group name="RootNode">
                <group name="TV" position={[0, 0, -1850]}>
                  <mesh
                    name="TV_TV_0"
                    castShadow
                    receiveShadow
                    geometry={nodes.TV_TV_0.geometry}
                    material={materials.material}
                  />
                  <group name="Screen" position={[0, 0, 1850]}>
                    <mesh
                      ref={screenMeshRef}
                      name="Screen_screen_0"
                      castShadow
                      receiveShadow
                      geometry={nodes.Screen_screen_0.geometry}
                      material={materials.screen}
                    />
                  </group>
                </group>
              </group>
            </group>
          </group>
        </group>
      </group>
    </group>
  )
}