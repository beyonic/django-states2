# -*- coding: utf-8 -*-
"""Signals"""
from __future__ import absolute_import

import django.dispatch

#: Signal that is sent before a state transition is executed
# providing_args=['from_state','to_state']
before_state_execute = django.dispatch.Signal()

#: Signal that s sent after a state transition is executed
# providing_args=['from_state','to_state']
after_state_execute = django.dispatch.Signal()
