declare module 'react-plotly.js' {
  import * as React from 'react';
  import type { Config, Data, Layout } from 'plotly.js';

  export interface PlotParams {
    data?: Data[];
    layout?: Partial<Layout>;
    config?: Partial<Config>;
    style?: React.CSSProperties;
    className?: string;
    useResizeHandler?: boolean;
    onInitialized?: (figure: unknown) => void;
    onUpdate?: (figure: unknown) => void;
    onPurge?: () => void;
    onError?: (err: unknown) => void;
    divId?: string;
    revision?: number;
  }

  export default class Plot extends React.Component<PlotParams> {}
}
