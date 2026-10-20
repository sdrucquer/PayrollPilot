import React from 'react';
import {Composition} from 'remotion';
import {Demo} from './v2/Demo';
import {Hook} from './v2/scenes';
import data from './generated/demo.json';

export const Root: React.FC = () => (
  <>
    <Composition id="PayrollPilotDemo" component={Demo} durationInFrames={Math.ceil(data.total * 30)} fps={30} width={1920} height={1080} />
    {/* Pitch-deck cover still: the hook flood without captions or labels. */}
    <Composition id="HookStill" component={() => <Hook dur={13} voAt={0.4} voDur={7.4} still />} durationInFrames={390} fps={30} width={1920} height={1080} />
  </>
);
