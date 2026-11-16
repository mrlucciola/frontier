# Probe report log

One file per report pasted back from the work machine. File name:
`<date>-kiro<version>.txt`, for example `2026-11-20-kiro2.17.0.txt`.

Contents are the verbatim `kiro-probe` output: lines of the form
`PASS <id> <detail|->`, `FAIL <id> <detail|->`, `SKIP <id> <reason|->` and
`INFO <id> <detail>`, at most 40 lines, ending with the line `PROBE-END`.
Save the report exactly as produced; findings and follow-ups go in the plan,
not into the report file.
