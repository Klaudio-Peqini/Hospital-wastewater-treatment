from pathlib import Path

from polymer_bl.model import PolymerBLParams, compare_cases, save_case_bundle, run_transport_bridge
from polymer_bl.plotting import plot_fractional_flow, plot_profiles, plot_production, plot_transport_bridge
from hospital_wwtp.config import default_config
from hospital_wwtp.simulation import simulate_plant


def main() -> None:
    out = Path("outputs_bridge")
    out.mkdir(exist_ok=True, parents=True)

    params = PolymerBLParams(mu_w=1.0, mu_wp=12.0, mu_o=5.0, pvi_max=2.0, profile_pvi=(0.2, 0.5, 1.0))
    bundle = compare_cases(params)
    save_case_bundle(bundle, out)
    plot_fractional_flow(bundle, out)
    plot_profiles(bundle, out)
    plot_production(bundle, out)

    cfg = default_config("nominal")
    wwtp_results = simulate_plant(cfg)
    bridge_df = run_transport_bridge(params, wwtp_results)
    bridge_df.to_csv(out / "transport_bridge.csv", index=False)
    plot_transport_bridge(bridge_df, out)
    print(f"Saved coupled transport outputs to {out}")


if __name__ == "__main__":
    main()
