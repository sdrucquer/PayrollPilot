import React from 'react';
import {Composition} from 'remotion';
import {Demo} from './v2/Demo';
import data from './generated/demo.json';

export const Root: React.FC = () => (
  <Composition id="PayrollPilotDemo" component={Demo} durationInFrames={Math.ceil(data.total * 30)} fps={30} width={1920} height={1080} />
);
