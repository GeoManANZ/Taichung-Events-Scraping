# Spikes

Throwaway probes used to validate the scraper's design decisions. Kept for
provenance — none of these run in production. The production entry point is
`../taichung_events.py`.

| File | What it established |
|---|---|
| `probe_candidates.py` | Ran the tier ladder + signal score against 14 candidate event sources → identified the 10 added in the 2026-09-11 coverage audit |
| `probe_candidates_results.txt` | Raw output of that probe (per-candidate tier, signal score, extract yield) |
| `spike_tiers.py` | Which fetch tiers actually work from a plain-script context (fastcrw yes, groktocrawl needs `groktocrawl-agent-svc-1`, two gov sites fail TLS on direct) |
| `spike_extract.py` | Whether dates are extractable from fetched content |
| `spike_quality_gate.py` | The signal-gate idea: a tier returning 200 with a JS shell must not count as success |
| `spike_dates.py` | Actual date formats in the wild (Meetup `Thu, Sep 17`; NTT is a link grid with bare day numbers) |
| `diag_quality.py` | Content-quality diagnostic for deciding when to escalate |

## Re-running the coverage audit

`probe_candidates.py` is the tool to re-run when asking "are we missing
sources?". It imports the production module, so it always tests against the
current tier ladder:

```bash
python3 spikes/probe_candidates.py
```

Add URLs to the `CANDIDATES` list. A candidate qualifies only if the probe
shows `OK` with a real extract yield — never add a source on the assumption
that it will work.
