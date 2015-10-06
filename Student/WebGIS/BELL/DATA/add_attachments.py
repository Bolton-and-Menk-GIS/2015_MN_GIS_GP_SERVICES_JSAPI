import arcpy
import os
import glob
import sys

path = os.path.dirname(os.path.abspath(sys.argv[0]))

def addAttachments(fc, folder, ftype=['*.pdf']):
    """add dummy attachments to features, just goes based on order of features and
    files in a folder.  For demo purposes only!
    """

    # get list of photos
    photos = []
    for ext in ftype:
        photos += glob.glob(os.path.join(folder, ext))
        
    # photo id field
    att_ids = []
    PHOTO_ID = 'PHOTO_ID_X_Y_Z__'
    arcpy.management.AddField(fc, PHOTO_ID, 'TEXT')
    with arcpy.da.UpdateCursor(fc, PHOTO_ID) as rows:
        for i,row in enumerate(rows):
            att_id = 'P-{}'.format(i)
            rows.updateRow((att_id,))
            att_ids.append(att_id)

    att_dict = dict(zip(att_ids, photos))

    # create temp table
    arcpy.management.AddGlobalIDs(fc)
    arcpy.management.EnableAttachments(fc)
    tmp_tab = r'in_memory\temp_photo_points'
    arcpy.management.CreateTable('in_memory', 'temp_photo_points')
    for field in [PHOTO_ID, 'PATH', 'PHOTO_NAME']:
        arcpy.management.AddField(tmp_tab, field, 'TEXT', field_length=255)

    with arcpy.da.InsertCursor(tmp_tab, [PHOTO_ID, 'PATH', 'PHOTO_NAME']) as irows:
        for k, v in att_dict.iteritems():
            irows.insertRow((k,) + os.path.split(v))

     # add attachments
    arcpy.management.AddAttachments(fc, PHOTO_ID, tmp_tab, PHOTO_ID,
                                    'PHOTO_NAME', in_working_folder=folder)
    arcpy.management.Delete(tmp_tab)
    arcpy.management.DeleteField(fc, PHOTO_ID)
    print 'Added attachments for {}'.format(os.path.basename(fc))
    return

if __name__ == '__main__':

    # dict for attachment matching
    feats = {os.path.join(path, 'forSDE.gdb', 'BellePlaine', 'Fire_Hydrants'):
                 os.path.join(path, 'utilities', 'Hydrants'),
             os.path.join(path, 'forSDE.gdb', 'BellePlaine', 'Storm_Culverts'):
                 os.path.join(path, 'utilities', 'Culverts')}

    # add attachments
    for fc, folder in feats.iteritems():
        addAttachments(fc, folder)

    
    





