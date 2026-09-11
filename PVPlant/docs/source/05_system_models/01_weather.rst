.. title:: PVPlant | System Models | Weather

.. include:: ..\globals.inc

.. _weather_model:

Weather Model
=============

Needs to differentiate between instantaneous data such as SARAH2 or averaged data such as ERA5.  
Keep in mind the resolution of ERA data is 5 times looser than SARAH data.

The output Weather
Profile contains the components of radiant energy, wind speed, temperature, in that period and 
the next. This model linearly interpolates data, so Weather Data parameters at each step is the 
average of the measured value at that time step and the next.  All time-base computed values use the
midpoint time between this time step and the next.
