from direction import direction
from pin_layout import pin_layout
from vector3d import vector3d
from vector import vector
import grid_utils
from tech import drc
import debug

class pin_group:
    """
    A class to represent a group of rectangular design pin. 
    It requires a router to define the track widths and blockages which 
    determine how pin shapes get mapped to tracks. 
    It is initially constructed with a single set of (touching) pins.
    """
    def __init__(self, name, pin_set, router):
        self.name = name
        # Flag for when it is routed
        self.routed = False
        # Flag for when it is enclosed
        self.enclosed = False
        
        # Remove any redundant pins (i.e. contained in other pins)
        irredundant_pin_set = self.remove_redundant_shapes(list(pin_set))
        
        # This is a list because we can have a pin group of disconnected sets of pins
        # and these are represented by separate lists
        self.pins = [set(irredundant_pin_set)]

        self.router = router
        # These are the corresponding pin grids for each pin group.
        self.grids = set()
        # These are the secondary grids that could or could not be part of the pin
        self.secondary_grids = set()
        
        # The corresponding set of partially blocked grids for each pin group.
        # These are blockages for other nets but unblocked for routing this group.
        # These are also blockages if we used a simple enclosure to route to a rail.
        self.blockages = set()

        # This is a set of pin_layout shapes to cover the grids
        self.enclosures = set()

    def __str__(self):
        """ override print function output """
        total_string = "(pg {} ".format(self.name)
        
        pin_string = "\n  pins={}".format(self.pins)
        total_string += pin_string
        
        grids_string = "\n  grids={}".format(self.grids)
        total_string += grids_string

        grids_string = "\n  secondary={}".format(self.secondary_grids)
        total_string += grids_string
        
        if self.enclosed:
            enlosure_string = "\n  enclose={}".format(self.enclosures)
            total_string += enclosure_string

        total_string += ")"
        return total_string

    def __repr__(self):
        """ override repr function output """
        return str(self)
    
    def size(self):
        return len(self.grids)

    def set_routed(self, value=True):
        self.routed = value

    def is_routed(self):
        return self.routed
        
    def pins_enclosed(self):
        """
        Check if all of the pin shapes are enclosed.
        Does not check if the DRC is correct, but just touching.
        """
        for pin_list in self.pins:
            pin_is_enclosed=False
            for pin in pin_list:
                if pin_is_enclosed:
                    break
                for encosure in self.enclosures:
                    if pin.overlaps(enclosure):
                        pin_is_enclosed=True
                        break
            else:
                return False
            
        return True
        
    def remove_redundant_shapes(self, pin_list):
        """
        Remove any pin layout that is contained within another.
        Returns a new list without modifying pin_list.
        """
        local_debug = False
        if local_debug:
            debug.info(0,"INITIAL: {}".format(pin_list))
        
        # Make a copy of the list to start
        new_pin_list = pin_list.copy()

        remove_indices = set()
        # This is n^2, but the number is small
        for index1,pin1 in enumerate(pin_list):
            # If we remove this pin, it can't contain other pins
            if index1 in remove_indices:
                continue
            
            for index2,pin2 in enumerate(pin_list):
                # Can't contain yourself, but compare the indices and not the pins
                # so you can remove duplicate copies.
                if index1==index2:
                    continue
                # If we already removed it, can't remove it again...
                if index2 in remove_indices:
                    continue
                
                if pin1.contains(pin2):
                    if local_debug:
                        debug.info(0,"{0} contains {1}".format(pin1,pin2))
                    remove_indices.add(index2)

        # Remove them in decreasing order to not invalidate the indices
        for i in sorted(remove_indices, reverse=True):
            del new_pin_list[i]
                        
        if local_debug:
            debug.info(0,"FINAL  : {}".format(new_pin_list))
            
        return new_pin_list

    # FIXME: This relies on some technology parameters from router which is not clean.
    def compute_enclosures(self):
        """
        Find the minimum rectangle enclosures of the given tracks.
        """
        # Enumerate every possible enclosure
        pin_list = []
        for seed in self.grids:
            (ll, ur) = self.enclose_pin_grids(seed, direction.NORTH, direction.EAST)
            enclosure = self.router.compute_pin_enclosure(ll, ur, ll.z)
            pin_list.append(enclosure)

            (ll, ur) = self.enclose_pin_grids(seed, direction.EAST, direction.NORTH)
            enclosure = self.router.compute_pin_enclosure(ll, ur, ll.z)
            pin_list.append(enclosure)


        # Now simplify the enclosure list 
        new_pin_list = self.remove_redundant_shapes(pin_list)
            
        return new_pin_list
        
    def compute_connector(self, pin, enclosure):
        """ 
        Compute a shape to connect the pin to the enclosure shape. 
        This assumes the shape will be the dimension of the pin.
        """
        if pin.xoverlaps(enclosure):
            # Is it vertical overlap, extend pin shape to enclosure
            plc = pin.lc()
            prc = pin.rc()
            elc = enclosure.lc()
            erc = enclosure.rc()
            ymin = min(plc.y,elc.y)
            ymax = max(plc.y,elc.y)
            ll = vector(plc.x, ymin)
            ur = vector(prc.x, ymax)
        elif pin.yoverlaps(enclosure):
            # Is it horizontal overlap, extend pin shape to enclosure
            pbc = pin.bc()
            puc = pin.uc()
            ebc = enclosure.bc()
            euc = enclosure.uc()
            xmin = min(pbc.x,ebc.x)
            xmax = max(pbc.x,ebc.x)
            ll = vector(xmin, pbc.y)
            ur = vector(xmax, puc.y)
        else:
            # Neither, so we must do a corner-to corner
            pc = pin.center()
            ec = enclosure.center()
            xmin = min(pc.x, ec.x)
            xmax = max(pc.x, ec.x)
            ymin = min(pc.y, ec.y)
            ymax = max(pc.y, ec.y)
            ll = vector(xmin, ymin)
            ur = vector(xmax, ymax)

        if ll.x==ur.x or ll.y==ur.y:
            return None
        p = pin_layout(pin.name, [ll, ur], pin.layer)
        return p

    def find_above_connector(self, pin, enclosures):
        """ 
        Find the enclosure that is to above the pin
        and make a connector to it's upper edge.
        """
        # Create the list of shapes that contain the pin edge
        edge_list = []
        for shape in enclosures:
            if shape.xcontains(pin):
                edge_list.append(shape)
        
        # Sort them by their bottom edge
        edge_list.sort(key=lambda x: x.by(), reverse=True)

        # Find the bottom edge that is next to the pin's top edge
        above_item = None
        for item in edge_list:
            if item.by()>=pin.uy():
                above_item = item
            else:
                break

        # There was nothing 
        if above_item==None:
            return None
        # If it already overlaps, no connector needed
        if above_item.overlaps(pin):
            return None

        # Otherwise, make a connector to the item
        p = self.compute_connector(pin, above_item)
        return p

    def find_below_connector(self, pin, enclosures):
        """ 
        Find the enclosure that is below the pin
        and make a connector to it's upper edge.
        """
        # Create the list of shapes that contain the pin edge
        edge_list = []
        for shape in enclosures:
            if shape.xcontains(pin):
                edge_list.append(shape)
        
        # Sort them by their upper edge
        edge_list.sort(key=lambda x: x.uy())

        # Find the upper edge that is next to the pin's bottom edge
        bottom_item = None
        for item in edge_list:
            if item.uy()<=pin.by():
                bottom_item = item
            else:
                break

        # There was nothing to the left
        if bottom_item==None:
            return None
        # If it already overlaps, no connector needed
        if bottom_item.overlaps(pin):
            return None
        
        # Otherwise, make a connector to the item
        p = self.compute_connector(pin, bottom_item)
        return p
    
    def find_left_connector(self, pin, enclosures):
        """ 
        Find the enclosure that is to the left of the pin
        and make a connector to it's right edge.
        """
        # Create the list of shapes that contain the pin edge
        edge_list = []
        for shape in enclosures:
            if shape.ycontains(pin):
                edge_list.append(shape)
        
        # Sort them by their right edge
        edge_list.sort(key=lambda x: x.rx())

        # Find the right edge that is to the pin's left edge
        left_item = None
        for item in edge_list:
            if item.rx()<=pin.lx():
                left_item = item
            else:
                break

        # There was nothing to the left
        if left_item==None:
            return None
        # If it already overlaps, no connector needed
        if left_item.overlaps(pin):
            return None
        
        # Otherwise, make a connector to the item
        p = self.compute_connector(pin, left_item)
        return p
    
    def find_right_connector(self, pin, enclosures):
        """ 
        Find the enclosure that is to the right of the pin
        and make a connector to it's left edge.
        """
        # Create the list of shapes that contain the pin edge
        edge_list = []
        for shape in enclosures:
            if shape.ycontains(pin):
                edge_list.append(shape)
        
        # Sort them by their right edge
        edge_list.sort(key=lambda x: x.lx(), reverse=True)

        # Find the left edge that is next to the pin's right edge
        right_item = None
        for item in edge_list:
            if item.lx()>=pin.rx():
                right_item = item
            else:
                break

        # There was nothing to the right
        if right_item==None:
            return None
        # If it already overlaps, no connector needed
        if right_item.overlaps(pin):
            return None
        
        # Otherwise, make a connector to the item
        p = self.compute_connector(pin, right_item)
        return p
    
    def find_smallest_connector(self, pin_list, shape_list):
        """
        Compute all of the connectors between the overlapping pins and enclosure shape list..
        Return the smallest.
        """
        smallest = None
        for pin in pin_list:
            for enclosure in shape_list:
                new_enclosure = self.compute_connector(pin, enclosure)
                if smallest == None or new_enclosure.area()<smallest.area():
                    smallest = new_enclosure
                    
        return smallest

    def find_smallest_overlapping(self, pin_list, shape_list):
        """
        Find the smallest area shape in shape_list that overlaps with any 
        pin in pin_list by a min width.
        """

        smallest_shape = None
        for pin in pin_list:
            overlap_shape = self.find_smallest_overlapping_pin(pin,shape_list)
            if overlap_shape:
                overlap_length = pin.overlap_length(overlap_shape)
                if smallest_shape == None or overlap_shape.area()<smallest_shape.area():
                    smallest_shape = overlap_shape
                        
        return smallest_shape


    def find_smallest_overlapping_pin(self, pin, shape_list):
        """
        Find the smallest area shape in shape_list that overlaps with any 
        pin in pin_list by a min width.
        """

        smallest_shape = None
        zindex=self.router.get_zindex(pin.layer_num)
        (min_width,min_space) = self.router.get_layer_width_space(zindex)

        # Now compare it with every other shape to check how much they overlap
        for other in shape_list:
            overlap_length = pin.overlap_length(other)
            if overlap_length > min_width:
                if smallest_shape == None or other.area()<smallest_shape.area():
                    smallest_shape = other
                        
        return smallest_shape
    
    def overlap_any_shape(self, pin_list, shape_list):
        """
        Does the given pin overlap any of the shapes in the pin list.
        """
        for pin in pin_list:
            for other in shape_list:
                if pin.overlaps(other):
                    return True

        return False

    
    def max_pin_layout(self, pin_list):
        """ 
        Return the max area pin_layout
        """
        biggest = pin_list[0]
        for pin in pin_list:
            if pin.area() > biggest.area():
                biggest = pin
                
        return pin

    def enclose_pin_grids(self, ll, dir1=direction.NORTH, dir2=direction.EAST):
        """
        This encloses a single pin component with a rectangle
        starting with the seed and expanding right until blocked
        and then up until blocked.
        dir1 and dir2 should be two orthogonal directions.
        """

        offset1= direction.get_offset(dir1)
        offset2= direction.get_offset(dir2)

        # We may have started with an empty set
        if not self.grids:
            return None

        # Start with the ll and make the widest row
        row = [ll]
        # Move in dir1 while we can
        while True:
            next_cell = row[-1] + offset1
            # Can't move if not in the pin shape 
            if next_cell in self.grids and next_cell not in self.router.blocked_grids:
                row.append(next_cell)
            else:
                break
        # Move in dir2 while we can
        while True:
            next_row = [x+offset2 for x in row]
            for cell in next_row:
                # Can't move if any cell is not in the pin shape 
                if cell not in self.grids or cell in self.router.blocked_grids:
                    break
            else:
                row = next_row
                # Skips the second break
                continue
            # Breaks from the nested break
            break

        # Add a shape from ll to ur
        ur = row[-1]
        return (ll,ur)

    
    def enclose_pin(self):
        """
        If there is one set of connected pin shapes, 
        this will find the smallest rectangle enclosure that overlaps with any pin.
        If there is not, it simply returns all the enclosures.
        """
        self.enclosed = True
        
        # Compute the enclosure pin_layout list of the set of tracks
        self.enclosures = self.compute_enclosures()

        for pin_list in self.pins:
            for pin in pin_list:
                
                # If it is contained, it won't need a connector
                if pin.contained_by_any(self.enclosures):
                    continue

                # Find a connector in the cardinal directions
                # If there is overlap, but it isn't contained, these could all be None
                # These could also be none if the pin is diagonal from the enclosure
                left_connector = self.find_left_connector(pin, self.enclosures)
                right_connector = self.find_right_connector(pin, self.enclosures)
                above_connector = self.find_above_connector(pin, self.enclosures)
                below_connector = self.find_below_connector(pin, self.enclosures)
                connector_list = [left_connector, right_connector, above_connector, below_connector]
                filtered_list = list(filter(lambda x: x!=None, connector_list))
                if (len(filtered_list)>0):
                    import copy
                    bbox_connector =  copy.copy(pin)
                    bbox_connector.bbox(filtered_list)
                    self.enclosures.append(bbox_connector)

        # Now, make sure each pin touches an enclosure. If not, add another (diagonal) connector.
        # This could only happen when there was no enclosure in any cardinal direction from a pin
        for pin_list in self.pins:
            if not self.overlap_any_shape(pin_list, self.enclosures):
                connector = self.find_smallest_connector(pin_list, self.enclosures)
                if connector==None:
                    debug.error("Could not find a connector for {} with {}".format(pin_list, self.enclosures))
                    self.router.write_debug_gds("no_connector.gds")
                self.enclosures.append(connector)

                        
        debug.info(3,"Computed enclosure(s) {0}\n  {1}\n  {2}\n  {3}".format(self.name,
                                                                             self.pins,
                                                                             self.grids,
                                                                             self.enclosures))

    def combine_groups(self, pg1, pg2):
        """
        Combine two pin groups into one.
        """
        self.pins = [*pg1.pins, *pg2.pins] # Join the two lists of pins
        self.grids = pg1.grids | pg2.grids # OR the set of grid locations
        self.secondary_grids = pg1.secondary_grids | pg2.secondary_grids

    def add_group(self, pg):
        """
        Combine the pin group into this one. This will add to the first item in the pins
        so this should be used before there are disconnected pins.
        """
        debug.check(len(self.pins)==1,"Don't know which group to add pins to.")
        self.pins[0].update(*pg.pins) # Join the two lists of pins
        self.grids |= pg.grids # OR the set of grid locations
        self.secondary_grids |= pg.secondary_grids
        
    def add_enclosure(self, cell):
        """
        Add the enclosure shape to the given cell.
        """
        for enclosure in self.enclosures:
            debug.info(2,"Adding enclosure {0} {1}".format(self.name, enclosure))  
            cell.add_rect(layer=enclosure.layer,
                          offset=enclosure.ll(),
                          width=enclosure.width(),
                          height=enclosure.height())
        

    def perimeter_grids(self):
        """
        Return a list of the grids on the perimeter.
        This assumes that we have a single contiguous shape.
        """
        perimeter_set = set()
        cardinal_offsets = direction.cardinal_offsets()
        for g1 in self.grids:
            neighbor_grids = [g1 + offset for offset in cardinal_offsets]
            neighbor_count = sum([x in self.grids for x in neighbor_grids])
            # If we aren't completely enclosed, we are on the perimeter
            if neighbor_count < 4:
                perimeter_set.add(g1)
                
        return perimeter_set
    
    def adjacent(self, other):
        """ 
        Chck if the two pin groups have at least one adjacent pin grid.
        """
        # We could optimize this to just check the boundaries
        for g1 in self.perimeter_grids():
            for g2 in other.perimeter_grids():
                if g1.adjacent(g2):
                    return True

        return False


    def adjacent_grids(self, other, separation):
        """ 
        Determine the sets of grids that are within a separation distance
        of any grid in the other set.
        """
        # We could optimize this to just check the boundaries
        adj_grids = set()
        for g1 in self.grids:
            for g2 in other.grids:
                if g1.distance(g2) <= separation:
                    adj_grids.add(g1)

        return adj_grids
    
    def convert_pin(self):
        """
        Convert the list of pin shapes into sets of routing grids.
        The secondary set of grids are "optional" pin shapes that could be
        should be either blocked or part of the pin.
        """
        pin_set = set()
        partial_set = set()
        blockage_set = set()

        for pin_list in self.pins:
            for pin in pin_list:
                debug.info(2,"  Converting {0}".format(pin))
                # Determine which tracks the pin overlaps 
                (sufficient,insufficient)=self.router.convert_pin_to_tracks(self.name, pin)
                pin_set.update(sufficient)
                partial_set.update(insufficient)
                
                # Blockages will be a super-set of pins since it uses the inflated pin shape.
                blockage_in_tracks = self.router.convert_blockage(pin) 
                blockage_set.update(blockage_in_tracks)

        # If we have a blockage, we must remove the grids
        # Remember, this excludes the pin blockages already
        shared_set = pin_set & self.router.blocked_grids
        if len(shared_set)>0:
            debug.info(2,"Removing pins {}".format(shared_set))
        pin_set.difference_update(shared_set)
        shared_set = partial_set & self.router.blocked_grids
        if len(shared_set)>0:
            debug.info(2,"Removing pins {}".format(shared_set))
        partial_set.difference_update(shared_set)
        shared_set = blockage_set & self.router.blocked_grids
        if len(shared_set)>0:
            debug.info(2,"Removing blocks {}".format(shared_set))
        blockage_set.difference_update(shared_set)
        
        # At least one of the groups must have some valid tracks
        if (len(pin_set)==0 and len(partial_set)==0 and len(blockage_set)==0):
            #debug.warning("Pin is very close to metal blockage.\nAttempting to expand blocked pin {}".format(self.pins))
            
            for pin_list in self.pins:
                for pin in pin_list:
                    debug.warning("  Expanding conversion {0}".format(pin))
                    # Determine which tracks the pin overlaps 
                    (sufficient,insufficient)=self.router.convert_pin_to_tracks(self.name, pin, expansion=1)
                    pin_set.update(sufficient)
                    partial_set.update(insufficient)
                    
            if len(pin_set)==0 and len(partial_set)==0:
                debug.error("Unable to find unblocked pin {} {}".format(self.name, self.pins))
                self.router.write_debug_gds("blocked_pin.gds")

        # Consider all the grids that would be blocked
        self.grids = pin_set  | partial_set
        # Remember the secondary grids for removing adjacent pins 
        self.secondary_grids = partial_set 

        debug.info(2,"     pins   {}".format(self.grids))
        debug.info(2,"     secondary {}".format(self.secondary_grids))
        
    # def recurse_simple_overlap_enclosure(self, start_set, direct):
    #     """
    #     Recursive function to return set of tracks that connects to
    #     the actual supply rail wire in a given direction (or terminating
    #     when any track is no longer in the supply rail.
    #     """
    #     next_set = grid_utils.expand_border(start_set, direct)

    #     supply_tracks = self.router.supply_rail_tracks[self.name]
    #     supply_wire_tracks = self.router.supply_rail_wire_tracks[self.name]
        
    #     supply_overlap = next_set & supply_tracks
    #     wire_overlap = next_set & supply_wire_tracks

    #     # If the rail overlap is the same, we are done, since we connected to the actual wire
    #     if len(wire_overlap)==len(start_set):
    #         new_set = start_set | wire_overlap
    #     # If the supply overlap is the same, keep expanding unti we hit the wire or move out of the rail region
    #     elif len(supply_overlap)==len(start_set):
    #         recurse_set = self.recurse_simple_overlap_enclosure(supply_overlap, direct)
    #         new_set = start_set | supply_overlap | recurse_set
    #     else:
    #         # If we got no next set, we are done, can't expand!
    #         new_set = set()
            
    #     return new_set
            
    # def create_simple_overlap_enclosure(self, start_set):
    #     """
    #     This takes a set of tracks that overlap a supply rail and creates an enclosure
    #     that is ensured to overlap the supply rail wire.
    #     It then adds rectangle(s) for the enclosure.
    #     """
    #     additional_set = set()
    #     # Check the layer of any element in the pin to determine which direction to route it
    #     e = next(iter(start_set))
    #     new_set = start_set.copy()
    #     if e.z==0:
    #         new_set = self.recurse_simple_overlap_enclosure(start_set, direction.NORTH)
    #         if not new_set:
    #             new_set = self.recurse_simple_overlap_enclosure(start_set, direction.SOUTH)
    #     else:
    #         new_set = self.recurse_simple_overlap_enclosure(start_set, direction.EAST)
    #         if not new_set:
    #             new_set = self.recurse_simple_overlap_enclosure(start_set, direction.WEST)

    #     # Expand the pin grid set to include some extra grids that connect the supply rail
    #     self.grids.update(new_set)

    #     # Block the grids
    #     self.blockages.update(new_set)

    #     # Add the polygon enclosures and set this pin group as routed
    #     self.set_routed()
    #     self.enclosures = self.compute_enclosures()


        

