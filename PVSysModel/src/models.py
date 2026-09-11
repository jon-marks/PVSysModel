
#import numpy as np
#from tl import *
#from production import *

#from globals import *

#from load import *
from tou_billing import *
from battery import *


def sim_to_load (req_load:  Elec,
                 outages:   Bool2d,
                 tou_tbl:   Obj2d,
                 rates:     dict) -> tuple[Elec, pd.DataFrame, pd.DataFrame]:

    util = Elec(fP = np.where(outages, 0, req_load.fP),
                fQ = np.where(outages, 0, req_load.fQ),
                fE = np.where(outages, 0, req_load.fE),
                tP = np.where(outages, 0, req_load.tP),
                tQ = np.where(outages, 0, req_load.tQ),
                tE = np.where(outages, 0, req_load.tE))

    mtou = monthly_tou(util.fE, util.tE, tou_tbl)
    mvamax = monthly_maxva(util.fP, util.fQ)
    if TRC.REACTIVE_PF_THRESH in rates:
        mreactive = monthly_reactive(util.fP, util.fQ, util.tP, util.tQ, rates[TRC.REACTIVE_PF_THRESH])
        mbilling, mrates = monthly_billing(rates, mtou, mvamax, mreactive)
    else:
        mbilling, mrates = monthly_billing(rates, mtou, mvamax)

    return util, mbilling, mrates


def sim_gt_pv_to_load(rqd_load: Elec,
                      pv:       Elec,
                      outages:  Bool2d,
                      tou_tbl:  Obj2d,
                      rates:    dict) -> tuple[Elec, pd.DataFrame, pd.DataFrame]:

    e1 = Elec.add(rqd_load, pv)

    util   = Elec(fP = np.where(outages, 0, e1.fP),
                  fQ = np.where(outages, 0, e1.fQ),
                  fE = np.where(outages, 0, e1.fE),
                  tP = np.where(outages, 0, e1.tP),
                  tQ = np.where(outages, 0, e1.tQ),
                  tE = np.where(outages, 0, e1.tE))

    mtou = monthly_tou(util.fE, util.tE, tou_tbl)
    mvamax = monthly_maxva(util.fP, util.fQ)
    if TRC.REACTIVE_PF_THRESH in rates:
        mreactive = monthly_reactive(util.fP, util.fQ, util.tP, util.tQ, rates[TRC.REACTIVE_PF_THRESH])
        mbilling, mrates = monthly_billing(rates, mtou, mvamax, mreactive)
    else:
        mbilling, mrates = monthly_billing(rates, mtou, mvamax)

    return util, mbilling, mrates

def sim_gt_batt_to_load(load:       Elec,
                        batt_parms: dict,
                        outages:    Bool2d,
                        tou_tbl:    Obj2d,
                        rates:      dict) -> tuple[Elec, Elec, pd.DataFrame, pd.DataFrame, Bool2d]:

    if TRC.NOT_MAX_DMD in rates:
        kva_lim = rates[TRC.NOT_MAX_DMD]
    elif TRC.MAX_DMD_LMT in rates:
        kva_lim = rates[TRC.MAX_DMD_LMT]
    else: raise "Both Notified Max Demand and Maximum Demand Limit not specified in Rate Parameters file."

    batt, soc, batt_outages = sim_batt(load, tou_tbl, outages, batt_parms, kva_lim)
    e1 = Elec.add (batt, load)

    util = Elec(fP = np.where(outages, 0, e1.fP),
                fQ = np.where(outages, 0, e1.fQ),
                fE = np.where(outages, 0, e1.fE),
                tP = np.where(outages, 0, e1.tP),
                tQ = np.where(outages, 0, e1.tQ),
                tE = np.where(outages, 0, e1.tE))

    sload = Elec(fP = np.where(batt_outages, 0, load.fP),
                 fQ = np.where(batt_outages, 0, load.fQ),
                 fE = np.where(batt_outages, 0, load.fE),
                 tP = np.where(batt_outages, 0, load.tP),
                 tQ = np.where(batt_outages, 0, load.tQ),
                 tE = np.where(batt_outages, 0, load.tE))

    mtou = monthly_tou(util.fE, util.tE, tou_tbl)
    mvamax = monthly_maxva(util.fP, util.fQ)
    if TRC.REACTIVE_PF_THRESH in rates:
        mreactive = monthly_reactive(util.fP, util.fQ, util.tP, util.tQ, rates[TRC.REACTIVE_PF_THRESH])
        mbilling, mrates = monthly_billing(rates, mtou, mvamax, mreactive)
    else:
        mbilling, mrates = monthly_billing(rates, mtou, mvamax)

    return sload, util, mbilling, mrates, batt_outages

def sim_gt_pv_batt_to_load(load:       Elec,
                           pv:         Elec,
                           batt_parms: dict,
                           outages:    Bool2d,
                           tou_tbl:    Obj2d,
                           rates:      dict) -> tuple[Elec, Elec, pd.DataFrame, pd.DataFrame, Bool2d]:

    if TRC.NOT_MAX_DMD in rates:
        kva_lim = rates[TRC.NOT_MAX_DMD]
    elif TRC.MAX_DMD_LMT in rates:
        kva_lim = rates[TRC.MAX_DMD_LMT]
    else: raise "Both Notified Max Demand and Maximum Demand Limit not specified in Rate Parameters file."

    e1 = Elec.add (pv, load)
    batt, soc, batt_outages = sim_batt(e1, tou_tbl, outages, batt_parms, kva_lim)
    e2 = Elec.add(e1, batt)

    util = Elec(fP = np.where(outages, 0, e2.fP),
                fQ = np.where(outages, 0, e2.fQ),
                fE = np.where(outages, 0, e2.fE),
                tP = np.where(outages, 0, e2.tP),
                tQ = np.where(outages, 0, e2.tQ),
                tE = np.where(outages, 0, e2.tE))

    sload = Elec(fP = np.where(batt_outages, 0, load.fP),
                 fQ = np.where(batt_outages, 0, load.fQ),
                 fE = np.where(batt_outages, 0, load.fE),
                 tP = np.where(batt_outages, 0, load.tP),
                 tQ = np.where(batt_outages, 0, load.tQ),
                 tE = np.where(batt_outages, 0, load.tE))

    mtou = monthly_tou(util.fE, util.tE, tou_tbl)
    mvamax = monthly_maxva(util.fP, util.fQ)
    if TRC.REACTIVE_PF_THRESH in rates:
        mreactive = monthly_reactive(util.fP, util.fQ, util.tP, util.tQ, rates[TRC.REACTIVE_PF_THRESH])
        mbilling, mrates = monthly_billing(rates, mtou, mvamax, mreactive)
    else:
        mbilling, mrates = monthly_billing(rates, mtou, mvamax)

    return sload, util, mbilling, mrates, batt_outages

'''



def sim_gt_pv_gen_to_load(pv, genset, load, outages, ydow, tou_tbl, rates):

def sim_gt_batt_gen_to_load(pv, genset, load, outages, ydow, tou_tbl, rates):

def sim_gt_pv_batt_gen_to_load(pv, batt, genset, load, outages, ydow, tou_tbl, rates):

def sim_og_pv_batt_gen_to_load(pv, batt, genset, load, outages, ydow, tou_tbl, rates):



    outages = np.zeros((365,48),np.bool)  # false = 0

    def __init__(self):
        pass
'''
