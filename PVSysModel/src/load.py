"""
    When data spans a leap year, data for 29 Feb is ignored and Dow array is adjusted for missing day.


"""


from calendar import monthrange, isleap
import datetime as dt
import os
from pathlib import Path

import pandas as pd

from globals import *



def read_hist_cons(ft: CFT, loc: str) -> tuple[Elec, Uint81d]:


    ydates = [0] * 365
    ydow = np.empty(365, np.uint8)
    load  = Elec()
    pub_hols = pd.read_excel(list(Path(DATA_DIR + TARF_SUB_DIR).glob(PUB_HOLS))[0], comment = "#")

    match ft:
        case CFT.ECWIN:
            for fn in os.listdir(loc):
                df = pd.read_excel(loc + fn).fillna(0)
                # TODO: Load file formats: can add error checking later, assume 4 cols (date, P and Q, kVAmax) or 5 cols (date, P Import, Q, and P Export, kVAmax)
                #       still need to verify which col is which.
                t_p = t_q = f_p = -1
                for c in range(1, len(df.columns)):
                    if "P Imp" in df.columns[c]: t_p = c
                    if "Q (kV" in df.columns[c]: t_q = c
                    if "P Exp" in df.columns[c]: f_p = c
                if t_p == -1 or t_q == -1 or f_p == -1: raise f"Can't find required columns in consumption file: '{fn}'."

                # noinspection unresolved-references
                sd = df.iat[0, 0].to_pydatetime()
                ofs = (sd - dt.datetime(sd.year, 1, 1)).days
                if isleap(sd.year) and sd.month > 2: ofs -= 1
                dow = sd.weekday()

                for d in range(ofs, ofs + monthrange(sd.year, sd.month)[1]):
                    # noinspection bad-index
                    ydates[d] = (sd + dt.timedelta(days = d - ofs)).date()
                    ydow[d] = dow; dow = (dow + 1) % 7


                for ph in pub_hols.itertuples(index = False):
                    yd = -1
                    try:
                        yd = ydates.index(ph[0].date())
                    except ValueError:
                        pass
                    if yd >= 0: ydow[yd] = 6 if ph[2] == "Sunday" else 5

                i = ofs * 48
                q = df.iloc[:, t_q].to_numpy(copy = True)
                load.tP.ravel()[i:i + len(df)] = df.iloc[:, t_p].to_numpy(copy = True)
                load.fP.ravel()[i:i + len(df)] = df.iloc[:, f_p].to_numpy(copy = True)
                np.copyto(load.tQ.ravel()[i:i + len(df)], q, where = (load.tP.ravel()[i:i + len(df)] > 0))
                np.copyto(load.fQ.ravel()[i:i + len(df)], q, where = (load.fP.ravel()[i:i + len(df)] > 0))
                pass

        case CFT.PNPSCADA:
            raise "Load file type 'pnpscada' not implemented yet."

        case _:
            raise f"Unsupported consumption file type: '{ft}'."

    # noinspection bad-return
    return load, ydow


def create_load_prof (load: Elec,
                      ydow: Uint81d,
                      lpi: LoadProfInst
                      ) -> tuple[Elec, Elec, Elec,  Bool2d]:
    # creates a load profile (total, essential and non-essential) and fills outages in the load profile, both per instructions in lpi.

    outages = np.zeros((365,48), np.bool)

    tl = Elec(fP = load.fP.copy(),
              fQ = load.fQ.copy(),
              tP = load.tP.copy(),
              tQ = load.tQ.copy())

    match lpi.OutageFill:
        case OUTAGEFILL.NONE: pass
        case OUTAGEFILL.AVG:
            for d in range(365):
                for hh in range(48):
                    if load.tP[d, hh] == 0 and load.fP[d, hh] == 0:
                        outages[d, hh] = True
                        src_p = []; src_q = []; snk_p = []; snk_q = []
                        # find values to avg to interpolate - look back and forward same time and same day of week (not pub hol) to collect values.
                        for dd in range(d - 30, d + 30):
                            if ydow[d] == ydow[dd] and (tl.tP[dd, hh] != 0 or tl.fP[dd, hh] != 0):
                                src_p.append(tl.fP[dd, hh])
                                src_q.append(tl.fQ[dd, hh])
                                snk_p.append(tl.tP[dd, hh])
                                snk_q.append(tl.tQ[dd, hh])
                        tl.fP[d, hh] = sum(src_p) / len(src_p) if snk_p else 0
                        tl.fQ[d, hh] = sum(snk_q) / len(snk_q) if snk_q else 0
                        tl.tP[d, hh] = sum(snk_p) / len(snk_p) if snk_p else 0
                        tl.tQ[d, hh] = sum(snk_q) / len(snk_q) if snk_q else 0

            tl.tE = tl.tP / 2       # halve values to get kWh from kW per half hour.
            tl.fE = tl.fP / 2
        case _:  raise f"Unsupported outage fil method '{lpi.OutageFill}'."
## technique to count number of outages and duration.  Ultimately we want for each month. start datetime and # of 1/2h counts.
## this info is needed to calc the cost of outage, or cost of genset running during an outage.  perhaps make it its own function
## because unsupplied load will be different when battery is involved.


#    return list(zip(starts, lengths))

    # TODO: create essential and non essential profiles.  They could be meter data read in like consumption data, or estimated with
    #       a formula.  For the initial development of code set to ess / non ess 90% / 10%.  Ess / Non-Ess loads only make sense
    #       with a site energy backup like battery and/or generator
    el  = Elec(fP = tl.fP * lpi.EssLoadMult,
               fQ = tl.fQ * lpi.EssLoadMult,
               fE = tl.fE * lpi.EssLoadMult,
               tP = tl.tP * lpi.EssLoadMult,
               tQ = tl.tQ * lpi.EssLoadMult,
               tE = tl.tE * lpi.EssLoadMult)

    nel = Elec(fP = tl.fP * (1 - lpi.EssLoadMult),
               fQ = tl.fQ * (1 - lpi.EssLoadMult),
               fE = tl.fE * (1 - lpi.EssLoadMult),
               tP = tl.tP * (1 - lpi.EssLoadMult),
               tQ = tl.tQ * (1 - lpi.EssLoadMult),
               tE = tl.tE * (1 - lpi.EssLoadMult))

    return tl, el, nel, outages

def outages_to_outage_list (Outage: Bool2d) -> pd.DataFrame:

    padded_outages = np.concatenate(([False], Outage.ravel(), [False]))
    diff = np.diff(padded_outages.astype(int))
    starts = np.where(diff == 1)[0]
    ends = np.where(diff == -1)[0]
    lengths = ends - starts
    sdt = pd.to_datetime(str(HypotheticalYear) + "-01-01")
    return pd.DataFrame(index = sdt + pd.to_timedelta(starts * 30, unit='m'),
                        data = pd.to_timedelta(lengths * 30, unit = 'm'))




#class Load:

#    Dow = np.empty (365, np.uint64)                     # Dow array used in TOU billing
#
#    tl  = Elec()    # Total load
#    el  = Elec()    # Essential load
#    nel = Elec()    # Non-essential load
#
#   def __init__ (self, ft, outages):
#        pass
#        dates = [0] * 365
#        pub_hols = pd.read_excel (list (Path (DATA_DIR + TARIFF_SUB_DIR).glob (PUB_HOLS))[0], comment = "#")
#        loc = DATA_DIR + CONS_SUB_DIR
#        match ft:
#            case CFT.ECWIN:
#                for fn in os.listdir (loc):
#                    df = pd.read_excel (loc + fn).fillna(0)
#                    # TODO: Load file formats: can add error checking later, assume 4 cols (date, P and Q, kVAmax) or 5 cols (date, P Import, Q, and P Export, kVAmax)
#                    #       still need to verify which col is which.
#                    snk_p = snk_q = src_p = -1
#                    for c in range(1, len(df.columns)):
#                        if "P Imp" in df.columns[c]: snk_p = c
#                        if "Q (kV" in df.columns[c]: snk_q = c
#                        if "P Exp" in df.columns[c]: src_p = c
#                    if snk_p == -1 or snk_q == -1 or src_p == -1: raise f"Can't find required columns in consumption file: '{fn}'."
#
#                    # noinspection unresolved-references
#                    sd = df.iat[0,0].to_pydatetime()
#                    ofs = (sd - dt.datetime(sd.year,1,1)).days
#                    if isleap(sd.year) and sd.month > 2: ofs -= 1
#                    dow = sd.weekday()
#
#                    for d in range(ofs, ofs+ monthrange(sd.year,sd.month)[1]):
#                        ydow[d] = dow; dow = (dow + 1) % 7
#                        # noinspection bad-index
#                        dates [d] = (sd + dt.timedelta(days = d - ofs)).date()
#
#                    for ph in pub_hols.itertuples (index = False):
#                        yd = -1
#                        try:
#                            yd = dates.index (ph[0].date ())
#                        except ValueError:
#                            pass
#                        if yd >= 0: ydow[yd] = 6 if ph[2] == "Sunday" else 5
#
#                    i = ofs * 48
#                    self.tl.tP.ravel()[i:i + len(df)] = df.iloc[:, snk_p].to_numpy(copy = True)
#                    self.tl.tQ.ravel()[i:i + len(df)] = df.iloc[:, snk_q].to_numpy(copy = True)
#                    self.tl.fP.ravel()[i:i + len(df)] = df.iloc[:, src_p].to_numpy(copy = True)
#
#            case CFT.PNPSCADA:
#                raise "Load file type 'pnpscada' not implemented yet."
#
#            case _:
#                raise f"Unsupported consumption file type: '{ft}'."
#
#        for d in range(365):
#            for hh in range(48):
#                if self.tl.tP[d,hh] == 0 and self.tl.fP[d,hh] == 0:
#                    outages[d, hh] = True
#                    snk_p = []; snk_q = []; src_p = []
#                    # find values to avg to interpolate - look back and forward same time and same day of week (not pub hol) to collect values.
#                    for dd in range (d - 22, d + 22):
#                        if ydow [d] == ydow [dd] and (self.tl.tP [dd, hh] != 0 or self.tl.fP [dd, hh] != 0):
#                            snk_p.append(self.tl.tP [dd, hh])
#                            snk_q.append(self.tl.tQ [dd, hh])
#                            src_p.append(self.tl.fP [dd, hh])
#                    self.tl.tP[d, hh] = sum(snk_p) / len(snk_p) if snk_p else 0
#                    self.tl.tQ[d, hh] = sum(snk_q) / len(snk_q) if snk_q else 0
#                    self.tl.fP[d, hh] = sum(src_p) / len(src_p) if snk_p else 0
#
#        self.tl.tE = self.tl.tP / 2; self.tl.fE = self.tl.fP / 2  # halve values to get kWh from kW per half hour.
#
#        # TODO: create essential and non essential profiles.  They could be meter data read in like consumption data, or estimated with
#        #       a formula.  For the initial development of code set to ess / non ess 90% / 10%.  Ess / Non-Ess loads only make sense
#        #       with a site energy backup like battery and/or generator
#        self.el.tP = .9 * self.tl.tP; self.el.tQ = .9 * self.tl.tQ; self.el.fP = .9 * self.tl.fP
#        self.el.tE = self.el.tP / 2; self.el.fE = self.el.fP / 2
#
#        self.nel.tP = .1 * self.tl.tP; self.nel.tQ = .1 * self.tl.tQ; self.nel.fP = .1 * self.tl.fP
#        self.nel.tE = self.nel.tP / 2; self.nel.fE = self.nel.fP / 2
#        pass
#
