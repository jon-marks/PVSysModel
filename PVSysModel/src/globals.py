from dataclasses import dataclass, field
import datetime as dt
from enum import Enum
import numpy as np

HypotheticalYear = 2026   # must not be a leap year.
MonthStartYday = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365]

#TARIFF = "26-27 Eskom Ruraflex > 900km"
TARIFF = "26-27 NMBM 40X+40Z"
# Tariff Parameters
HIGH_SEASON_START = dt.date(HypotheticalYear, 6, 1)
LOW_SEASON_START = dt.date(HypotheticalYear, 9, 1)

# Load / consumption source enumerations
class CFT(Enum): # CFT -> Load data file type
    ECWIN                = 0
    PNPSCADA             = 1
    ESKOM                = 2

# PV source enumerations
class PFT(Enum): # PFT -> PV data file type
    PVSYST               = 0
    OTHER                = 1

# rate charges
class TRC(Enum): # TRC -> Tariff Rate Charges
    IMP_HIGH_PEAK           = 0
    IMP_HIGH_STD            = 1
    IMP_HIGH_OFF_PEAK       = 2
    IMP_LOW_PEAK            = 3
    IMP_LOW_STD             = 4
    IMP_LOW_OFF_PEAK        = 5
    EXP_HIGH_PEAK           = 6
    EXP_HIGH_STD            = 7
    EXP_HIGH_OFF_PEAK       = 8
    EXP_LOW_PEAK            = 9
    EXP_LOW_STD             = 10
    EXP_LOW_OFF_PEAK        = 11
    LOW_SEASON_REACTIVE     = 12
    HIGH_SEASON_REACTIVE    = 13
    REACTIVE_PF_THRESH      = 14
    LEGACY                  = 15
    GEN_CAP                 = 16
    NET_CAP                 = 17
    SERVICE                 = 18
    ADMIN                   = 19
    ANCILLARY_SERVICE       = 20
    NET_DMD                 = 21
    EXCESS_NETWORK_CAPACITY = 22
    NOT_MAX_DMD             = 23
    BASIC                   = 24
    MAX_DMD                 = 25
    SSEG                    = 26
    MAX_DMD_LMT             = 27

rates_map = {
    'Import High Peak'       : TRC.IMP_HIGH_PEAK,
    'Import High Standard'   : TRC.IMP_HIGH_STD,
    'Import High Off-Peak'   : TRC.IMP_HIGH_OFF_PEAK,
    'Import Low Peak'        : TRC.IMP_LOW_PEAK,
    'Import Low Standard'    : TRC.IMP_LOW_STD,
    'Import Low Off-Peak'    : TRC.IMP_LOW_OFF_PEAK,
    'Export High Peak'       : TRC.EXP_HIGH_PEAK,
    'Export High Standard'   : TRC.EXP_HIGH_STD,
    'Export High Off-Peak'   : TRC.EXP_HIGH_OFF_PEAK,
    'Export Low Peak'        : TRC.EXP_LOW_PEAK,
    'Export Low Standard'    : TRC.EXP_LOW_STD,
    'Export Low Off-Peak'    : TRC.EXP_LOW_OFF_PEAK,
    'Low Reactive'           : TRC.LOW_SEASON_REACTIVE,
    'High Reactive'          : TRC.HIGH_SEASON_REACTIVE,
    'Reactive pf thresh'     : TRC.REACTIVE_PF_THRESH,
    'Legacy'                 : TRC.LEGACY,
    'Generation Capacity'    : TRC.GEN_CAP,
    'Network Capacity'       : TRC.NET_CAP,
    'Service'                : TRC.SERVICE,
    'Admin'                  : TRC.ADMIN,
    'Ancillary Service'      : TRC.ANCILLARY_SERVICE,
    "Network Demand"         : TRC.NET_DMD,
    'Excess Network Capacity': TRC.EXCESS_NETWORK_CAPACITY,
    'Notified Max Demand'    : TRC.NOT_MAX_DMD,
    'Basic'                  : TRC.BASIC,
    'Maximum Demand'         : TRC.MAX_DMD,
    'SSEG'                   : TRC.SSEG,
    'Maximum Demand Limit'   : TRC.MAX_DMD_LMT,
    }


class BP(Enum):     # BP -> Battery Params
    TOT_CAP          = 0
    USE_CAP          = 1
    OUT_RES          = 2
    CRG_RATE         = 3
    DCRG_RATE        = 4
    CRG_EFF          = 5
    DCRG_EFF         = 6
    ANN_DEGR         = 7
    OUT_PF           = 8
    OFF_PEAK_CRG_LIM = 9
    STD_DCRG_MORN    = 10
    STD_DCRG_ANOON   = 11
    STD_CRG          = 12
    INIT_SOC         = 13

bp_map = {
    'Battery Total Capacity'        : BP.TOT_CAP,
    'Useable Capacity'              : BP.USE_CAP,
    'Outage Reserve'                : BP.OUT_RES,
    'Charging Rate'                 : BP.CRG_RATE,
    'Discharging Rate'              : BP.DCRG_RATE,
    'Charging Efficiency'           : BP.CRG_EFF,
    'Discharging Efficiency'        : BP.DCRG_EFF,
    'Annual Degradation'            : BP.ANN_DEGR,
    'Output Power Factor'           : BP.OUT_PF,
    'Off Peak Cap Charge Limit'     : BP.OFF_PEAK_CRG_LIM,
    'Std Discharge Mornings %'      : BP.STD_DCRG_MORN,
    'Std Discharge Afternoons %'    : BP.STD_DCRG_ANOON,
    'Std Charge %'                  : BP.STD_CRG,
    'Initial State Of Charge'       : BP.INIT_SOC
    }


class TTV (Enum): # TTV -> Tariff table Values
    PEAK                  = 0
    STD                   = 1
    OFF_PEAK              = 2

class TOUC (Enum): # TOU Table columns
    IMPORT_PEAK          = 0
    IMPORT_STD           = 1
    IMPORT_OFF_PEAK      = 2
    IMPORT_TOTAL         = 3
    EXPORT_PEAK          = 4
    EXPORT_STD           = 5
    EXPORT_OFF_PEAK      = 6
    EXPORT_TOTAL         = 7

# dataclasses (C's typdefs)

# Numpy array typedefs
Uint81d  = np.ndarray[tuple [int], np.dtype[np.uint8]]
Real1d = np.ndarray[tuple [int], np.dtype[np.float64]]
Real2d = np.ndarray[tuple [int,int], np.dtype[np.float64]]
Obj2d  = np.ndarray[tuple [int,int], np.dtype[np.object_]]
Bool2d = np.ndarray[tuple [int,int], np.dtype[np.bool]]

# Elec Profile
@dataclass
class Elec:
# The 1/2 hourly values over a year of the electricity parms entering and leaving
# an electrical entity (tl, PV, Batt, Gen or Supply, etc.)
# See https://www.storymelange.com/posts/technical/be-careful-using-pythons-dataclass.html for reasons to use "field(default_factory=lambda:"
    fP: np.ndarray = field(default_factory = lambda: np.zeros ((365, 48), np.float64))  # Source Power 365 days x 48 half hours
    fQ: np.ndarray = field(default_factory = lambda: np.zeros ((365, 48), np.float64))  # Source reactive Power 365 days x 48 half hours
    fE: np.ndarray = field(default_factory = lambda: np.zeros ((365, 48), np.float64))  # Source reactive Power 365 days x 48 half hours
    tP: np.ndarray = field(default_factory = lambda: np.zeros ((365, 48), np.float64))  # Sink Power 365 days x 48 half hours
    tQ: np.ndarray = field(default_factory = lambda: np.zeros ((365, 48), np.float64))  # Sink reactive Power 365 days x 48 half hours
    tE: np.ndarray = field(default_factory = lambda: np.zeros ((365, 48), np.float64))  # Source reactive Power 365 days x 48 half hours

#    @staticmethod
#    def add (el0: Elec, el1: Elec) -> Elec:
#        fp = el0.fP + el1.fP
#        tp = el0.tP + el1.tP
#        return Elec(fP = fp,
#                    fQ = el0.fQ + el1.fQ,
#                    fE = fp / 2,
#                    tP =tp,
#                    tQ = el0.tQ + el1.tQ,
#                    tE = tp / 2)

#    def util (e :Elec) -> Elec:
#    # e.f ==> export, e.t ==> import
#        p = (e.tP - e.fP).ravel(); q = (e.tQ - e.fQ).ravel()
#        ps = np.where(p >= 0, 1, -1); qs = np.where(q >= 0, 1, -1)
#        pd = np.diff(ps, prepend = ps [-1]); qd = np.diff(qs, prepend = qs[-1])
#        # incomplete
#
#        el = Elec(fP = np.where(p >= 0, p, 0),
#                  fQ = np.where(q >= 0, q, 0),
#                  fE = np.where(p >= 0, p / 2, 0),
#                  tP = np.where(p < 0, -p, 0),
#                  tQ = np.where(q < 0, -q, 0),
#                  tE = np.where(p < 0, -p / 2, 0))
#        return el

    @staticmethod
    def add(el0: Elec, el1: Elec) -> Elec:
        p = (el0.fP + el1.fP) - (el0.tP + el1.tP)
        q = (el0.fQ + el1.fQ) - (el0.tQ + el1.tQ)
        el = Elec(fP = np.where(p >= 0, p, 0),
                  fQ = np.where(q >= 0, q, 0),
                  fE = np.where(p >= 0, p / 2, 0),
                  tP = np.where(p < 0, -p, 0),
                  tQ = np.where(q < 0, -q, 0),
                  tE = np.where(p < 0, -p / 2, 0))
        return el
#
#    @staticmethod
#    def subtract (el0: Elec, el1: Elec) -> Elec:
#        p = (el0.fP - el1.fP) - (el0.tP - el1.tP)
#        q = (el0.fQ - el1.fQ) - (el0.tQ - el1.tQ)
#        el = Elec(fP = np.where(p >= 0, p, 0),
#                  fQ = np.where(q >= 0, q, 0),
#                  fE = np.where(p >= 0, p / 2, 0),
#                  tP = np.where(p < 0, -p, 0),
#                  tQ = np.where(q < 0, -q, 0),
#                  tE = np.where(p < 0, -p / 2, 0))
#        return el


class OUTAGEFILL (Enum):
    NONE = 0
    AVG = 1

@dataclass
class LoadProfInst:
    #instructions on how to create a load profile
    OutageFill: OUTAGEFILL
    EssLoadMult: float  # TODO:  create more sophisticated creation of essential and non essential loads

@dataclass
class PvProfInst:
    Uncert: float

@dataclass
class GenSpec:
    MinPwr: np.float64
    MaxPwr: np.float64

### Site related settings

# TODO:  Need to be able to enter uncertainties and compute
SITE_UNCERTAINTIES = .06   # Std dev %

# Default dirs
DATA_DIR       = "./../data/"
CONS_SUB_DIR   = "cons/"    # historical consumption for cons model contains 12 consecutive monthly files of ecwin or pnpscada data files
PROD_SUB_DIR   = "prod/"    # contains a pvsyst hourly pvsyst sim out put file E_grid in Col 4 an EReGrid in Col 5
TARF_SUB_DIR   = "tariff/"  # contains the tariff data files
BATT_SUB_DIR   = "batt/"    # contains all the battery information

# Production Data files
PV_PROD         = "PV*"

# Tariff Data files
PUB_HOLS        = "Public Holidays*"    # list of pub holidays in consumption data period and Eskom dow treatment
TOU             = "TOU*"                # table of TOU tariff types per hour over a low season week and a high season week
RATES           = "Rates*"

# Battery params data file
BATT_PARM       = "Battery*"

# Plant enums
PC_LOAD = 0b00000001  #  1
PC_SPLY = 0b00000010  #  2
PC_PV   = 0b00000100  #  4
PC_GEN  = 0b00001000  #  8
PC_BATT = 0b00010000  # 16

class PC (Enum):
    SPLY_PV               = PC_SPLY + PC_PV
    LOAD_PV               = PC_LOAD + PC_PV
    LOAD_PV_GEN           = PC_LOAD + PC_PV + PC_GEN
    LOAD_PV_BATT          = PC_LOAD + PC_PV + PC_BATT
    LOAD_PV_GEN_BATT      = PC_LOAD + PC_PV + PC_GEN + PC_BATT
    LOAD_SPLY             = PC_LOAD + PC_SPLY
    LOAD_SPLY_PV          = PC_LOAD + PC_SPLY + PC_PV
    LOAD_SPLY_PV_GEN      = PC_LOAD + PC_SPLY + PC_PV + PC_GEN
    LOAD_SPLY_PV_BATT     = PC_LOAD + PC_SPLY + PC_PV + PC_BATT
    LOAD_SPLY_PV_GEN_BATT = PC_LOAD + PC_SPLY + PC_PV + PC_GEN + PC_BATT
