#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      calebma
#
# Created:     24/03/2015
# Copyright:   (c) calebma 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import arcpy
import sys
import time
sys.path.append(r'\\arcserver1\some_foldr\Python\PyLibrary') # shared python library
import cleanup # custom, included
import os
# custom library can be downloaded here:
#   https://github.com/Bolton-and-Menk-GIS/restapi
import restapi 
arcpy.env.overwriteOutput = True

# Globals
PATH_URL = r'http://your_domain.com/TempFiles'
PATH2 = r'\\arcserver2\wwwroot\TempFiles'
PATH3 = r'\\arcserver3\wwwroot\TempFiles'
DATE = time.strftime('%Y%m%d%H%M%S')

def RowHandler(string, fields):
    """will handle records as field or text string for cursor

    Required:
        string -- string that defines string, field(s) or cancatenation
        fields -- list of fields used for index in result RowHandler callback
    """
    vals = map(lambda x: x.strip().replace('"',''), string.split('+'))
    callback = []
    for v in vals:
    	if v in fields:
    		callback.append({'field': fields.index(v)})
    	else:
    		callback.append({'string': v})
    return callback

def createStr(Handler, Row, fields, allFields):
    """handle row from RowHander output to format address string

    Required:
        Handler -- RowHander object (JSON)
        Row -- row tuple in cursor that contains values to be substituted for field
            tokens or concatenation of strings and/or field(s)
        fields -- field list for cursor object
        allFields -- entire field list for feature layer
    example:
            city         hard coded string       zip
        [{'field': 4}, {'string': u', MN '}, {'field': 5}]
        ->  PAYNESVILE, MN 56362

    """
    fullStr = ''
    for dct in Handler:
        if 'field' in dct:
            fullStr += str(Row[fields.index(allFields[dct['field']])])
        else:
            fullStr += str(dct['string'])
    return fullStr

def mailingLabels(feature_set, site, mail_type='taxpayer', out_url=''):
    """Create mailing labels

    Required:
        feature_set -- input feature set
        site -- name of site in "WebSchema" table...Must match exactly
        mail_type -- type of mailing label (taxpayer|owner|current)

    Derived:
        out_url -- dummy argument, output variable for GP Task.  Do nothing with this
    """

    # clean up - remove files getnerated the day before
    cleanup.remove_files(PATH2, 1/24.0)
    cleanup.remove_files(PATH3, 1/24.0)

    # read table
    web_schemas = r'\\arcserver2\WebGIS\_Templates\GP_Tasks.gdb\Web_Schemas'
    fields = [u'Site', u'Parcel_REST_Endpoint', u'TaxPayer_Name', u'Parcel_Owner_Field',#0,1,2,3
              u'Taxpayer_Address_Field', u'Taxpayer_City_State_Zip',#4,5
              u'Property_Address', u'Property_City_State_Zip'] #6,7

    # type dictionary for mailing labels
    TAX = [fields[i] for i in (2,4,5)]
    OWNER = [fields[i] for i in (3,6,7)]
    CURRENT = [fields[i] for i in (6,7)]
    type_d = {'taxpayer': TAX, 'owner': OWNER, 'current': CURRENT}

    # get fields for address info
    where = "Site = '{}'".format(site)
    searchFields = type_d[mail_type.lower()]
    with arcpy.da.SearchCursor(web_schemas, fields, where) as rows:
        for row in rows:
            fieldDefs = list(zip(fields, row))

    # make sure we have the full parcels REST endpoint
    # let option for map service endpoint because layer id CAN change
    rest = fieldDefs[1][1]
    if not rest[-1].isdigit():
        usr, pw = ('domain\\username', 'password') # only required if secured service
        mp = restapi.MapService(rest, usr, pw)
        pars = mp.layer('parcels') # name of parcels layer
    else:
        pars = restapi.MapServiceLayer(rest, usr, pw)

    # build list
    allFields = pars.list_fields()
    temp = arcpy.CreateUniqueName ('temp_xxx', 'in_memory')
    arcpy.management.CopyFeatures(feature_set, temp)
    desc = arcpy.Describe(temp)

    # get cursor
    sr = desc.spatialReference.factoryCode
    geometry = restapi.Geometry(temp)
    shape = geometry.geometryType
    geojson = geometry.dumps()
    out_sr = sr
    d = {'geometryType' : shape,
         'geometry': geojson,
         'inSR' : sr, 'outSR': out_sr}

    # build field list
    CUR = mail_type.lower() == 'current'
    cur_fields, cursor_list = [], []
    for f, fld_or_value in fieldDefs:
        if f in searchFields:
            handler = RowHandler(fld_or_value, allFields)
            for dct in handler:
                if 'field' in dct:
                    cur_fields.append(allFields[dct['field']])
            cursor_list.append(handler)

    # cursor object (restapi.Cursor)
    cursor = pars.cursor(cur_fields, add_params=d)

    # create addresses
    addresses = []
    for row in cursor.rows():
        subset = []
        for it in cursor_list:
            subset.append(createStr(it, row, cur_fields, allFields))
        if CUR:
            subset.insert(0, 'CURRENT RESIDENT')
        addresses.append(subset)

    # now we can run mailing labels against this
    for p in (PATH2, PATH3):
        if not os.path.exists(p):
            os.makedirs(p)
    ags2 = os.path.join(PATH2, 'MailingLabels_{}{}.pdf'.format(mail_type, DATE))
    NAME = os.path.basename(ags2)
    ags3 = os.path.join(PATH3, NAME)

    # need to create in both places because of cluster
    for outfile in [ags2, ags3]:
        bmi.avery5160(outfile, addresses)
    arcpy.management.Delete(temp)
    OUT_URL = '/'.join([PATH_URL, NAME])
    bmi.Message(OUT_URL)
    arcpy.SetParameter(3, OUT_URL)
    return OUT_URL

if __name__ == '__main__':

    # run tool
    mailingLabels(*[arcpy.GetParameter(i) for i in range(arcpy.GetArgumentCount())])

