#!/usr/bin/env python
""" PIPE RGB - Version 1.1.0

    Code for StepRGB in pipeline: combines filters to colored image & adds a label

    This module defines the HAWC pipeline step parent object. Pipe steps are
    the modules responsible for all HAWC data reduction. They are called by
    the pipeline and work with pipedata objects. All pipe step objects are
    descendants from this one. Pipe steps are callable objects that return
    the reduced data product (as pipedata object).
    
    @author: berthoud
"""

import os # os library
import numpy # numpy library
import logging # logging object library
import pylab # pylab library for creating rgb image
import img_scale # image scaling for balancing the different filters
from PIL import Image # image library for saving rgb file as JPEG
'''import tifffile as tiff # tiff library for saving data as .tif file'''
from PIL import ImageFont # Libraries for adding a label to the color image
from PIL import Image
from PIL import ImageDraw
from drp.pipedata import PipeData # pipeline data object
from drp.stepmiparent import StepMIParent # pipe step parent object

class StepRGB(StepMIParent):
    """ HAWC Pipeline Step Parent Object
        The object is callable. It requires a valid configuration input
        (file or object) when it runs.
    """
    stepver = '0.1' # pipe step version

    def __init__(self):
        """ Constructor: Initialize data objects and variables
        """
	# call superclass constructor (calls setup)
        super(StepRGB,self).__init__()
	# list of data
        self.datalist = [] # used in run() for every new input data file
	# set configuration
        self.log.debug('Init: done')
    
    def setup(self):
        """ ### Names and Prameters need to be Set Here ###
            Sets the internal names for the function and for saved files.
            Defines the input parameters for the current pipe step.
            Setup() is called at the end of __init__
            The parameters are stored in a list containing the following
            information:
            - name: The name for the parameter. This name is used when
                    calling the pipe step from command line or python shell.
                    It is also used to identify the parameter in the pipeline
                    configuration file.
            - default: A default value for the parameter. If nothing, set
                       '' for strings, 0 for integers and 0.0 for floats
            - help: A short description of the parameter.
        """
        ### Set Names
        # Name of the pipeline reduction step
        self.name='makergb'
        # Shortcut for pipeline reduction step and identifier for
        # saved file names.
        self.procname = 'rgb'
        # Set Logger for this pipe step
        self.log = logging.getLogger('hawc.pipe.step.%s' % self.name)
        ### Set Parameter list
        # Clear Parameter list
        self.paramlist = []
        # Append parameters
        self.paramlist.append(['minpercent', 0.05, 
		'Specifies the percentile for the minimum scaling'])
	self.paramlist.append(['maxpercent', 0.999,
		'Specifies the percentile for the maximum scaling'])

    def run(self):
        """ Runs the combining algorithm. The self.datain is run
            through the code, the result is in self.dataout.
        """
	# Copy input to output header
	self.log.debug('Number of input files = %d' % len(self.datain))
	self.dataout.header = self.datain[0].header
	self.dataout.filename = self.datain[0].filename
	img = self.datain[0].image
	
	''' Finding Min/Max scaling values '''
	# Create a Data Cube with floats
	datacube = numpy.zeros((self.datain[0].image.shape[0], self.datain[0].image.shape[1], 3), dtype=float)
	# Enter the image data into the cube so an absolute max can be found
	datacube[:,:,0] = self.datain[0].image
	datacube[:,:,1] = self.datain[1].image
	datacube[:,:,2] = self.datain[2].image
	# Find how many data points are in the data cube
	datalength = self.datain[0].image.shape[0] * self.datain[0].image.shape[1] * 3
	# Create a 1-dimensional array with all the data, then sort it	
	datacube.shape=(datalength,)
	datacube.sort()
	# Now use arrays for each filter to find separate min values
	rarray = self.datain[0].image.copy()
	garray = self.datain[1].image.copy()
	barray = self.datain[2].image.copy()
	# Shape and sort the arrays
	arrlength = self.datain[0].image.shape[0] * self.datain[0].image.shape[1]
        print(rarray.shape,self.datain[0].image.shape,arrlength)
	rarray.shape=(arrlength,)
	rarray.sort()
	garray.shape=(arrlength,)
	garray.sort()
	barray.shape=(arrlength,)
	barray.sort()
	# Find the min/max percentile values in the data for scaling
	# Values are determined by user's raw input; either a custom value or
	# 'default', which is set by parameters in the pipe configuration file
	while True:
	    minvalue = raw_input("Choose a percentile value for the minimum scaling. You may enter your own or type \"Default\" to use the default value (50%). Custom values must be integers only (without a percent sign): ")
	    try:
		if minvalue == "Default" or minvalue == "default":
		    minpercent = arrlength * self.getarg('minpercent')
		    break
		elif int(minvalue):
		    minpercent = arrlength * float('0.%d' % int(minvalue))
		    break
	    except ValueError:
	        print "***ERROR: Input is invalid. Please try again.***"
	while True:
	    maxvalue = raw_input("Choose a percentile value for the maximum scaling. You may enter your own or type \"Default\" to use the default value (99.9%). Custom values must be integers only (without a percent sign): ")
	    try:
		if maxvalue == 'Default' or maxvalue == 'default':
		    maxpercent = datalength * self.getarg('maxpercent')
		    break
		elif int(maxvalue):
		    maxpercent = datalength * float('0.%d' % int(maxvalue))
		    break
	    except ValueError:
		print "***ERROR: Input is invalid. Please try again.***"
	# Find the final data values to use for scaling from the image data
	rminsv = rarray[minpercent]  #sv stands for "scalevalue"
	gminsv = garray[minpercent]
	bminsv = barray[minpercent]
	maxsv = datacube[maxpercent]
	self.log.info(' Scale min r/g/b: %f/%f/%f' % (rminsv,gminsv,bminsv))
	self.log.info(' Scale max: %f' % maxsv)
	# The same min/max values will be used to scale all filters
	''' Finished Finding scaling values	'''
	
	''' Combining Function '''
	# Make new cube with the proper data type for color images (uint8)
	# Use square root (sqrt) scaling for each filter
	# log or asinh scaling is also available
	imgcube = numpy.zeros((self.datain[0].image.shape[0], self.datain[0].image.shape[1], 3), dtype='uint8')
	imgcube[:,:,0] = 255 * img_scale.sqrt(self.datain[0].image, scale_min= rminsv, scale_max= maxsv)
	imgcube[:,:,1] = 255 * img_scale.sqrt(self.datain[1].image, scale_min= gminsv, scale_max= maxsv)
	imgcube[:,:,2] = 255 * img_scale.sqrt(self.datain[2].image, scale_min= bminsv, scale_max= maxsv)
        self.dataout.image = imgcube
	# Create variable containing all the scaled image data
	imgcolor = Image.fromarray(self.dataout.image, mode='RGB')
	# Save colored image as a .tif file (without the labels)
	imgcolortif = imgcube.copy()
	imgcolortif.astype('uint16')
	### tiff.imsave('%s.tif' % self.dataout.filenamebase, imgcolortif)
	''' End of combining function '''
	
	''' Add a Label to the Image '''
	draw = ImageDraw.Draw(imgcolor)
	# Use a variable to make the positions and size of text relative
	imgwidth = self.datain[0].image.shape[0]
	imgheight = self.datain[0].image.shape[1]
	# Open Sans Serif Font with a size relative to the picture size
	font = ImageFont.truetype('/usr/share/fonts/liberation/LiberationSans-Regular.ttf',imgheight/41)
	# Use the beginning of the FITS filename as the object name
	filename = os.path.split(self.dataout.filename)[-1]
	objectname = filename.split('_')[0]
	objectname = objectname[0].upper()+objectname[1:]
	objectname = 'Object:  %s' % objectname
	# Print labels at their respective position (kept relative to image size)
	# Left corner: object, observer, observatory
	# Right corner: Filters used for red, green, and blue colors
	# Read FITS keywords for the observer, observatory, and filters
	# Print them if they exist
	draw.text((imgwidth/100,imgheight/1.114), objectname, (255,255,255), font=font)
	if self.dataout.header.has_key('OBSERVER'):
	    observer = 'Observer:  %s' % self.dataout.getheadval('OBSERVER')
	    draw.text((imgwidth/100,imgheight/1.073), observer, (255,255,255), font=font)
	if self.dataout.header.has_key('OBSERVAT'):
	    observatory = 'Observatory:  %s' % self.dataout.getheadval('OBSERVAT')
	    draw.text((imgwidth/100,imgheight/1.035), observatory, (255,255,255), font=font)
	if self.datain[0].header.has_key('FILTER'):
	    red = 'R:  %s' % self.datain[0].getheadval('FILTER')
	    draw.text((imgwidth/1.15,imgheight/1.114),red, (255,255,255), font=font)
	if self.datain[1].header.has_key('FILTER'):
	    green = 'G:  %s' % self.datain[1].getheadval('FILTER')
	    draw.text((imgwidth/1.15,imgheight/1.073),green, (255,255,255), font=font)
	if self.datain[2].header.has_key('FILTER'):
	    blue = 'B:  %s' % self.datain[2].getheadval('FILTER')
	    draw.text((imgwidth/1.15,imgheight/1.035),blue, (255,255,255), font=font)
	# Save the completed image
	imgcolor.save('%s.jpg' % self.dataout.filenamebase)
	''' End of Label Code '''
        # Set complete flag
        self.dataout.setheadval('COMPLETE',1,
                                'Data Reduction Pipe: Complete Data Flag')
    
    def reset(self):
        """ Resets the step to the same condition as it was when it was
            created. Internal variables are reset, any stored data is
            erased.
        """
        self.log.debug('Reset: done')
        
    def test(self):
        """ Test Pipe Step Parent Object:
            Runs a set of basic tests on the object
        """
        # log message
        self.log.info('Testing pipe step rgb')

        # log message
        self.log.info('Testing pipe step rgb - Done')
    
if __name__ == '__main__':
    """ Main function to run the pipe step from command line on a file.
        Command:
          python stepparent.py input.fits -arg1 -arg2 . . .
        Standard arguments:
          --config=ConfigFilePathName.txt : name of the configuration file
          -t, --test : runs the functionality test i.e. pipestep.test()
          --loglevel=LEVEL : configures the logging output for a particular level
          -h, --help : Returns a list of 
    """
    StepRGB().execute()

""" === History ===
    2014-06-30 New file created by Neil Stilin from template file by Nicolas Chapman
    2014-07-09 Main code for creating RBG image added by Neil Stilin
    2014-07-29 Code has been improved by adding better scaling and image labels
    2014-08-06 Added 'if' functions to the label printing so that if keywords do not exist in the header(s), they are skipped rather than raising an error --NS
    2014-08-07 Edited code so that raw inputs are used to determine the scaling values. Another copy (steprgbauto.py) was made of the original that runs the pipeline without input (automatically uses default values).  --NS
"""