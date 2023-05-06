#!/usr/bin/python3

import PySimpleGUI as sg
import os

from managers import *
from filenameTagger import *


def main():

    # setup managers
    MImages = ImageManager(os.getcwd())
    MTags = TagManager()
    tagger = FilenameTagger()

    # maybe add loading bar?
    MTags.tags = tagger.parse_tags(MImages)

    # prepare tag descriptions
    comboboxTags = getTagTypesSummary(tagger.tagtypes)
    options = list(comboboxTags.keys())

    menu = [["File", ["Load tag scheme..."]],
            ["Tools", [
                "Filenames to tags... (Merge)", "Filenames to tags... (Overwrite)"]],
            ["Help", ["About"]]
            ]

    rcolumn_layout = [
        [sg.Listbox(key='tags', values=MTags.tags[MImages.current()],
                    expand_y=True, expand_x=True)],
        [sg.Text("Tag:"), sg.Input(key="new_tag_value"), sg.Text("Type:"), sg.Combo(
            options, default_value=options[0])],
        [sg.Button("Add tag", key='add_tag'), sg.Button(
            "Remove selected tag", key='remove_tag')]
    ]

    image_display = [[sg.Image(MImages.currentBytes().getvalue(
    ), key='img'), sg.Column(rcolumn_layout, expand_y=True)]]
    navbar = [sg.Button("Prev"), sg.Button("Next"), sg.Text(
        os.getcwd()), sg.FolderBrowse("Change")]

    layout = [[sg.Menu(menu)], navbar, [sg.Frame('Display', image_display)]]
    window = sg.Window('Tag app', layout, resizable=True)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:  # if user closes window or clicks cancel
            if sg.popup_yes_no("Overwrite tags.json?") == 'Yes':
                MTags.save_tags_file()
                print("Wrote tags")
            break
        elif event == "Prev":
            window['img'].update(MImages.prev().getvalue())
            window['tags'].update(MTags.tags[MImages.current()])
        elif event == "Next":
            window['img'].update(MImages.next().getvalue())
            window['tags'].update(MTags.tags[MImages.current()])
        elif event == "add_tag":
            print("Adding:", window['new_tag_value'])
        elif event == "Filenames to tags... (Merge)":
            for image in ImageManager:
                tags = tagger.parse_tags(MImages)
                MTags.merge_tags(tags)
        elif event == "Filenames to tags... (Overwrite)":
            for image in ImageManager:
                tags = tagger.parse_tags(MImages)
                MTags.overwrite_tags(tags)
        print('You entered ', event, values)

    window.close()


if __name__ == "__main__":
    main()
