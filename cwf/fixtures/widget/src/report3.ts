export const updateReportWidget = (w: {value:number}, delta:number) => ({...w, value: Math.max(0, w.value + delta)});
