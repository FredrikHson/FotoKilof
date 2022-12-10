# -*- coding: utf-8 -*-

"""
Copyright (c) 2022 Tomasz Łuczak, TeaM-TL

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

Converters
- rotate - rotate picture
- mirror - mirroring picture
- border - add border to picture
- text - add text into picture
- bw - black and white or sepia
- resize - resize picture
- normalize - normalize levels

- convert_preview_crop_gravity - convert corrdinates from crop3
- convert_crop - crop picture
- convert_contrast - modify contrast
- convert_pip - picture in picture, for inserting logo
- gravity - translate eg. NS to Northsouth as Tk expect
- gravity_outside - translate gravitation for adding text outside
"""

import os
from wand.color import Color
from wand.drawing import Drawing
from wand.font import Font
from wand.image import Image
from wand.version import fonts as fontsList
from wand.version import MAGICK_VERSION, VERSION


# my modules
import common
import convert
import magick
import mswindows


def rotate(file_in, work_dir, extension, angle, color):
    """ rotate """
    file_out = magick.pre_magick(file_in, work_dir, extension)
    with Image(filename=file_in) as image:
        with image.clone() as clone:
            clone.rotate(angle, background=color)
            clone.save(filename=file_out)
    return file_out


def mirror(file_in, work_dir, extension, flip, flop):
    """ mirror: flip and flop """
    file_out = magick.pre_magick(file_in, work_dir, extension)
    with Image(filename=file_in) as image:
        with image.clone() as clone:
            if flip:
                clone.flip()
            if flop:
                clone.flop()
            clone.save(filename=file_out)
    return file_out


def border(file_in, work_dir, extension, color, x, y):
    """ mirror: flip and flop """
    file_out = magick.pre_magick(file_in, work_dir, extension)
    with Image(filename=file_in) as image:
        with image.clone() as clone:
            clone.border(color, common.empty(x), common.empty(y))
            clone.save(filename=file_out)
    return file_out


def text(file_in, work_dir, extension, 
            in_out, text_color, font, text_size, 
            gravity_onoff, gravity, 
            box, box_color,
            text_x, text_y, text):
    """ add text into picture """

    file_out = magick.pre_magick(file_in, work_dir, extension)
    with Image(filename=file_in) as image:
        with image.clone() as clone:
            if in_out == 0:
            # inside
                with Drawing() as draw:
                    draw.fill_color = text_color
                    draw.font = font
                    draw.font_size = common.empty(text_size)
                    if gravity_onoff == 0:
                        draw.gravity = 'forget'
                    else:
                        draw.gravity = convert.gravity(gravity)
                    if box:
                        draw.text_under_color = box_color
                    draw.text(common.empty(text_x), common.empty(text_y), text)
                    draw(clone)
            else:
                # it has to be fixed
                style = Font(font, common.empty(text_size), text_color)
                clone.font = style
                if box:
                    clone.label(text, gravity=convert.gravity(gravity), background_color=box_color)
                else:
                    clone.label(text, gravity=convert.gravity(gravity))
            clone.save(filename=file_out)
    return file_out


def bw(file_in, work_dir, extension, bw, sepia):
    """ black and white or sepia """
    file_out = magick.pre_magick(file_in, work_dir, extension)
    with Image(filename=file_in) as image:
        with image.clone() as clone:
            if bw == 1:
                # black-white
                clone.type = 'grayscale';
            else:
                # sepia
                clone.sepia_tone(threshold=common.empty(sepia)/100)
            clone.save(filename=file_out)
    return file_out


def resize(file_in, work_dir, extension, resize, pixel, percent, border):
    """ resize picture """

    border = 2 * abs(int(border))
    if resize == 1:
        command = pixel + "x" + pixel
        sub_dir = pixel
    elif resize == 2:
        if percent > 100:
            percent = 100
        if percent == 0:
            percent = 1
        command = str(percent) + "%"
        sub_dir = str(percent)
    elif resize == 3:
        command = str(1920 - border) + "x" + str(1080 - border)
        sub_dir = "1920x1080"
    elif resize == 4:
        command = str(2048 - border) + "x" + str(1556 - border)
        sub_dir = "2048x1556"
    elif resize == 5:
        command = str(4096 - border) + "x" + str(3112 - border)
        sub_dir = "4096x3112"

    file_out = magick.pre_magick(file_in, os.path.join(work_dir, sub_dir), extension)
    with Image(filename=file_in) as image:
        with image.clone() as clone:
            clone.transform(crop='', resize=command)
            clone.save(filename=file_out)

    return file_out

def normalize(file_in, work_dir, extension, normalize, channel)
    """ normalize levels of colors """

    file_out = magick.pre_magick(file_in, os.path.join(work_dir, sub_dir), extension)
    with Image(filename=file_in) as image:
        with image.clone() as clone:
            if normalize == 1:
                if channel != "None":
                    command = "-channel " + channel + " -equalize"
                else:
                    command = "-equalize"
            elif normalize == 2:
                command = "-auto-level"
            else:
                command = ""
            clone.transform(crop='', resize=command)
            clone.save(filename=file_out)

    return file_out
