import pandas as pd


from globals import *




def daily_tou (imp_e: Real2d,
               exp_e: Real2d,
               tarf_tou: Obj2d
               ) -> Real2d:

    dtou = np.empty ((365, 8), np.float64)

    dtou [:][TOUC.IMPORT_PEAK.value]      = np.where(tarf_tou == TTV.PEAK,     imp_e[:], 0).sum()
    dtou [:][TOUC.IMPORT_STD.value]       = np.where(tarf_tou == TTV.STD,      imp_e[:], 0).sum()
    dtou [:][TOUC.IMPORT_OFF_PEAK.value]  = np.where(tarf_tou == TTV.OFF_PEAK, imp_e[:], 0).sum()
    dtou [:][TOUC.IMPORT_TOTAL.value]     = np.sum(imp_e[:])
    dtou [:][TOUC.EXPORT_PEAK.value]      = np.where(tarf_tou == TTV.PEAK,     exp_e[:], 0).sum()
    dtou [:][TOUC.EXPORT_STD.value]       = np.where(tarf_tou == TTV.STD,      exp_e[:], 0).sum()
    dtou [:][TOUC.EXPORT_OFF_PEAK.value]  = np.where(tarf_tou == TTV.OFF_PEAK, exp_e[:], 0).sum()
    dtou [:][TOUC.EXPORT_TOTAL.value]     = np.sum(imp_e[:])

    return dtou

def monthly_tou(imp_e: Real2d,
                exp_e: Real2d,
                tou_tbl: Obj2d
                ) -> Real2d:

    mtou = np.zeros((12,8), np.float64)
    for m in range(12):
        m1 = MonthStartYday[m]; m2 = MonthStartYday[m + 1]
        mtou[m][TOUC.IMPORT_PEAK.value]     = np.where(tou_tbl[m1:m2] == TTV.PEAK, imp_e[m1:m2], 0).sum()
        mtou[m][TOUC.IMPORT_STD.value]      = np.where(tou_tbl[m1:m2] == TTV.STD, imp_e[m1:m2], 0).sum()
        mtou[m][TOUC.IMPORT_OFF_PEAK.value] = np.where(tou_tbl[m1:m2] == TTV.OFF_PEAK, imp_e[m1:m2], 0).sum()
        mtou[m][TOUC.IMPORT_TOTAL.value]    = np.sum(imp_e[m1:m2])
        mtou[m][TOUC.EXPORT_PEAK.value]     = np.where(tou_tbl[m1:m2] == TTV.PEAK, exp_e[m1:m2], 0).sum()
        mtou[m][TOUC.EXPORT_STD.value]      = np.where(tou_tbl[m1:m2] == TTV.STD, exp_e[m1:m2], 0).sum()
        mtou[m][TOUC.EXPORT_OFF_PEAK.value] = np.where(tou_tbl[m1:m2] == TTV.OFF_PEAK, exp_e[m1:m2], 0).sum()
        mtou[m][TOUC.EXPORT_TOTAL.value]    = np.sum(exp_e[m1:m2])
    return mtou

def monthly_maxva(src_p: Real2d,
                  src_q: Real2d
                  ) -> Real1d:

    mvamax = np.zeros(12, np.float64)
    va = np.sqrt(src_p**2 + src_q**2)
    for m in range (12): mvamax[m] = va[MonthStartYday[m]:MonthStartYday[m + 1],].max()
    return mvamax

def monthly_reactive(src_p: Real2d,
                     src_q: Real2d,
                     snk_p: Real2d,
                     snk_q: Real2d,
                     pft: float
                     ) -> Real1d:

    mr = np.empty(12, np.float64)
    p = src_p - snk_p; q = src_q - snk_q
    s = np.sqrt(p * p + q * q); s = np.where(s != 0, s, 0.0000000000001)
    pf = p / s
    for m in range(12): mr[m] = np.where(pf[MonthStartYday[m]:MonthStartYday[m + 1]] < pft, q[MonthStartYday[m]:MonthStartYday[m + 1]], 0).sum() / 2
    return mr

def monthly_billing(rates: dict,
                    mtou: Real2d,
                    mvamax: Real1d,
                    mreactive: Real1d | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:

    mtou_cols = [["Import", "Import",  "Import",   "Import", "Export", "Export",   "Export",   "Export"],
                 ["Peak",   "Standard", "Off-Peak", "Total",  "Peak",   "Standard", "Off-Peak", "Total"],
                 ["kWh",    "kWh",     "kWh",      "kWh",    "kWh",    "kWh",      "kWh",      "kWh"]]
    mtou_idx = pd.date_range(start = dt.date(HypotheticalYear, 1, 1), periods = 12, freq = "ME")
    mtou_df = pd.DataFrame (mtou, columns = mtou_cols, index = mtou_idx)
    mtou_df["Maximum", "Demand", "kVAmax"] = mvamax
    if TRC.REACTIVE_PF_THRESH in rates: mtou_df["Reactive", "Energy", f"kVArh pf<{rates[TRC.REACTIVE_PF_THRESH]}"] = mreactive

    imp_pk = [rates[TRC.IMP_LOW_PEAK]] * 5;     imp_pk += [rates[TRC.IMP_HIGH_PEAK]] * 3;     imp_pk += [rates[TRC.IMP_LOW_PEAK]] * 4
    imp_st = [rates[TRC.IMP_LOW_STD]] * 5;      imp_st += [rates[TRC.IMP_HIGH_STD]] * 3;      imp_st += [rates[TRC.IMP_LOW_STD]]  * 4
    imp_op = [rates[TRC.IMP_LOW_OFF_PEAK]] * 5; imp_op += [rates[TRC.IMP_HIGH_OFF_PEAK]] * 3; imp_op += [rates[TRC.IMP_LOW_OFF_PEAK]] * 4
    exp_pk = [rates[TRC.EXP_LOW_PEAK]] * 5;     exp_pk += [rates[TRC.EXP_HIGH_PEAK]] * 3;     exp_pk += [rates[TRC.EXP_LOW_PEAK]] * 4
    exp_st = [rates[TRC.EXP_LOW_STD]] * 5;      exp_st += [rates[TRC.EXP_HIGH_STD]] * 3;      exp_st += [rates[TRC.EXP_LOW_STD]] * 4
    exp_op = [rates[TRC.EXP_LOW_OFF_PEAK]] * 5; exp_op += [rates[TRC.EXP_HIGH_OFF_PEAK]] * 3; exp_op += [rates[TRC.EXP_LOW_OFF_PEAK]] * 4
    mrates_df = pd.DataFrame (index = mtou_idx)
    mrates_df["Import", "Peak",     "R/kWh"] = imp_pk
    mrates_df["Import", "Standard", "R/kWh"] = imp_st
    mrates_df["Import", "Off-Peak", "R/kWh"] = imp_op
    mrates_df["Export", "Peak",     "R/kWh"] = exp_pk
    mrates_df["Export", "Standard", "R/kWh"] = exp_st
    mrates_df["Export", "Off-Peak", "R/kWh"] = exp_op

    mtou_df["Import", "Peak",     "R"] = mtou_df["Import", "Peak",     "kWh"] * mrates_df["Import", "Peak",     "R/kWh"]
    mtou_df["Import", "Standard", "R"] = mtou_df["Import", "Standard", "kWh"] * mrates_df["Import", "Standard", "R/kWh"]
    mtou_df["Import", "Off-Peak", "R"] = mtou_df["Import", "Off-Peak", "kWh"] * mrates_df["Import", "Off-Peak", "R/kWh"]
    mtou_df["Import", "Total",    "R"] = mtou_df["Import", "Peak", "R"] + mtou_df["Import", "Standard", "R"] + mtou_df["Import", "Off-Peak", "R"]
    mtou_df["Export", "Peak",     "R"] = mtou_df["Export", "Peak",     "kWh"] * mrates_df["Export", "Peak",     "R/kWh"]
    mtou_df["Export", "Standard", "R"] = mtou_df["Export", "Standard", "kWh"] * mrates_df["Export", "Standard", "R/kWh"]
    mtou_df["Export", "Off-Peak", "R"] = mtou_df["Export", "Off-Peak", "kWh"] * mrates_df["Export", "Off-Peak", "R/kWh"]
    mtou_df["Export", "Total",    "R"] = mtou_df["Export", "Peak", "R"] + mtou_df["Export", "Standard", "R"] + mtou_df["Export", "Off-Peak", "R"]
    mtou_df["Credit", "Total",    "R"] = 0.0
    mtou_df["Nett",   "Total",    "R"] = 0.0

    # noinspection unresolved-references
    prev_mo_cred = max (0.0, mtou_df.at[mtou_idx[11], ("Export", "Total", "R")] - mtou_df.at[mtou_idx[11], ("Import", "Total", "R")])
    for m in mtou_df.index:
        # noinspection unresolved-references
        x = mtou_df.at[m, ("Import", "Total", "R")] - mtou_df.at[m, ("Export", "Total", "R")] - prev_mo_cred
        mtou_df.at[m, ("Nett",   "Total", "R")] = max(0.0, x)
        mtou_df.at[m, ("Credit", "Total", "R")] = prev_mo_cred = max(0.0, -x)
    acc_cost = mtou_df["Nett", "Total", "R"].to_numpy(copy = True)

    if TRC.REACTIVE_PF_THRESH in rates:
        react = [rates[TRC.LOW_SEASON_REACTIVE]] * 5; react += [rates[TRC.HIGH_SEASON_REACTIVE]] * 3; react += [rates[TRC.LOW_SEASON_REACTIVE]] * 4
        mtou_df["Reactive", "Charge", "R"] = mtou_df["Reactive", "Energy", f"kVArh pf<{rates[TRC.REACTIVE_PF_THRESH]}"] * react
        mrates_df["Reactive", "Charge", f"R/kVArh pf<{rates[TRC.REACTIVE_PF_THRESH]}"] = react
        acc_cost += mtou_df["Reactive", "Charge", "R"].to_numpy()

    if TRC.LEGACY in rates:
        mtou_df["Legacy", "Charge", "R"]       = mtou_df["Import", "Total", "kWh"] * rates[TRC.LEGACY]
        mrates_df["Legacy", "Charge", "R/kWh"] = rates[TRC.LEGACY]
        acc_cost += mtou_df["Legacy", "Charge", "R"].to_numpy()

    if TRC.NOT_MAX_DMD in rates:
        mrates_df["Notified", "Max Demand]", "kVA"]      = rates[TRC.NOT_MAX_DMD]
        if TRC.GEN_CAP in rates:
            mtou_df["Generation", "Capacity", "R"]       = rates[TRC.GEN_CAP] * rates[TRC.NOT_MAX_DMD]
            mrates_df["Generation", "Capacity", "R/NMD"] = rates[TRC.GEN_CAP]
            acc_cost += mtou_df["Generation", "Capacity", "R"].to_numpy()
        if TRC.NET_CAP in rates:
            mtou_df["Network", "Capacity", "R"]          = rates[TRC.NET_CAP] * rates[TRC.NOT_MAX_DMD]
            mrates_df["Network", "Capacity", "R/NMD"]    = rates[TRC.NET_CAP]
            acc_cost += mtou_df["Network", "Capacity", "R"].to_numpy()

    d_in_mo = mtou_idx.days_in_month
    if TRC.SERVICE in rates:
        mtou_df["Service", "Charge", "R"]       = rates[TRC.SERVICE] * d_in_mo
        mrates_df["Service", "Charge", "R/day"] = rates[TRC.SERVICE]
        acc_cost += mtou_df["Service", "Charge", "R"].to_numpy()

    if TRC.ADMIN in rates:
        mtou_df["Admin", "Charge", "R"]       = rates[TRC.ADMIN] * d_in_mo
        mrates_df["Admin", "Charge", "R/day"] = rates[TRC.ADMIN]
        acc_cost += mtou_df["Admin", "Charge", "R"].to_numpy()

    if TRC.ANCILLARY_SERVICE in rates:
        mtou_df["Ancillary", "Charge", "R"]       = mtou_df["Import", "Total", "kWh"] * rates[TRC.ANCILLARY_SERVICE]
        mrates_df["Ancillary", "Charge", "R/kWh"] = rates[TRC.ANCILLARY_SERVICE]
        acc_cost += mtou_df["Ancillary", "Charge", "R"].to_numpy()

    if TRC.NET_DMD in rates:
        mtou_df["Network", "Demand", "R"]       = mtou_df["Import", "Total", "kWh"] * rates[TRC.NET_DMD]
        mrates_df["Network", "Demand", "R/kWh"] = rates[TRC.NET_DMD]
        acc_cost += mtou_df["Network", "Demand", "R"].to_numpy()

    if TRC.EXCESS_NETWORK_CAPACITY in rates:
        exc_dmd_ctr = 1
        mtou_df["NMD", "Exceedance", "R"] = 0.0
        for m in mtou_df.index:
            # noinspection unresolved-references
            x = mtou_df.at[m, ("Maximum", "Demand", "kVAmax")] - rates[TRC.NOT_MAX_DMD]
            if x > 0: mtou_df.at[m, ("NMD", "Exceedance", "R")] = x * exc_dmd_ctr * rates[TRC.EXCESS_NETWORK_CAPACITY]
            exc_dmd_ctr += 1
        mrates_df["NMD", "Exceedance", "R/kVA-NMD/Incid"] = rates[TRC.EXCESS_NETWORK_CAPACITY]
        acc_cost += mtou_df["NMD", "Exceedance", "R"].to_numpy()

    if TRC.BASIC in rates:
        mtou_df["Basic", "Charge", "R"]   = rates[TRC.BASIC]
        mrates_df["Basic", "Charge", "R"] = rates[TRC.BASIC]
        acc_cost += mtou_df["Basic", "Charge", "R"].to_numpy()

    if TRC.MAX_DMD in rates:
        mtou_df["Maximum", "Demand", "R"]          = mtou_df["Maximum", "Demand", "kVAmax"] * rates[TRC.MAX_DMD]
        mrates_df["Maximum", "Demand", "R/kVAmax"] = rates[TRC.MAX_DMD]
        acc_cost += mtou_df["Maximum", "Demand", "R"].to_numpy()

    if TRC.SSEG in rates:
        mtou_df["SSEG", "Charge", "R"] = rates[TRC.SSEG]
        mrates_df["SSEG", "Charge", "R"] = rates[TRC.SSEG]
        acc_cost += mtou_df["SSEG", "Charge", "R"].to_numpy()

    mtou_df["Total", "", "R"] = acc_cost

    mtou_df.loc["Totals"] = mtou_df.sum(axis=0)
    mtou_df.at["Totals", ("Maximum", "Demand", "kVAmax")] = np.nan

    return mtou_df, mrates_df
