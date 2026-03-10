from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SOURCE_JSON = ROOT / "out.json"
SIMPLE_JSON = ROOT / "ieee9_sc_simple.json"
PP_JSON = ROOT / "ieee9_sc_pandapower.json"
PF_RESULTS_CSV = ROOT / "pf_results.csv"
PP_RESULTS_CSV = ROOT / "pandapower_results.csv"
COMPARISON_RESULTS_CSV = ROOT / "comparison_results.csv"

SC_GENERATOR_DEFAULTS = {
    "G1": {
        "sn_mva": 250.0,
        "vn_kv": 16.5,
        "xdss_pu": 0.22,
        "rdss_ohm": 0.0,
        "cos_phi": 0.85,
        "pg_percent": 0.0,
        "power_station_trafo_name": "T1",
        "slack": True,
    },
    "G2": {
        "sn_mva": 200.0,
        "vn_kv": 18.0,
        "xdss_pu": 0.22,
        "rdss_ohm": 0.0,
        "cos_phi": 0.85,
        "pg_percent": 0.0,
        "power_station_trafo_name": "T2",
        "slack": False,
    },
    "G3": {
        "sn_mva": 150.0,
        "vn_kv": 13.8,
        "xdss_pu": 0.24,
        "rdss_ohm": 0.0,
        "cos_phi": 0.85,
        "pg_percent": 0.0,
        "power_station_trafo_name": "T3",
        "slack": False,
    },
}


def decode_frame(frame: dict[str, Any]) -> list[dict[str, Any]]:
    payload = json.loads(frame["_object"])
    columns = payload["columns"]
    return [dict(zip(columns, row, strict=True)) for row in payload["data"]]


def load_raw_net(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())["_object"]


def build_simple_model(raw_net: dict[str, Any]) -> dict[str, Any]:
    buses = decode_frame(raw_net["bus"])
    lines = decode_frame(raw_net["line"])
    trafos = decode_frame(raw_net["trafo"])
    ext_grids = decode_frame(raw_net["ext_grid"])
    gens = decode_frame(raw_net["gen"])
    loads = decode_frame(raw_net["load"])
    switches = decode_frame(raw_net["switch"])
    ext_grid_by_name = {item["name"]: item for item in ext_grids}

    bus_lookup = {
        idx: {
            "index": idx,
            "name": bus["name"],
            "vn_kv": bus["vn_kv"],
            "type": bus["type"],
            "zone": bus["zone"],
            "in_service": bus["in_service"],
        }
        for idx, bus in enumerate(buses)
    }

    simple = {
        "meta": {
            "name": raw_net["name"],
            "f_hz": raw_net["f_hz"],
            "sn_mva": raw_net["sn_mva"],
            "source_file": SOURCE_JSON.name,
            "note": (
                "Converted from the original export into a flat JSON structure. "
                "The short-circuit-ready model uses calibrated synchronous-machine "
                "data for G1, G2, and G3 and links each machine to its power "
                "station transformer."
            ),
        },
        "buses": list(bus_lookup.values()),
        "reference_ext_grids": [
            {
                "name": item["name"],
                "bus": item["bus"],
                "vm_pu": item["vm_pu"],
                "va_degree": item["va_degree"],
                "in_service": item["in_service"],
                "s_sc_max_mva": item["s_sc_max_mva"],
                "s_sc_min_mva": item["s_sc_min_mva"],
                "rx_max": item.get("rx_max", 0.1),
                "rx_min": item.get("rx_min", 0.1),
            }
            for item in ext_grids
        ],
        "generators": [
            {
                "name": "G1",
                "bus": ext_grid_by_name["G1"]["bus"],
                "p_mw": abs(ext_grid_by_name["G1"]["p_disp_mw"]),
                "vm_pu": ext_grid_by_name["G1"]["vm_pu"],
                "sn_mva": SC_GENERATOR_DEFAULTS["G1"]["sn_mva"],
                "min_p_mw": 0.0,
                "max_p_mw": SC_GENERATOR_DEFAULTS["G1"]["sn_mva"],
                "min_q_mvar": -999.0,
                "max_q_mvar": 999.0,
                "in_service": ext_grid_by_name["G1"]["in_service"],
                "vn_kv": SC_GENERATOR_DEFAULTS["G1"]["vn_kv"],
                "xdss_pu": SC_GENERATOR_DEFAULTS["G1"]["xdss_pu"],
                "rdss_ohm": SC_GENERATOR_DEFAULTS["G1"]["rdss_ohm"],
                "cos_phi": SC_GENERATOR_DEFAULTS["G1"]["cos_phi"],
                "pg_percent": SC_GENERATOR_DEFAULTS["G1"]["pg_percent"],
                "power_station_trafo_name": SC_GENERATOR_DEFAULTS["G1"]["power_station_trafo_name"],
                "slack": SC_GENERATOR_DEFAULTS["G1"]["slack"],
            },
            *[
                {
                    "name": item["name"],
                    "bus": item["bus"],
                    "p_mw": item["p_mw"],
                    "vm_pu": item["vm_pu"],
                    "sn_mva": SC_GENERATOR_DEFAULTS[item["name"]]["sn_mva"],
                    "min_p_mw": item["min_p_mw"],
                    "max_p_mw": item["max_p_mw"],
                    "min_q_mvar": item["min_q_mvar"],
                    "max_q_mvar": item["max_q_mvar"],
                    "in_service": item["in_service"],
                    "vn_kv": SC_GENERATOR_DEFAULTS[item["name"]]["vn_kv"],
                    "xdss_pu": SC_GENERATOR_DEFAULTS[item["name"]]["xdss_pu"],
                    "rdss_ohm": SC_GENERATOR_DEFAULTS[item["name"]]["rdss_ohm"],
                    "cos_phi": SC_GENERATOR_DEFAULTS[item["name"]]["cos_phi"],
                    "pg_percent": SC_GENERATOR_DEFAULTS[item["name"]]["pg_percent"],
                    "power_station_trafo_name": SC_GENERATOR_DEFAULTS[item["name"]]["power_station_trafo_name"],
                    "slack": SC_GENERATOR_DEFAULTS[item["name"]]["slack"],
                }
                for item in gens
            ],
        ],
        "loads": [
            {
                "name": item["name"],
                "bus": item["bus"],
                "p_mw": item["p_mw"],
                "q_mvar": item["q_mvar"],
                "in_service": item["in_service"],
            }
            for item in loads
        ],
        "lines": [
            {
                "name": item["name"],
                "from_bus": item["from_bus"],
                "to_bus": item["to_bus"],
                "length_km": item["length_km"],
                "r_ohm_per_km": item["r_ohm_per_km"],
                "x_ohm_per_km": item["x_ohm_per_km"],
                "c_nf_per_km": item["c_nf_per_km"],
                "max_i_ka": item["max_i_ka"],
                "parallel": item["parallel"],
                "in_service": item["in_service"],
            }
            for item in lines
        ],
        "trafos": [
            {
                "name": item["name"],
                "hv_bus": item["hv_bus"],
                "lv_bus": item["lv_bus"],
                "sn_mva": item["sn_mva"],
                "vn_hv_kv": item["vn_hv_kv"],
                "vn_lv_kv": item["vn_lv_kv"],
                "vk_percent": item["vk_percent"],
                "vkr_percent": item["vkr_percent"],
                "shift_degree": item["shift_degree"],
                "vector_group": item["vector_group"],
                "in_service": item["in_service"],
            }
            for item in trafos
        ],
        "switches": [
            {
                "bus": item["bus"],
                "element": item["element"],
                "et": item["et"],
                "type": item["type"],
                "closed": item["closed"],
                "name": item["name"],
            }
            for item in switches
        ],
    }
    return simple


def write_simple_json(source: Path = SOURCE_JSON, target: Path = SIMPLE_JSON) -> Path:
    raw_net = load_raw_net(source)
    simple = build_simple_model(raw_net)
    target.write_text(json.dumps(simple, indent=2))
    return target


def build_pandapower_net(simple_path: Path):
    try:
        import pandapower as pp
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "pandapower is not installed. Install it first, for example with "
            "`uv add pandapower` or `pip install pandapower`."
        ) from exc

    simple = json.loads(simple_path.read_text())
    net = pp.create_empty_network(
        name=simple["meta"]["name"],
        f_hz=simple["meta"]["f_hz"],
        sn_mva=simple["meta"]["sn_mva"],
    )

    for bus in simple["buses"]:
        pp.create_bus(
            net,
            index=bus["index"],
            name=bus["name"],
            vn_kv=bus["vn_kv"],
            type=bus["type"],
            zone=bus["zone"],
            in_service=bus["in_service"],
        )

    for item in simple["loads"]:
        pp.create_load(
            net,
            bus=item["bus"],
            name=item["name"],
            p_mw=item["p_mw"],
            q_mvar=item["q_mvar"],
            in_service=item["in_service"],
        )

    for item in simple["lines"]:
        pp.create_line_from_parameters(
            net,
            from_bus=item["from_bus"],
            to_bus=item["to_bus"],
            length_km=item["length_km"],
            r_ohm_per_km=item["r_ohm_per_km"],
            x_ohm_per_km=item["x_ohm_per_km"],
            c_nf_per_km=item["c_nf_per_km"],
            max_i_ka=item["max_i_ka"],
            name=item["name"],
            parallel=item["parallel"],
            in_service=item["in_service"],
        )

    trafo_name_to_index: dict[str, int] = {}
    for item in simple["trafos"]:
        idx = pp.create_transformer_from_parameters(
            net,
            hv_bus=item["hv_bus"],
            lv_bus=item["lv_bus"],
            sn_mva=item["sn_mva"],
            vn_hv_kv=item["vn_hv_kv"],
            vn_lv_kv=item["vn_lv_kv"],
            vk_percent=item["vk_percent"],
            vkr_percent=item["vkr_percent"],
            pfe_kw=0.0,
            i0_percent=0.0,
            shift_degree=item["shift_degree"],
            vector_group=item["vector_group"],
            name=item["name"],
            in_service=item["in_service"],
        )
        trafo_name_to_index[item["name"]] = idx

    for item in simple["generators"]:
        pp.create_gen(
            net,
            bus=item["bus"],
            p_mw=item["p_mw"],
            vm_pu=item["vm_pu"],
            sn_mva=item["sn_mva"],
            name=item["name"],
            min_q_mvar=item["min_q_mvar"],
            max_q_mvar=item["max_q_mvar"],
            min_p_mw=item["min_p_mw"],
            max_p_mw=item["max_p_mw"],
            slack=item["slack"],
            in_service=item["in_service"],
            vn_kv=item["vn_kv"],
            xdss_pu=item["xdss_pu"],
            rdss_ohm=item["rdss_ohm"],
            cos_phi=item["cos_phi"],
            pg_percent=item["pg_percent"],
            power_station_trafo=trafo_name_to_index[item["power_station_trafo_name"]],
        )

    for item in simple["switches"]:
        pp.create_switch(
            net,
            bus=item["bus"],
            element=item["element"],
            et=item["et"],
            type=item["type"],
            closed=item["closed"],
            name=item["name"],
        )

    return net


def write_pandapower_json(simple_path: Path = SIMPLE_JSON, target: Path = PP_JSON) -> Path:
    try:
        import pandapower as pp
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "pandapower is not installed. Install it first, then rerun `build-net`."
        ) from exc

    net = build_pandapower_net(simple_path)
    pp.to_json(net, str(target))
    return target


def run_short_circuit(simple_path: Path = SIMPLE_JSON) -> None:
    try:
        import pandapower.shortcircuit as sc
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "pandapower is not installed. Install it first, then rerun `run-sc`."
        ) from exc

    net = build_pandapower_net(simple_path)
    sc.calc_sc(net, case="max", fault="3ph")
    print(net.res_bus_sc[["ikss_ka", "skss_mw"]].to_string())


def compare_with_powerfactory(
    simple_path: Path = SIMPLE_JSON, results_path: Path = PF_RESULTS_CSV
) -> None:
    try:
        import pandas as pd
        import pandapower.shortcircuit as sc
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "pandapower and pandas are required. Install the project dependencies first."
        ) from exc

    net = build_pandapower_net(simple_path)
    sc.calc_sc(net, case="max", fault="3ph")
    pf = pd.read_csv(results_path, sep="\t", skiprows=[1], decimal=",")
    pf = pf.rename(
        columns={
            "Ik\"": "ik_pf_ka",
            "Sk\"": "sk_pf_mva",
            "Name": "name",
        }
    )
    merged = net.bus[["name", "vn_kv"]].join(
        net.res_bus_sc[["ikss_ka", "skss_mw"]]
    ).merge(
        pf[["name", "ik_pf_ka", "sk_pf_mva"]], on="name", how="left"
    )
    merged["ik_abs_error_ka"] = merged["ikss_ka"] - merged["ik_pf_ka"]
    merged["ik_rel_error_percent"] = merged["ik_abs_error_ka"] / merged["ik_pf_ka"] * 100
    merged["sk_abs_error_mva"] = merged["skss_mw"] - merged["sk_pf_mva"]
    merged["sk_rel_error_percent"] = merged["sk_abs_error_mva"] / merged["sk_pf_mva"] * 100
    print(
        merged[
            [
                "name",
                "vn_kv",
                "ikss_ka",
                "ik_pf_ka",
                "ik_abs_error_ka",
                "ik_rel_error_percent",
                "skss_mw",
                "sk_pf_mva",
                "sk_abs_error_mva",
                "sk_rel_error_percent",
            ]
        ].to_string(index=False)
    )


def export_comparison_csv(
    simple_path: Path = SIMPLE_JSON,
    results_path: Path = PF_RESULTS_CSV,
    output_path: Path = COMPARISON_RESULTS_CSV,
) -> Path:
    try:
        import pandas as pd
        import pandapower.shortcircuit as sc
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "pandapower and pandas are required. Install the project dependencies first."
        ) from exc

    net = build_pandapower_net(simple_path)
    sc.calc_sc(net, case="max", fault="3ph")
    pf = pd.read_csv(results_path, sep="\t", skiprows=[1], decimal=",")
    pf = pf.rename(
        columns={
            "Ik\"": "ik_pf_ka",
            "Sk\"": "sk_pf_mva",
            "Name": "name",
        }
    )
    merged = net.bus[["name", "vn_kv"]].join(
        net.res_bus_sc[["ikss_ka", "skss_mw"]]
    ).merge(
        pf[["name", "ik_pf_ka", "sk_pf_mva"]], on="name", how="left"
    )
    merged["ik_abs_error_ka"] = merged["ikss_ka"] - merged["ik_pf_ka"]
    merged["ik_rel_error_percent"] = merged["ik_abs_error_ka"] / merged["ik_pf_ka"] * 100
    merged["sk_abs_error_mva"] = merged["skss_mw"] - merged["sk_pf_mva"]
    merged["sk_rel_error_percent"] = merged["sk_abs_error_mva"] / merged["sk_pf_mva"] * 100
    merged.to_csv(output_path, index=False)
    return output_path


def export_pandapower_results_csv(
    simple_path: Path = SIMPLE_JSON, output_path: Path = PP_RESULTS_CSV
) -> Path:
    try:
        import pandapower.shortcircuit as sc
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "pandapower is required. Install the project dependencies first."
        ) from exc

    net = build_pandapower_net(simple_path)
    sc.calc_sc(net, case="max", fault="3ph")
    result = net.bus[["name", "vn_kv"]].join(net.res_bus_sc[["ikss_ka", "skss_mw"]])
    result.to_csv(output_path, index=False)
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert the exported IEEE 9-bus JSON into a flatter JSON and build pandapower inputs."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    convert = subparsers.add_parser("convert", help="Write the simplified JSON model.")
    convert.add_argument("--source", type=Path, default=SOURCE_JSON)
    convert.add_argument("--target", type=Path, default=SIMPLE_JSON)

    build = subparsers.add_parser(
        "build-net",
        help="Build a pandapower network from the simple JSON and write a pandapower JSON file.",
    )
    build.add_argument("--source", type=Path, default=SIMPLE_JSON)
    build.add_argument("--target", type=Path, default=PP_JSON)

    run_sc_cmd = subparsers.add_parser(
        "run-sc",
        help="Run a 3-phase short-circuit study from the simple JSON.",
    )
    run_sc_cmd.add_argument("--source", type=Path, default=SIMPLE_JSON)

    compare_cmd = subparsers.add_parser(
        "compare-pf",
        help="Run the pandapower short-circuit and compare it with pf_results.csv.",
    )
    compare_cmd.add_argument("--source", type=Path, default=SIMPLE_JSON)
    compare_cmd.add_argument("--results", type=Path, default=PF_RESULTS_CSV)

    export_cmd = subparsers.add_parser(
        "export-csv",
        help="Run the pandapower short-circuit and export the bus results to CSV.",
    )
    export_cmd.add_argument("--source", type=Path, default=SIMPLE_JSON)
    export_cmd.add_argument("--output", type=Path, default=PP_RESULTS_CSV)

    export_compare_cmd = subparsers.add_parser(
        "export-compare-csv",
        help="Export the PowerFactory vs pandapower comparison table to CSV.",
    )
    export_compare_cmd.add_argument("--source", type=Path, default=SIMPLE_JSON)
    export_compare_cmd.add_argument("--results", type=Path, default=PF_RESULTS_CSV)
    export_compare_cmd.add_argument("--output", type=Path, default=COMPARISON_RESULTS_CSV)

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "convert":
        path = write_simple_json(args.source, args.target)
        print(path)
    elif args.command == "build-net":
        path = write_pandapower_json(args.source, args.target)
        print(path)
    elif args.command == "run-sc":
        run_short_circuit(args.source)
    elif args.command == "compare-pf":
        compare_with_powerfactory(args.source, args.results)
    elif args.command == "export-csv":
        path = export_pandapower_results_csv(args.source, args.output)
        print(path)
    elif args.command == "export-compare-csv":
        path = export_comparison_csv(args.source, args.results, args.output)
        print(path)


if __name__ == "__main__":
    main()
