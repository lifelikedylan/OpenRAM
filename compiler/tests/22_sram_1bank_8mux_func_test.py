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

#@unittest.skip("SKIPPING 22_sram_1bank_8mux_func_test")
class sram_1bank_8mux_func_test(openram_test):

    def runTest(self):
        globals.init_openram("config_20_{0}".format(OPTS.tech_name))
        OPTS.analytical_delay = False
        OPTS.netlist_only = True
        OPTS.trim_netlist = False
        
        # This is a hack to reload the characterizer __init__ with the spice version
        from importlib import reload
        import characterizer
        reload(characterizer)
        from characterizer import functional, delay
        if not OPTS.spice_exe:
            debug.error("Could not find {} simulator.".format(OPTS.spice_name),-1)

        from sram import sram
        from sram_config import sram_config
        c = sram_config(word_size=4,
                        num_words=256,
                        num_banks=1)
        c.words_per_row=8
        c.recompute_sizes()
        debug.info(1, "Functional test for sram with {} bit words, {} words, {} words per row, {} banks".format(c.word_size,
                                                                                                                c.num_words,
                                                                                                                c.words_per_row,
                                                                                                                c.num_banks))
        s = sram(c, name="sram")
        tempspice = OPTS.openram_temp + "temp.sp"        
        s.sp_write(tempspice)
        
        corner = (OPTS.process_corners[0], OPTS.supply_voltages[0], OPTS.temperatures[0])
        f = functional(s.s, tempspice, corner)
        d = delay(s.s, tempspice, corner)
        feasible_period = self.find_feasible_test_period(d, s.s, f.load, f.slew)
        
        f.num_cycles = 10
        (fail, error) = f.run()
        self.assertTrue(fail,error)
        
        globals.end_openram()
        
# run the test from the command line
if __name__ == "__main__":
    (OPTS, args) = globals.parse_args()
    del sys.argv[1:]
    header(__file__, OPTS.tech_name)
    unittest.main()
