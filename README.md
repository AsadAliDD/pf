## Usage

Convert the original export into a flat JSON:

```bash
python3 main.py convert
```

Build a pandapower JSON from the flat JSON:

```bash
python3 main.py build-net
```

Run a 3-phase short-circuit calculation:

```bash
python3 main.py run-sc
```

Compare the pandapower short-circuit results with the PowerFactory CSV:

```bash
uv run python main.py compare-pf
```

Export the pandapower short-circuit results to CSV:

```bash
uv run python main.py export-csv
```

## Notes

The original `out.json` is already a pandapower JSON export. The generated
`ieee9_sc_simple.json` is a flatter representation that is easier to inspect
and transform.

The source export does not include the synchronous-machine short-circuit
parameters pandapower needs for IEC 60909 calculations. The converter therefore
builds an SC-ready model with calibrated machine data for `G1`, `G2`, and `G3`
and links each generator to its step-up transformer as a power-station unit.

The original external-grid row is preserved in the flat JSON as
`reference_ext_grids` for traceability, but the pandapower network that is
written to `ieee9_sc_pandapower.json` uses generator sources for the
short-circuit study.

## Findings

The original `out.json` could not reproduce the PowerFactory short-circuit
results directly with pandapower because the export did not contain the IEC
60909 synchronous-machine source data needed for generator fault contribution.

Using only the exported `ext_grid` data in pandapower produced much lower fault
levels than PowerFactory. That indicates the PowerFactory study was effectively
including the three generators behind their step-up transformers, while the JSON
export did not preserve enough machine short-circuit information to rebuild that
behavior automatically.

To match the PowerFactory results, the pandapower model was rebuilt with three
explicit generator short-circuit sources and their associated power-station
transformers:

| Generator | sn_mva | vn_kv | xdss_pu | rdss_ohm | cos_phi | pg_percent | power_station_trafo | slack |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| G1 | 250.0 | 16.5 | 0.22 | 0.0 | 0.85 | 0.0 | T1 | True |
| G2 | 200.0 | 18.0 | 0.22 | 0.0 | 0.85 | 0.0 | T2 | False |
| G3 | 150.0 | 13.8 | 0.24 | 0.0 | 0.85 | 0.0 | T3 | False |

## Missing Variables In PowerFactory Export

The following values were missing or unusable in the exported JSON and had to be
supplied for pandapower short-circuit calculations:

- `G1` had no `gen` row at all; it only appeared as `ext_grid`
- `gen.sn_mva` was missing for `G2` and `G3`
- `gen.xdss_pu` was missing
- `gen.rdss_ohm` was missing
- `gen.cos_phi` was missing
- `gen.pg_percent` was missing
- `gen.power_station_trafo` was missing
- `ext_grid.rx_max` was missing
- `ext_grid.rx_min` was missing

For reference, the external-grid defaults used during the earlier
source-only test were:

| Variable | Value |
| --- | ---: |
| `rx_max` | 0.1 |
| `rx_min` | 0.1 |

## Result Quality

After calibration, the pandapower 3-phase short-circuit results matched the
PowerFactory `Ik"` and `Sk"` values closely. The remaining error is roughly
`0.06%` to `4.5%` across the buses and is due to inferred machine data rather
than an import failure.
