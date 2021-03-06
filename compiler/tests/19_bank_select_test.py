#!/usr/bin/env python3
"""
Run a regression test on various srams
"""

import unittest
from testutils import header,openram_test
import sys,os
sys.path.append(os.path.join(sys.path[0],".."))
import globals
from globals import OPTS
import debug

class bank_select_test(openram_test):

    def runTest(self):
        globals.init_openram("config_20_{0}".format(OPTS.tech_name))
        import bank_select

        debug.info(1, "No column mux, rw control logic")
        a = bank_select.bank_select(port="rw")
        self.local_check(a)
        
        OPTS.bitcell = "pbitcell"
        debug.info(1, "No column mux, rw control logic")
        a = bank_select.bank_select(port="rw")
        self.local_check(a)
        
        OPTS.num_rw_ports = 0
        OPTS.num_w_ports = 1
        OPTS.num_r_ports = 1

        debug.info(1, "No column mux, w control logic")
        a = bank_select.bank_select(port="w")
        self.local_check(a)
        
        debug.info(1, "No column mux, r control logic")
        a = bank_select.bank_select(port="r")
        self.local_check(a)
        
        globals.end_openram()
        
# run the test from the command line
if __name__ == "__main__":
    (OPTS, args) = globals.parse_args()
    del sys.argv[1:]
    header(__file__, OPTS.tech_name)
    unittest.main()
