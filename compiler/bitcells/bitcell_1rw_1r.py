import design
import debug
import utils
from tech import GDS,layer,parameter,drc

class bitcell_1rw_1r(design.design):
    """
    A single bit cell (6T, 8T, etc.)  This module implements the
    single memory cell used in the design. It is a hand-made cell, so
    the layout and netlist should be available in the technology
    library.
    """

    pin_names = ["bl0", "br0", "bl1", "br1", "wl0", "wl1", "vdd", "gnd"]
    (width,height) = utils.get_libcell_size("cell_1rw_1r", GDS["unit"], layer["boundary"])
    pin_map = utils.get_libcell_pins(pin_names, "cell_1rw_1r", GDS["unit"])

    def __init__(self, name=""):
        # Ignore the name argument
        design.design.__init__(self, "cell_1rw_1r")
        debug.info(2, "Create bitcell with 1RW and 1R Port")

        self.width = bitcell_1rw_1r.width
        self.height = bitcell_1rw_1r.height
        self.pin_map = bitcell_1rw_1r.pin_map

    def analytical_delay(self, slew, load=0, swing = 0.5):
        # delay of bit cell is not like a driver(from WL)
        # so the slew used should be 0
        # it should not be slew dependent?
        # because the value is there
        # the delay is only over half transsmission gate
        from tech import spice
        r = spice["min_tx_r"]*3
        c_para = spice["min_tx_drain_c"]
        result = self.cal_delay_with_rc(r = r, c =  c_para+load, slew = slew, swing = swing)
        return result
   
 
    def list_bitcell_pins(self, col, row):
        """ Creates a list of connections in the bitcell, indexed by column and row, for instance use in bitcell_array """
        bitcell_pins = ["bl0_{0}".format(col),
                        "br0_{0}".format(col),
                        "bl1_{0}".format(col),
                        "br1_{0}".format(col),
                        "wl0_{0}".format(row),
                        "wl1_{0}".format(row),
                        "vdd",
                        "gnd"]
        return bitcell_pins
    
    def list_all_wl_names(self):
        """ Creates a list of all wordline pin names """
        row_pins = ["wl0", "wl1"]    
        return row_pins
    
    def list_all_bitline_names(self):
        """ Creates a list of all bitline pin names (both bl and br) """
        column_pins = ["bl0", "br0", "bl1", "br1"]
        return column_pins
    
    def list_all_bl_names(self):
        """ Creates a list of all bl pins names """
        column_pins = ["bl0", "bl1"]
        return column_pins
        
    def list_all_br_names(self):
        """ Creates a list of all br pins names """
        column_pins = ["br0", "br1"]
        return column_pins
        
    def list_read_bl_names(self):
        """ Creates a list of bl pin names associated with read ports """
        column_pins = ["bl0", "bl1"]
        return column_pins
    
    def list_read_br_names(self):
        """ Creates a list of br pin names associated with read ports """
        column_pins = ["br0", "br1"]
        return column_pins
        
    def list_write_bl_names(self):
        """ Creates a list of bl pin names associated with write ports """
        column_pins = ["bl0"]
        return column_pins
    
    def list_write_br_names(self):
        """ Creates a list of br pin names asscociated with write ports"""
        column_pins = ["br0"]
        return column_pins
    
    def analytical_power(self, proc, vdd, temp, load):
        """Bitcell power in nW. Only characterizes leakage."""
        from tech import spice
        leakage = spice["bitcell_leakage"]
        dynamic = 0 #temporary
        total_power = self.return_power(dynamic, leakage)
        return total_power

    def get_wl_cin(self):
        """Return the relative capacitance of the access transistor gates"""
        #This is a handmade cell so the value must be entered in the tech.py file or estimated.
        #Calculated in the tech file by summing the widths of all the related gates and dividing by the minimum width.
        #FIXME: sizing is not accurate with the handmade cell. Change once cell widths are fixed.
        access_tx_cin = parameter["6T_access_size"]/drc["minwidth_tx"]
        return 2*access_tx_cin
