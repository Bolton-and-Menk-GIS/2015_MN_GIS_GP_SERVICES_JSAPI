#-------------------------------------------------------------------------------
# Name:        exportToExcel
# Purpose:     MN GIS LIS Demos
#
# Author:      Caleb Mackey
#
# Created:     9/30/2015
#-------------------------------------------------------------------------------
import arcpy
import sys
import os
sys.path.append(r'C:\WebGIS\PythonLibraries')
import arial10
import cleanup
import datetime
from xlwt import Workbook, Borders, Font, XFStyle

# env
arcpy.env.qualifiedFieldNames = False
arcpy.env.overwriteOutput = True

# Out Path
PATH = r'C:\inetpub\wwwroot\TempFiles'
PATH_URL = 'http://lt0212x1g2676/TempFiles'
cleanup.remove_files(PATH, 1/96.0)
cleanup.remove_folders(PATH, 1/96.0)

def CreateExcelSpreadsheet(table, output_excel, use_alias=True):
    """Exports table to excel

    Required:
        table -- input table
        output_excel -- output excel table (.xlsx, .xls)

    Optional:
        use_alias -- use field alias name for column headers. Default is True
    """
    # build field dict
    fieldNames = [(f.name, f.aliasName) for f in arcpy.ListFields(table) if f.type != 'Geometry']
    fields = [f[1] if use_alias in ('true', True) else f[0] for f in fieldNames]
    widths = {i: arial10.fitwidth(f) + 1024 for i,f in enumerate(fields)}

    # get field values  *Changed from type dict to list
    with arcpy.da.SearchCursor(table, [f[0] for f in fieldNames]) as rows:
        values = [r for r in rows]

    # Create spreadsheet
    wb = Workbook()
    ws = wb.add_sheet('Sheet 1')
    cols = len(fields)
    rows = len(values) + 1

    # set styles
    #***************************************************************************
    borders = Borders()
    borders.left = Borders.THIN
    borders.right = Borders.THIN
    borders.top = Borders.THIN
    borders.bottom = Borders.THIN

    style = XFStyle()
    style.borders = borders

    # headers
    fntHeaders = Font()
    fntHeaders.bold = True
    fntHeaders.height = 220

    styleHeaders = XFStyle()
    styleHeaders.font = fntHeaders
    styleHeaders.borders = borders

    # for date fields
    styleDate = XFStyle()
    styleDate.borders = borders
    styleDate.num_format_str = 'MM/DD/YYYY'
    #***************************************************************************

    # write headers and freeze panes
    for ci,field in enumerate(fields):
        ws.write(0, ci, field, styleHeaders)

    # freeze headers
    ws.set_panes_frozen(True)
    ws.set_horz_split_pos(1)

    # fill in values
    start = 1
    for vals in values:
        for i, value in enumerate(vals):
            ws.write(start, i, value, styleDate if isinstance(value, datetime.datetime) else style)
            v_width = arial10.fitwidth(str(value).strip())
            if v_width > widths[i]:
                widths[i] = v_width
        start += 1

        if not start % 1000:
            ws.flush_row_data()

    # autofit column widths
    for ci,width in widths.iteritems():
        ws.col(ci).width = int(width + 256) # just a little more padding

    # save workbook
    wb.save(output_excel)
    del wb
    out_url = '/'.join([PATH_URL, os.path.basename(out_file)])
    arcpy.SetParameter(2, out_url)
    arcpy.AddMessage(out_url)
    return out_url

if __name__ == '__main__':

    # get paramters
    table = arcpy.GetParameter(0)

    tableName = arcpy.ValidateTableName(arcpy.GetParameter(1), PATH)
    out_file = os.path.join(PATH, tableName + '.xls')
    if os.path.exists(out_file):
        out_file = os.path.splitext(out_file)[0] + '_{}.xls'.format(''.join(map(str, datetime.datetime.now().utctimetuple())))

    alias = arcpy.GetParameter(1)

    # run tool
    CreateExcelSpreadsheet(table, out_file, alias)
