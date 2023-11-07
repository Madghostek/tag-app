import yaml
import os

from classes import Tag, Img


class FilenameTagger():
    """
    Handles filename<->tags
    """

    def __init__(self):
        try:
            self.load_config()
        except FileNotFoundError:
            print("Warning: config not found")

    def load_config(self, path="./") -> list:
        """
        Loads tagging scheme definition - known tag types and separator.
        Tags are strings separated by some character, optinally
        wrapped in brackets or other stuff to tell types apart.
        """
        with open(path+"config.yaml", "r") as conf:
            self._config_raw = yaml.safe_load(conf)
        self.tagtypes = self._config_raw['tag types']
        self.separator = self._config_raw['tag separator']

    def filename_to_tags(self, fname):
        """
        filename can be with extension
        """

        tags = []
        name, _ = os.path.splitext(fname)
        for tag in name.split(self.separator):
            # figure out if this tag matches a specific type
            for tagtype, wraps in self.tagtypes.items():
                startlen, endlen = len(wraps[0]), len(wraps[1])
                if tag[:startlen] == wraps[0] and tag[-endlen-1:] == wraps[1]:
                    tags.append(
                        Tag(tag[startlen:-endlen-1], tagtype))
            else:
                tags.append(Tag(tag))

        return tags

    def tags_to_filename(self, taglist: list[Tag], sortTags=True):
        fname = []
        if sortTags:
            taglist.sort(key=lambda tag: tag.typeOrder)
        for tag in taglist:
            try:
                brackets = self.tagtypes[tag.type]['brackets']
            except KeyError:
                brackets = ['', '']  # no brackets
            fname.append(brackets[0]+tag.value+brackets[1])
        return self.separator.join(fname)

    def parse_tags(self, images: list[Img]):
        return {image: self.filename_to_tags(
            image.fname) for image in images}


def getTagTypesSummary(tagtypes):
    # returns dict of description like [author]: ["[","]"]
    res = {"default": ["", ""]}
    for t in tagtypes:
        pattern = tagtypes[t][0]+t+tagtypes[t][1]
        res[pattern] = tagtypes[t]
    return res
