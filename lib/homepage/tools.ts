export interface ToolEntry {
  href: string;
  name: string;
  description: string;
}

export interface ToolGroup {
  id: string;
  label: string;
  entries: ToolEntry[];
}

/**
 * Every page under app/(studio). Descriptions follow what those pages do.
 * A new studio route must be added here or the homepage test fails.
 */
export const toolIndex: ToolGroup[] = [
  {
    id: 'decision-tools',
    label: 'Decision tools',
    entries: [
      {
        href: '/monitor',
        name: 'Live Monitor',
        description:
          'Shows ERCOT weather and grid context when a source is available. The next-hour risk score stays empty while prediction is gated.',
      },
      {
        href: '/scenario',
        name: 'Scenario Lab',
        description:
          'Sends a perturbed weather case to the scenario endpoint. That endpoint stays gated until a model is validated, and the page says so.',
      },
      {
        href: '/events/polar-vortex',
        name: 'Event Replay',
        description:
          'Steps through a labeled educational reconstruction of a polar-vortex trace. The page states it is not an official historical record.',
      },
    ],
  },
  {
    id: 'data-history',
    label: 'Data and history',
    entries: [
      {
        href: '/history',
        name: 'Historical Lab',
        description:
          'A deterministic teaching exercise over three deliberately chosen 72-hour windows of recorded ERCOT load. Capacity and a uniform reduction are assumptions. It is not a validated forecast or a representative backtest.',
      },
      {
        href: '/dashboard',
        name: 'Dashboard',
        description: 'Redirects to the Historical Lab. This address is not a separate forecast or operations view.',
      },
    ],
  },
  {
    id: 'research-briefs',
    label: 'Research and briefs',
    entries: [
      {
        href: '/briefs/winter-load',
        name: 'Grid Notes',
        description:
          'A short note on the February 2021 curve: recorded use can fall when customers are disconnected, so the measurement is not unmet demand.',
      },
      {
        href: '/briefs/same-meter',
        name: 'Same meter, two worlds',
        description:
          'A five-minute invented counterexample where two situations share a meter reading and differ in unmet demand. Not historical data.',
      },
      {
        href: '/benchmark',
        name: 'Benchmarks',
        description:
          'Publishes the rejected candidate’s gates, skill, and calibration from the v1.4 evidence file. The production backtest stays locked.',
      },
      {
        href: '/review',
        name: 'Review & Reproduce',
        description:
          'A guided check of the historical cases: recompute a row, download the report, and leave a public note if you choose.',
      },
      {
        href: '/community',
        name: 'Community Evidence',
        description:
          'Shows what reviewers have published and which criticisms are still open. Private replies stay off this page.',
      },
    ],
  },
  {
    id: 'project',
    label: 'Project',
    entries: [
      {
        href: '/about',
        name: 'Methodology',
        description:
          'States the method: tail demand against capacity, promotion gates, and a limit that this is decision support rather than grid control.',
      },
      {
        href: '/research',
        name: 'Open Research',
        description: 'Points to the public source, the evidence page, and a way to challenge an assumption in the open.',
      },
    ],
  },
];

export function toolEntries(): ToolEntry[] {
  return toolIndex.flatMap((group) => group.entries);
}

export function toolHrefs(): string[] {
  return toolEntries().map((entry) => entry.href).sort();
}
