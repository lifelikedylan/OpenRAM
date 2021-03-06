#!/usr/bin/env python3
"""
This is a script to load data from the characterization and layout processes into
a web friendly html datasheet.
"""
# TODO:
# include power
# Diagram generation
# Improve css


from globals import OPTS
import os
import math
import csv
import datasheet
import table_gen


def process_name(corner):
    """
    Expands the names of the characterization corner types into something human friendly
    """
    if corner == "TT":
        return "Typical - Typical"
    if corner == "SS":
        return "Slow - Slow"
    if corner == "FF":
        return "Fast - Fast"
    else:
        return "custom"


def parse_characterizer_csv(f, pages):
    """
    Parses output data of the Liberty file generator in order to construct the timing and
    current table
    """
    with open(f) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:

            found = 0
            col = 0

            # defines layout of csv file
            NAME = row[col]
            col += 1

            NUM_WORDS = row[col]
            col += 1

            NUM_BANKS = row[col]
            col += 1

            NUM_RW_PORTS = row[col]
            col += 1

            NUM_W_PORTS = row[col]
            col += 1

            NUM_R_PORTS = row[col]
            col += 1

            TECH_NAME = row[col]
            col += 1

            TEMP = row[col]
            col += 1

            VOLT = row[col]
            col += 1

            PROC = row[col]
            col += 1

            MIN_PERIOD = row[col]
            col += 1

            OUT_DIR = row[col]
            col += 1

            LIB_NAME = row[col]
            col += 1

            WORD_SIZE = row[col]
            col += 1

            ORIGIN_ID = row[col]
            col += 1

            DATETIME = row[col]
            col += 1

            DRC = row[col]
            col += 1

            LVS = row[col]
            col += 1

            AREA = row[col]
            col += 1
            for sheet in pages:

                if sheet.name == NAME:

                    found = 1
                    # if the .lib information is for an existing datasheet compare timing data

                    for item in sheet.operating_table.rows:
                        # check if the new corner data is worse than the previous worse corner data

                        if item[0] == 'Operating Temperature':
                            if float(TEMP) > float(item[3]):
                                item[2] = item[3]
                                item[3] = TEMP
                            if float(TEMP) < float(item[1]):
                                item[2] = item[1]
                                item[1] = TEMP

                        if item[0] == 'Power supply (VDD) range':
                            if float(VOLT) > float(item[3]):
                                item[2] = item[3]
                                item[3] = VOLT
                            if float(VOLT) < float(item[1]):
                                item[2] = item[1]
                                item[1] = VOLT

                        if item[0] == 'Operating Frequncy (F)':
                            try:
                                if float(math.floor(1000/float(MIN_PERIOD)) < float(item[3])):
                                    item[3] = str(math.floor(
                                        1000/float(MIN_PERIOD)))
                            except Exception:
                                pass

                    while(True):
                        col_start = col
                        if(row[col].startswith('DIN')):
                            start = col
                            for item in sheet.timing_table.rows:
                                if item[0].startswith(row[col]):

                                    if item[0].endswith('setup rising'):
                                        if float(row[col+1]) < float(item[1]):
                                            item[1] = row[col+1]
                                        if float(row[col+2]) > float(item[2]):
                                            item[2] = row[col+2]

                                        col += 2

                                    elif item[0].endswith('setup falling'):
                                        if float(row[col+1]) < float(item[1]):
                                            item[1] = row[col+1]
                                        if float(row[col+2]) > float(item[2]):
                                            item[2] = row[col+2]

                                        col += 2

                                    elif item[0].endswith('hold rising'):
                                        if float(row[col+1]) < float(item[1]):
                                            item[1] = row[col+1]
                                        if float(row[col+2]) > float(item[2]):
                                            item[2] = row[col+2]

                                        col += 2

                                    elif item[0].endswith('hold falling'):
                                        if float(row[col+1]) < float(item[1]):
                                            item[1] = row[col+1]
                                        if float(row[col+2]) > float(item[2]):
                                            item[2] = row[col+2]

                                        col += 2

                            col += 1

                        elif(row[col].startswith('DOUT')):
                            start = col
                            for item in sheet.timing_table.rows:
                                if item[0].startswith(row[col]):

                                    if item[0].endswith('cell rise'):
                                        if float(row[col+1]) < float(item[1]):
                                            item[1] = row[col+1]
                                        if float(row[col+2]) > float(item[2]):
                                            item[2] = row[col+2]

                                        col += 2

                                    elif item[0].endswith('cell fall'):
                                        if float(row[col+1]) < float(item[1]):
                                            item[1] = row[col+1]
                                        if float(row[col+2]) > float(item[2]):
                                            item[2] = row[col+2]

                                        col += 2

                                    elif item[0].endswith('rise transition'):
                                        if float(row[col+1]) < float(item[1]):
                                            item[1] = row[col+1]
                                        if float(row[col+2]) > float(item[2]):
                                            item[2] = row[col+2]

                                        col += 2

                                    elif item[0].endswith('fall transition'):
                                        if float(row[col+1]) < float(item[1]):
                                            item[1] = row[col+1]
                                        if float(row[col+2]) > float(item[2]):
                                            item[2] = row[col+2]

                                        col += 2

                            col += 1

                        elif(row[col].startswith('CSb')):
                            start = col
                            for item in sheet.timing_table.rows:
                                if item[0].startswith(row[col]):

                                    if item[0].endswith('setup rising'):
                                        if float(row[col+1]) < float(item[1]):
                                            item[1] = row[col+1]
                                        if float(row[col+2]) > float(item[2]):
                                            item[2] = row[col+2]

                                        col += 2

                                    elif item[0].endswith('setup falling'):
                                        if float(row[col+1]) < float(item[1]):
                                            item[1] = row[col+1]
                                        if float(row[col+2]) > float(item[2]):
                                            item[2] = row[col+2]

                                        col += 2

                                    elif item[0].endswith('hold rising'):
                                        if float(row[col+1]) < float(item[1]):
                                            item[1] = row[col+1]
                                        if float(row[col+2]) > float(item[2]):
                                            item[2] = row[col+2]

                                        col += 2

                                    elif item[0].endswith('hold falling'):
                                        if float(row[col+1]) < float(item[1]):
                                            item[1] = row[col+1]
                                        if float(row[col+2]) > float(item[2]):
                                            item[2] = row[col+2]

                                        col += 2

                            col += 1

                        elif(row[col].startswith('WEb')):
                            start = col
                            for item in sheet.timing_table.rows:
                                if item[0].startswith(row[col]):

                                    if item[0].endswith('setup rising'):
                                        if float(row[col+1]) < float(item[1]):
                                            item[1] = row[col+1]
                                        if float(row[col+2]) > float(item[2]):
                                            item[2] = row[col+2]

                                        col += 2

                                    elif item[0].endswith('setup falling'):
                                        if float(row[col+1]) < float(item[1]):
                                            item[1] = row[col+1]
                                        if float(row[col+2]) > float(item[2]):
                                            item[2] = row[col+2]

                                        col += 2

                                    elif item[0].endswith('hold rising'):
                                        if float(row[col+1]) < float(item[1]):
                                            item[1] = row[col+1]
                                        if float(row[col+2]) > float(item[2]):
                                            item[2] = row[col+2]

                                        col += 2

                                    elif item[0].endswith('hold falling'):
                                        if float(row[col+1]) < float(item[1]):
                                            item[1] = row[col+1]
                                        if float(row[col+2]) > float(item[2]):
                                            item[2] = row[col+2]

                                        col += 2

                            col += 1

                        elif(row[col].startswith('ADDR')):
                            start = col
                            for item in sheet.timing_table.rows:
                                if item[0].startswith(row[col]):

                                    if item[0].endswith('setup rising'):
                                        if float(row[col+1]) < float(item[1]):
                                            item[1] = row[col+1]
                                        if float(row[col+2]) > float(item[2]):
                                            item[2] = row[col+2]

                                        col += 2

                                    elif item[0].endswith('setup falling'):
                                        if float(row[col+1]) < float(item[1]):
                                            item[1] = row[col+1]
                                        if float(row[col+2]) > float(item[2]):
                                            item[2] = row[col+2]

                                        col += 2

                                    elif item[0].endswith('hold rising'):
                                        if float(row[col+1]) < float(item[1]):
                                            item[1] = row[col+1]
                                        if float(row[col+2]) > float(item[2]):
                                            item[2] = row[col+2]

                                        col += 2

                                    elif item[0].endswith('hold falling'):
                                        if float(row[col+1]) < float(item[1]):
                                            item[1] = row[col+1]
                                        if float(row[col+2]) > float(item[2]):
                                            item[2] = row[col+2]

                                        col += 2

                            col += 1

                        else:
                            for element in row[col_start: col - 1]:
                                sheet.description.append(str(element))
                            break

                    new_sheet.corners_table.add_row([PROC, process_name(
                        PROC), VOLT, TEMP, LIB_NAME.replace(OUT_DIR, '').replace(NAME, '')])
                    new_sheet.dlv_table.add_row(
                        ['.lib', 'Synthesis models', '<a href="file://{0}">{1}</a>'.format(LIB_NAME, LIB_NAME.replace(OUT_DIR, ''))])

            if found == 0:

                # if this is the first corner for this sram, run first time configuration and set up tables
                new_sheet = datasheet.datasheet(NAME)
                pages.append(new_sheet)

                new_sheet.git_id = ORIGIN_ID
                new_sheet.time = DATETIME
                new_sheet.DRC = DRC
                new_sheet.LVS = LVS
                new_sheet.description = [NAME, NUM_WORDS, NUM_BANKS, NUM_RW_PORTS, NUM_W_PORTS,
                                         NUM_R_PORTS, TECH_NAME, MIN_PERIOD, WORD_SIZE, ORIGIN_ID, DATETIME]

                new_sheet.corners_table = table_gen.table_gen("corners")
                new_sheet.corners_table.add_row(
                    ['Corner Name', 'Process', 'Power Supply', 'Temperature', 'Library Name Suffix'])
                new_sheet.corners_table.add_row([PROC, process_name(
                    PROC), VOLT, TEMP, LIB_NAME.replace(OUT_DIR, '').replace(NAME, '')])
                new_sheet.operating_table = table_gen.table_gen(
                    "operating_table")
                new_sheet.operating_table.add_row(
                    ['Parameter', 'Min', 'Typ', 'Max', 'Units'])
                new_sheet.operating_table.add_row(
                    ['Power supply (VDD) range', VOLT, VOLT, VOLT, 'Volts'])
                new_sheet.operating_table.add_row(
                    ['Operating Temperature', TEMP, TEMP, TEMP, 'Celsius'])

                try:
                    new_sheet.operating_table.add_row(['Operating Frequency (F)', '', '', str(
                        math.floor(1000/float(MIN_PERIOD))), 'MHz'])
                except Exception:
                    # failed to provide non-zero MIN_PERIOD
                    new_sheet.operating_table.add_row(
                        ['Operating Frequency (F)', '', '', "not available in netlist only", 'MHz'])
                new_sheet.timing_table = table_gen.table_gen("timing")
                new_sheet.timing_table.add_row(
                    ['Parameter', 'Min', 'Max', 'Units'])
                while(True):
                    col_start = col
                    if(row[col].startswith('DIN')):
                        start = col

                        new_sheet.timing_table.add_row(
                            ['{0} setup rising'.format(row[start]), row[col+1], row[col+2], 'ns'])
                        col += 2

                        new_sheet.timing_table.add_row(
                            ['{0} setup falling'.format(row[start]), row[col+1], row[col+2], 'ns'])

                        col += 2

                        new_sheet.timing_table.add_row(
                            ['{0} hold rising'.format(row[start]), row[col+1], row[col+2], 'ns'])

                        col += 2

                        new_sheet.timing_table.add_row(
                            ['{0} hold falling'.format(row[start]), row[col+1], row[col+2], 'ns'])

                        col += 2

                        col += 1

                    elif(row[col].startswith('DOUT')):
                        start = col

                        new_sheet.timing_table.add_row(
                            ['{0} cell rise'.format(row[start]), row[col+1], row[col+2], 'ns'])
                        col += 2

                        new_sheet.timing_table.add_row(
                            ['{0} cell fall'.format(row[start]), row[col+1], row[col+2], 'ns'])

                        col += 2

                        new_sheet.timing_table.add_row(
                            ['{0} rise transition'.format(row[start]), row[col+1], row[col+2], 'ns'])

                        col += 2

                        new_sheet.timing_table.add_row(
                            ['{0} fall transition'.format(row[start]), row[col+1], row[col+2], 'ns'])

                        col += 2

                        col += 1

                    elif(row[col].startswith('CSb')):
                        start = col

                        new_sheet.timing_table.add_row(
                            ['{0} setup rising'.format(row[start]), row[col+1], row[col+2], 'ns'])
                        col += 2

                        new_sheet.timing_table.add_row(
                            ['{0} setup falling'.format(row[start]), row[col+1], row[col+2], 'ns'])

                        col += 2

                        new_sheet.timing_table.add_row(
                            ['{0} hold rising'.format(row[start]), row[col+1], row[col+2], 'ns'])

                        col += 2

                        new_sheet.timing_table.add_row(
                            ['{0} hold falling'.format(row[start]), row[col+1], row[col+2], 'ns'])

                        col += 2

                        col += 1

                    elif(row[col].startswith('WEb')):
                        start = col

                        new_sheet.timing_table.add_row(
                            ['{0} setup rising'.format(row[start]), row[col+1], row[col+2], 'ns'])
                        col += 2

                        new_sheet.timing_table.add_row(
                            ['{0} setup falling'.format(row[start]), row[col+1], row[col+2], 'ns'])

                        col += 2

                        new_sheet.timing_table.add_row(
                            ['{0} hold rising'.format(row[start]), row[col+1], row[col+2], 'ns'])

                        col += 2

                        new_sheet.timing_table.add_row(
                            ['{0} hold falling'.format(row[start]), row[col+1], row[col+2], 'ns'])

                        col += 2

                        col += 1

                    elif(row[col].startswith('ADDR')):
                        start = col

                        new_sheet.timing_table.add_row(
                            ['{0} setup rising'.format(row[start]), row[col+1], row[col+2], 'ns'])
                        col += 2

                        new_sheet.timing_table.add_row(
                            ['{0} setup falling'.format(row[start]), row[col+1], row[col+2], 'ns'])

                        col += 2

                        new_sheet.timing_table.add_row(
                            ['{0} hold rising'.format(row[start]), row[col+1], row[col+2], 'ns'])

                        col += 2

                        new_sheet.timing_table.add_row(
                            ['{0} hold falling'.format(row[start]), row[col+1], row[col+2], 'ns'])

                        col += 2

                        col += 1

                    else:
                        for element in row[col_start:col-1]:
                            sheet.description.append(str(element))
                        break

                new_sheet.dlv_table = table_gen.table_gen("dlv")
                new_sheet.dlv_table.add_row(['Type', 'Description', 'Link'])

                new_sheet.io_table = table_gen.table_gen("io")
                new_sheet.io_table.add_row(['Type', 'Value'])

                if not OPTS.netlist_only:
                    # physical layout files should not be generated in netlist only mode
                    new_sheet.dlv_table.add_row(
                        ['.gds', 'GDSII layout views', '<a href="{0}.{1}">{0}.{1}</a>'.format(OPTS.output_name, 'gds')])
                    new_sheet.dlv_table.add_row(
                        ['.lef', 'LEF files', '<a href="{0}.{1}">{0}.{1}</a>'.format(OPTS.output_name, 'lef')])

                new_sheet.dlv_table.add_row(
                    ['.log', 'OpenRAM compile log', '<a href="{0}.{1}">{0}.{1}</a>'.format(OPTS.output_name, 'log')])
                new_sheet.dlv_table.add_row(
                    ['.v', 'Verilog simulation models', '<a href="{0}.{1}">{0}.{1}</a>'.format(OPTS.output_name, 'v')])
                new_sheet.dlv_table.add_row(
                    ['.html', 'This datasheet', '<a href="{0}.{1}">{0}.{1}</a>'.format(OPTS.output_name, 'html')])
                new_sheet.dlv_table.add_row(
                    ['.lib', 'Synthesis models', '<a href="{1}">{1}</a>'.format(LIB_NAME, LIB_NAME.replace(OUT_DIR, ''))])
                new_sheet.dlv_table.add_row(
                    ['.py', 'OpenRAM configuration file', '<a href="{0}.{1}">{0}.{1}</a>'.format(OPTS.output_name, 'py')])
                new_sheet.dlv_table.add_row(
                    ['.sp', 'SPICE netlists', '<a href="{0}.{1}">{0}.{1}</a>'.format(OPTS.output_name, 'sp')])

                new_sheet.io_table.add_row(['WORD_SIZE', WORD_SIZE])
                new_sheet.io_table.add_row(['NUM_WORDS', NUM_WORDS])
                new_sheet.io_table.add_row(['NUM_BANKS', NUM_BANKS])
                new_sheet.io_table.add_row(['NUM_RW_PORTS', NUM_RW_PORTS])
                new_sheet.io_table.add_row(['NUM_R_PORTS', NUM_R_PORTS])
                new_sheet.io_table.add_row(['NUM_W_PORTS', NUM_W_PORTS])
                new_sheet.io_table.add_row(['Area', AREA])


class datasheet_gen():
    def datasheet_write(name):

        in_dir = OPTS.openram_temp

        if not (os.path.isdir(in_dir)):
            os.mkdir(in_dir)

        datasheets = []
        parse_characterizer_csv(in_dir + "/datasheet.info", datasheets)

        for sheets in datasheets:
            with open(name, 'w+') as f:
                sheets.generate_html()
                f.write(sheets.html)
