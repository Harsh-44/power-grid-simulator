const frequencyNumber = new Intl.NumberFormat(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 3 });
const elapsedNumber = new Intl.NumberFormat(undefined, { maximumFractionDigits: 3 });
const timestampNumber = new Intl.NumberFormat(undefined, { maximumFractionDigits: 8, useGrouping: false });
const percentNumber = new Intl.NumberFormat(undefined, { style: "unit", unit: "percent", maximumFractionDigits: 2 });

export const frequencyConditions = {
  normal: "Within limits",
  under_frequency: "Under-frequency",
  over_frequency: "Over-frequency",
} as const;

export const formatFrequencyNumber = (value: number) => frequencyNumber.format(value);
export const formatFrequency = (value: number) => `${formatFrequencyNumber(value)} Hz`;
export const formatDuration = (value: number) => value > 0 && value < 0.001
  ? `<${elapsedNumber.format(0.001)} s`
  : `${elapsedNumber.format(value)} s`;
export const formatTimestamp = (value: number) => `${timestampNumber.format(value)} s`;
export const formatPercent = (value: number) => percentNumber.format(value);
