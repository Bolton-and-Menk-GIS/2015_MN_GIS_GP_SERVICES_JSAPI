import textwrap
import os
import arcpy
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

def avery5160(outfile, addressInput, font='Helvetica', font_size=10, filter_dups=True):
    '''
    Uses reportlab to generate mailing labels in avery5160 format.
    Output is a pdf.  This was modified from esri's public notification
    script sample.

    outfile -- output pdf file
    addressInput -- list of address labels (nested list)
                    [[Name, Address, City_St_Zip]...]
    font -- font style for output pdf. Default is "Helvetica"
    font_size -- font size for output labels. default is 10.
    filter_dups -- remove duplicates.  Default is true
    '''
 
    # PDF vars
    if os.path.exists(outfile):
        os.remove(outfile)
    out_pdf = canvas.Canvas(outfile, pagesize = letter)
    out_pdf.setFont(font, font_size)
    hs = 0.25
    vs = 10.3
    horizontal_start = hs * inch
    vertical_start = vs * inch
    count = 0

    # loop thru addresses and remove duplicates if chosen
    if filter_dups:
        count_add = len(addressInput)
        unique = list(set('~'.join(map(str, filter(None, it))) for it in addressInput))
        addresses = [s.split('~') for s in unique if s.count('~') in (2,3)]
        arcpy.AddMessage('Removed {} duplicates'.format(count_add - len(addresses)))
    else:
        addresses = addressInput

    # write pdf
    for item in sorted(addresses):
        if len(filter(None, [str(i).strip() for i in item])) in (3,4):

            if count > 0 and count % 30 == 0 and len(item) > 0:
                out_pdf.showPage()
                out_pdf.setFont(font, font_size)
                horizontal_start = hs * inch
                vertical_start = vs * inch

            # new column
            elif count > 0 and count % 10 == 0 and len(item) > 0:
                horizontal_start += 2.8 *inch
                vertical_start = vs * inch

            label = out_pdf.beginText()
            label.setTextOrigin(horizontal_start, vertical_start)

            # textwrap for labels (no more than 30 chars, max of two lines)
            for detail in item:
                for line in textwrap.wrap(str(detail)[:59], 30):
                    label.textLine(line)

            out_pdf.drawText(label)
            vertical_start -= 1.05 * inch
            count += 1

    # save pdf
    out_pdf.showPage()
    out_pdf.save()
    arcpy.AddMessage('\nCreated %s\n' %outfile)
    return out_pdf
