
#from globals import *


from load import *
from pv import *
from tariff import *
#from tou_billing import *
#from battery import *
from models import *

#from supply import *
#from plant import *

lpf = LoadProfInst(OUTAGEFILL.AVG, 0.9)
load, ydow = read_hist_cons(CFT.ECWIN, DATA_DIR + CONS_SUB_DIR)
tl, el, nel, outages = create_load_prof (load, ydow, lpf)
outage_list = outages_to_outage_list(outages)

tou_tbl = bld_tou_tbl (DATA_DIR + TARF_SUB_DIR, ydow)
rates = read_rates (DATA_DIR + TARF_SUB_DIR)


util_load_only, mbilling_load_only, mrates = sim_to_load (tl, outages, tou_tbl, rates)

ppf = PvProfInst(Uncert = SITE_UNCERTAINTIES)
pv_prod = read_pv_prod(PFT.PVSYST, DATA_DIR + PROD_SUB_DIR)
pv_p = create_pv_profs(pv_prod, uncert = SITE_UNCERTAINTIES, percentiles = (0.75, 0.90, 0.95, 0.99))

util_pv_load, mbilling_pv_load, mrates_pv_load = sim_gt_pv_to_load (tl, pv_prod, outages, tou_tbl, rates)

batt_parms = read_batt_parms(DATA_DIR + BATT_SUB_DIR)

sload_batt_load, util_batt_load, mbilling_batt_load, mrates_batt_load, batt_outages = sim_gt_batt_to_load (el, batt_parms, outages, tou_tbl, rates)

sload_batt_pv_load, util_batt_pv_load, mbilling_batt_pv_load, mrates_batt_pv_load, batt__pv_outages = sim_gt_pv_batt_to_load (el, pv_prod, batt_parms, outages, tou_tbl, rates)

pass
'''
tl_less_pv_p90 = Elec.subtract(tl, pv_prod_pot_p90)
el_less_pv_p50 = Elec.subtract(el, pv_prod_pot_p50)
el_less_pv_p90 = Elec.subtract(el, pv_prod_pot_p90)



mtou_load = monthly_tou(tl.fE, tl.tE, tou_tbl)
mtou_util_p50 = monthly_tou(tl_less_pv_p50.fE, tl_less_pv_p50.tE, tou_tbl)
mtou_util_p90 = monthly_tou(tl_less_pv_p90.fE, tl_less_pv_p90.tE, tou_tbl)

mvamax_load = monthly_maxva (tl.fP, tl.fQ)
mvamax_util_p50 = monthly_maxva (tl_less_pv_p50.fP, tl_less_pv_p50.fQ)
mvamax_util_p90 = monthly_maxva (tl_less_pv_p90.fP, tl_less_pv_p90.fQ)

mreactive_load = monthly_reactive (tl.fP, tl.fQ, tl.tP, tl.tQ, rates[TRC.REACTIVE_PF_THRESH])
mreactive_util_p50 = monthly_reactive (tl_less_pv_p50.fP, tl_less_pv_p50.fQ, tl_less_pv_p50.tP, tl_less_pv_p50.tQ, rates[TRC.REACTIVE_PF_THRESH])
mreactive_util_p90 = monthly_reactive (tl_less_pv_p90.fP, tl_less_pv_p90.fQ, tl_less_pv_p90.tP, tl_less_pv_p90.tQ, rates[TRC.REACTIVE_PF_THRESH])

batt_parms = read_batt_parms(DATA_DIR + BATT_SUB_DIR)

batt_sim_p50, batt_soc_p50 = sim_batt(el_less_pv_p50, tou_tbl, ydow, outages, batt_parms, rates[TRC.NOT_MAX_DMD])
batt_sim_p90, batt_soc_p90 = sim_batt(el_less_pv_p90, tou_tbl, ydow, outages, batt_parms, rates[TRC.NOT_MAX_DMD])

el_less_pv_batt_p50 = Elec.subtract(el_less_pv_p50, batt_sim_p50)
el_less_pv_batt_p90 = Elec.subtract(el_less_pv_p90, batt_sim_p90)

# model pv only with gen

pass



#Site = Plant()
#Util = Supply()
#Draw = Load (CFT.ECWIN, Util.outages)  # returns historical tl which is the consumption model
#Prod = PV (PFT.PVSYST)
#Tarf = Tariff (Load.Dow)
#
#
#DailyLoadTOU = daily_tou (Draw.tl.tE, Draw.tl.fE)
#DailyP50PvTOU = daily_tou (Prod.p50.tE, Prod.p50.fE)
#DailyP90PvTOU = daily_tou (Prod.p90.tE, Prod.p90.fE)
#
#MonthlyLoadTOU = monthly_tou (DailyLoadTOU)
#MonthlyP50PvTOU = monthly_tou (DailyP50PvTOU)
#
#e = combine_elec (Draw.tl, Prod.p50)
#pass
#
#PVandLoadE, PVandLoadP   = Supply.with_pv_and_load (Prod.Ep50, )

pass
'''
