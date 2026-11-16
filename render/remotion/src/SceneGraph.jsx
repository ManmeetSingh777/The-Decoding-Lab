import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame} from 'remotion';

// Interpolate one numeric property across keyframes [{frame, value, easing?}] (clamped).
// R3 F13: the easing of each segment is taken from the keyframe that ENDS it, as compiled from a skill-owned motion program
// ('hold' = stepped/held, 'ease_in_out' = cubic in-out). Keys without an easing (legacy / diagnostic scenes) interpolate linearly.
const EASE = {ease_in_out: Easing.inOut(Easing.cubic)};
const track = (keys, frame, prop, fallback) => {
  const k = (keys || []).filter((x) => x[prop] !== undefined).sort((a, b) => a.frame - b.frame);
  if (k.length === 0) return fallback;
  if (k.length === 1 || frame <= k[0].frame) return k[0][prop];
  if (frame >= k[k.length - 1].frame) return k[k.length - 1][prop];
  let i = 0;
  while (i < k.length - 1 && frame > k[i + 1].frame) i += 1;
  const a = k[i];
  const b = k[i + 1];
  if (b.easing === 'hold') return frame >= b.frame ? b[prop] : a[prop];
  return interpolate(frame, [a.frame, b.frame], [a[prop], b[prop]], {
    easing: EASE[b.easing] || ((t) => t),
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
};

// Drawing-state substitution: pick the approved state image active at this frame.
const activeSrc = (layer, frame) => {
  const s = (layer.states || []).find((st) => frame >= st.from_frame && frame <= st.to_frame);
  return s ? s.src : layer.src;
};

// R3-C03: per-layer attention (brightness / local scale) executes the skill-selected mechanism on the TARGET layers only.
const Layer = ({layer, frame}) => {
  const x = track(layer.keyframes, frame, 'x', layer.x);
  const y = track(layer.keyframes, frame, 'y', layer.y);
  const r = track(layer.keyframes, frame, 'rotation', 0);
  const s = track(layer.keyframes, frame, 'scale', 1);
  const o = track(layer.keyframes, frame, 'opacity', 1);
  const ab = track(layer.attentionKeyframes, frame, 'brightness', 1);
  const as = track(layer.attentionKeyframes, frame, 'scale', 1);
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
      <div style={{width: layer.w, height: layer.h, transformOrigin: '50% 50%', transform: `scale(${as})`, filter: `brightness(${ab})`}}>
        <Img src={staticFile(activeSrc(layer, frame))} style={{width: layer.w, height: layer.h}} />
      </div>
      {(layer.children || []).map((c) => (
        <Layer key={c.id} layer={c} frame={frame} />
      ))}
    </div>
  );
};

// R3-C02/C04: every value arrives in OUTPUT PIXELS (the Python ShotCoordinateSpace is the only transform). The camera moves each
// root layer by its own skill-owned coefficient (world depth parallax); actors sit on the reference plane (coefficient 1).
export const SceneGraphComposition = ({scene}) => {
  const frame = useCurrentFrame();
  if (scene.units !== undefined && scene.units !== 'px') {
    throw new Error(`scene units must be px (got ${scene.units}); the renderer never rescales`);
  }
  const cx = track(scene.camera.keyframes, frame, 'x', 0);
  const cy = track(scene.camera.keyframes, frame, 'y', 0);
  const cs = track(scene.camera.keyframes, frame, 'scale', 1);
  const roots = [...scene.layers].sort((a, b) => a.z - b.z);
  return (
    <AbsoluteFill style={{backgroundColor: scene.background || '#000000', overflow: 'hidden'}}>
      {roots.map((l) => {
        const k = l.cameraCoefficient === undefined ? 1 : l.cameraCoefficient;
        const sk = 1 + (cs - 1) * k;
        return (
          <div
            key={l.id}
            style={{
              position: 'absolute',
              width: scene.width,
              height: scene.height,
              transformOrigin: '0px 0px',
              transform: `translate(${-cx * k}px, ${-cy * k}px) scale(${sk})`,
            }}
          >
            <Layer layer={l} frame={frame} />
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
