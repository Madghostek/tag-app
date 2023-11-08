#!/usr/bin/python3

# mostly windowing logic, but slightly coupled with what the app is meant for

import PySimpleGUI as sg
import os

from managers import *
from filenameTagger import *

import logging
logging.basicConfig(level=logging.DEBUG)


def buildWindow(options, taglist, imgwidget, block=False):
    # Layout
    menu = [["File", ["Load tag scheme...", "Apply tag changes..."]],
            ["Tools", [
                "Filenames to tags... (Merge)", "Filenames to tags... (Overwrite)"]],
            ["Help", ["About"]]
            ]

    rcolumn_layout = [
        [sg.Listbox(key='tags', values=taglist,
                    expand_y=True, expand_x=True)],
        [sg.Text("Tag:"), sg.Input(key="new_tag_value"), sg.Text("Type:"), sg.Combo(
            options, default_value=options[0], key='new_tag_type')],
        [sg.Button("Add tag", key='add_tag'), sg.Button(
            "Remove selected tag", key='remove_tag')]
    ]
    image_display = [[imgwidget, sg.Column(rcolumn_layout, expand_y=True)]]
    navbar = [sg.Button("Prev"), sg.Button("Next"), sg.InputText(
        os.getcwd(), enable_events=True, disabled=True, key="folder_browse"), sg.FolderBrowse("Change"), sg.Text("Nothing to save", key="status_text")]

    layout = [[sg.Menu(menu)], navbar, [sg.Frame('Display', image_display)]]
    window = sg.Window('Tag app', layout, resizable=True,
                       enable_close_attempted_event=True)

    return window


def windowInit(MImages, MTags, tagger):

    options = list(tagger.tagtypes.keys())
    options.append("default")

    first_tags = ["No images in this directory"] if MImages.err else MTags.get_tags(
        MImages.current())

    first_image = sg.Image("errorimg") if MImages.err else sg.Image(
        MImages.currentBytes().getvalue(), key='img')
    return buildWindow(options, first_tags, first_image, MImages.err)


def main():

    # setup managers
    MImages = ImageManager()
    if MImages.err:
        print("No images found")
    MTags = TagManager(os.getcwd())
    MTags.register_tag_change_callback(lambda: window['tags'].update(list(MTags.get_tags(MImages.current()))))
    tagger = FilenameTagger()

    window = windowInit(MImages, MTags, tagger)

    # Event loop
    while True:
        event, values = window.read()
        print("event", event)
        if event == sg.WIN_CLOSED:
            break
        elif event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT or event == 'Exit':
            if MTags.stale and sg.popup_yes_no("Overwrite tags.json?") == 'Yes':
                MTags.save_tags_file()
                print("Wrote tags")
            break
        elif event == "folder_browse":
            path = window['folder_browse'].get()
            MImages = ImageManager(path)
            if MImages.err:
                print("No images found")
            MTags = TagManager(path)

            # Rebuild window
            window.close()
            window = windowInit(MImages, MTags, tagger)
        elif event == "Prev" or event == "Next":
            try:
                MImages.prev() if event == "Prev" else MImages.next()
                window['img'].update(MImages.currentBytes().getvalue())
            except NoImagesException:
                logging.info("Cannot move between images, because there are none.")

        elif event == "add_tag":
            print("Adding:", window['new_tag_value'])
            value = window['new_tag_value'].get()
            type = window['new_tag_type'].get()
            MTags.add_tag(MImages.current(), value, type)
        elif event == "remove_tag":
            selected = window['tags'].get()
            print("Removing:", selected)
            MTags.remove_tags(MImages.current(), selected)

        elif event == "Filenames to tags... (Merge)":
            tags = tagger.parse_tags(MImages)
            MTags.merge_tags(tags)
        elif event == "Filenames to tags... (Overwrite)":
            tags = tagger.parse_tags(MImages)
            MTags.overwrite_tags(tags)
        elif event == "Apply tag changes...":
            MTags.write_tags_to_filenames(MImages, tagger)

        logging.debug(f'You entered {event}, {values}')


    window.close()


if __name__ == "__main__":
    main()
