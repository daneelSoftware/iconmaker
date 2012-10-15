# -*- coding: utf-8 -*-

import subprocess
import os
import sys
import utils
import tempfile
import requests
import StringIO
from PIL import Image

from logger import logging

FORMAT_PNG = 'png'
FORMAT_GIF = 'gif'
FORMAT_ICO = 'ico'
FORMAT_ICNS = 'icns'


class Converter(object):
    """Convert a set of PNG/GIF icons to either ICO or ICNS format.
    """

    def _fetch_image(self, url):
        """Fetch the requested image and save it in a temporary file.

            :params input: 
                URL of the image to fetch.
            :returns: 
                Path to the saved_filename.
        """

        # get the image
        response = requests.get(url)

        # save the image
        im = Image.open(StringIO.StringIO(response.content))
        image_format = im.format.lower()
        if image_format not in self.supported_source_formats:
            raise Exception('The source file is not of a supported format. Supported formats are: %s' % 
                            join(', ',self.supported_source_formats)) 

        # generate temp filename for it
        saved_file = tempfile.NamedTemporaryFile(prefix='downloaded_', suffix='.' + image_format, dir='/tmp', delete=False)
        saved_filename = saved_file.name            
        
        im.save(saved_filename)

        return saved_filename


    def __init__(self):
        """Initializer.
        """

        self.supported_source_formats = [FORMAT_GIF, FORMAT_PNG]
        self.supported_target_formats = [FORMAT_ICO, FORMAT_ICNS]
        self.png2ico = '/usr/local/bin/png2ico'
        self.png2icns = '/usr/local/bin/png2icns'
        self.gif2png = '/opt/local/bin/convert'

        # check and/or find the correct file locations
        if not os.path.isfile(self.png2ico):
            self.png2ico = utils.which(os.path.basename(self.png2ico))
            if not self.png2ico:
                raise Exception("The binary png2ico was not found")

        if not os.path.isfile(self.png2icns):
            self.png2icns = utils.which(os.path.basename(self.png2icns))
            if not self.png2icns:
                raise Exception("The binary png2icns was not found")

        if not os.path.isfile(self.gif2png):
            self.gif2png = utils.which(os.path.basename(self.gif2png))
            if not self.gif2png:
                raise Exception("The binary gif2png was not found")

        self.convert_binaries = {FORMAT_ICO:self.png2ico, FORMAT_ICNS:self.png2icns}


    def convert(self,
                target_format, 
                image_list):
        """Convert a list of image files to an ico/icns file.

        :param target_format: 
            ICO or ICNS.
        :param image_list: 
            List of image files to convert (either local paths or URLs).

        :returns: 
            Local path to the generated ico or None if an error occured.
        """


        # check our input arguments
        try:
            target_format = target_format.lower()
            conversion_binary = self.convert_binaries[target_format]
        except:
            raise Exception("Invalid target format. Target format must be either ICO or ICNS.")

        try:
            assert len(image_list) > 0
        except:
            raise Exception("Input list cannot be empty.")


        # image_list can contain either a local path or an http url
        new_icon_list = []
        for image_location in image_list:
            if image_location.startswith("http:") or image_location.startswith("https:"):
                try:
                    image_location = self._fetch_image(image_location)
                except:
                    raise Exception("Problem fetching image.")

            # check the extension to see if we'll need to convert something else to PNG
            image_base, image_extension = os.path.splitext(image_location)
            image_extension = image_extension[1:]

            if image_extension == FORMAT_GIF:
                logging.debug('converting png to gif: %s' % image_location)
                image_location_png = "%s.%s" % (image_base, FORMAT_PNG)

                try:
                    retcode = subprocess.call([self.gif2png, image_location, image_location_png])
                    assert retcode == 0
                except:
                    raise Exception('GIF to PNG conversion failed. (%s)' % image_location)

                image_location = image_location_png

            new_icon_list.append(image_location)

        image_list = new_icon_list

        # output file in ICNS or ICO format
        output_file = tempfile.NamedTemporaryFile(prefix='output_', suffix='.%s' % target_format, dir='/tmp', delete=False)
        output_filename = output_file.name

        # builds args for the conversion command
        logging.debug('image list: %s' % image_list)
        args = image_list
        args.insert(0, output_filename)
        args.insert(0, conversion_binary)

        # execute conversion command
        try:
            retcode = subprocess.call(args)
            assert retcode == 0
        except:
            raise Exception("Icon conversion failed. (%s)" % output_filename)

        return output_filename