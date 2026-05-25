# Legacy run normalization

This slice adds reproducible derived metadata for old or loose artifacts without changing raw data.

## Quick path

```bash
python scripts/normalize_legacy_runs.py
python scripts/build_run_catalog.py
```

Outputs:

- `data/derived/normalized/normalized_runs.csv`
- `data/derived/normalized/normalization_report.csv`
- refreshed `data/derived/catalog/*.csv`

## Policies

| Legacy shape | Policy | Result |
|---|---|---|
| Dual run with old webcam columns | Accept `timestamp_s` as conservative fallback marker for `perf_counter_s` | `partial` if derived pulse/coincidence tables are missing |
| Webcam sweep CSV with companion metric paths | Group by the `csv` column and validate linked metric files exist | `valid` when every companion exists |
| Empty latency results CSV | Preserve summary/log links, do not fabricate rows | `invalid_empty` |
| Loose OP598/webcam docs or logs | Mark explicitly as unrecoverable loose artifacts | `legacy_unstructured` |

## Non-goals

- No hardware access.
- No raw data mutation or file movement.
- No synthetic timing precision or missing measurements.
- No reconstruction of missing `pulse_events.csv` or `coincidence_table.csv`.
