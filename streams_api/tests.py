# -*- coding: utf-8 -*-
from nose.tools import eq_, ok_
from .emails import _calc_mon_thu_sat_delta
from datetime import date, timedelta

def test_date_calculations():
    # Monday
    d = date(2017, 8, 14)
    eq_(d-_calc_mon_thu_sat_delta(d), date(2017, 8, 12))
    eq_((d-_calc_mon_thu_sat_delta(d)).isoweekday(), 6)

    # Thursday
    d = date(2017, 8, 17)
    eq_(d-_calc_mon_thu_sat_delta(d), date(2017, 8, 14))
    eq_((d-_calc_mon_thu_sat_delta(d)).isoweekday(), 1)

    # Saturday
    d = date(2017, 8, 19)
    eq_(d-_calc_mon_thu_sat_delta(d), date(2017, 8, 17))
    eq_((d-_calc_mon_thu_sat_delta(d)).isoweekday(), 4)
