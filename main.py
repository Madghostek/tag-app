#!/usr/bin/python3

import PySimpleGUI as sg
import PIL.Image as Image
import os
import re
import io
import yaml
import json


class Tag():
    def __init__(self, value, type="default"):
        self.value = value
        self.type = type

    def __repr__(self):
        return f"({self.type}) {self.value}"


class FilenameTagger():
    """
    Handles filename<->tags
    """

    def __init__(self):
        try:
            self.load_config()
        except FileNotFoundError:
            sg.popup("Warning: config not found")

    def load_config(self) -> list:
        """
        Loads tagging scheme definition - known tag types and separator.
        Tags are strings separated by some character, optinally wrapped in brackets or other stuff
        to tell types apart.
        """
        with open("config.yaml", "r") as conf:
            self._config_raw = yaml.safe_load(conf)
        self.tagtypes = self._config_raw['tag types']
        self.separator = self._config_raw['tag separator']

    def filename_to_tags(self, fname):
        """
        filename can be with extension
        """

        tags = []

        # name,_ = os.path.splitext(self.collection[self.index])
        name, _ = os.path.splitext(fname)
        # taglist = name.split(self.separator)
        for tag in name.split(self.separator):
            # figure out if this tag matches a specific type
            for tagtype, wraps in self.tagtypes.items():
                startlen, endlen = len(wraps[0]), len(wraps[1])
                if tag[:startlen] == wraps[0] and tag[-endlen-1:] == wraps[1]:
                    tags.append(
                        Tag(tag[startlen+1:-endlen-1], tagtype))
            else:
                tags.append(Tag(tag))

        return tags


class TagManager():
    """
    Stores all known tags, also handles json file <-> tags.
    """

    def __init__(self):
        # this is the master tag storage, any up to date tag must be here
        self.tags = self.load_tags_file()

    def load_tags_file(self, path="tags.json"):
        tags = {}
        with open(path, "r") as f:
            jsontags = json.load(f)
        for image in jsontags:
            tagarray = jsontags[image]
            tags[image] = []
            for tag in tagarray:
                if 'type' not in tag:
                    tag['type'] = 'default'
                tags[image].append(Tag(tag['value'], tag['type']))

        print(f"Loaded tags from '{path}'")
        return tags

    def save_tags_file(self, path="tags.json"):
        tagjson = {}

        for image in self.tags:
            tagjson[image] = []
            for tag in self.tags[image]:
                builded = {}
                builded['type'] = tag.type
                builded['value'] = tag.value
                tagjson[image].append(builded)

        with open(path, "w") as f:
            json.dump(tagjson, f)

        print(f"Saved tags to '{path}'")


class ImageManager():
    supported_images = ['png', 'jpg', 'jpeg', 'gif']

    def __init__(self, path, pattern=""):
        self.index = 0

        r = re.compile(pattern)

        images = []
        for ext in self.supported_images:
            images.extend(img for img in os.listdir(path)
                          if img.endswith(ext) and r.match(img))

        self.collection = images

    def next(self):
        self.index = (self.index+1) % len(self.collection)
        return self.currentBytes()

    def prev(self):
        self.index = (self.index-1) % len(self.collection)
        return self.currentBytes()

    def currentBytes(self):
        bio = io.BytesIO()
        print("Selecting", self.collection[self.index])
        img = Image.open(self.collection[self.index])
        img.thumbnail((500, 500))
        img.save(bio, format="PNG")
        return bio

    def current(self):
        return self.collection[self.index]

    def __iter__(self):
        return iter(self.collection)


def getTagTypesSummary(tagtypes):
    # returns dict of description like [author]: ["[","]"]
    res = {"default": ["", ""]}
    for t in tagtypes:
        pattern = tagtypes[t][0]+t+tagtypes[t][1]
        res[pattern] = tagtypes[t]
    return res


def main():

    images = ImageManager(os.getcwd())
    tags = TagManager()
    tagger = FilenameTagger()
    comboboxTags = getTagTypesSummary(tagger.tagtypes)

    tags = {image: tagger.filename_to_tags(image) for image in images}

    menu = [["File", ["Load tag scheme..."]],
            ["Help", ["About"]]
            ]

    rcolumn_layout = [
        [sg.Listbox(key='tags', values=tags[images.current()],
                    expand_y=True, expand_x=True)],
        [sg.Text("Tag:"), sg.Input(key="new_tag_value"), sg.Text("Type:"), sg.Combo(
            list(comboboxTags.keys()), default_value=list(comboboxTags.keys())[0])],
        [sg.Button("Add tag", key='add_tag'), sg.Button(
            "Remove selected tag", key='remove_tag')]
    ]

    image_display = [[sg.Image(images.currentBytes().getvalue(
    ), key='img'), sg.Column(rcolumn_layout, expand_y=True)]]
    navbar = [sg.Button("Prev"), sg.Button("Next"), sg.Text(
        os.getcwd()), sg.FolderBrowse("Change")]

    layout = [[sg.Menu(menu)], navbar, [sg.Frame('Display', image_display)]]
    window = sg.Window('Tag app', layout, resizable=True)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:  # if user closes window or clicks cancel
            tags.save_tags_file()
            break
        elif event == "Prev":
            window['img'].update(images.prev().getvalue())
            window['tags'].update(tags[images.current()])
        elif event == "Next":
            window['img'].update(images.next().getvalue())
            window['tags'].update(tags[images.current()])
        elif event == "add_tag":
            print("Adding:", window['new_tag_value'])
        print('You entered ', event, values)

    window.close()


if __name__ == "__main__":
    main()
