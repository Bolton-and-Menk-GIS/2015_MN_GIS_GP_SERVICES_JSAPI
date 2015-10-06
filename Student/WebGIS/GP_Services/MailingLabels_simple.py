#-------------------------------------------------------------------------------
# Name:        mailing labels
# Purpose:     MN GIS LIS Demo
#
# Author:      Caleb Mackey
#
# Created:     09/18/2015
#-------------------------------------------------------------------------------
import os
import arcpy
import time
import sys

# need to be hard code py library path, script gets coppied to arcgisserver folder
sys.path.append(r'C:\WebGIS\PythonLibraries') # change this to correct path

# import custom modules
import avery
import cleanup
import json

# path for output files
PATH = r'C:\inetpub\wwwroot\TempFiles' # change this to correct path
PATH_URL = 'http://lt0212x1g2676/TempFiles'
DATE = time.strftime('%Y%m%d%H%M%S')

def mailingLabels(feature_set, site, mail_type='taxpayer', out_url=''):
    """Create mailing labels

    Required:
        feature_set -- input feature set
        site -- name of site in "WebSchema" table...Must match exactly
        mail_type -- type of mailing label (taxpayer|owner|current)

    Derived:
        out_url -- dummy argument, output variable for GP Task.  Do nothing with this
    """
    if isinstance(feature_set, arcpy.mapping.Layer):
        feature_set = json.loads(arcpy.FeatureSet(feature_set).JSON)

    if isinstance(feature_set, (arcpy.RecordSet, arcpy.FeatureSet)):
        feature_set = json.loads(feature_set.JSON)

    #arcpy.AddMessage(feature_set.JSON)
    # clean up - remove files older than 1 hour
    cleanup.remove_files(PATH, 1/24.0)

    # read schema table
    web_schemas = r'C:\WebGIS\General\WebGIS.gdb\Web_Schemas' # change this to correct path
    fields = [u'Site', u'Parcel_REST_Endpoint', u'TaxPayer_Name', u'Parcel_Owner_Field',#0,1,2,3
              u'Taxpayer_Address_Field', u'Taxpayer_City_State_Zip',#4,5
              u'Property_Address', u'Property_City_State_Zip'] #6,7

    # type dictionary for mailing labels (tuples are field indices)
    TAX = (2,4,5)
    OWNER = (3,6,7)
    CURRENT = (6,7)
    type_d = {'taxpayer': TAX, 'owner': OWNER, 'current': CURRENT}

    # get fields for address info
    where = "Site = '{}'".format(site)
    searchFields = type_d[mail_type.lower()]
    with arcpy.da.SearchCursor(web_schemas, fields, where) as rows:
        for row in rows:
            fieldDefs = [row[i] for i in type_d[mail_type.lower()]]

    # create addresses
    allFields = [f['name'] for f in feature_set['fields']]
    mailFields = [f for f in allFields if f in fieldDefs]
    addresses = [[row['attributes'][f] for f in mailFields] for row in feature_set['features']]

    # add "CURRENT RESIDENT" to first item in each list
    if mail_type.lower() == 'current':
        [a.insert(0, 'CURRENT RESIDENT') for a in addresses]

    # now we can run mailing labels against this
    if not os.path.exists(PATH):
        os.makedirs(PATH)
    ags2 = os.path.join(PATH, 'MailingLabels_{}{}.pdf'.format(mail_type.title(), DATE))
    NAME = os.path.basename(ags2)

    # need to create in both places because of cluster
    avery.avery5160(ags2, addresses)
    OUT_URL = '/'.join([PATH_URL, NAME])
    arcpy.AddMessage(OUT_URL)
    arcpy.SetParameter(3, OUT_URL)
    return OUT_URL

if __name__ == '__main__':

    # run tool
    mailingLabels(*[arcpy.GetParameter(i) for i in range(arcpy.GetArgumentCount())])
