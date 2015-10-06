#-------------------------------------------------------------------------------
# Name:        download photos
# Purpose:     MN GIS LIS Demos
#
# Author:      Caleb Mackey
#
# Created:     09/29/2015
# Copyright:   (c) calebma-admin 2015
#-------------------------------------------------------------------------------
import sys
sys.path.append(r'C:\WebGIS\PythonLibraries')
import restapi
import arcpy
import os
import cleanup
import zipfile
import json
import time

PATH = r'C:\inetpub\wwwroot\TempFiles'
DATE = time.strftime('%Y%m%d%H%M%S')
PATH_URL = 'http://lt0212x1g2676/TempFiles'

# clean up temp files folder
cleanup.remove_files(PATH, 1/96.0)
cleanup.remove_folders(PATH, 1/96.0, del_gdb=True)

def zipdir(path, out_zip=''):
    """zips a folder and all subfolders

    Required:
        path -- folder to zip

    Optional:
        out_zip -- output zip folder. Default is path + '.zip'
    """
    rootDIR = os.path.basename(path)
    if not out_zip:
        out_zip = path + '.zip'
    else:
        if not out_zip.strip().endswith('.zip'):
            out_zip = os.path.splitext(out_zip)[0] + '.zip'
    zipFile = zipfile.ZipFile(path + '.zip', 'w', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(path):
        for fl in files:
            if not fl.endswith('.lock'):
                subfolder = os.path.basename(root)
                if subfolder == rootDIR:
                    subfolder = ''
                zipFile.write(os.path.join(root, fl), os.path.join(subfolder, fl))
    return out_zip

def exportFeatures(boundary, endpoint, folder_name, include_features=True):
    """exports features from a map

    boundary -- input area of interest
    endpoint -- REST endpoint of layer to export
    atachments_only -- option to download feature attachments only
    """

    # get boundary feature set
    if isinstance(boundary, (arcpy.FeatureSet, arcpy.RecordSet)):
        geom = restapi.Geometry(json.loads(boundary.JSON))

    # make folder
    out_path = os.path.join(PATH, folder_name)
    if os.path.exists(out_path):
        # avoid name conflict
        os.makedirs(out_path + '_{}'.format(DATE))
    else:
        os.makedirs(out_path)

    # export layer
    if include_features in ('true', True):
        restapi.exportFeaturesWithAttachments(out_path, endpoint, geometry=geom.dumps(), geometryType='esriGeometryPolygon')
    else:
        lyr = restapi.MapServiceLayer(endpoint)
        oids = lyr.getOIDs(geometry=geom.dumps(), geometryType='esriGeometryPolygon')

        # download all attachments
        for oid in oids:

            # get attachments for each feature
            for attInfo in lyr.attachments(oid):
                attInfo.download(out_path)

    # zip output folder
    zipped = zipdir(out_path)
    arcpy.management.Delete(out_path)
    out_url = '{}/{}'.format(PATH_URL, os.path.basename(zipped))
    arcpy.AddMessage(out_url)
    arcpy.SetParameter(4, out_url)
    return out_url

if __name__ == '__main__':

    # run tool
    exportFeatures(*[arcpy.GetParameter(i) for i in range(arcpy.GetArgumentCount())][:-1])
