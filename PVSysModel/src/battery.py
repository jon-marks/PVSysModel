import math
import pandas as pd
from pathlib import Path

# import numpy as np

from globals import *


def read_batt_parms(loc: str) -> dict:

    d = Path(loc)
    bp_table: pd.DataFrame = pd.read_excel(list(d.glob(BATT_PARM))[0], comment = "#")
    bpt = {}
    for r in range(len(bp_table)):
        if bp_table.iloc[r, 0] in bp_map.keys():
            bpt[bp_map[bp_table.iloc[r, 0]]] = bp_table.iloc[r, 2]
    return bpt


def sim_batt(node: Elec,
             tou_tbl: Obj2d,
             outages: Bool2d,
             batt_parms: dict,
             nmd: np.float64) -> tuple[Elec, Real2d, Bool2d]:

#    soc = np.zeros((365, 48), np.float64)
#    socv = soc.ravel()

    soc_max = batt_parms[BP.TOT_CAP]
    soc_min = (1 - batt_parms[BP.USE_CAP]) * batt_parms[BP.TOT_CAP]
    crg_rate = batt_parms[BP.CRG_RATE] * batt_parms[BP.TOT_CAP] / 2
    dcrg_rate = batt_parms[BP.DCRG_RATE] * batt_parms[BP.TOT_CAP] / 2
    crg_eff = batt_parms[BP.CRG_EFF]
    dcrg_eff = batt_parms[BP.DCRG_EFF]
    off_peak_crg_lim = batt_parms[BP.OFF_PEAK_CRG_LIM] * batt_parms[BP.TOT_CAP]
    out_res = batt_parms[BP.OUT_RES] * batt_parms[BP.TOT_CAP]
    std_dcrg_anoon = batt_parms[BP.STD_DCRG_ANOON]
    std_dcrg_morn = batt_parms[BP.STD_DCRG_MORN]
    std_crg = batt_parms[BP.STD_CRG]

    yhhrs = 365 * 48
    inflow = np.zeros((365, 48), np.float64)
    outflow = np.zeros((365, 48), np.float64)
    socf = np.zeros((365*48 +1), np.float64)
    socf[0] = batt_parms[BP.INIT_SOC] * batt_parms[BP.TOT_CAP]
    batt_outages = np.zeros((365, 48), np.bool)

    for yhh in range(0, yhhrs):
        d = yhh // 48; hh = yhh % 48

        if outages[d, hh]:
            soc1 = socf[yhh]
            # first, whatever the battery can absorb from solar, it must
            inflow[d, hh] = crg_eff * min(max(soc_max - soc1, 0),
                                          crg_rate,
                                          node.fE[d, hh])
            soc1 += inflow [d, hh]
            # then, whatever it has available for discharge, it must.
            outflow[d, hh] = dcrg_eff * min(dcrg_rate,
                                            node.tE[d, hh],
                                            max(socf[yhh] - soc_min, 0))
            soc1 -= outflow [d, hh]
            socf[yhh + 1] = soc1
            if soc1 <= soc_min: batt_outages[d, hh] = True

        else:   #   Arbitrage battery use
            match (tou_tbl[d, hh]):
                case TTV.OFF_PEAK:
                    # Don't discharge battery in off-peak when no outage
                    # First charge the battery with available solar
                    soc1 = socf[yhh]
                    inflow[d, hh] = crg_eff * min(max(soc_max - soc1, 0),
                                                  crg_rate,
                                                  node.fE[d, hh])
                    soc1 += inflow[d, hh]
                    # then charge the battery with utility power
                    inflow[d, hh] += crg_eff * min(max(off_peak_crg_lim - soc1, 0),
                                                  crg_rate,
                                                  math.sqrt(nmd**2 - node.fQ[d, hh]**2) / 2)
                    soc1 += inflow[d, hh]
                    socf[yhh+1] = soc1
                    if soc1 <= soc_min: batt_outages[d, hh] = True

                case TTV.STD:
                    soc1 = socf[yhh]
                    # discharge
                    if hh < 24:  # mornings
                        outflow[d, hh] = std_dcrg_morn * dcrg_eff * min(dcrg_rate,
                                                                         node.tE[d, hh],
                                                                         max(soc1 - out_res, 0))
                    else:  # afternoons
                        outflow[d, hh] = std_dcrg_anoon * dcrg_eff * min(dcrg_rate,
                                                                         node.tE[d, hh],
                                                                         max(soc1 - out_res, 0))
                    soc1 -= outflow[d, hh]

                    # Charging
                    # First charge battery with available solar
                    inflow[d, hh] = crg_eff * min(max(soc_max - soc1, 0),
                                                  crg_rate,
                                                  node.fE[d, hh])
                    soc1 += inflow[d, hh]
                    # then charge from util
                    inflow[d, hh] += std_crg * crg_eff * min(max(soc_max - soc1, 0),
                                                  crg_rate,
                                                  math.sqrt(nmd**2 - node.fQ[d, hh]**2) / 2)
                    soc1 += inflow[d, hh]
                    socf[yhh+1] = soc1
                    if soc1 <= soc_min: batt_outages[d, hh] = True

                case TTV.PEAK:
                    #  Discharge battery over utility
                    soc1 = socf[yhh]
                    outflow [d, hh] = dcrg_eff * min(dcrg_rate,
                                                     node.tE[d, hh],
                                                     max(soc1 - out_res, 0))
                    soc1 -= outflow[d, hh]
                    # charge with any excess solar energy
                    inflow[d, hh] = crg_eff * min(max(soc_max - soc1, 0),
                                                  crg_rate,
                                                  node.fE[d, hh])
                    soc1 += inflow[d, hh]
                    socf[yhh + 1] = soc1
                    if soc1 <= soc_min: batt_outages[d, hh] = True

    src_p = outflow * 2
    batt_flow = Elec (fP = src_p,
                      fQ = np.sqrt((src_p / batt_parms[BP.OUT_PF])**2 - src_p**2),
                      fE = outflow,
                      tP = inflow * 2,
                      tQ = np.zeros((365, 48), dtype = np.float64),
                      tE = inflow)


#    padded_outages = np.concatenate(([False], batt_outages.ravel(), [False]))
#    diff = np.diff(padded_outages.astype(int))
#    starts = np.where(diff == 1)[0]
#    ends = np.where(diff == -1)[0]
#    lengths = ends - starts
#    sdt = pd.to_datetime(str(HypotheticalYear) + "-01-01")
#    outage_list = pd.DataFrame(index = sdt + pd.to_timedelta(starts * 30, unit = 'm'), data = pd.to_timedelta(lengths * 30, unit = 'm'))

    return batt_flow, socf[1:].reshape((365, 48)), batt_outages



#    elif node.tE[0, 0] > 0:  # solar energy available to charge the battery
#        inflow[0, 0] = crg_eff * min(max(soc_max - soc_init, 0),
#                                     crg_rate,
#                                     node.tE[0, 0])
#    elif tou_tbl[0, 0] == TTV.OFF_PEAK and soc_init < off_peak_crg_lim:  # or charge in off-peak
#        inflow[0, 0] = crg_eff * min(max(off_peak_crg_lim - soc_init, 0),
#                                     crg_rate,
#                                     math.sqrt(nmd**2 - node.fQ[0, 0]**2) / 2)
#    elif node.fE[0, 0] > 0:  # plant can benefit from battery energy
#        if 5 <= ydow[0] <= 6:  # on weekends
#            if tou_tbl[0, 0] == TTV.STD:  # simply discharge in std TOU
#                outflow[0, 0] = dcrg_eff * min(dcrg_rate,
#                                               node.fE[0, 0],
#                                               max(soc_init - out_res, 0))
#        else:  # weekdays
#            if tou_tbl[0, 0] == TTV.OFF_PEAK:
#                outflow[0, 0] = dcrg_eff * min(dcrg_rate,
#                                               node.fE[0, 0],
#                                               max(soc_init - out_res, 0))
#            elif tou_tbl[0, 0] == TTV.STD:
#                    outflow[0, 0]  = std_dcrg_fract * dcrg_eff * min(dcrg_rate,
#                                                                     node.fE[0, 0],
#                                                                     max(soc_init - out_res, 0))
#    socv[0] = soc_init + inflow [0, 0] - outflow [0, 0]

#    if outages [0, 0]:
#        outflow[0, 0] = dcrg_eff * min(dcrg_rate,
#                                       node.fE[0, 0],
#                                       max(soc_init - soc_min, 0))
#        inflow[0, 0]  = crg_eff  * min(max(soc_max - soc_init, 0),
#                                       crg_rate,
#                                       node.tE[0, 0])

#    elif node.tE[0, 0] > 0:  # solar energy available to charge the battery
#        inflow[0, 0] = crg_eff * min(max(soc_max - soc_init, 0),
#                                     crg_rate,
#                                     node.tE[0, 0])
#    elif tou_tbl[0, 0] == TTV.OFF_PEAK and soc_init < off_peak_crg_lim:  # or charge in off-peak
#        inflow[0, 0] = crg_eff * min(max(off_peak_crg_lim - soc_init, 0),
#                                     crg_rate,
#                                     math.sqrt(nmd**2 - node.fQ[0, 0]**2) / 2)
#    elif node.fE[0, 0] > 0:  # plant can benefit from battery energy
#        if 5 <= ydow[0] <= 6:  # on weekends
#            if tou_tbl[0, 0] == TTV.STD:  # simply discharge in std TOU
#                outflow[0, 0] = dcrg_eff * min(dcrg_rate,
#                                               node.fE[0, 0],
#                                               max(soc_init - out_res, 0))
#        else:  # weekdays
#            if tou_tbl[0, 0] == TTV.OFF_PEAK:
#                outflow[0, 0] = dcrg_eff * min(dcrg_rate,
#                                               node.fE[0, 0],
#                                               max(soc_init - out_res, 0))
#            elif tou_tbl[0, 0] == TTV.STD:
#                    outflow[0, 0]  = std_dcrg_fract * dcrg_eff * min(dcrg_rate,
#                                                                     node.fE[0, 0],
#                                                                     max(soc_init - out_res, 0))
#    socv[0] = soc_init + inflow [0, 0] - outflow [0, 0]

#    for yhh in range(1, yhhrs):
#        d = yhh // 48; hh = yhh % 48
#        if outages [d, hh]:
#            outflow[d, hh] = dcrg_eff * min(dcrg_rate,
#                                            node.fE[d,hh],
#                                            max(socv[yhh - 1] -soc_min), 0)
#        elif node.tE [d,hh] > 0: # solar energy available to charge the battery
#            inflow [d, hh] = crg_eff * min(max(soc_max - socv[yhh - 1], 0),
#                                           crg_rate,
#                                           node.tE [d,hh])
#        elif tou_tbl [d, hh] == TTV.OFF_PEAK and socv[yhh - 1] < off_peak_crg_lim:  # or charge in off-peak
#            inflow [d, hh] = crg_eff * min(max(off_peak_crg_lim - socv[yhh - 1], 0),
#                                           crg_rate,
#                                           math.sqrt(nmd**2 - node.fQ[d, hh]**2) / 2)
#        elif node.fE [d,hh] > 0: # plant can benefit from battery energy
#            if 5 <= ydow[d] <= 6:  # on weekends
#                if tou_tbl [d, hh] == TTV.STD:  # simply discharge in std TOU
#                    outflow [d, hh] = dcrg_eff * min(dcrg_rate,
#                                                     node.fE[d,hh],
#                                                     max(socv[yhh - 1] - out_res, 0))
#            else:  # weekdays
#                if tou_tbl [d, hh] == TTV.PEAK:
#                    outflow [d, hh] = dcrg_eff * min(dcrg_rate,
#                                                     node.fE[d,hh],
#                                                     max(socv [yhh - 1] - out_res, 0))
#                elif tou_tbl [d, hh] == TTV.STD:
#                        if std_dcrg_morn and hh < 12:
#                            outflow [d, hh] = std_dcrg_fract * dcrg_eff * min(dcrg_rate,
#                                                                              node.fE[d,hh],
#                                                                              max(socv [yhh - 1] - out_res, 0))
#        socv[yhh] = socv[yhh - 1] + inflow[d, hh] - outflow[d, hh]
#    src_p = outflow * 2
#    batt_flow = Elec (fP = src_p,
#                      fQ = np.sqrt((src_p / batt_parms[BP.OUT_PF])**2 - src_p**2),
#                      fE = outflow,
#                      tP = inflow * 2,
#                      tQ = np.zeros((365, 48), dtype = np.float64),
#                      tE = inflow)
#    return batt_flow, soc
#

'''

# PC_SPLY_PV               = PC_SPLY + PC_PV
# PC_LOAD_PV               = PC_LOAD + PC_PV
# PC_LOAD_PV_GEN           = PC_LOAD + PC_PV + PC_GEN
# PC_LOAD_PV_BATT          = PC_LOAD + PC_PV + PC_BATT
# PC_LOAD_PV_GEN_BATT      = PC_LOAD + PC_PV + PC_GEN + PC_BATT
# PC_LOAD_SPLY             = PC_LOAD + PC_SPLY
# PC_LOAD_SPLY_GEN_BATT    = PC_LOAD + PC_SPLY + PC_GEN + PC_BATT
# PC_LOAD_SPLY_PV          = PC_LOAD + PC_SPLY + PC_PV
# PC_LOAD_SPLY_PV_GEN      = PC_LOAD + PC_SPLY + PC_PV + PC_GEN
# PC_LOAD_SPLY_PV_BATT     = PC_LOAD + PC_SPLY + PC_PV + PC_BATT
# PC_LOAD_UTIL_PV_GEN_BATT = PC_LOAD + PC_SPLY + PC_PV + PC_GEN + PC_BATT

# Combine electrical profiles
def add_elec (el0: Elec, el1: Elec) -> Elec:
    # Note: summing a sourced E profile with a sunk E profile is equivalent to finding the difference.

    el = Elec()
    p = (el0.fP + el1.fP) - (el0.tP + el1.tP)
    q = (el0.fQ + el1.fQ) - (el0.tQ + el1.tQ)
    np.copyto(el.fP, p, where = (p > 0))
    np.copyto(el.tP, -p, where = (p < 0))
    np.copyto(el.fQ, q, where = (q < 0))
    np.copyto(el.tQ, -q, where = (q < 0))
    np.copyto(el.fE, el.fP / 2)
    np.copyto(el.tE, el.tP / 2)
    return el

def subt_elec (el0: Elec, el1: Elec) -> Elec:
    # Note: subtracting a sunk E profile from a sourced E profile is the equivalent of summing as resulting source
    #       subtracting a sourced E profile from a sunk E profile is the equivalent to summing as resulting sunk

    el = Elec()
    p = (el0.fP - el1.fP) - (el0.tP - el1.tP)
    q = (el0.fQ - el1.fQ) - (el0.tQ - el1.tQ)
    np.copyto(el.fP, p, where = (p > 0))
    np.copyto(el.tP, -p, where = (p < 0))
    np.copyto(el.fQ, q, where = (q < 0))
    np.copyto(el.tQ, -q, where = (q < 0))
    np.copyto(el.fE, el.fP / 2)
    np.copyto(el.tE, el.tP / 2)
    return el


def model_pv_to_load (des_load, pot_pv: Elec) -> Elec:

    act_to_load = add_elec(pot_pv, des_load)
    return act_to_load

def model_pv_and_gen_to_load(des_load, pot_pv: Elec, gen_spec: GenSpec) -> tuple[Elec, Elec, Elec]:

    if gen_spec.MinPwr >5: pass
    elif gen_spec.MinPwr < 5: pass
    act_pv = =add_elec(pot_pv, des_load)
    #act_pv = Elec()
    act_gen = Elec()
    act_to_load = Elec()
    return act_pv, act_gen, act_to_load


def model_pv_and_batt_to_load(des_load, pot_pv: Elec, batt_spec: BattSpec) -> tuple[Elec, Elec, Elec]:

    if batt_spec.Capacity > 5: pass
    elif batt_spec.Capacity < 5: pass
    act_pv =add_elec(pot_pv, des_load)    # act_pv = Elec()
    act_batt = Elec()
    act_to_load = Elec()
    return act_pv, act_batt, act_to_load



    return el, e2, el2

def process_plant(plant_comps: int):

    match plant_comps:
        # Wheeling Model
        # ##############
        case PC.SPLY_PV:
            # Simple wheeling configuration - PV is exported to supply grid for commercial benefit.
            # The pv model on its own provides the energy supplied.  The resulting supply elec model is simply the
            # PV elec model with src and snk swapped - what the PV sources, the utility supply sinks.  The
            # supply elec model is used to forecast the wheeling income.

            pass

        # Off Grid Models
        # ###############

        # A characteristic of off grid models is that the load profile is actually a desired load profile
        # that the PV system makes its best effort to meet.
        case PC.LOAD_PV:
            # Off Grid option where PV is used to power load in applications that are not time-dependent on
            # when they operate.  Loads must be able to operate at less than their required demand.
            # This model calculates the energy generated from PV on a monthly and annual
            # basis to determine if the PV system can provide sufficient energy for the application

            # Actual load profile is found by adding desired load profile (sunk E) with the potential PV profile (sourced E).
            # Then Zero the resulting src values because impossible to export and inverter gets throttled to the
            # instantaneous power it needs to provide.  Then clamp this profile to the maximum inverter power.

            pass

        case PC.LOAD_PV_GEN:
            # Off Grid option were genset is supplemented by PV power. For applications that requires set power
            # at specific times to satisfy the desired load profile.  PV supplements genset to reduce energy
            # generation costs.

            # An interim load profile is created by zeroing out the desired load profile energy values below the
            # genset minimum power.

            # A desired PV profile is created by adding the minimum genset energy (srcd E) to interim load profile (sunk E)

            # The actual PV profile is created by clamping the potential PV profile to the desired PV profile.

            # The actual genset profile is created by adding the actual PV profile (srcd E) from the
            # interim load profile (sunk E) and clamping it to the genset maximum power.

            # Actual load profile is the sum of the actual PV and genset profiles.

            pass

        case PC.LOAD_PV_BATT:
            # Off Grid option where PV and battery are used to power load in applications that are not
            # time-dependent on when they operate.  Battery is charged with excess solar energy, and discharges
            # when there is insufficient solar energy.  Loads must be able to operate at less than their
            # required demand.
            #
            # An interim elec profile is created by adding the desired load profile (sunk E) with the potential
            # PV profile (srcd E)



            # A battery elec model is created - charging with the excess solar, and discharging
            # when insufficient solar.  This model will calculate the energy generated from PV on a monthly and annual
            # basis to determine if the PV system can provide sufficient energy for the application

            # Combine the desired load load and pv models.  The available energy is the resulting sunk energy.  Resulting source
            # energy charges the battery.  Where the resulting energy is less than the load available battery energy
            # can be discharged to meet the load requirement creating an The excess source
            # energy above max load is lost as there is no where it can go.  If loads require a minimum load to operate
            # any sunk energy below this minimum can be zeroed in the resulting sunk energy.
            pass

        case PC.LOAD_PV_GEN_BATT:

            pass

        case PC.LOAD_SPLY:

            pass


        case PC.LOAD_SPLY_PV:

            pass

        case PC.LOAD_SPLY_PV_GEN:

            pass

        case PC.LOAD_SPLY_PV_BATT:

            pass

        case PC.LOAD_SPLY_PV_GEN_BATT:

            pass

        case _:
            # All other component configurations are not considered for the following reasons
            #   1.  Only consider load options.
            #   2.  For off grid (no supply) the only sensible non-trivial options require PV to generate energy
            #   3.  For grid tied options without PV, a genset and/or battery makes sense for electricity
            #       security, but there is none to minimal utility supply offset benefit.
            pass


class Plant:

    def __init__(self) -> None:
        pass
        '''
