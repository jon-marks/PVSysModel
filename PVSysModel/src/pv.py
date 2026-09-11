"""
   When using pvsyst, pvsyst cvs data need to be set with the 4th column = E_grid -> Energy
   injected into the grid, and the 5th column = EReGrid -> Reactive energy to the grid.  Reactive
   Energy is found in pvsyst in advanced simulation / output file / Simulation variables / System / EReGrid.

"""

from pathlib import Path
from statistics import NormalDist

from globals import *

def read_pv_prod (ft: PFT, loc) -> Elec:


    match ft:
        case PFT.PVSYST:
            d = Path(loc)
            # only one pvsyst file in directory.  Needs to be interpolated from hourly to 1/2 hourly increments
            na = np.loadtxt(list(d.glob(PV_PROD))[0], dtype = np.float64, skiprows = 13, usecols = [4, 5], delimiter = ',')

            # interpolate to half hour intervals.
            x = np.linspace(0, 8760, 8760)
            xi = np.linspace(0, 8760, 8760 * 2)
            p = np.interp(xi, x, na[:, 0]).reshape(365, 48)
            q = np.interp(xi, x, na[:, 1]).reshape(365, 48)
            pv = Elec(fP = np.where(p >= 0, p, 0),
                      fQ = np.where(q >= 0, q, 0),
                      fE = np.where(p >= 0, p / 2, 0),
                      tP = np.where(p < 0, -p, 0),
                      tQ = np.where(q < 0, -q, 0),
                      tE = np.where(p < 0, -p / 2, 0))
            return pv
        case _:
            raise f"Unsupported production file type '{ft}'."

def create_pv_profs(pv :Elec, uncert: float, percentiles: tuple) -> tuple[Elec, ...]:
# Stats lesson:
# A normal distribution (created with statistics.NormalDist(mu = 0.0, sigma = 0.06)
#   where mu = mean = 0.0 = peak of bell curve, sigma = std dev or uncertainties in this case.

# In this normal distribution we are looking for the Z value which is the number along the x-axis for the
# desired probability, e.g. P90 = 0.90. (P90 value is the probability of occurrence exceeding 90%)

# Z = (x - mu) / sigma.  for 90% = 1.2816
# x is found using NormDist(mu, sigma).inv_cdf(Pxx).  Note that if mu = 0 and sigma = 1, Z = x, and because mu =0.0, Z = NormDist(mu, sigma)/sigma
# inv-cdf ==> inverse cummulative distribution function - read python.org library docs for statistic module NormalDist.

# However we calc the prob of power being below a certain prob using the formula Pwr * (1 - Z * sigma),
# and substituting x / sigma for Z we get Pwr * (1 - x)

    pv_p = []
    for percentile in percentiles:
        x_d = 1 - NormalDist(mu = 0.0, sigma = uncert).inv_cdf(percentile)
        pv_p.append(Elec(pv.fP * x_d, pv.fQ * x_d, pv.fE * x_d, pv.tP * x_d, pv.tQ * x_d, pv.tE * x_d))

    return tuple(pv_p)

#class PV:
#
#    p50 = Elec()    # p50 site electricity production
#    p90 = Elec()    # p90 site electricity production
#
#    def __init__(self, ft):
#
#        loc = DATA_DIR + PROD_SUB_DIR
#        match ft:
#            case PFT.PVSYST:
#                # Only one Csv file in the directory.
#                fn = os.listdir (loc)[0]
#                na = np.loadtxt (loc + "/" + fn, dtype = np.float64, skiprows = 13, usecols = [4, 5], delimiter = ',')
#
#                # interpolate to half hour intervals.
#                x = np.linspace(0, 8760, 8760)
#                xi = np.linspace(0, 8760, 8760*2)
#                p = np.interp(xi, x, na[:, 0])
#                q = np.interp(xi, x, na[:, 1])
#                np.copyto(self.p50.fP.ravel()[:], p, where = (p > 0))
#                np.copyto(self.p50.tP.ravel()[:], -p, where = (p < 0))
#                np.copyto(self.p50.fQ.ravel()[:], q, where = (q > 0))
#                np.copyto(self.p50.tQ.ravel()[:], -q, where = (q < 0))
#                self.p50.fE = self.p50.fP / 2; self.p50.tE = self.p50.tP / 2
#
#
#            case _: raise f"Unsupported production file type '{ft}'."
#
#        self.p90.fP = self.p50.fP * (1 - 1.2816 * SITE_UNCERTAINTIES)
#        self.p90.fQ = self.p50.fQ * (1 - 1.2816 * SITE_UNCERTAINTIES)
#        self.p90.fE = self.p90.fP / 2
#        self.p90.tP = self.p50.tP * (1 - 1.2816 * SITE_UNCERTAINTIES)
#        self.p90.tQ = self.p50.tQ * (1 - 1.2816 * SITE_UNCERTAINTIES)
#        self.p90.tE = self.p90.tP / 2
#
