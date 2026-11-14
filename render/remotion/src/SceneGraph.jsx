import React from 'react';
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame} from 'remotion';

// Interpolate one numeric property across keyframes [{frame, value}] (clamped, linear).
const track = (keys, frame, prop, fallback) => {
  const k = (keys || []).filter((x) => x[prop] !== undefined);
  if (k.length === 0) return fallback;
  if (k.length === 1) return k[0][prop];
  return interpolate(frame, k.map((x) => x.frame), k.map((x) => x[prop]), {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
};

// Drawing-state substitution: pick the approved state image active at this frame.
const activeSrc = (layer, frame) => {
  const s = (layer.states || []).find((st) => frame >= st.from_frame && frame <= st.to_frame);
  return s ? s.src : layer.src;
};

const Layer = ({layer, frame}) => {
  const x = track(layer.keyframes, frame, 'x', layer.x);
  const y = track(layer.keyframes, frame, 'y', layer.y);
  const r = track(layer.keyframes, frame, 'rotation', 0);
  const s = track(layer.keyframes, frame, 'scale', 1);
  const o = track(layer.keyframes, frame, 'opacity', 1);
  const px = layer.pivot ? layer.pivot[0] : 0;
  const py = layer.pivot ? layer.pivot[1] : 0;
  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: y,
        width: layer.w,
        height: layer.h,
        opacity: o,
        transformOrigin: `${px}px ${py}px`,
        transform: `rotate(${r}deg) scale(${s})`,
      }}
    >
      <Img src={staticFile(activeSrc(layer, frame))} style={{width: layer.w, height: layer.h}} />
      {(layer.children || []).map((c) => (
        <Layer key={c.id} layer={c} frame={frame} />
      ))}
    </div>
  );
};

export const SceneGraphComposition = ({scene}) => {
  const frame = useCurrentFrame();
  const cx = track(scene.camera.keyframes, frame, 'x', 0);
  const cy = track(scene.camera.keyframes, frame, 'y', 0);
  const cs = track(scene.camera.keyframes, frame, 'scale', 1);
  const roots = [...scene.layers].sort((a, b) => a.z - b.z);
  return (
    <AbsoluteFill style={{backgroundColor: scene.background || '#000000', overflow: 'hidden'}}>
      <div
        style={{
          position: 'absolute',
          width: scene.width,
          height: scene.height,
          transformOrigin: '0px 0px',
          transform: `translate(${-cx}px, ${-cy}px) scale(${cs})`,
        }}
      >
        {roots.map((l) => (
          <Layer key={l.id} layer={l} frame={frame} />
        ))}
      </div>
    </AbsoluteFill>
  );
};
