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

    # prepare tag descriptions
    comboboxTags = getTagTypesSummary(tagger.tagtypes)
    options = list(comboboxTags.keys())

    menu = [["File", ["Load tag scheme..."]],
            ["Tools", [
                "Filenames to tags... (Merge)", "Filenames to tags... (Overwrite)"]],
            ["Help", ["About"]]
            ]

    rcolumn_layout = [
        [sg.Listbox(key='tags', values=MTags.get_tags(MImages.current()),
                    expand_y=True, expand_x=True)],
        [sg.Text("Tag:"), sg.Input(key="new_tag_value"), sg.Text("Type:"), sg.Combo(
            options, default_value=options[0], key='new_tag_type')],
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
            MImages.prev()
            window['img'].update(MImages.currentBytes().getvalue())
            window['tags'].update(list(MTags.get_tags(MImages.current())))
        elif event == "Next":
            MImages.next()
            window['img'].update(MImages.currentBytes().getvalue())
            window['tags'].update(list(MTags.get_tags(MImages.current())))
        elif event == "add_tag":
            print("Adding:", window['new_tag_value'])
            value = window['new_tag_value'].get()
            type = window['new_tag_type'].get()
            MTags.add_tag(MImages.current(), Tag(value, type))
            window['tags'].update(list(MTags.get_tags(MImages.current())))
        elif event == "Filenames to tags... (Merge)":
            tags = tagger.parse_tags(MImages)
            MTags.merge_tags(tags)
            window['tags'].update(list(MTags.get_tags(MImages.current())))
        elif event == "Filenames to tags... (Overwrite)":
            tags = tagger.parse_tags(MImages)
            MTags.overwrite_tags(tags)
            window['tags'].update(list(MTags.get_tags(MImages.current())))
        print('You entered ', event, values)

    window.close()


if __name__ == "__main__":
    main()
