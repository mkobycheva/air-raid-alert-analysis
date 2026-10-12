Descriptive, two-sided STL on 180 complete TRAIN days gives NATIONAL F_T=0.1453 and F_S=0.0000.

The trend component has the larger NATIONAL variance-reduction strength under this decomposition; this is not forecast skill.

The east/center/west representatives were chosen from first-fold TRAIN rates: highest east, center nearest the overall median, and lowest west; their individual strengths are in stl_strength.csv.

STL uses observations on both sides of each date, so its components never enter model features; the supplied December 2025 definition break also limits causal interpretation.

The ACF is for daily national exposure: its lag is in days and is not the hourly forecast lead k.
