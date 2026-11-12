export function modifyWidget1v1(w: { value: number }, delta: number) { return { ...w, value: Math.max(0, w.value + delta) }; }
export function modifyWidget1v2(w: { value: number }, delta: number, audit = false) {
  const next = { ...w, value: Math.max(0, w.value + delta) };
  if (audit) console.info('widget modified');
  return next;
}
