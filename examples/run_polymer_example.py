from pathlib import Path

from polymer_bl.model import PolymerBLParams, compare_cases, save_case_bundle
from polymer_bl.plotting import plot_fractional_flow, plot_profiles, plot_production


def main() -> None:
    params = PolymerBLParams(mu_w=1.0, mu_wp=12.0, mu_o=5.0, pvi_max=2.0, profile_pvi=(0.2, 0.5, 1.0, 1.5))
    bundle = compare_cases(params)
    out = Path("outputs_polymer")
    save_case_bundle(bundle, out)
    plot_fractional_flow(bundle, out)
    plot_profiles(bundle, out)
    plot_production(bundle, out)
    print(f"Saved example Buckley-Leverett outputs to {out}")


if __name__ == "__main__":
    main()
