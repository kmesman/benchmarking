#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 20 15:54:21 2022

@author: koen
"""


from qcodes import Instrument
from qcodes.instrument.parameter import ManualParameter
from qcodes.utils import validators


class MockLocalOscillator(Instrument):  # pylint: disable=too-few-public-methods
    """
    A class representing a dummy Local Oscillator,
    for development and testing purposes.
    """

    def __init__(self, name: str):
        """
        Create an instance of the Generic instrument.

        Args:
            name: QCoDeS'name
        """
        super().__init__(name)
        self._add_qcodes_parameters_dummy()

    def _add_qcodes_parameters_dummy(self):
        """
        Used for faking communications
        """
        self.add_parameter(
            name="status",
            initial_value=False,
            vals=validators.Bool(),
            docstring="turns the output on/off",
            parameter_class=ManualParameter,
        )
        self.add_parameter(
            name="frequency",
            label="Frequency",
            unit="Hz",
            initial_value=7e9,
            docstring="The RF Frequency in Hz",
            vals=validators.Numbers(min_value=250e3, max_value=20e9),
            parameter_class=ManualParameter,
        )
        self.add_parameter(
            name="power",
            label="Power",
            unit="dBm",
            initial_value=15.0,
            vals=validators.Numbers(min_value=-60.0, max_value=20.0),
            docstring="Signal power in dBm",
            parameter_class=ManualParameter,
        )