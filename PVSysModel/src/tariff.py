

from pathlib import Path
import pandas as pd

from globals import *


def bld_tou_tbl(loc: str, ydow: np.ndarray) -> np.ndarray[tuple[int, int], np.dtype[np.object_]]:
    tou   = np.empty((365,48), TTV)


    d = Path(loc)
    tou_table:   pd.DataFrame  = pd.read_excel(list(d.glob(TOU))[0], index_col = 0, comment = "#")

    for d in range(HIGH_SEASON_START.timetuple().tm_yday):
        for h in range(24):
            hh = h * 2
            match tou_table.iat[ydow[d], h]:
                case "Low Peak":        tou[d][hh:hh+2] = TTV.PEAK
                case "Low Standard":    tou[d][hh:hh+2] = TTV.STD
                case "Low Off Peak":    tou[d][hh:hh+2] = TTV.OFF_PEAK
                case _:
                    raise f"Unknown TOU Rate."
    for d in range(HIGH_SEASON_START.timetuple().tm_yday, LOW_SEASON_START.timetuple().tm_yday):
        for h in range(24):
            hh = h * 2
            match tou_table.iat[ydow[d] + 7, h]:
                case "High Peak":       tou[d][hh:hh+2] = TTV.PEAK
                case "High Standard":   tou[d][hh:hh+2] = TTV.STD
                case "High Off Peak":   tou[d][hh:hh+2] = TTV.OFF_PEAK
                case _:
                    raise f"Unknown TOU Rate."
    for d in range(LOW_SEASON_START.timetuple().tm_yday, 365):
        for h in range(24):
            hh = h * 2
            match tou_table.iat[ydow[d], h]:
                case "Low Peak":        tou[d][hh:hh+2] = TTV.PEAK
                case "Low Standard":    tou[d][hh:hh+2] = TTV.STD
                case "Low Off Peak":    tou[d][hh:hh+2] = TTV.OFF_PEAK
                case _:
                    raise f"Unknown TOU Rate."
    return tou


def read_rates(loc: str) -> dict:

    d = Path(loc)
    rate_table: pd.DataFrame = pd.read_excel(list(d.glob(RATES))[0], comment = "#")
    rates = {}
    for r in range(len(rate_table)):
        if rate_table.at[r, "Charge"] in rates_map.keys() and pd.notna(rate_table.at[r, TARIFF]):
            rates[rates_map[rate_table.iloc[r, 0]]] = rate_table.at[r, TARIFF]

    return rates
