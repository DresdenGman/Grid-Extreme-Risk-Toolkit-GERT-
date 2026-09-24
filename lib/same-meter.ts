export const SAME_METER_VERSION = 'same-meter-v1';
export const SAME_METER_LIMITATION = 'Invented two-hour teaching model, not ERCOT observations or an estimate of historical outage losses. A downloaded snapshot is not evidence of participation, review, or independent use.';

function world(demandMw: number[], deliveryCeilingMw: number[]) {
  const rows = demandMw.map((demand, i) => {
    const deliveredMw = Math.min(demand, deliveryCeilingMw[i]);
    return {
      hour: i + 1,
      assumedDemandMw: demand,
      assumedDeliveryCeilingMw: deliveryCeilingMw[i],
      deliveredMw,
      unservedMwh: (demand - deliveredMw) * 1,
    };
  });
  return { rows, totalUnservedMwh: rows.reduce((sum, row) => sum + row.unservedMwh, 0) };
}

export function sameMeterScenario(secondHourDemandMw: number) {
  if (!Number.isFinite(secondHourDemandMw) || secondHourDemandMw < 45000 || secondHourDemandMw > 90000) {
    throw new RangeError('Second-hour demand must be between 45,000 and 90,000 MW.');
  }
  const a = world([60000, 45000], [90000, 90000]);
  const b = world([60000, secondHourDemandMw], [90000, 45000]);
  return {
    a, b,
    sameReadings: a.rows.every((row, i) => row.deliveredMw === b.rows[i].deliveredMw),
    differentUnservedEnergy: a.totalUnservedMwh !== b.totalUnservedMwh,
  };
}

export function sameMeterSnapshot(secondHourDemandMw: number, createdAt: string) {
  if (!Number.isFinite(Date.parse(createdAt))) throw new RangeError('Invalid creation time.');
  return {
    schema: 'gert-teaching-snapshot-v1',
    activity_version: SAME_METER_VERSION,
    created_at: createdAt,
    model: 'delivered = min(assumed demand, assumed delivery ceiling); unserved energy = (assumed demand - delivered) × interval hours',
    interval_hours: 1,
    second_hour_demand_mw: secondHourDemandMw,
    ...sameMeterScenario(secondHourDemandMw),
    evidence_status: 'local_model_snapshot_not_verified_participation',
    limitations: SAME_METER_LIMITATION,
  };
}
