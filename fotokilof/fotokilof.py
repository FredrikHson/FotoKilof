# -*- coding: utf-8 -*-
# pylint: disable=bare-except
# pylint: disable=too-many-branches
# pylint: disable=too-many-lines
# pylint: disable=too-many-statements
# pylint disable=invalid-name

"""
Copyright (c) 2019-2023 Tomasz Łuczak, TeaM-TL

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

nice GUI for ImageMagick command common used (by me)
"""

from tkinter import Tk, ttk, Label, PhotoImage, Canvas
from tkinter.scrolledtext import ScrolledText
from tkinter import filedialog, messagebox
from tkinter import StringVar, IntVar, TclError, TkVersion
from tkinter import N, S, W, E, X, BOTH, LEFT, RIGHT, TOP, BOTTOM, END, DISABLED, NORMAL, HORIZONTAL

try:
    from tkcolorpicker import askcolor
except:
    from tkinter.colorchooser import askcolor

try:
    from wand.version import MAGICK_VERSION, VERSION
    IMAGEMAGICK_WAND_VERSION = "IM " + MAGICK_VERSION.split(' ')[1] + " : Wand " + VERSION
    IMAGEMAGICK_WAND = "OK"
except:
    print(" ImageMagick or Wand-py not found")
    IMAGEMAGICK_WAND_VERSION = "Missing ImageMagick"
    IMAGEMAGICK_WAND = None

# standard modules
import datetime
import gettext
import os
import platform
import sys
import tempfile
from idlelib.tooltip import Hovertip

# my modules
import convert
import convert_wand
import common
import gui
import ini_read
import ini_save
import log
import magick
import mswindows
import preview
import version

# Start logging
log.write_log('Start', "M", "w", 1)

if mswindows.windows() or mswindows.macos():
    from PIL import ImageGrab
# set locale and clipboard for Windows
if mswindows.windows():
    import locale
    if os.getenv('LANG') is None:
        os.environ['LANG'] = locale.getlocale()[0]

localedir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'locale')
if not os.path.isdir(localedir):
    localedir = os.path.join(os.getcwd(), 'locale')
log.write_log(str("Locale directory: " + localedir), "M")

translate = gettext.translation('fotokilof', localedir, fallback=True)
gettext.install('fotokilof', localedir)
_ = translate.gettext

###################
# CONSTANTS
if mswindows.windows() == 1:
    PREVIEW_ORIG = 400  # preview original
    PREVIEW_NEW = 400  # preview result
    PREVIEW_LOGO = 80  # preview logo
else:
    PREVIEW_ORIG = 450
    PREVIEW_NEW = 450
    PREVIEW_LOGO = 100

preview_size_list = (300, 350, 400, 450, 500, 550, 600, 650, 700, 800,
        900, 1000, 1200, 1400, 1600, 1800, 1920, 'none')
##########################


def print_command(cmd):
    """ print command in custom window """
    t_custom.insert(END, cmd + " ")


def convert_custom_clear():
    """ clear custom widget """
    t_custom.delete(1.0, END)


def preview_orig_clear():
    """ clear every preview if doesn't choose file """
    log.write_log("clear preview", "M")
    c_preview_orig_pi.delete('all')
    c_histogram_orig.delete('all')
    # if no original, new preview should be clear too
    preview_new_clear()


def preview_new_clear():
    """ clear every preview if doesn't choose file """
    log.write_log("clear preview", "M")
    c_preview_new_pi.delete('all')
    c_histogram_new.delete('all')


def preview_new_refresh(event):
    """ callback after selection of size preview"""
    # to define file_out
    if path_to_file_out(resized.get()) is not None:
        if os.path.isfile(path_to_file_out(resized.get())):
            preview_new(path_to_file_out(resized.get()))
        else:
            preview_new_clear()
    else:
        preview_new_clear()


def preview_new(file_out):
    """ generate result preview """
    if co_preview_selector_new.get() != "none":
        preview_picture = preview.preview_wand(file_out,
                                int(co_preview_selector_new.get()))

        try:
            pi_preview_new.configure(file=preview_picture['filename'])
            c_preview_new_pi.delete('all')
            c_preview_new_pi.configure(width=preview_picture['preview_width'],
                                        height=preview_picture['preview_height'])
            c_preview_new_pi.create_image(0, 0, image=pi_preview_new, anchor='nw')

            l_preview_new.configure(text=preview_picture['width'] + "x" \
                                + preview_picture['height'] \
                                + " - " \
                                + preview_picture['size'])
        except:
            log.write_log("preview_new: Cannot read preview", "E")

        gui.copy_to_clipboard(file_out)

        if img_histograms_on.get() == 1:
            try:
                pi_histogram_new.configure(file=preview.preview_histogram(file_out))
                c_histogram_new.delete('all')
                #c_histogram_orig.configure(width=400, height=400)
                c_histogram_new.create_image(0, 0, image=pi_histogram_new, anchor='nw')
            except:
                log.write_log("previe_new: errot in preview histogram_new", "E")
    else:
        preview_new_clear()


def preview_orig_button():
    """ original preview """
    # global file_in_path
    try:
        convert_wand.display_image(file_in_path.get())
    except:
        log.write_log("No orig picture to preview", "W")


def preview_new_button():
    """ preview new picture """
    # to define file_out
    if os.path.isfile(path_to_file_out(resized.get())):
        convert_wand.display_image(path_to_file_out(resized.get()))


def extension_from_file():
    """ set extension in ComboBox same as opened file"""
    path = os.path.splitext(file_in_path.get())
    extension = path[1].lower()
    # try:
        # co_apply_type.current(file_extension.index(extension))
    # except:
        # log.write_log("extension_from_file: wrong extension", "W")
        # co_apply_type.current(file_extension.index(".jpg"))


def path_to_file_out(resize):
    """ create filename of out file """
    if resize:
        subdir = common.resize_subdir(img_resize.get(),
                                            common.empty(e1_resize_x.get()),
                                            common.empty(e1_resize_y.get()),
                                            common.empty(e2_resize.get()))
        workdir = os.path.join(work_dir.get(), subdir[0])
        resized.set(1)
    else:
        workdir = work_dir.get()
        resized.set(0)

    filename = convert.out_full_filename(file_in_path.get(), workdir, co_apply_type.get())
    return filename


def apply_all_button():
    """ all option together, processing one file or whole directory """
    if os.path.isfile(file_in_path.get()):
        progress_files.set(_("Processing"))
        root.update_idletasks()

        # single file or whole directory
        i = 0
        if file_dir_selector.get() == 0:
            files_list = [ file_in_path.get() ]
        else:
            dirname = os.path.dirname(file_in_path.get())
            files_list_short = common.list_of_images(dirname)
            files_list = []
            for filename_short in files_list_short:
                files_list.append(os.path.join(dirname, filename_short))

        file_list_len = len(files_list)
        for file_in in files_list:
            clone = convert_wand.make_clone(file_in, img_vignette_color.get())
            if img_crop_on.get():
                convert_wand.crop(file_in, clone, img_crop.get(),
                                    img_crop_gravity.get(), convert_crop_entries())
            if img_mirror_on.get():
                convert_wand.mirror(clone, img_mirror_flip.get(), img_mirror_flop.get())
            if img_bw_on.get():
                convert_wand.bw(clone, img_bw.get(), e_bw_sepia.get())
            if img_contrast_on.get():
                convert_wand.contrast(clone, img_contrast.get(),
                                        co_contrast_selection.get(),
                                        e1_contrast.get(), e2_contrast.get())
            if img_normalize_on.get():
                convert_wand.normalize(clone, img_normalize.get(), co_normalize_channel.get())
            if img_vignette_on.get():
                convert_wand.vignette(clone, e_vignette_dx.get(), e_vignette_dy.get(),
                                e_vignette_radius.get(), e_vignette_radius.get())
            if img_rotate_on.get():
                convert_wand.rotate(clone, img_rotate.get(),
                                    img_rotate_color.get(), e_rotate_own.get())
            if img_border_on.get():
                convert_wand.border(clone, img_border_color.get(),
                                    e_border_we.get(), e_border_ns.get())
            if img_resize_on.get():
                #  subdir for results if resize
                subdir_command = common.resize_subdir(img_resize.get(),
                                                        common.empty(e1_resize_x.get()),
                                                        common.empty(e1_resize_y.get()),
                                                        common.empty(e2_resize.get()))
                subdir = os.path.join(work_dir.get(), subdir_command[0])
                convert_wand.resize(clone, subdir_command[1])
                resized.set(1)
            else:
                resized.set(0)
                # standard subdir for result picture
                subdir = work_dir.get()
            if img_text_on.get():
                convert_text_data = (clone, img_text_inout.get(), e_text_angle.get(),
                            img_text_rotate.get(), img_text_color.get(), img_text_font.get(),
                            e_text_size.get(), img_text_gravity_onoff.get(), img_text_gravity.get(),
                            img_text_box.get(), img_text_box_color.get(),
                            e_text_x.get(), e_text_y.get(), e_text.get())
                convert_wand.text(convert_text_data)
            if img_logo_on.get():
                coordinates = (common.empty(e_logo_dx.get()), common.empty(e_logo_dy.get()),
                                common.empty(e_logo_width.get()), common.empty(e_logo_height.get()),
                                img_logo_gravity.get())
                height = clone.height
                width = clone.width
                convert_wand.pip(clone, file_logo_path.get(), coordinates, width, height)

            file_out = convert.out_full_filename(file_in, subdir, co_apply_type.get())
            convert_wand.save_close_clone(clone, file_out, img_exif_on.get())
            preview_new(file_out)
            # progressbar
            i = i + 1
            progress_files.set(str(i) + " " + _("of") + " " + str(file_list_len) )
            progressbar_var.set(i / file_list_len * 100)
            progress_var.set(i)
            root.update_idletasks()

        file_in_path.set(file_in)
        preview_orig()

        progress_var.set(0)
        progress_files.set(_("done"))
        progressbar_var.set(0)
        root.update_idletasks()
        #work_sub_dir.set("")  # reset subdir name for next processing
    else:
        log.write_log("No file selected", "M")


def convert_custom_button():
    """ execute custom command """
    progress_files.set(_("Processing"))
    root.update_idletasks()
    out_file = convert.out_full_filename(file_in_path.get(),
                                 work_dir.get(),
                                 co_apply_type.get())
    cmd = t_custom.get('1.0', 'end-1c')
    result = magick.magick(cmd, file_in_path.get(), out_file, "convert")
    if result == "OK":
        preview_new(out_file)
    progress_files.set(_("done"))


def convert_contrast_button():
    """ contrast button """
    progress_files.set(_("Processing"))
    root.update_idletasks()
    clone = convert_wand.make_clone(file_in_path.get())
    if clone is not None:
        convert_wand.contrast(clone, img_contrast.get(), co_contrast_selection.get(),
                                e1_contrast.get(), e2_contrast.get())
        convert_wand.save_close_clone(clone, path_to_file_out(0), img_exif_on.get())
        preview_new(path_to_file_out(0))
    progress_files.set(_("done"))


def convert_bw_button():
    """ black-white or sepia button """
    progress_files.set(_("Processing"))
    root.update_idletasks()
    clone = convert_wand.make_clone(file_in_path.get())
    if clone is not None:
        convert_wand.bw(clone, img_bw.get(), e_bw_sepia.get())
        convert_wand.save_close_clone(clone, path_to_file_out(0), img_exif_on.get())
        preview_new(path_to_file_out(0))
    progress_files.set(_("done"))


def convert_normalize_button():
    """ normalize button """
    progress_files.set(_("Processing"))
    root.update_idletasks()
    clone = convert_wand.make_clone(file_in_path.get())
    if clone is not None:
        convert_wand.normalize(clone, img_normalize.get(), co_normalize_channel.get())
        convert_wand.save_close_clone(clone, path_to_file_out(0), img_exif_on.get())
        preview_new(path_to_file_out(0))
    progress_files.set(_("done"))


def convert_rotate_button():
    """ Rotate button """
    progress_files.set(_("Processing"))
    root.update_idletasks()
    clone = convert_wand.make_clone(file_in_path.get())
    if clone is not None:
        convert_wand.rotate(clone, img_rotate.get(), img_rotate_color.get(), e_rotate_own.get())
        convert_wand.save_close_clone(clone, path_to_file_out(0), img_exif_on.get())
        preview_new(path_to_file_out(0))
    progress_files.set(_("done"))


def convert_mirror_button():
    """ Mirror button """
    progress_files.set(_("Processing"))
    root.update_idletasks()
    clone = convert_wand.make_clone(file_in_path.get())
    if clone is not None:
        convert_wand.mirror(clone, img_mirror_flip.get(), img_mirror_flop.get())
        convert_wand.save_close_clone(clone, path_to_file_out(0), img_exif_on.get())
        preview_new(path_to_file_out(0))
    progress_files.set(_("done"))


def convert_resize_button():
    """ Resize button """
    progress_files.set(_("Processing"))
    root.update_idletasks()

    resize_command = common.resize_subdir(img_resize.get(),
                                            common.empty(e1_resize_x.get()),
                                            common.empty(e1_resize_y.get()),
                                            common.empty(e2_resize.get()))
    file_out = path_to_file_out(1)
    clone = convert_wand.make_clone(file_in_path.get())
    if clone is not None:
        convert_wand.resize(clone, resize_command[1])
        convert_wand.save_close_clone(clone, file_out, img_exif_on.get())
        preview_new(file_out)
    progress_files.set(_("done"))


def convert_border_button():
    """ Border button """
    progress_files.set(_("Processing"))
    root.update_idletasks()
    clone = convert_wand.make_clone(file_in_path.get())
    if clone is not None:
        convert_wand.border(clone, img_border_color.get(), e_border_we.get(), e_border_ns.get())
        convert_wand.save_close_clone(clone, path_to_file_out(0), img_exif_on.get())
        preview_new(path_to_file_out(0))
    progress_files.set(_("done"))


def convert_vignette_button():
    """ Vignette button """
    progress_files.set(_("Processing"))
    root.update_idletasks()
    clone = convert_wand.make_clone(file_in_path.get(), img_vignette_color.get())
    if clone is not None:
        convert_wand.vignette(clone, e_vignette_dx.get(), e_vignette_dy.get(),
                                e_vignette_radius.get(), e_vignette_radius.get())
        convert_wand.save_close_clone(clone, path_to_file_out(0), img_exif_on.get())
        preview_new(path_to_file_out(0))
    progress_files.set(_("done"))


def crop_read():
    """ Read size of picture and load into crop widget """
    if file_in_path.get() is not None:
        if os.path.isfile(file_in_path.get()):
            image_size_xy = convert_wand.get_image_size(file_in_path.get())
            if image_size_xy != (0, 0):
                width = image_size_xy[0]
                height = image_size_xy[1]
                e1_crop_1.delete(0, "end")
                e1_crop_1.insert(0, "0")
                e2_crop_1.delete(0, "end")
                e2_crop_1.insert(0, "0")
                e3_crop_1.delete(0, "end")
                e3_crop_1.insert(0, width)
                e4_crop_1.delete(0, "end")
                e4_crop_1.insert(0, height)
                e1_crop_2.delete(0, "end")
                e1_crop_2.insert(0, "0")
                e2_crop_2.delete(0, "end")
                e2_crop_2.insert(0, "0")
                e3_crop_2.delete(0, "end")
                e3_crop_2.insert(0, width)
                e4_crop_2.delete(0, "end")
                e4_crop_2.insert(0, height)
                e1_crop_3.delete(0, "end")
                e1_crop_3.insert(0, "0")
                e2_crop_3.delete(0, "end")
                e2_crop_3.insert(0, "0")
                e3_crop_3.delete(0, "end")
                e3_crop_3.insert(0, width)
                e4_crop_3.delete(0, "end")
                e4_crop_3.insert(0, height)
                img_crop_gravity.set("C")


def convert_crop_entries():
    """ dictionary with values for convert_crop function """
    dict_return = {}
    dict_return['one_x1'] = common.empty(e1_crop_1.get())
    dict_return['one_y1'] = common.empty(e2_crop_1.get())
    dict_return['one_x2'] = common.empty(e3_crop_1.get())
    dict_return['one_y2'] = common.empty(e4_crop_1.get())
    dict_return['two_x1'] = common.empty(e1_crop_2.get())
    dict_return['two_y1'] = common.empty(e2_crop_2.get())
    dict_return['two_width'] = common.empty(e3_crop_2.get())
    dict_return['two_height'] = common.empty(e4_crop_2.get())
    dict_return['three_dx'] = common.empty(e1_crop_3.get())
    dict_return['three_dy'] = common.empty(e2_crop_3.get())
    dict_return['three_width'] = common.empty(e3_crop_3.get())
    dict_return['three_height'] = common.empty(e4_crop_3.get())
    return dict_return


def convert_crop_button():
    """ Crop button """
    progress_files.set(_("Processing"))
    root.update_idletasks()
    clone = convert_wand.make_clone(file_in_path.get())
    if clone is not None:
        convert_wand.crop(file_in_path.get(), clone, img_crop.get(),
                            img_crop_gravity.get(), convert_crop_entries())
        convert_wand.save_close_clone(clone, path_to_file_out(0), img_exif_on.get())
        preview_new(path_to_file_out(0))
    progress_files.set(_("done"))


def convert_text_button():
    """ add text """
    progress_files.set(_("Processing"))
    root.update_idletasks()
    clone = convert_wand.make_clone(file_in_path.get())
    if clone is not None:
        convert_text_data = (clone, img_text_inout.get(), e_text_angle.get(), img_text_rotate.get(),
                            img_text_color.get(), img_text_font.get(), e_text_size.get(),
                            img_text_gravity_onoff.get(), img_text_gravity.get(),
                            img_text_box.get(), img_text_box_color.get(),
                            e_text_x.get(), e_text_y.get(), e_text.get())
        convert_wand.text(convert_text_data)
        convert_wand.save_close_clone(clone, path_to_file_out(0), img_exif_on.get())
        preview_new(path_to_file_out(0))
    progress_files.set(_("done"))


def fonts():
    """ preparing font names for ImageMagick and load into listbox """
    result = convert_wand.fonts_list()
    co_text_font['values'] = result
    return result


def font_selected(event):
    """ callback via bind for font selection """
    img_text_font.set(co_text_font.get())


def convert_logo_button():
    """ Logo button """
    progress_files.set(_("Processing"))
    root.update_idletasks()
    coordinates = (common.empty(e_logo_dx.get()), common.empty(e_logo_dy.get()),
                    common.empty(e_logo_width.get()), common.empty(e_logo_height.get()),
                    img_logo_gravity.get())
    clone = convert_wand.make_clone(file_in_path.get())
    if clone is not None:
        convert_wand.pip(clone, file_logo_path.get(), coordinates, clone.width, clone.height )
        convert_wand.save_close_clone(clone, path_to_file_out(0), img_exif_on.get())
        preview_new(path_to_file_out(0))
    progress_files.set(_("done"))


def open_file_logo():
    """ open logo file for inserting """
    filename = open_file_dialog(os.path.dirname(file_logo_path.get()),
                                _("Select logo picture for inserting"))

    file_logo_path.set(filename)

    if os.path.isfile(file_logo_path.get()):
        preview_logo()
    else:
        preview_logo_clear()


def open_file():
    """ open image for processing """

    dirname = os.path.dirname(file_in_path.get())
    filename = open_file_dialog(dirname,
                                _("Select picture for processing"))
    open_file_common(dirname, filename)


def open_file_common(cwd, filename):
    """ common function for: open, first, last, next, prev """
    if filename is not None:
        try:
            file_in_path.set(os.path.normpath(os.path.join(cwd, filename)))
            root.title(window_title + file_in_path.get())
            image_size =  convert_wand.get_image_size(file_in_path.get())
            if image_size != (0, 0):
                file_in_width.set(image_size[0])
                file_in_height.set(image_size[1])
                preview_orig()
                extension_from_file()
                preview_new_refresh("none")
            else:
                preview_orig_clear()
        except:
            log.write_log("Error in open_file_common", "E")


def open_file_dialog(dir_initial, title):
    """ open file dialog function for image and logo """
    if mswindows.windows() == 1:
        filetypes = ((_("All graphics files"),
                    ".JPG .JPEG .PNG .TIF .TIFF"),
                     (_("JPG files"), ".JPG .JPEG"),
                     (_("PNG files"), ".PNG"),
                     (_("TIFF files"), ".TIF .TIFF"),
                     (_("ALL types"), "*"))
    else:
        filetypes = ((_("All graphics files"),
                    ".JPG .jpg .JPEG .jpeg .PNG .png .TIF .tif .TIFF .tiff"),
                     (_("JPG files"), ".JPG .jpg .JPEG .jpeg"),
                     (_("PNG files"), ".PNG .png"),
                     (_("TIFF files"), ".TIF .tif .TIFF .tiff"),
                     (_("ALL types"), "*"))
    # Wand doesn't like SVG: (_("SVG files"), ".SVG .svg"),
    filename = None
    filename = filedialog.askopenfilename(initialdir=dir_initial,
                                        filetypes=filetypes,
                                        title=title)
    return filename


def open_file_last_key(event):
    """ call open_file_last from bind"""
    open_file_last()


def open_file_last():
    """ Open last file """
    if file_in_path.get():
        if os.path.isfile(file_in_path.get()):
            dir_name = os.path.dirname(file_in_path.get())
            file_list = common.list_of_images(dir_name)
            current_file = os.path.basename(file_in_path.get())
            filename = common.file_from_list_of_images(file_list,
                                                   current_file,
                                                   "last")
            open_file_common(dir_name, filename)


def open_file_next_key(event):
    """ call open_file_next from bind"""
    open_file_next()


def open_file_next():
    """ Open next file """
    if file_in_path.get():
        if os.path.isfile(file_in_path.get()):
            dir_name = os.path.dirname(file_in_path.get())
            file_list = common.list_of_images(dir_name)
            current_file = os.path.basename(file_in_path.get())
            filename = common.file_from_list_of_images(file_list,
                                                   current_file,
                                                   "next")
            open_file_common(dir_name, filename)


def open_file_first_key(event):
    """ call open_file_first from bind"""
    open_file_first()


def open_file_first():
    """ Open first file """
    if file_in_path.get():
        if os.path.isfile(file_in_path.get()):
            dir_name = os.path.dirname(file_in_path.get())
            file_list = common.list_of_images(dir_name)
            current_file = os.path.basename(file_in_path.get())
            filename = common.file_from_list_of_images(file_list,
                                                   current_file,
                                                   "first")
            open_file_common(dir_name, filename)


def open_file_prev_key(event):
    """ call open_file_prev from bind"""
    open_file_prev()


def open_file_prev():
    """ Open previous file """
    if file_in_path.get():
        if os.path.isfile(file_in_path.get()):
            dir_name = os.path.dirname(file_in_path.get())
            file_list = common.list_of_images(dir_name)
            current_file = os.path.basename(file_in_path.get())
            filename = common.file_from_list_of_images(file_list,
                                                   current_file,
                                                   "previous")
            open_file_common(dir_name, filename)


def open_screenshot():
    """ Make screenshot """
    now = datetime.datetime.now()
    today = now.strftime("%F")
    today_dir = os.path.join(tempfile.gettempdir(), today)
    if not os.path.isdir(today_dir):
        try:
            os.mkdir(today_dir)
        except:
            log.write_log("Error in open_screenshot, make today directory", "E")

    filename = now.strftime("%F_%H-%M-%S_%f") + ".png"
    out_file = os.path.normpath(os.path.join(today_dir, filename))
    do_it = 1
    if mswindows.windows() or mswindows.macos():
        screenshot = ImageGrab.grabclipboard()
        try:
            screenshot.save(out_file, 'PNG')
        except:
            log.write_log('open_screenshot(), error save from clipboards', 'E')
            do_it = 0
    else:
        try:
            magick.magick(" ", "-quiet", out_file, "import")
        except:
            log.write_log('open_screenshot(), error in make screeshot ', 'E')
            do_it = 1
    if do_it:
        open_file_common(today_dir, filename)


def color_choose_rotate():
    """ color selection for rotate"""
    color = askcolor(img_rotate_color.get())
    if color[1] is not None:
        img_rotate_color.set(color[1])
        l_rotate_color.configure(bg=color[1])


def color_choose_border():
    """ Border color selection """
    color = askcolor(img_border_color.get())
    if color[1] is not None:
        img_border_color.set(color[1])
        l_border_color.configure(bg=color[1])


def color_choose_vignette():
    """ color selection for rotate"""
    color = askcolor(img_vignette_color.get())
    if color[1] is not None:
        img_vignette_color.set(color[1])
        l_vignette_color.configure(bg=color[1])


def color_choose_box():
    """ Background color selection """
    color = askcolor(img_text_color.get())
    if color[1] is not None:
        img_text_box_color.set(color[1])
        l_text_color.configure(bg=img_text_box_color.get())


def color_choose():
    """ Color selection """
    color = askcolor(img_text_color.get())
    if color[1] is not None:
        img_text_color.set(color[1])
        l_text_color.configure(fg=img_text_color.get())


def ini_read_wraper():
    """ Read config INI file """
    # main
    ini_entries = ini_read.main(FILE_INI, preview_size_list)
    file_in_path.set(ini_entries['file_in_path'])
    file_dir_selector.set(ini_entries['file_dir_selector'])
    work_dir.set(ini_entries['work_dir'])
    img_exif_on.set(ini_entries['img_exif_on'])
    img_histograms_on.set(ini_entries['img_histograms_on'])
    co_preview_selector_orig.current(preview_size_list.index(ini_entries['preview_orig']))
    co_preview_selector_new.current(preview_size_list.index(ini_entries['preview_new']))
    log_level.set(ini_entries['log_level'])
    # resize
    ini_entries = ini_read.resize(FILE_INI)
    img_resize_on.set(ini_entries['img_resize_on'])
    img_resize.set(ini_entries['img_resize'])
    e1_resize_x.delete(0, "end")
    e1_resize_x.insert(0, ini_entries['resize_size_pixel_x'])
    e1_resize_y.delete(0, "end")
    e1_resize_y.insert(0, ini_entries['resize_size_pixel_y'])
    e2_resize.delete(0, "end")
    e2_resize.insert(0, ini_entries['resize_size_percent'])
    # text
    ini_entries = ini_read.text(FILE_INI, img_text_font_dict)
    img_text_on.set(ini_entries['img_text_on'])
    img_text_inout.set(ini_entries['img_text_inout'])
    img_text_font.set(ini_entries['text_font'])
    img_text_color.set(ini_entries['text_color'])
    img_text_gravity.set(ini_entries['img_text_gravity'])
    img_text_gravity_onoff.set(ini_entries['img_text_gravity_onoff'])
    img_text_box.set(ini_entries['text_box'])
    img_text_box_color.set(ini_entries['text_box_color'])
    l_text_color.configure(fg=img_text_color.get(),bg=img_text_box_color.get())
    img_text_rotate.set(ini_entries['text_rotate'])
    e_text.delete(0, "end")
    e_text.insert(0, ini_entries['text_text'])
    e_text_size.delete(0, "end")
    e_text_size.insert(0, ini_entries['text_size'])
    e_text_x.delete(0, "end")
    e_text_x.insert(0, ini_entries['text_x'])
    e_text_y.delete(0, "end")
    e_text_y.insert(0, ini_entries['text_y'])
    e_text_angle.delete(0, "end")
    e_text_angle.insert(0, ini_entries['text_rotate_own'])
    # rotate
    ini_entries = ini_read.rotate(FILE_INI)
    img_rotate_on.set(ini_entries['img_rotate_on'])
    img_rotate.set(ini_entries['img_rotate'])
    e_rotate_own.delete(0, "end")
    e_rotate_own.insert(0, ini_entries['img_rotate_own'])
    img_rotate_color.set(ini_entries['img_rotate_color'])
    l_rotate_color.configure(bg=img_rotate_color.get())
    # crop
    ini_entries = ini_read.crop(FILE_INI)
    img_crop_on.set(ini_entries['img_crop_on'])
    img_crop.set(ini_entries['img_crop'])
    img_crop_gravity.set(ini_entries['img_crop_gravity'])
    e1_crop_1.delete(0, "end")
    e1_crop_1.insert(0, ini_entries['crop_1_x1'])
    e2_crop_1.delete(0, "end")
    e2_crop_1.insert(0, ini_entries['crop_1_y1'])
    e3_crop_1.delete(0, "end")
    e3_crop_1.insert(0, ini_entries['crop_1_x2'])
    e4_crop_1.delete(0, "end")
    e4_crop_1.insert(0, ini_entries['crop_1_y2'])
    e1_crop_2.delete(0, "end")
    e1_crop_2.insert(0, ini_entries['crop_2_x1'])
    e2_crop_2.delete(0, "end")
    e2_crop_2.insert(0, ini_entries['crop_2_y1'])
    e3_crop_2.delete(0, "end")
    e3_crop_2.insert(0, ini_entries['crop_2_width'])
    e4_crop_2.delete(0, "end")
    e4_crop_2.insert(0, ini_entries['crop_2_height'])
    e1_crop_3.delete(0, "end")
    e1_crop_3.insert(0, ini_entries['crop_3_dx'])
    e2_crop_3.delete(0, "end")
    e2_crop_3.insert(0, ini_entries['crop_3_dy'])
    e3_crop_3.delete(0, "end")
    e3_crop_3.insert(0, ini_entries['crop_3_width'])
    e4_crop_3.delete(0, "end")
    e4_crop_3.insert(0, ini_entries['crop_3_height'])
    # border
    ini_entries = ini_read.border(FILE_INI)
    img_border_on.set(ini_entries['img_border_on'])
    img_border_color.set(ini_entries['img_border_color'])
    l_border_color.configure(bg=img_border_color.get())
    e_border_ns.delete(0, "end")
    e_border_ns.insert(0, ini_entries['img_border_size_x'])
    e_border_we.delete(0, "end")
    e_border_we.insert(0, ini_entries['img_border_size_y'])
    # vignette
    ini_entries = ini_read.vignette(FILE_INI)
    img_vignette_on.set(ini_entries['on'])
    img_vignette_color.set(ini_entries['color'])
    l_vignette_color.configure(bg=img_vignette_color.get())
    e_vignette_dx.delete(0, "end")
    e_vignette_dx.insert(0, ini_entries['dx'])
    e_vignette_dy.delete(0, "end")
    e_vignette_dy.insert(0, ini_entries['dy'])
    e_vignette_radius.delete(0, "end")
    e_vignette_radius.insert(0, ini_entries['radius'])
    e_vignette_sigma.delete(0, "end")
    e_vignette_sigma.insert(0, ini_entries['sigma'])
    # color
    ini_entries = ini_read.colors(FILE_INI)
    img_bw_on.set(ini_entries['color_on'])
    img_bw.set(ini_entries['black_white'])
    e_bw_sepia.delete(0, "end")
    e_bw_sepia.insert(0, ini_entries['sepia'])
    # normalize
    ini_entries = ini_read.normalize(FILE_INI, normalize_channels)
    img_normalize_on.set(ini_entries['normalize_on'])
    img_normalize.set(ini_entries['normalize'])
    co_normalize_channel.current(normalize_channels.index(ini_entries['channel']))
    # contrast
    ini_entries = ini_read.contrast(FILE_INI, contrast_selection)
    img_contrast_on.set(ini_entries['contrast_on'])
    img_contrast.set(ini_entries['contrast'])
    co_contrast_selection.current(contrast_selection.index(ini_entries['contrast_selection']))
    e1_contrast.delete(0, "end")
    e1_contrast.insert(0, ini_entries['contrast_stretch_1'])
    e2_contrast.delete(0, "end")
    e2_contrast.insert(0, ini_entries['contrast_stretch_2'])
    # logo
    ini_entries = ini_read.logo(FILE_INI)
    img_logo_on.set(ini_entries['img_logo_on'])
    file_logo_path.set(ini_entries['logo_logo'])
    img_logo_gravity.set(ini_entries['img_logo_gravity'])
    e_logo_width.delete(0, "end")
    e_logo_width.insert(0, ini_entries['logo_width'])
    e_logo_height.delete(0, "end")
    e_logo_height.insert(0, ini_entries['logo_height'])
    e_logo_dx.delete(0, "end")
    e_logo_dx.insert(0, ini_entries['logo_dx'])
    e_logo_dy.delete(0, "end")
    e_logo_dy.insert(0, ini_entries['logo_dy'])
    # mirror
    ini_entries = ini_read.mirror(FILE_INI)
    img_mirror_on.set(ini_entries['img_mirror_on'])
    img_mirror_flip.set(ini_entries['img_mirror_flip'])
    img_mirror_flop.set(ini_entries['img_mirror_flop'])


def ini_save_wraper():
    """ Write variables into config file INI """
    # main
    config = {'section': 'Konfiguracja', 'path': file_in_path.get(),
                'custom_on': img_custom_on.get(),
                'work_dir': work_dir.get(), 'file_dir': file_dir_selector.get(),
                'exif': img_exif_on.get(), 'preview_new': co_preview_selector_new.get(),
                'histograms': img_histograms_on.get(),
                'log': log_level.get(), 'preview_orig': co_preview_selector_orig.get()}
    # resize
    resize = {'section': 'Resize', 'on': img_resize_on.get(),
                'resize': img_resize.get(), 'size_percent': e2_resize.get(),
                'size_pixel_x': e1_resize_x.get(), 'size_pixel_y': e1_resize_y.get()}
    # text
    text = {'section': 'Text', 'on': img_text_on.get(),
            'inout': img_text_inout.get(), 'text': e_text.get(),
            'gravity': img_text_gravity.get(),
            'gravity_onoff': img_text_gravity_onoff.get(),
            'font': img_text_font.get(), 'size': e_text_size.get(),
            'color': img_text_color.get(), 'box': img_text_box.get(),
            'box_color': img_text_box_color.get(),
            'x': e_text_x.get(), 'y': e_text_y.get(),
            'text_rotate': img_text_rotate.get(), 'text_rotate_own': e_text_angle.get()}
    # rotate
    rotate = {'section': 'Rotate', 'on': img_rotate_on.get(),
                'rotate': img_rotate.get(), 'own': e_rotate_own.get(),
                'color': img_rotate_color.get()}
    # crop
    crop = {'section': 'Crop', 'on': img_crop_on.get(), 'crop': img_crop.get(),
            '1_x1': e1_crop_1.get(), '1_y1': e2_crop_1.get(),
            '1_x2': e3_crop_1.get(), '1_y2': e4_crop_1.get(),
            '2_x1': e1_crop_2.get(), '2_y1': e2_crop_2.get(),
            '2_width': e3_crop_2.get(), '2_height': e4_crop_2.get(),
            '3_dx': e1_crop_3.get(), '3_dy': e2_crop_3.get(),
            '3_width': e3_crop_3.get(), '3_height': e4_crop_3.get(),
            'gravity': img_crop_gravity.get()}
    # border
    border = {'section': 'Border', 'on': img_border_on.get(), 'color': img_border_color.get(),
                'size_x': e_border_ns.get(), 'size_y': e_border_we.get()}
    # color
    color = {'section': 'Color', 'on': img_bw_on.get(),
                'black-white': img_bw.get(), 'sepia': e_bw_sepia.get()}
    # normalize
    normalize = {'section': 'Normalize', 'on': img_normalize_on.get(),
                 'normalize': img_normalize.get(), 'channel': co_normalize_channel.get()}
    # contrast
    contrast = {'section': 'Contrast', 'on': img_contrast_on.get(),
                'contrast': img_contrast.get(), 'selection': co_contrast_selection.get(),
                'contrast_stretch_1': e1_contrast.get(), 'contrast_stretch_2': e2_contrast.get()}
    # mirror
    mirror = {'section': 'Mirror', 'on': img_mirror_on.get(),
                'flip': img_mirror_flip.get(), 'flop': img_mirror_flop.get()}
    # vignette
    vignette = {'section': 'Vignette', 'on': img_vignette_on.get(),
                'color': img_vignette_color.get(),
                'dx': e_vignette_dx.get(), 'dy': e_vignette_dy.get(),
                'radius': e_vignette_radius.get(), 'sigma': e_vignette_sigma.get()}
    # logo
    logo = { 'section': 'Logo', 'on': img_logo_on.get(),
                'logo': file_logo_path.get(), 'gravity': img_logo_gravity.get(),
                'width': e_logo_width.get(), 'height': e_logo_height.get(),
                'dx': e_logo_dx.get(), 'dy': e_logo_dy.get()}

    ini_save_data = (FILE_INI, config, resize, text, rotate, crop, border,
                    color, normalize, contrast, mirror, vignette, logo)
    ini_save.save(ini_save_data)


def help_info(event):
    """ okno info """
    # global PWD
    license_file = os.path.join(os.path.dirname(PWD), "LICENSE")
    try:
        with open(license_file, "r", encoding="utf8") as license_fh:
            message = ""
            for line in license_fh:
                message = message + line
    except:
        log.write_log("help_info: error during loading license file: " + license_file, "W")
        message = ("Copyright " + version.__copyright__ + " "
                    + version.__author__ + " under MIT license")
    messagebox.showinfo(title=_("License"), message=message)


def close_program():
    """ close program window """
    log.write_log("closed", "M")
    root.quit()
    root.destroy()
    sys.exit()


def mouse_crop_nw(event):
    """ Left-Upper corner """
    x_preview = event.x
    y_preview = event.y

    xy_max = common.mouse_crop_calculation(file_in_width.get(),
                                           file_in_height.get(),
                                           int(co_preview_selector_orig.get()))
    width = int(x_preview*xy_max['x_orig']/xy_max['x_max'])
    height = int(y_preview*xy_max['y_orig']/xy_max['y_max'])

    if img_crop_on.get() == 1:
        if img_crop.get() == 1:
            e1_crop_1.delete(0, "end")
            e1_crop_1.insert(0, width)
            e2_crop_1.delete(0, "end")
            e2_crop_1.insert(0, height)
        elif img_crop.get() == 2:
            e1_crop_2.delete(0, "end")
            e1_crop_2.insert(0, width)
            e2_crop_2.delete(0, "end")
            e2_crop_2.insert(0, height)
        preview_orig()

    if img_text_on.get() and not img_text_gravity_onoff.get():
        e_text_x.delete(0, "end")
        e_text_x.insert(0, width)
        e_text_y.delete(0, "end")
        e_text_y.insert(0, height)


def mouse_crop_se(event):
    """ Right-Lower corner """
    if img_crop_on.get() == 1:
        x_preview = event.x
        y_preview = event.y
        xy_max = common.mouse_crop_calculation(file_in_width.get(),
                                               file_in_height.get(),
                                               int(co_preview_selector_orig.get()))
        width = int(x_preview*xy_max['x_orig']/xy_max['x_max'])
        height = int(y_preview*xy_max['y_orig']/xy_max['y_max'])
        e3_crop_1.delete(0, "end")
        e3_crop_1.insert(0, width)
        e4_crop_1.delete(0, "end")
        e4_crop_1.insert(0, height)

        preview_orig()


def preview_orig_refresh(event):
    """ callback after selection of size preview"""
    preview_orig()


def preview_orig():
    """
    generation preview of original picture
    and add crop rectangle
    """
    if co_preview_selector_orig.get() != "none":
        if os.path.isfile(file_in_path.get()):
            if img_crop_on.get() == 1:
                # draw crop rectangle on preview
                xy_max = common.mouse_crop_calculation(file_in_width.get(),
                                               file_in_height.get(),
                                               int(co_preview_selector_orig.get()))
                if img_crop.get() == 1:
                    x0 = common.empty(e1_crop_1.get())
                    y0 = common.empty(e2_crop_1.get())
                    x1 = common.empty(e3_crop_1.get())
                    y1 = common.empty(e4_crop_1.get())
                elif img_crop.get() == 2:
                    x0 = common.empty(e1_crop_2.get())
                    y0 = common.empty(e2_crop_2.get())
                    x1 = x0 + common.empty(e3_crop_2.get())
                    y1 = y0 + common.empty(e4_crop_2.get())
                elif img_crop.get() == 3:
                    coord_for_crop = (common.empty(e1_crop_3.get()),
                                        common.empty(e2_crop_3.get()),
                                        common.empty(e3_crop_3.get()),
                                        common.empty(e4_crop_3.get()),
                                        img_crop_gravity.get())
                    coord = common.preview_crop_gravity(coord_for_crop,
                                                             xy_max['x_orig'],
                                                             xy_max['y_orig'])
                    x0 = coord[0]
                    y0 = coord[1]
                    x1 = coord[2]
                    y1 = coord[3]
                if (xy_max['x_orig'] > 0) and (xy_max['y_orig'] > 0):
                    ratio_x = xy_max['x_max'] / xy_max['x_orig']
                    ratio_y = xy_max['y_max'] / xy_max['y_orig']
                else:
                    ratio_x = 1
                    ratio_y = 1
                x0 = int(x0 * ratio_x)
                y0 = int(y0 * ratio_y)
                x1 = int(x1 * ratio_x)
                y1 = int(y1 * ratio_y)

                crop_rectangle = (x0, y0, x1, y1)
            else:
                crop_rectangle = (" ")

            preview_picture = preview.preview_wand(file_in_path.get(),
                                                  int(co_preview_selector_orig.get()),
                                                  crop_rectangle)

            try:
                pi_preview_orig.configure(file=preview_picture['filename'])
                c_preview_orig_pi.delete('all')
                c_preview_orig_pi.configure(width=preview_picture['preview_width'],
                                            height=preview_picture['preview_height'])
                c_preview_orig_pi.create_image(0, 0, image=pi_preview_orig, anchor='nw')
            except:
                log.write_log("preview_orig: Cannot load preview", "E")

            try:
                l_preview_orig.configure(text=preview_picture['width'] + "x" \
                                     + preview_picture['height'] \
                                     + " - " \
                                     + preview_picture['size'])
            except:
                log.write_log("preview_orig: Cannot load image size", "E")

            if img_histograms_on.get() == 1:
                pi_histogram_orig.configure(
                        file=preview.preview_histogram(file_in_path.get()))
                c_histogram_orig.delete('all')
                #c_histogram_orig.configure(width=400, height=400)
                c_histogram_orig.create_image(0, 0, image=pi_histogram_orig, anchor='nw')
        else:
            preview_orig_clear()
    progress_files.set(_("Ready"))


def preview_logo():
    """ generating logo preview """
    if os.path.isfile(file_logo_path.get()):
        l_logo_filename.configure(text=os.path.basename(file_logo_path.get()))
        preview_picture = preview.preview_wand(file_logo_path.get(), PREVIEW_LOGO)

        try:
            pi_logo_preview.configure(file=preview_picture['filename'])
        except:
            log.write_log("Preview_logo: Cannot display file", "E")

        l_logo_preview.configure(text=preview_picture['width'] + "x" + preview_picture['height'])
    else:
        log.write_log("Preview_logo: Cannot load file", "E")


def preview_logo_clear():
    """ clear if no logo picture is selected """
    l_logo_filename.configure(text=_("No file selected"))
    pi_logo_preview.configure(file="")
    l_logo_preview.configure(text="")


def tools_set_event(event):
    """tool set for event """
    tools_set(1)


def tools_set_on():
    """tool set for event """
    tools_set(1)


def tools_set_off():
    """tool set for event """
    tools_set(0)


def tools_set(preview_on):
    """ selection tools for showing """
    l_info_when_no_tool.grid()

    if img_crop_on.get() == 0:
        frame_crop.grid_remove()
    else:
        frame_crop.grid()
        crop_tool_hide_show()
        l_info_when_no_tool.grid_remove()

    if img_mirror_on.get() == 0:
        frame_mirror.grid_remove()
    else:
        frame_mirror.grid(row=1, column=1, sticky=(W, N, S), padx=5)
        l_info_when_no_tool.grid_remove()

    if img_bw_on.get() == 0:
        frame_bw.grid_remove()
    else:
        frame_bw.grid(row=1, column=1, sticky=W, padx=5)
        l_info_when_no_tool.grid_remove()

    if img_contrast_on.get() == 0:
        frame_contrast.grid_remove()
    else:
        frame_contrast.grid(row=1, column=2, sticky=W, padx=5)
        l_info_when_no_tool.grid_remove()

    if img_normalize_on.get() == 0:
        frame_normalize.grid_remove()
    else:
        frame_normalize.grid(row=1, column=2, sticky=W, padx=5)
        l_info_when_no_tool.grid_remove()

    if img_vignette_on.get() == 0:
        frame_vignette.grid_remove()
    else:
        frame_vignette.grid(row=1, column=2, sticky=W, padx=5)
        l_info_when_no_tool.grid_remove()

    if img_border_on.get() == 0:
        frame_border.grid_remove()
    else:
        frame_border.grid(row=1, column=1, sticky=W, padx=5)
        l_info_when_no_tool.grid_remove()

    if img_rotate_on.get() == 0:
        frame_rotate.grid_remove()
    else:
        frame_rotate.grid()
        l_info_when_no_tool.grid_remove()

    if img_resize_on.get() == 0:
        frame_resize.grid_remove()
    else:
        frame_resize.grid()
        l_info_when_no_tool.grid_remove()

    if img_text_on.get() == 0:
        frame_text.grid_remove()
    else:
        frame_text.grid()
        l_info_when_no_tool.grid_remove()

    if img_logo_on.get() == 0:
        frame_logo.grid_remove()
    else:
        frame_logo.grid()
        l_info_when_no_tool.grid_remove()

    if img_custom_on.get() == 0:
        frame_custom.grid_remove()
    else:
        frame_custom.grid()
        l_info_when_no_tool.grid_remove()

    if img_histograms_on.get() == 0:
        frame_histogram_orig.grid_remove()
        frame_histogram_new.grid_remove()
    else:
        frame_histogram_orig.grid()
        frame_histogram_new.grid()

    if (img_bw_on.get() == 0) and (img_contrast_on.get() == 0):
        frame_bw_contrast.grid_remove()
    else:
        frame_bw_contrast.grid()

    if (img_border_on.get() == 0) and (img_normalize_on.get() == 0):
        frame_border_normalize.grid_remove()
    else:
        frame_border_normalize.grid()

    if (img_mirror_on.get() == 0) and (img_vignette_on.get() == 0):
        frame_mirror_vignette.grid_remove()
    else:
        frame_mirror_vignette.grid()

    if preview_on:
        preview_orig()


def crop_tool_hide_show():
    """hide not necessary things, or show if the are needed"""
    if img_crop.get() == 1:
        f_clickL_crop.grid()
        f_clickR_crop.grid()
        e1_crop_2.grid_remove()
        e2_crop_2.grid_remove()
        e3_crop_2.grid_remove()
        e4_crop_2.grid_remove()
        e1_crop_3.grid_remove()
        e2_crop_3.grid_remove()
        e3_crop_3.grid_remove()
        e4_crop_3.grid_remove()
        frame_crop_gravity.grid_remove()
    elif img_crop.get() == 2:
        f_clickL_crop.grid_remove()
        f_clickR_crop.grid_remove()
        e1_crop_2.grid()
        e2_crop_2.grid()
        e3_crop_2.grid()
        e4_crop_2.grid()
        e1_crop_3.grid_remove()
        e2_crop_3.grid_remove()
        e3_crop_3.grid_remove()
        e4_crop_3.grid_remove()
        frame_crop_gravity.grid_remove()
    elif img_crop.get() == 3:
        f_clickL_crop.grid_remove()
        f_clickR_crop.grid_remove()
        e1_crop_2.grid_remove()
        e2_crop_2.grid_remove()
        e3_crop_2.grid_remove()
        e4_crop_2.grid_remove()
        e1_crop_3.grid()
        e2_crop_3.grid()
        e3_crop_3.grid()
        e4_crop_3.grid()
        frame_crop_gravity.grid()
    preview_orig()


def text_tool_hide_show():
    """hide not necessary things, or show if the are needed"""
    if img_text_inout.get():
        # Outside
        l_text_xy_x.grid_remove()
        l_text_xy_y.grid_remove()
        e_text_x.grid_remove()
        e_text_y.grid_remove()
        rb_text_NW.grid_remove()
        rb_text_N.grid_remove()
        rb_text_NE.grid_remove()
        rb_text_W.grid()
        rb_text_C.grid()
        rb_text_E.grid()
        rb_text_SW.grid_remove()
        rb_text_S.grid_remove()
        rb_text_SE.grid_remove()
        cb_text_gravity.grid_remove()
        frame_text_rotate.grid_remove()
    else:
        # Inside
        l_text_xy_x.grid()
        l_text_xy_y.grid()
        e_text_x.grid()
        e_text_y.grid()
        cb_text_gravity.grid()
        if img_text_gravity_onoff.get():
            # Gravity on
            rb_text_NW.grid()
            rb_text_N.grid()
            rb_text_NE.grid()
            rb_text_W.grid()
            rb_text_C.grid()
            rb_text_E.grid()
            rb_text_SW.grid()
            rb_text_S.grid()
            rb_text_SE.grid()
            l_text_xy_x.configure(text=_("dx"))
            l_text_xy_y.configure(text=_("dy"))
        else:
            # Gravity off
            rb_text_NW.grid_remove()
            rb_text_N.grid_remove()
            rb_text_NE.grid_remove()
            rb_text_W.grid_remove()
            rb_text_C.grid_remove()
            rb_text_E.grid_remove()
            rb_text_SW.grid_remove()
            rb_text_S.grid_remove()
            rb_text_SE.grid_remove()
            l_text_xy_x.configure(text=_("x"))
            l_text_xy_y.configure(text=_("y"))
        frame_text_rotate.grid()


###############################################################################
# GUI main window
###############################################################################

root = Tk()

# hidden file
# https://code.activestate.com/lists/python-tkinter-discuss/3723/
try:
    # call a dummy dialog with an impossible option to initialize the file
    # dialog without really getting a dialog window; this will throw a
    # TclError, so we need a try...except :
    try:
        root.tk.call('tk_getOpenFile', '-foobarbaz')
    except TclError:
        pass
    # now set the magic variables accordingly
    root.tk.call('set', '::tk::dialog::file::showHiddenBtn', '1')
    root.tk.call('set', '::tk::dialog::file::showHiddenVar', '0')
except:
    pass

style = ttk.Style()
style.configure("Blue.TButton", foreground="blue")
style.configure("Brown.TButton", foreground="#8B0000")
style.configure("Blue.TLabelframe.Label", foreground="blue")
style.configure("Fiolet.TLabelframe.Label", foreground="#800080")
style.configure("Rotate.TEntry", fieldbackground="#FFFFFF")

##########################
# global variables
FILE_INI = os.path.join(os.path.expanduser("~"), ".fotokilof.ini")
PWD = os.getcwd()
log_level = StringVar() # E(rror), W(arning), M(essage)
work_dir = StringVar()  # default: "FotoKilof"
work_sub_dir = StringVar()  # subdir for resized pictures
work_sub_dir.set("")  # default none
file_dir_selector = IntVar()
file_in_path = StringVar()  # fullpath original picture
file_in_width = IntVar() # width original picture
file_in_height = IntVar() # height original picture
file_in_size = IntVar() # size original picture (bytes)
img_histograms_on = IntVar()
img_logo_on = IntVar()  # Logo
file_logo_path = StringVar()  # fullpath logo file
img_logo_gravity = StringVar()
img_resize_on = IntVar()  # Resize
img_resize = IntVar()  # (1, 2, 3, 4, 5)
resized = IntVar() # for proper display
img_text_on = IntVar()  # Text
img_text_gravity = StringVar()
img_text_gravity_onoff = IntVar()
img_text_font = StringVar()
img_text_font_dict = {}  # dict with available fonts, from fonts()
img_text_color = StringVar()
img_text_box = IntVar()
img_text_box_color = StringVar()
img_text_inout = IntVar()  # Text inside or outside picture
img_text_rotate =IntVar()
img_rotate_on = IntVar()  # Rotate
img_rotate = IntVar()
img_rotate_own = IntVar()
img_rotate_color = StringVar()
img_crop_on = IntVar()  # Crop
img_crop = IntVar()  # (1, 2, 3)
img_crop_gravity = StringVar()
img_border_on = IntVar()  # Border
img_border_color = StringVar()
img_normalize_on = IntVar()  # Normalize
img_normalize = IntVar()  #  (1,2,3)
normalize_channels = ("None", "Red", "Green", "Blue", "Alpha", "Gray",
                      "Cyan", "Magenta", "Yellow", "Black", "Opacity",
                      "Index", "RGB", "RGBA", "CMYK", "CMYKA")
img_bw_on = IntVar()  # Black-white
img_bw = IntVar()
img_contrast_on = IntVar()  # Contrast
img_contrast = IntVar()  # (1, 2)
img_mirror_on = IntVar()  # Mirror
img_mirror_flip = IntVar()  # (0, 1)
img_mirror_flop = IntVar()  # (0, 1)
contrast_selection = ("+5", "+4", "+3", "+2", "+1", "-1", "-2", "-3", "-4", "-5")
img_custom_on = IntVar()  # Custom
img_exif_on = IntVar()
img_vignette_on = IntVar()
img_vignette_color = StringVar()
progress_var = IntVar()  # progressbar
progressbar_var = IntVar()
progress_files = StringVar()
file_extension = (".jpeg", ".jpg", ".png", ".tif")

######################################################################
# Tabs
######################################################################
main_menu = ttk.Frame()
main_tools = ttk.Frame()
main_paned = ttk.PanedWindow(orient=HORIZONTAL, width=5)
main_progress = ttk.Frame()

main_menu.pack(side=TOP, expand=0, fill=BOTH)
main_tools.pack(side=TOP, expand=0, fill=BOTH)
main_progress.pack(side=BOTTOM, expand=0, fill=X, anchor=S)
main_paned.pack(side=BOTTOM, expand=1, fill=BOTH)


validation = main_paned.register(gui.only_numbers)  # Entry validation
validationint = main_paned.register(gui.only_integer)  # Entry validation integer value
####################################################################
progressbar = ttk.Progressbar(main_progress, orient=HORIZONTAL, mode='determinate',
                                variable=progressbar_var, maximum=100)
progressbar.pack(side=BOTTOM, padx=0, pady=0, fill=X, expand=0, anchor=S)
####################################################################
# main_menu row
####################################################################
###########################
# Picture selection
###########################
frame_file_select = ttk.Labelframe(main_menu, text=_("Image"),
                                   style="Fiolet.TLabelframe")
frame_file_select.grid(row=1, column=1, sticky=(N, W, E, S), padx=5, pady=5)

b_file_select = ttk.Button(frame_file_select, text=_("File selection"),
                           command=open_file, style="Blue.TButton")

b_file_select_screenshot = ttk.Button(frame_file_select, text=_("Screenshot"),
                                 command=open_screenshot)
if mswindows.windows() or mswindows.macos():
    b_file_select_screenshot.configure(text=_("Clipboard"))

b_file_select_first = ttk.Button(frame_file_select, text=_("First"),
                                 command=open_file_first)
b_file_select_prev = ttk.Button(frame_file_select, text=_("Previous"),
                                command=open_file_prev)
b_file_select_next = ttk.Button(frame_file_select, text=_("Next"),
                                command=open_file_next)
b_file_select_last = ttk.Button(frame_file_select, text=_("Last"),
                                command=open_file_last)

b_file_select.grid(column=1, row=1, padx=5, pady=5, sticky=W)
#
b_file_select_screenshot.grid(column=2, row=1, padx=10, pady=5, sticky=W)
#
b_file_select_first.grid(column=5, row=1, padx=5, pady=5, sticky=W)
b_file_select_prev.grid(column=6, row=1, padx=5, pady=5, sticky=W)
b_file_select_next.grid(column=7, row=1, padx=5, pady=5, sticky=W)
b_file_select_last.grid(column=8, row=1, padx=5, pady=5, sticky=W)

##########################
# Execute all
##########################
frame_apply = ttk.LabelFrame(main_menu, text=_("Execute all"),
                             style="Fiolet.TLabelframe")
frame_apply.grid(row=1, column=2, sticky=(N, W, E, S), padx=5, pady=5)

rb_apply_dir = ttk.Radiobutton(frame_apply, text=_("Folder"),
                               variable=file_dir_selector, value="1")
rb_apply_file = ttk.Radiobutton(frame_apply, text=_("File"),
                                variable=file_dir_selector, value="0")
co_apply_type = ttk.Combobox(frame_apply, width=4, values=file_extension)
co_apply_type.configure(state='readonly')
co_apply_type.current(file_extension.index(".jpg"))
b_apply_run = ttk.Button(frame_apply, text=_("Execute all"),
                         command=apply_all_button,
                         style="Blue.TButton")

b_apply_run.pack(side=LEFT, padx=5, pady=5, anchor=W)
rb_apply_dir.pack(side=LEFT, pady=5, anchor=W)
rb_apply_file.pack(side=LEFT, padx=5, pady=5, anchor=W)

co_apply_type.pack(side=LEFT, padx=5, pady=1, anchor=W)

l_pb = ttk.Label(frame_apply, textvariable=progress_files, width=15)
l_pb.pack(side=LEFT, padx=5, pady=2, anchor=W)

###########################
# Buttons
###########################
frame_save = ttk.LabelFrame(main_menu, text=_("Settings"),
                       style="Fiolet.TLabelframe")
frame_save.grid(row=1, column=3, sticky=(N, W, E, S), padx=5, pady=5)

b_last_save = ttk.Button(frame_save, text=_("Save"), command=ini_save_wraper)
b_last_read = ttk.Button(frame_save, text=_("Load"), command=ini_read_wraper)

b_last_save.pack(padx=5, pady=1, anchor=W, side=LEFT)
b_last_read.pack(padx=5, pady=1, anchor=W, side=LEFT)

####################################################################
# main_tools row
####################################################################
frame_tools_selection = ttk.Frame(main_paned)

############################
# Tools selection
############################
frame_tools_set = ttk.Labelframe(main_tools, text=_("Tools"),
                                style="Fiolet.TLabelframe")
frame_tools_set.grid(row=1, column=1, padx=5, pady=2, sticky=(W, E))

cb_resize = ttk.Checkbutton(frame_tools_set, text=_("Scaling/Resize"),
                            variable=img_resize_on,
                            offvalue="0", onvalue="1",
                            command=tools_set_off)
cb_crop = ttk.Checkbutton(frame_tools_set, text=_("Crop"),
                          variable=img_crop_on,
                          offvalue="0", onvalue="1",
                          command=tools_set_on)
cb_text = ttk.Checkbutton(frame_tools_set, text=_("Text"),
                          variable=img_text_on,
                          onvalue="1", offvalue="0",
                          command=tools_set_off)
cb_rotate = ttk.Checkbutton(frame_tools_set, text=_("Rotate"),
                            variable=img_rotate_on,
                            offvalue="0", onvalue="1",
                            command=tools_set_off)
cb_border = ttk.Checkbutton(frame_tools_set, text=_("Border"),
                            variable=img_border_on,
                            offvalue="0", onvalue="1",
                            command=tools_set_off)
cb_bw = ttk.Checkbutton(frame_tools_set, text=_("Black&white"),
                        variable=img_bw_on, offvalue="0",
                        command=tools_set_off)
cb_normalize = ttk.Checkbutton(frame_tools_set, text=_("Colors normalize"),
                               variable=img_normalize_on,
                               offvalue="0", onvalue="1",
                               command=tools_set_off)
cb_contrast = ttk.Checkbutton(frame_tools_set, text=_("Contrast"),
                              variable=img_contrast_on,
                              offvalue="0", onvalue="1",
                              command=tools_set_off)
cb_mirror = ttk.Checkbutton(frame_tools_set, text=_("Mirror"),
                              variable=img_mirror_on,
                              offvalue="0", onvalue="1",
                              command=tools_set_off)
cb_logo = ttk.Checkbutton(frame_tools_set, text=_("Logo"),
                          variable=img_logo_on,
                          offvalue="0", onvalue="1",
                          command=tools_set_off)
cb_custom = ttk.Checkbutton(frame_tools_set, text=_("Custom"),
                            variable=img_custom_on,
                            offvalue="0", onvalue="1",
                            command=tools_set_off)
cb_vignette = ttk.Checkbutton(frame_tools_set, text=_("Vignette"),
                            variable=img_vignette_on,
                            offvalue="0", onvalue="1",
                            command=tools_set_off)
cb_exif = ttk.Checkbutton(frame_tools_set, text=_("EXIF"),
                                variable=img_exif_on,
                                offvalue="0", onvalue="1",
                                command=tools_set_off)
cb_histograms = ttk.Checkbutton(frame_tools_set, text=_("Histograms"),
                                variable=img_histograms_on,
                                offvalue="0", onvalue="1",
                                command=tools_set_off)

cb_crop.pack(padx=5, pady=1, anchor=W, side=LEFT)
cb_mirror.pack(padx=5, pady=1, anchor=W, side=LEFT)
cb_bw.pack(padx=5, pady=1, anchor=W, side=LEFT)
cb_contrast.pack(padx=5, pady=1, anchor=W, side=LEFT)
cb_normalize.pack(padx=5, pady=1, anchor=W, side=LEFT)
cb_vignette.pack(padx=5, pady=1, anchor=W, side=LEFT)
cb_border.pack(padx=5, pady=1, anchor=W, side=LEFT)
cb_rotate.pack(padx=5, pady=1, anchor=W, side=LEFT)
cb_resize.pack(padx=5, pady=1, anchor=W, side=LEFT)
cb_text.pack(padx=5, pady=1, anchor=W, side=LEFT)
cb_logo.pack(padx=5, pady=1, anchor=W, side=LEFT)
cb_custom.pack(padx=5, pady=1, anchor=W, side=LEFT)
cb_exif.pack(padx=5, pady=1, anchor=W, side=LEFT)
#cb_histograms.pack(padx=5, pady=1, anchor=W, side=LEFT)

####################################################################
# main row
####################################################################
#####################################################
# First column
#####################################################
frame_first_col = ttk.Frame()

###########################
# Label if no any tool selected
l_info_when_no_tool = ttk.Label(frame_first_col,
                        text=_("Open file for processing\nSelect tools for conversion\nExecute conversion or perform all conversion in one run"))

###########################
# Resize
###########################
frame_resize = ttk.Labelframe(frame_first_col, text=_("Scale/Resize"),
                              style="Fiolet.TLabelframe")
###
frame_resize_row1 = ttk.Frame(frame_resize)
rb_resize_3 = ttk.Radiobutton(frame_resize_row1, text="FullHD (1920x1080)",
                              variable=img_resize, value="3")
rb_resize_4 = ttk.Radiobutton(frame_resize_row1, text="2K (2048×1556)",
                              variable=img_resize, value="4")
rb_resize_5 = ttk.Radiobutton(frame_resize_row1, text="4K (4096×3112)",
                              variable=img_resize, value="5")
frame_resize_row2 = ttk.Frame(frame_resize)
rb_resize_1 = ttk.Radiobutton(frame_resize_row2, text=_("Max"),
                              variable=img_resize, value="1")
l_resize_x = ttk.Label(frame_resize_row2, text="X")
e1_resize_x = ttk.Entry(frame_resize_row2, width=4,
                      validate="key", validatecommand=(validation, '%S'))
l_resize_y = ttk.Label(frame_resize_row2, text="Y")
e1_resize_y = ttk.Entry(frame_resize_row2, width=4,
                      validate="key", validatecommand=(validation, '%S'))
rb_resize_2 = ttk.Radiobutton(frame_resize_row2, text=_("Percent"),
                              variable=img_resize, value="2")
e2_resize = ttk.Entry(frame_resize_row2, width=3,
                      validate="key", validatecommand=(validation, '%S'))
b_resize_run = ttk.Button(frame_resize_row2, text=_("Execute"),
                          style="Brown.TButton",
                          command=convert_resize_button)

rb_resize_3.pack(side=LEFT, padx=5)
rb_resize_4.pack(side=LEFT, padx=5)
rb_resize_5.pack(side=LEFT, padx=5)
rb_resize_1.pack(side=LEFT, padx=5)
l_resize_x.pack(side=LEFT, padx=5)
e1_resize_x.pack(side=LEFT, padx=0)
l_resize_y.pack(side=LEFT, padx=5)
e1_resize_y.pack(side=LEFT, padx=0)
rb_resize_2.pack(side=LEFT, padx=5)
e2_resize.pack(side=LEFT, padx=0)
b_resize_run.pack(side=LEFT, padx=25)

frame_resize_row1.pack(side=TOP, fill=X, expand=1)
frame_resize_row2.pack(side=TOP, fill=X, expand=1)

############################
# crop
############################
frame_crop = ttk.Labelframe(frame_first_col, text=_("Crop"),
                            style="Fiolet.TLabelframe")
frame_crop.grid(row=3, column=1, columnspan=2,
                sticky=(N, W, E, S), padx=5, pady=1)
###
rb1_crop = ttk.Radiobutton(frame_crop, variable=img_crop, value="1",
                           text=_("Coordinates (x1, y1) and (x2, y2)"),
                           command=crop_tool_hide_show)
f_clickL_crop = ttk.Frame(frame_crop)
l_clickL_crop = ttk.Label(f_clickL_crop, text=_("Left Upper\ncorner\nClick left"))
e1_crop_1 = ttk.Entry(f_clickL_crop, width=4,
                      validate="key", validatecommand=(validation, '%S'))
e2_crop_1 = ttk.Entry(f_clickL_crop, width=4,
                      validate="key", validatecommand=(validation, '%S'))
f_clickR_crop = ttk.Frame(frame_crop)
l_clickR_crop = ttk.Label(f_clickR_crop, text=_("Right Lower\ncorner\nClick right"))
e3_crop_1 = ttk.Entry(f_clickR_crop, width=4,
                      validate="key", validatecommand=(validation, '%S'))
e4_crop_1 = ttk.Entry(f_clickR_crop, width=4,
                      validate="key", validatecommand=(validation, '%S'))

rb2_crop = ttk.Radiobutton(frame_crop, variable=img_crop, value="2",
                           text=_("Origin (x1,y1) and dimensions (X, Y)"),
                           command=crop_tool_hide_show)
e1_crop_2 = ttk.Entry(frame_crop, width=4,
                      validate="key", validatecommand=(validation, '%S'))
e2_crop_2 = ttk.Entry(frame_crop, width=4,
                      validate="key", validatecommand=(validation, '%S'))
e3_crop_2 = ttk.Entry(frame_crop, width=4,
                      validate="key", validatecommand=(validation, '%S'))
e4_crop_2 = ttk.Entry(frame_crop, width=4,
                      validate="key", validatecommand=(validation, '%S'))

rb3_crop = ttk.Radiobutton(frame_crop, variable=img_crop, value="3",
                           text=_("Offset (dx,dy), dimensions (X, Y)\nand gravity"),
                           command=crop_tool_hide_show)
e1_crop_3 = ttk.Entry(frame_crop, width=4,
                      validate="key", validatecommand=(validation, '%S'))
e2_crop_3 = ttk.Entry(frame_crop, width=4,
                      validate="key", validatecommand=(validation, '%S'))
e3_crop_3 = ttk.Entry(frame_crop, width=4,
                      validate="key", validatecommand=(validation, '%S'))
e4_crop_3 = ttk.Entry(frame_crop, width=4,
                      validate="key", validatecommand=(validation, '%S'))

frame_crop_gravity = ttk.Frame(frame_crop)
rb_crop_NW = ttk.Radiobutton(frame_crop_gravity, text="NW",
                             variable=img_crop_gravity, value="NW",
                             command=preview_orig)
rb_crop_N = ttk.Radiobutton(frame_crop_gravity, text="N",
                            variable=img_crop_gravity, value="N",
                             command=preview_orig)
rb_crop_NE = ttk.Radiobutton(frame_crop_gravity, text="NE",
                             variable=img_crop_gravity, value="NE",
                             command=preview_orig)
rb_crop_W = ttk.Radiobutton(frame_crop_gravity, text="W",
                            variable=img_crop_gravity, value="W",
                             command=preview_orig)
rb_crop_C = ttk.Radiobutton(frame_crop_gravity, text=_("Center"),
                            variable=img_crop_gravity, value="C",
                             command=preview_orig)
rb_crop_E = ttk.Radiobutton(frame_crop_gravity, text="E",
                            variable=img_crop_gravity, value="E",
                             command=preview_orig)
rb_crop_SW = ttk.Radiobutton(frame_crop_gravity, text="SW",
                             variable=img_crop_gravity, value="SW",
                             command=preview_orig)
rb_crop_S = ttk.Radiobutton(frame_crop_gravity, text="S",
                            variable=img_crop_gravity, value="S",
                             command=preview_orig)
rb_crop_SE = ttk.Radiobutton(frame_crop_gravity, text="SE",
                             variable=img_crop_gravity, value="SE",
                             command=preview_orig)
frame_crop_buttons = ttk.Frame(frame_crop)

b_crop_show = ttk.Button(frame_crop_buttons, text=_("Preview"),
                         command=preview_orig)
b_crop_read = ttk.Button(frame_crop_buttons, text=_("From image"),
                         command=crop_read)
b_crop_run = ttk.Button(frame_crop, text=_("Execute"),
                        style="Brown.TButton",
                        command=convert_crop_button)

rb1_crop.grid(row=2, column=1, sticky=W, padx=5, pady=5)
f_clickL_crop.grid(row=1, column=2, rowspan=4, columnspan=2, padx=5, sticky=N)
f_clickR_crop.grid(row=1, column=4, rowspan=4, columnspan=2, padx=5, sticky=N)
e1_crop_1.grid(row=1, column=1, sticky=W, padx=5, pady=5)
e2_crop_1.grid(row=1, column=2, sticky=W, padx=5, pady=5)
e3_crop_1.grid(row=1, column=1, sticky=W, padx=5, pady=5)
e4_crop_1.grid(row=1, column=2, sticky=W, padx=5, pady=5)
l_clickL_crop.grid(row=2, column=1, columnspan=2, sticky=(W, E))
l_clickR_crop.grid(row=2, column=1, columnspan=2, sticky=(W, E))
rb2_crop.grid(row=3, column=1, sticky=W, padx=5, pady=5)
e1_crop_2.grid(row=3, column=2, sticky=W, padx=10, pady=5)
e2_crop_2.grid(row=3, column=3, sticky=W, padx=5, pady=5)
e3_crop_2.grid(row=3, column=4, sticky=W, padx=5, pady=5)
e4_crop_2.grid(row=3, column=5, sticky=W, padx=5, pady=5)
rb3_crop.grid(row=4, column=1, sticky=W, padx=5, pady=1)
e1_crop_3.grid(row=4, column=2, sticky=W, padx=10, pady=1)
e2_crop_3.grid(row=4, column=3, sticky=W, padx=5, pady=1)
e3_crop_3.grid(row=4, column=4, sticky=W, padx=5, pady=1)
e4_crop_3.grid(row=4, column=5, sticky=W, padx=5, pady=1)
frame_crop_gravity.grid(row=2, column=2, rowspan=2, padx=5, columnspan=4, sticky=E)
rb_crop_NW.grid(row=1, column=1, sticky=W, pady=1)
rb_crop_N.grid(row=1, column=2, pady=1)
rb_crop_NE.grid(row=1, column=3, sticky=W, pady=1)
rb_crop_W.grid(row=2, column=1, sticky=W, pady=1)
rb_crop_C.grid(row=2, column=2, sticky=W, pady=1)
rb_crop_E.grid(row=2, column=3, sticky=W, pady=1)
rb_crop_SW.grid(row=3, column=1, sticky=W, pady=1)
rb_crop_S.grid(row=3, column=2, pady=1)
rb_crop_SE.grid(row=3, column=3, sticky=W, pady=1)
frame_crop_buttons.grid(row=5, column=1, sticky=(W, E))
b_crop_read.grid(row=1, column=1, sticky=W, padx=15, pady=5)
b_crop_show.grid(row=1, column=2, sticky=W, padx=5, pady=5)
b_crop_run.grid(row=5, column=4, columnspan=2, sticky=W, padx=5, pady=5)

###########################
# Tekst
###########################
frame_text = ttk.Labelframe(frame_first_col, text=_("Add text"),
                            style="Fiolet.TLabelframe")
###
e_text = ttk.Entry(frame_text, width=55, style='Color.TEntry')
#frame_text_text.grid(row=1, column=1, columnspan=5, sticky=(W, E))
e_text.grid(row=1, column=1, columnspan=5, sticky=W, padx=5)

###
rb_text_in = ttk.Radiobutton(frame_text, text=_("Inside"),
                             variable=img_text_inout, value="0",
                             command=text_tool_hide_show)
rb_text_out = ttk.Radiobutton(frame_text, text=_("Outside"),
                              variable=img_text_inout, value="1",
                             command=text_tool_hide_show)
cb_text_box = ttk.Checkbutton(frame_text, text=_("Background"),
                              variable=img_text_box,
                              onvalue="1", offvalue="0")
cb_text_gravity = ttk.Checkbutton(frame_text, text=_("Gravity"),
                              variable=img_text_gravity_onoff,
                              onvalue="1", offvalue="0",
                              command=text_tool_hide_show)
#l_text_xy_l = ttk.Label(frame_text, text=_("Offset"))
l_text_xy_x = ttk.Label(frame_text, text=_("dx"))
l_text_xy_y = ttk.Label(frame_text, text=_("dy"))
e_text_x = ttk.Entry(frame_text, width=4,
                     validate="key", validatecommand=(validation, '%S'))
e_text_y = ttk.Entry(frame_text, width=4,
                     validate="key", validatecommand=(validation, '%S'))

rb_text_out.grid(row=2, column=1, sticky=W, padx=5, pady=1)
rb_text_in.grid(row=3,  column=1, sticky=W, padx=5, pady=1)
cb_text_box.grid(row=4, column=1, sticky=W, padx=5, pady=1)
cb_text_gravity.grid(row=2, column=3, columnspan=2, sticky=W, pady=1)

l_text_xy_x.grid(row=3, column=3, sticky=W, padx=5, pady=1)
l_text_xy_y.grid(row=3, column=4, sticky=W, padx=5, pady=1)
e_text_x.grid(row=4, column=3, sticky=(W, N), padx=5, pady=1)
e_text_y.grid(row=4, column=4, sticky=(W, N), padx=5, pady=1)

###
frame_text_gravity = ttk.Frame(frame_text)
rb_text_NW = ttk.Radiobutton(frame_text_gravity, text="NW",
                             variable=img_text_gravity, value="NW")
rb_text_N = ttk.Radiobutton(frame_text_gravity, text="N",
                            variable=img_text_gravity, value="N")
rb_text_NE = ttk.Radiobutton(frame_text_gravity, text="NE",
                             variable=img_text_gravity, value="NE")
rb_text_W = ttk.Radiobutton(frame_text_gravity, text="W",
                            variable=img_text_gravity, value="W")
rb_text_C = ttk.Radiobutton(frame_text_gravity, text=_("Center"),
                            variable=img_text_gravity, value="C")
rb_text_E = ttk.Radiobutton(frame_text_gravity, text="E",
                            variable=img_text_gravity, value="E")
rb_text_SW = ttk.Radiobutton(frame_text_gravity, text="SW",
                             variable=img_text_gravity, value="SW")
rb_text_S = ttk.Radiobutton(frame_text_gravity, text="S",
                            variable=img_text_gravity, value="S")
rb_text_SE = ttk.Radiobutton(frame_text_gravity, text="SE",
                             variable=img_text_gravity, value="SE")
frame_text_gravity.grid(row=2, column=2, rowspan=3,  padx=25, pady=2, sticky=(W, N))
rb_text_NW.grid(row=1, column=1, sticky=W, pady=1)
rb_text_N.grid(row=1, column=2, pady=1)
rb_text_NE.grid(row=1, column=3, sticky=W, pady=1)
rb_text_W.grid(row=2, column=1, sticky=W, pady=1)
rb_text_C.grid(row=2, column=2, pady=1)
rb_text_E.grid(row=2, column=3, sticky=W, pady=1)
rb_text_SW.grid(row=3, column=1, sticky=W, pady=1)
rb_text_S.grid(row=3, column=2, pady=1)
rb_text_SE.grid(row=3, column=3, sticky=W, pady=1)

###
co_text_font = ttk.Combobox(frame_text, width=30,
                            textvariable=img_text_font)
co_text_font.configure(state='readonly')
e_text_size = ttk.Entry(frame_text, width=3,
                        validate="key", validatecommand=(validation, '%S'))
l_text_color = Label(frame_text, text=_("Color test"))
b_text_color = ttk.Button(frame_text, text=_("Font"),
                          command=color_choose)
l_text_heght = ttk.Label(frame_text, text=_("Height"))
b_text_box_color = ttk.Button(frame_text, text=_("Background"),
                              command=color_choose_box)
b_text_run = ttk.Button(frame_text, text=_("Execute"),
                        style="Brown.TButton", command=convert_text_button)

l_text_color.grid(row=2, column=5, sticky=(W, E), padx=5, pady=1)
b_text_color.grid(row=3, column=5, sticky=(W, E), padx=5, pady=1)
b_text_box_color.grid(row=4, column=5, sticky=(W, E), padx=5, pady=1)
co_text_font.grid(row=5, column=1, columnspan=2, sticky=(W, E), padx=5)
l_text_heght.grid(row=5, column=3, sticky=W, padx=5)
e_text_size.grid(row=5, column=4, sticky=W, padx=5)
b_text_run.grid(row=5, column=5, sticky=(E), padx=5, pady=1)

frame_text_rotate = ttk.Frame(frame_text)
rb_text_rotate_0 = ttk.Radiobutton(frame_text_rotate, text="0",
                               variable=img_text_rotate, value="0")
rb_text_rotate_90 = ttk.Radiobutton(frame_text_rotate, text="90",
                               variable=img_text_rotate, value="90")
rb_text_rotate_180 = ttk.Radiobutton(frame_text_rotate, text="180",
                                variable=img_text_rotate, value="180")
rb_text_rotate_270 = ttk.Radiobutton(frame_text_rotate, text="270",
                                variable=img_text_rotate, value="270")
rb_text_rotate_own = ttk.Radiobutton(frame_text_rotate, text=_("Custom"),
                                variable=img_text_rotate, value="-1")
e_text_angle = ttk.Entry(frame_text_rotate, width=3,
                        validate="key", validatecommand=(validation, '%S'))
rb_text_rotate_0.grid(row=1, column=1, sticky=(N, W, E, S), padx=5, pady=5)
rb_text_rotate_90.grid(row=1, column=2, sticky=(N, W, E, S), padx=5, pady=5)
rb_text_rotate_180.grid(row=1, column=3, sticky=(N, W, E, S), padx=5, pady=5)
rb_text_rotate_270.grid(row=1, column=4, sticky=(N, W, E, S), padx=5, pady=5)
rb_text_rotate_own.grid(row=1, column=5, sticky=(N, W, E, S), padx=5, pady=5)
e_text_angle.grid(row=1, column=6, sticky=(N, W, E, S), padx=5, pady=5)
frame_text_rotate.grid(row=6, column=1, columnspan=6, sticky=W, padx=5)

###########################
# Rotate
###########################
frame_rotate = ttk.LabelFrame(frame_first_col, text=_("Rotate"),
                              style="Fiolet.TLabelframe")
###
rb_rotate_90 = ttk.Radiobutton(frame_rotate, text="90",
                               variable=img_rotate, value="90")
rb_rotate_180 = ttk.Radiobutton(frame_rotate, text="180",
                                variable=img_rotate, value="180")
rb_rotate_270 = ttk.Radiobutton(frame_rotate, text="270",
                                variable=img_rotate, value="270")
rb_rotate_own = ttk.Radiobutton(frame_rotate, text=_("Custom"),
                                variable=img_rotate, value="0")
e_rotate_own = ttk.Entry(frame_rotate, width=3, style='Rotate.TEntry',
                     validate="key", validatecommand=(validation, '%S'))
l_rotate_color = Label(frame_rotate, text=_("  "))
b_rotate_color = ttk.Button(frame_rotate, text=_("Color"),
                          command=color_choose_rotate)
b_rotate_run = ttk.Button(frame_rotate, text=_("Execute"),
                          style="Brown.TButton",
                          command=convert_rotate_button)

rb_rotate_90.pack(side=LEFT, padx=5, pady=5)
rb_rotate_180.pack(side=LEFT, padx=5, pady=5)
rb_rotate_270.pack(side=LEFT, padx=5, pady=5)
rb_rotate_own.pack(side=LEFT, padx=5, pady=5)
e_rotate_own.pack(side=LEFT, padx=5, pady=5)
l_rotate_color.pack(side=LEFT, pady=5)
b_rotate_color.pack(side=LEFT, padx=5, pady=5)
b_rotate_run.pack(side=LEFT, padx=5, pady=5)

###########################
# frames for two widgets
###########################
frame_mirror_vignette = ttk.Frame(frame_first_col)
frame_bw_contrast = ttk.Frame(frame_first_col)
frame_border_normalize = ttk.Frame(frame_first_col)

###########################
# Border
###########################
frame_border = ttk.Labelframe(frame_border_normalize, text=_("Border"),
                              style="Fiolet.TLabelframe")
###
l_border_color = Label(frame_border, text=_("  "))
l_border_we = ttk.Label(frame_border, text="WE")
e_border_we = ttk.Entry(frame_border, width=3,
                     validate="key", validatecommand=(validation, '%S'))
l_border_ns = ttk.Label(frame_border, text="NS")
e_border_ns = ttk.Entry(frame_border, width=3,
                     validate="key", validatecommand=(validation, '%S'))
b_border_color = ttk.Button(frame_border, text=_("Color"),
                            command=color_choose_border)
b_border_run = ttk.Button(frame_border, text=_("Execute"),
                          style="Brown.TButton",
                          command=convert_border_button)

l_border_we.grid(row=1, column=1, padx=5, pady=0)
e_border_we.grid(row=1, column=2, padx=5, pady=0)
l_border_ns.grid(row=2, column=1, padx=5, pady=5)
e_border_ns.grid(row=2, column=2, padx=5, pady=5)
l_border_color.grid(row=1, column=3)
b_border_color.grid(row=1, column=5, padx=5, pady=0)
b_border_run.grid(row=2, column=5, padx=5, pady=5, sticky=E)

############################
# Black-white
############################
frame_bw = ttk.LabelFrame(frame_bw_contrast, text=_("Black-white"),
                          style="Fiolet.TLabelframe")
###
rb1_bw = ttk.Radiobutton(frame_bw, text=_("Black-white"),
                         variable=img_bw, value="1")
rb2_bw = ttk.Radiobutton(frame_bw, text=_("Sepia"),
                         variable=img_bw, value="2")
e_bw_sepia = ttk.Entry(frame_bw, width=3,
                       validate="key", validatecommand=(validation, '%S'))
l_bw_sepia = ttk.Label(frame_bw, text="%")
b_bw_run = ttk.Button(frame_bw, text=_("Execute"),
                      style="Brown.TButton",
                      command=convert_bw_button)

rb2_bw.grid(row=1, column=1, padx=5, pady=5, sticky=W)
e_bw_sepia.grid(row=1, column=2, padx=5, pady=5, sticky=E)
l_bw_sepia.grid(row=1, column=3, padx=5, pady=5, sticky=W)
rb1_bw.grid(row=2, column=1, padx=5, pady=0, sticky=W)
b_bw_run.grid(row=2, column=2, columnspan=2, padx=5, pady=5, sticky=E)

########################
# Contrast
#########################
frame_contrast = ttk.Labelframe(frame_bw_contrast, text=_("Contrast"),
                                style="Fiolet.TLabelframe")
###
rb1_contrast = ttk.Radiobutton(frame_contrast, text=_("Stretch"),
                               variable=img_contrast, value="1")
rb2_contrast = ttk.Radiobutton(frame_contrast, text=_("Contrast"),
                               variable=img_contrast, value="2")
co_contrast_selection = ttk.Combobox(frame_contrast, width=3,
                                     values=contrast_selection)
co_contrast_selection.configure(state='readonly')

e1_contrast = ttk.Entry(frame_contrast, width=4)
e2_contrast = ttk.Entry(frame_contrast, width=4)
l1_contrast = ttk.Label(frame_contrast, text=_("Black"))
l2_contrast = ttk.Label(frame_contrast, text=_("White"))
b_contrast_run = ttk.Button(frame_contrast, text=_("Execute"),
                            style="Brown.TButton",
                            command=convert_contrast_button)

rb1_contrast.grid(row=1, column=1, padx=5, pady=5, sticky=W)
l1_contrast.grid(row=1, column=2, padx=5, pady=5, sticky=E)
e1_contrast.grid(row=1, column=3, padx=5, pady=5, sticky=E)
l2_contrast.grid(row=1, column=4, padx=5, pady=5, sticky=W)
e2_contrast.grid(row=1, column=5, padx=5, pady=5, sticky=W)
rb2_contrast.grid(row=2, column=1, padx=5, pady=5, sticky=W)
co_contrast_selection.grid(row=2, column=2, padx=5, pady=5, sticky=W)
b_contrast_run.grid(row=2, column=3, padx=5, pady=5, columnspan=3, sticky=E)

############################
# Color normalize
############################
frame_normalize = ttk.LabelFrame(frame_border_normalize, text=_("Color normalize"),
                                 style="Fiolet.TLabelframe")
###
rb1_normalize = ttk.Radiobutton(frame_normalize, text=_("Normalize"),
                                variable=img_normalize,
                                value="1")
rb2_normalize = ttk.Radiobutton(frame_normalize, text=_("AutoLevel"),
                                variable=img_normalize,
                                value="2")
l_normalize_channel = ttk.Label(frame_normalize, text=_("Channel:"))
co_normalize_channel = ttk.Combobox(frame_normalize, width=7,
                                    values=normalize_channels)
co_normalize_channel.configure(state='readonly')
b_normalize_run = ttk.Button(frame_normalize, text=_("Execute"),
                             style="Brown.TButton",
                             command=convert_normalize_button)

rb1_normalize.grid(row=1, column=1, padx=5, pady=0, sticky=W)
l_normalize_channel.grid(row=1, column=2, padx=5, pady=4, sticky=E)
co_normalize_channel.grid(row=1, column=3, padx=5, pady=4, sticky=E)
rb2_normalize.grid(row=2, column=1, padx=5, pady=4, sticky=W)
b_normalize_run.grid(row=2, column=2, columnspan=2, padx=5, pady=4, sticky=E)

###########################
# Mirror
###########################
frame_mirror = ttk.LabelFrame(frame_mirror_vignette, text=_("Mirror"),
                              style="Fiolet.TLabelframe")

cb_mirror_flip = ttk.Checkbutton(frame_mirror, text="NS",
                                 variable=img_mirror_flip,
                                 offvalue="0", onvalue="1")
cb_mirror_flop = ttk.Checkbutton(frame_mirror, text="WE",
                                 variable=img_mirror_flop,
                                 offvalue="0", onvalue="1")
b_mirror_run = ttk.Button(frame_mirror, text=_("Execute"),
                          style="Brown.TButton",
                          command=convert_mirror_button)

cb_mirror_flip.grid(row=1, column=1, sticky=(N, W, E, S), padx=5, pady=5)
cb_mirror_flop.grid(row=1, column=2, sticky=(N, W, E, S), padx=5, pady=5)
b_mirror_run.grid(row=1, column=5, sticky=E, padx=5, pady=5)

###########################
# vignette
###########################
frame_vignette = ttk.Labelframe(frame_mirror_vignette, text=_("Vignette"),
                              style="Fiolet.TLabelframe")
###
l_vignette_radius = ttk.Label(frame_vignette, text=_("Radius"))
e_vignette_radius = ttk.Entry(frame_vignette, width=3,
                     validate="key", validatecommand=(validation, '%S'))
l_vignette_sigma = ttk.Label(frame_vignette, text=_("Sigma"))
e_vignette_sigma = ttk.Entry(frame_vignette, width=3,
                     validate="key", validatecommand=(validation, '%S'))
l_vignette_dx = ttk.Label(frame_vignette, text=_("dx"))
e_vignette_dx = ttk.Entry(frame_vignette, width=3,
                     validate="key", validatecommand=(validationint, '%S'))
l_vignette_dy = ttk.Label(frame_vignette, text=_("dy"))
e_vignette_dy = ttk.Entry(frame_vignette, width=3,
                     validate="key", validatecommand=(validationint, '%S'))
l_vignette_color = Label(frame_vignette, text=_("  "))
b_vignette_color = ttk.Button(frame_vignette, text=_("Color"),
                            command=color_choose_vignette)
b_vignette_run = ttk.Button(frame_vignette, text=_("Execute"),
                          style="Brown.TButton",
                          command=convert_vignette_button)
l_vignette_radius.grid(row=1, column=1, padx=5, pady=0)
e_vignette_radius.grid(row=1, column=2, padx=5, pady=0)
l_vignette_sigma.grid(row=2, column=1, padx=5, pady=5)
e_vignette_sigma.grid(row=2, column=2, padx=5, pady=5)
l_vignette_dx.grid(row=1, column=3, padx=5, pady=0)
e_vignette_dx.grid(row=1, column=4, padx=5, pady=0)
l_vignette_dy.grid(row=2, column=3, padx=5, pady=5)
e_vignette_dy.grid(row=2, column=4, padx=5, pady=5)
l_vignette_color.grid(row=1, column=5)
b_vignette_color.grid(row=1, column=6, padx=5, pady=0)
b_vignette_run.grid(row=2, column=6, padx=5, pady=5)

###########################
# Logo
###########################
frame_logo = ttk.LabelFrame(frame_first_col, text=_("Logo"),
                            style="Fiolet.TLabelframe")

b_logo_select = ttk.Button(frame_logo, text=_("File selection"),
                           command=open_file_logo)

b_logo_run = ttk.Button(frame_logo, text=_("Execute"),
                        command=convert_logo_button,
                        style="Brown.TButton")
l_logo_filename = ttk.Label(frame_logo, width=25)

b_logo_select.grid(row=1, column=1, padx=5, pady=5)
l_logo_filename.grid(row=1, column=2, padx=5, pady=5, sticky=W)
b_logo_run.grid(row=1, column=3, pady=5, sticky=E)

###
frame_logo_xy = ttk.Frame(frame_logo)
l_logo_XxY = ttk.Label(frame_logo_xy, text=_("Width\nHeight"))
l_logo_dxdy = ttk.Label(frame_logo_xy, text=_("Offset\n(dx,dy)"))
e_logo_width = ttk.Entry(frame_logo_xy, width=4,
                         validate="key", validatecommand=(validation, '%S'))
e_logo_height = ttk.Entry(frame_logo_xy, width=4,
                          validate="key", validatecommand=(validation, '%S'))
e_logo_dx = ttk.Entry(frame_logo_xy, width=4,
                      validate="key", validatecommand=(validation, '%S'))
e_logo_dy = ttk.Entry(frame_logo_xy, width=4,
                      validate="key", validatecommand=(validation, '%S'))

frame_logo_xy.grid(row=2, column=2, padx=5, pady=5)
l_logo_XxY.grid(row=1, column=1, sticky=W, padx=5)
e_logo_width.grid(row=2, column=1, sticky=W, padx=5)
e_logo_height.grid(row=3, column=1, sticky=W, padx=5)
l_logo_dxdy.grid(row=1, column=2, sticky=W, padx=5)
e_logo_dx.grid(row=2, column=2, sticky=W, padx=5)
e_logo_dy.grid(row=3, column=2, sticky=W, padx=5)

###
frame_logo_gravity = ttk.Frame(frame_logo)
rb_logo_NW = ttk.Radiobutton(frame_logo_gravity, text="NW",
                             variable=img_logo_gravity, value="NW")
rb_logo_N = ttk.Radiobutton(frame_logo_gravity, text="N",
                            variable=img_logo_gravity, value="N")
rb_logo_NE = ttk.Radiobutton(frame_logo_gravity, text="NE",
                             variable=img_logo_gravity, value="NE")
rb_logo_W = ttk.Radiobutton(frame_logo_gravity, text="W",
                            variable=img_logo_gravity, value="W")
rb_logo_C = ttk.Radiobutton(frame_logo_gravity, text=_("Center"),
                            variable=img_logo_gravity, value="C")
rb_logo_E = ttk.Radiobutton(frame_logo_gravity, text="E",
                            variable=img_logo_gravity, value="E")
rb_logo_SW = ttk.Radiobutton(frame_logo_gravity, text="SW",
                             variable=img_logo_gravity, value="SW")
rb_logo_S = ttk.Radiobutton(frame_logo_gravity, text="S",
                            variable=img_logo_gravity, value="S")
rb_logo_SE = ttk.Radiobutton(frame_logo_gravity, text="SE",
                             variable=img_logo_gravity, value="SE")
frame_logo_gravity.grid(row=2, column=3, sticky=E)
rb_logo_NW.grid(row=1, column=1, sticky=W, pady=1)
rb_logo_N.grid(row=1, column=2, pady=1)
rb_logo_NE.grid(row=1, column=3, sticky=W, pady=1)
rb_logo_W.grid(row=2, column=1, sticky=W, pady=1)
rb_logo_C.grid(row=2, column=2, pady=1)
rb_logo_E.grid(row=2, column=3, sticky=W, pady=1)
rb_logo_SW.grid(row=3, column=1, sticky=W, pady=1)
rb_logo_S.grid(row=3, column=2, pady=1)
rb_logo_SE.grid(row=3, column=3, sticky=W, pady=1)

###
frame_logo_preview = ttk.Frame(frame_logo)
frame_logo_preview.grid(row=2, column=1)
pi_logo_preview = PhotoImage()
l_logo_preview_pi = ttk.Label(frame_logo_preview, image=pi_logo_preview)
l_logo_preview = ttk.Label(frame_logo_preview)
l_logo_preview_pi.grid(row=2, column=1, padx=5, pady=1)
l_logo_preview.grid(row=1, column=1, padx=5, pady=1)

############################
# Custom command
############################
frame_custom = ttk.LabelFrame(frame_first_col, text=_("Custom command"),
                              style="Fiolet.TLabelframe")

b_custom_clear = ttk.Button(frame_custom, text=_("Clear"),
                            command=convert_custom_clear)
b_custom_run = ttk.Button(frame_custom, text=_("Execute"),
                          style="Brown.TButton",
                          command=convert_custom_button)

t_custom = ScrolledText(frame_custom, state=NORMAL,
                        height=5, width=45,
                        wrap='word', undo=True)

t_custom.pack(expand=1, fill=BOTH, padx=5, pady=5)
b_custom_run.pack(side=RIGHT, padx=5, pady=5)
b_custom_clear.pack(side=RIGHT, padx=5, pady=5)

############################
# Pack frames
############################
l_info_when_no_tool.grid(row=1, column=1, padx=5, pady=5)
frame_crop.grid(row=2, column=1,             sticky=(N, W, S), padx=5, pady=1)
frame_mirror_vignette.grid(row=3, column=1,  sticky=(N, W, S), padx=0, pady=1)
frame_bw_contrast.grid(row=4, column=1,      sticky=(N, W, S), padx=0, pady=1)
frame_border_normalize.grid(row=5, column=1, sticky=(N, W, S), padx=0, pady=1)
frame_rotate.grid(row=7, column=1,           sticky=(N, W, S), padx=5, pady=1)
frame_resize.grid(row=8, column=1,           sticky=(N, W, S), padx=5, pady=5)
frame_text.grid(row=9, column=1,             sticky=(N, W, S), padx=5, pady=1)
frame_logo.grid(row=10, column=1,            sticky=(N, W, S), padx=5, pady=1)
frame_custom.grid(row=11, column=1,          sticky=(N, W, S), padx=5, pady=1)

#####################################################
# Second column
#####################################################
frame_second_col = ttk.Frame()

############################
# Original preview
############################
frame_preview_orig = ttk.Labelframe(frame_second_col, text=_("Original"),
                                    style="Fiolet.TLabelframe")
frame_preview_orig.grid(row=1, column=1, sticky=(N, W, E, S), padx=5, pady=5)
###
b_preview_orig_run = ttk.Button(frame_preview_orig, text=_("Preview"),
                                command=preview_orig_button)
l_preview_orig = ttk.Label(frame_preview_orig)
co_preview_selector_orig = ttk.Combobox(frame_preview_orig, width=4,
                                        values=preview_size_list)
co_preview_selector_orig.configure(state='readonly')
pi_preview_orig = PhotoImage()
c_preview_orig_pi = Canvas(frame_preview_orig)
c_preview_orig_pi.create_image(0, 0, image=pi_preview_orig, anchor='ne')

c_preview_orig_pi.pack(side=BOTTOM, anchor=W)
b_preview_orig_run.pack(side=LEFT, padx=5, pady=5)
l_preview_orig.pack(side=LEFT, padx=5, pady=5)
co_preview_selector_orig.pack(side=LEFT, padx=5, pady=1)

###########################
# Histogram original
###########################
frame_histogram_orig = ttk.LabelFrame(frame_second_col, text=_("Histogram"))
frame_histogram_orig.grid(row=2, column=1, sticky=(N, W, E, S), padx=5, pady=5)
###
pi_histogram_orig = PhotoImage()
c_histogram_orig = Canvas(frame_histogram_orig)
c_preview_orig_pi.create_image(0, 0, image=pi_histogram_orig, anchor='ne')
c_histogram_orig.grid(row=2, column=1, padx=10, pady=5)

#####################################################
# Third column
#####################################################
frame_third_col = ttk.Frame()

##########################
# Result preview
###########################
frame_preview_new = ttk.Labelframe(frame_third_col, text=_("Result"),
                                   style="Fiolet.TLabelframe")
frame_preview_new.grid(row=1, column=1, sticky=(N, W, E, S), padx=5, pady=5)
###
b_preview_new_run = ttk.Button(frame_preview_new, text=_("Preview"),
                               command=preview_new_button)
l_preview_new = ttk.Label(frame_preview_new)
co_preview_selector_new = ttk.Combobox(frame_preview_new, width=4,
                                       values=preview_size_list)
co_preview_selector_new.configure(state='readonly')
pi_preview_new = PhotoImage()
c_preview_new_pi = Canvas(frame_preview_new)
c_preview_orig_pi.create_image(0, 0, image=pi_preview_orig, anchor='ne')

c_preview_new_pi.pack(side=BOTTOM, anchor=W)
b_preview_new_run.pack(side=LEFT, padx=5, pady=5)
l_preview_new.pack(side=LEFT, padx=5, pady=5)
co_preview_selector_new.pack(side=LEFT, padx=5, pady=1)

###########################
# Histogram new
###########################
frame_histogram_new = ttk.LabelFrame(frame_third_col, text=_("Histogram"))
frame_histogram_new.grid(row=2, column=1, sticky=(N, W, E, S), padx=5, pady=5)
###
pi_histogram_new = PhotoImage()
c_histogram_new = Canvas(frame_histogram_new)
c_histogram_new.create_image(0, 0, image=pi_histogram_new, anchor='ne')
c_histogram_new.grid(row=2, column=1, padx=10, pady=5)

###############################################################################
# Add Frames into PanedWindow
###############################################################################
main_paned.add(frame_first_col)
main_paned.add(frame_second_col)
main_paned.add(frame_third_col)

###############################################################################
# bind
###############################################################################
# binding commands to widgets
co_preview_selector_orig.bind("<<ComboboxSelected>>", preview_orig_refresh)
co_preview_selector_new.bind("<<ComboboxSelected>>", preview_new_refresh)
co_text_font.bind("<<ComboboxSelected>>", font_selected)
c_preview_orig_pi.bind("<Button-1>", mouse_crop_nw)
if mswindows.macos():
    c_preview_orig_pi.bind("<Button-2>", mouse_crop_se)
else:
    c_preview_orig_pi.bind("<Button-3>", mouse_crop_se)
root.bind("<F1>", help_info)
root.protocol("WM_DELETE_WINDOW", close_program)

root.bind("<Prior>", open_file_prev_key)
root.bind("<Next>", open_file_next_key)
root.bind("<Home>", open_file_first_key)
root.bind("<End>", open_file_last_key)

###############################################################################
# toolTips
###############################################################################
# main first
Hovertip(b_file_select, _("Select image file for processing"))
Hovertip(b_file_select_screenshot, _("MacOS and Windows: take image from clipboard.\nLinux: make screenshot, click window or select area.\nGrabbed image is saved into %TEMP%/today directory ad load for processing."))
Hovertip(b_file_select_first, _("Load first image from current directory.\nUse Home key instead"))
Hovertip(b_file_select_prev, _("Load previous image from current directory.\nUse PgUp key instead"))
Hovertip(b_file_select_next, _("Load next image from current directory.\nUse PgDn key instead"))
Hovertip(b_file_select_last, _("Load last image from current directory.\nUse End key instead"))
Hovertip(rb_apply_dir, _("Processing all files in current directory"))
Hovertip(rb_apply_file, _("Processing only current file"))
Hovertip(co_apply_type, _("Selection of format output file; JPG, PNG or TIF"))
Hovertip(b_apply_run, _("Perform all selected conversion for current file or all files in current directory"))
Hovertip(b_last_save, _("Save all values into configuration file (~/.fotokilof.ini).\nFotoKilof will load it during starting"))
Hovertip(b_last_read, _("Load saved values of conversion"))
# main second
Hovertip(cb_resize, _("Scale image, proportions are saved.\nSpecify maximum dimensions of image or percent"))
Hovertip(cb_crop, _("Take part of image. Select crop by:\n- absolute coordinate\n- absolute coorinate left-top corner plus width and height\n- gravity plus width and height plus offset.\nRemember point (0,0) is located in left-top corner of image."))
Hovertip(cb_text, _("Insert text on picture or add text at bottom.\nText can be rotated, colored and with background.\nAll font from OS are available"))
Hovertip(cb_rotate, _("Rotate picture by 90, 180, 270 degree or specify own angle of rotation"))
Hovertip(cb_border, _("Add border around picture.\nSpecify width of horizontal and vertical border separately"))
Hovertip(cb_bw, _("Convert into black-white or sepia"))
Hovertip(cb_contrast, _("Change contrast or change range of contrast"))
Hovertip(cb_normalize, _("Normalize of color level"))
Hovertip(cb_mirror, _("Make mirror of picture in vertical or horizotal or both direction"))
Hovertip(cb_vignette, _("Add vignette as on old photography or not the best lens"))
Hovertip(cb_logo, _("Insert picture, eg. own logo, into picture"))
Hovertip(cb_custom, _("Processing ImageMagick command.\nWorks only on Linux OS"))
Hovertip(cb_exif, _("If ON keep EXIF data\nif OFF EXIF data will be removed"))
# preview
Hovertip(b_preview_orig_run, _("Display original image by IMdisplay or default image viewer of OS"))
Hovertip(co_preview_selector_orig, _("Select size of preview"))
Hovertip(b_preview_new_run, _("Display result image by IMdisplay or default image viewer of OS"))
Hovertip(co_preview_selector_new, _("Select size of preview"))
# Scaling
Hovertip(b_resize_run, _("Execute only resize conversion on current picture"))
# Crop
Hovertip(rb1_crop, _("Select crop by absolute coordinate.\nRemember point (0,0) is located in left-top corner of image."))
Hovertip(rb2_crop, _("Select crop by absolute coorinate left-top corner plus width and height.\nRemember point (0,0) is located in left-top corner of image."))
Hovertip(rb3_crop, _("Select crop by gravity plus width and height plus offset.\nRemember point (0,0) is located in left-top corner of image."))
Hovertip(e1_crop_1, _("x1 - horizontal position of left-top corner of crop\nClick left mouse button on preview in place of left-top corner"))
Hovertip(e2_crop_1, _("y1 - vertical position of left-top corner of crop\nClick left mouse button on preview in place of left-top corner"))
Hovertip(e3_crop_1, _("x2 - horizontal position of right-bottom corner of crop\nClick right mouse button on preview in place of left-top corner"))
Hovertip(e4_crop_1, _("y2 - vertical position of right-bottom corner of crop\nClick right mouse button on preview in place of left-top corner"))
Hovertip(e1_crop_2, _("x1 - horizontal position of left-top corner of crop"))
Hovertip(e2_crop_2, _("y1 - vertical position of left-top corner of crop"))
Hovertip(e3_crop_2, _("X - width of crop"))
Hovertip(e4_crop_2, _("Y - height of crop"))
Hovertip(e1_crop_3, _("dx - horizontal offset from gravity point"))
Hovertip(e2_crop_3, _("dy - vertical offsef from gravity point"))
Hovertip(e3_crop_3, _("X - width of crop"))
Hovertip(e4_crop_3, _("Y - height of crop"))
Hovertip(b_crop_read, _("Take size of crop from current picture.\nCrop will be 100% of original picture"))
Hovertip(b_crop_show, _("Refresh preview to see crop on picture"))
Hovertip(frame_crop_gravity, _("Use gravity direction for select crop"))
Hovertip(b_crop_run, _("Execute only crop conversion on current picture"))
# Text
Hovertip(e_text, _("Click here and type text"))
Hovertip(e_text_size, _("Text size"))
Hovertip(e_text_angle, _("Angle of text"))
Hovertip(co_text_font, _("Font"))
Hovertip(rb_text_in, _("Put text on picture"))
Hovertip(rb_text_out, _("Put text below picture"))
Hovertip(cb_text_gravity, _("Use gravity for putting text or Absolute position"))
Hovertip(frame_text_gravity, _("Use gravity direction for text placement"))
Hovertip(cb_text_box, _("Use background for text"))
Hovertip(e_text_x, _("Offset from gravity or absolute position"))
Hovertip(e_text_y, _("Offset from gravity or absolute position"))
Hovertip(l_text_color, _("Selected color of text and background"))
Hovertip(b_text_color,_("Select color of text"))
Hovertip(b_text_box_color, _("Select color of background"))
Hovertip(b_text_run, _("Execute only adding text on current picture"))
# Rotate
Hovertip(rb_rotate_own, _("Select if want to use own angle of rotation"))
Hovertip(e_rotate_own, _("Put angle of rotation. Rotation is in right direction.\nBackground color is as choosed by Color button"))
Hovertip(l_rotate_color, _("Selected color to fill a gap"))
Hovertip(b_rotate_color, _("If OWN is choosed, select color to fill a gap."))
Hovertip(b_rotate_run, _("Execute only rotate conversion on current picture"))
# Scaling
Hovertip(e2_resize, _("Put percent for rescale of picture"))
Hovertip(b_resize_run, _("Execute only resize conversion on current picture"))
# Border
Hovertip(e_border_ns, _("Put width of vertical part of border"))
Hovertip(e_border_we, _("Put width of horizontal part of border"))
Hovertip(l_border_color, _("Selected color of border"))
Hovertip(b_border_color, _("Select color of border"))
Hovertip(b_border_run, _("Execute only add border conversion on current picture"))
# Black-white
Hovertip(rb1_bw, _("Convert picture into gray scale - black-white"))
Hovertip(rb2_bw, _("Convert picture into sepia - old style silver based photography"))
Hovertip(e_bw_sepia, _("Put threshold of sepia, try values in range 80-95"))
Hovertip(b_bw_run, _("Execute only black-white/sepia conversion on current picture"))
# Contrast
Hovertip(e1_contrast, _("Black point.\nTry values in range 0-0.2"))
Hovertip(e2_contrast, _("White point.\nTry values in range 0-0.2"))
Hovertip(rb1_contrast, _("Enhance contrast of image by adjusting the span of the available colors"))
Hovertip(rb2_contrast, _("Enhances the difference between lighter & darker values of the image"))
Hovertip(co_contrast_selection, _("Select power of reduce (negative values) or increase (positive values) contrast"))
Hovertip(b_contrast_run, _("Execute only change contrast conversion on current picture"))
# Normalize
Hovertip(rb1_normalize, _("Normalize color channels"))
Hovertip(co_normalize_channel, _("Select channel for normalize"))
Hovertip(rb2_normalize, _("Scale the minimum and maximum values to a full quantum range"))
Hovertip(b_normalize_run, _("Execute only color normalize conversion on current picture"))
# Mirror
Hovertip(cb_mirror_flip, _("Mirror top-bottom"))
Hovertip(cb_mirror_flop, _("Mirror left-right"))
Hovertip(b_mirror_run, _("Execute only mirror conversion on current picture"))
# Vignette
Hovertip(e_vignette_radius, _("Radius of the Gaussian blur effect"))
Hovertip(e_vignette_sigma, _("Standard deviation of the Gaussian effect"))
Hovertip(e_vignette_dx, _("Horizontal offset of vignette"))
Hovertip(e_vignette_dy, _("Vertical offset of vignette"))
Hovertip(l_vignette_color, _("Selected color of corners"))
Hovertip(b_vignette_color, _("Select color of corners"))
Hovertip(b_vignette_run, _("Execute only vignette conversion on current picture"))
# Logo
Hovertip(b_logo_select, _("Select picture to put on picture"))
Hovertip(e_logo_width, _("Width picture"))
Hovertip(e_logo_height, _("Height picture"))
Hovertip(e_logo_dx, _("Horizontal offset from gravity point"))
Hovertip(e_logo_dy, _("Vertical offset from gravity point"))
Hovertip(frame_logo_gravity, _("Use gravity for putting picture"))
Hovertip(b_logo_run, _("Execute only add logo on current picture"))

##########################################
# Run functions
#

Python_version = "Py " + platform.python_version() + " Tk " + str(TkVersion)
window_title = ( version.__author__ + " : "
                + version.__appname__ + " "
                + version.__version__ + " : "
                + IMAGEMAGICK_WAND_VERSION + " : " + Python_version + " | " )
root.title(window_title)
if IMAGEMAGICK_WAND is not None:
    img_text_font_dict = fonts()    # Reading available fonts
    ini_read_wraper()  # Loading settings from config file
    tools_set(0)
    text_tool_hide_show()
    progress_files.set(_("Ready"))
    l_border_color.configure(bg=img_border_color.get())
    if os.path.isfile(file_in_path.get()):
        open_file_common("", file_in_path.get())
    if img_logo_on.get() == 1:
        if os.path.isfile(file_logo_path.get()):
            # Load preview logo
            preview_logo()
else:
    root.withdraw()
    messagebox.showerror(title=_("Error"),
                         message=_("ImageMagick nor GraphicsMagick are not installed in you system. Is impossible to process any graphics."))
    # disable processing buttons
    img_crop_on.set(0)
    img_normalize_on.set(0)
    img_contrast_on.set(0)
    img_logo_on.set(0)
    img_custom_on.set(0)
    img_histograms_on.set(0)
    b_logo_run.configure(state=DISABLED)
    b_resize_run.configure(state=DISABLED)
    b_crop_read.configure(state=DISABLED)
    b_crop_run.configure(state=DISABLED)
    b_text_run.configure(state=DISABLED)
    b_rotate_run.configure(state=DISABLED)
    b_bw_run.configure(state=DISABLED)
    b_border_run.configure(state=DISABLED)
    b_contrast_run.configure(state=DISABLED)
    b_normalize_run.configure(state=DISABLED)
    b_custom_run.configure(state=DISABLED)
    b_apply_run.configure(state=DISABLED)
    b_preview_orig_run.configure(state=DISABLED)
    b_preview_new_run.configure(state=DISABLED)
    b_file_select_first.configure(state=DISABLED)
    b_file_select_prev.configure(state=DISABLED)
    b_file_select_next.configure(state=DISABLED)
    b_file_select_last.configure(state=DISABLED)
    b_file_select.configure(state=DISABLED)
    b_file_select_screenshot.configure(state=DISABLED)
    root.deiconify()

# -------------------------------------------------------
# Lock in 4.0.0, will be unlocked or removed in next releases
img_histograms_on.set(0)
cb_histograms.configure(state=DISABLED)
# -------------------------------------------------------

root.mainloop()

# EOF
