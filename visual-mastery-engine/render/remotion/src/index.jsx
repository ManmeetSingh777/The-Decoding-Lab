import React from 'react';
import {registerRoot, Composition} from 'remotion';
import {SceneGraphComposition} from './SceneGraph.jsx';

const Root = () => (
  <Composition
    id="VMESceneGraph"
    component={SceneGraphComposition}
    durationInFrames={60}
    fps={30}
    width={640}
    height={360}
    defaultProps={{scene: null}}
    calculateMetadata={({props}) => ({
      durationInFrames: props.scene.durationInFrames,
      fps: props.scene.fps,
      width: props.scene.width,
      height: props.scene.height,
    })}
  />
);

registerRoot(Root);
