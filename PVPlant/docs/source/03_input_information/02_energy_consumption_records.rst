.. title:: PVPlant | Input Information | Energy Consumption Records

.. include:: ..\globals.inc

.. _energy_consumption_records:

Energy Consumption Records
==========================

Energy consumption records are the recent historical Load Demand.  This information together with 
anticipated changes in consumption is used by the PCC model to predict future Load Demand.  In
PVPlant modelling, Solar Energy production offset Load Demand time-step to time-step.  If the 
projected load-demand is not accurate, these inaccuracies accumulate as the Load Demand after Solar
Offset will not be accurate, billing will not be accurate, and nor will any of the resulting
financial modelling, leading to poor decision-making from inaccurate results.

Smart Meter Logs
----------------

If the site has been upgraded to a 4 quadrant measuring smart meter then the client's consumption
information is collected remotely by its electrical supply authority, and stored in a database
accessible by the client.  Sometimes clients have not applied for access to this database.  

Form Mandela Bay, Eastern Cape, an application form for access can be found 
:raw-html:`<a href="https://www.nelsonmandelabay.gov.za/datarepository/documents/gIH3S_Metering%20Web%20Site%20Access%20Application%20Form.doc"> here</a>`

When filled in, the application can be submitted to ecwin@mandelametro.gov.za.

For those unfamiliar with ECWin, once logged in:

*  Menus are found at the bottom in status line
*  Select Reports & Profiles
*  Select Profiles
*  Under entity selector select the devices, the Selected Items window will populate.
*  Under Timespan, select the month to yymm to review.
*  Keep the Chart type defaults - Profile Type = Standard and Data Class = Int Period.
*  Under layout and Selection - Press View.
*  In the Main data window switch between profile and Data.  
*  In the Data tab, select Export values.
 
Smart meters log instantaneous P (kW), S (kVA) and Q (kVAr), every half hour.  These records can be
downloaded in monthly quanta.  PVPlant requires the most recent year's data, ending at the prior 
month.

Energy usage is calculated by treating the instantaneous value as if it was the value between the 
previous time-step and this.  Energy (kWh, kVAh, and kVArh) is calculated by multiplying the 
instantaneous values by 1/2 hour, and treating them as the energy between the previous time-step and 
this time-step.  

PVPlant's time-step energy convention is energy values at a time-step and next.  To be consistent, 
the smart meter's logs time base nees to be shifted back by a half hour.

Billing Records
---------------

If Smart Meter Logging is not available, then the next best (a far second) is the consumption values
from billing records.  Many assumptions are made as to the consumption profile, which detracts from 
an accurate consumption model.  When using billing records, any following consumption and financial 
projections will not be definitive, and perhaps a guide or ballpark figures.  The PCC model will 
attempt to flesh out a 17 520 record database from the values in 12 billing records.
