// Usage: node render.mjs <scene.json> <out.mp4>
// Invoked ONLY by vme.render.renderer after the Python approval gate passes (or for an explicitly
// labelled DIAGNOSTIC_NOT_APPROVED technical fixture). Assets must already be in ./public.
import {bundle} from '@remotion/bundler';
import {renderMedia, selectComposition} from '@remotion/renderer';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const [sceneFile, outFile] = process.argv.slice(2);
if (!sceneFile || !outFile) {
  console.error('usage: node render.mjs <scene.json> <out.mp4>');
  process.exit(2);
}
const scene = JSON.parse(fs.readFileSync(sceneFile, 'utf8'));
const serveUrl = await bundle({entryPoint: path.join(here, 'src', 'index.jsx'), publicDir: path.join(here, 'public')});
const inputProps = {scene};
const composition = await selectComposition({serveUrl, id: 'VMESceneGraph', inputProps});
await renderMedia({composition, serveUrl, codec: 'h264', outputLocation: outFile, inputProps, logLevel: 'error'});
console.log(JSON.stringify({ok: true, out: outFile, frames: composition.durationInFrames, fps: composition.fps,
  width: composition.width, height: composition.height}));
