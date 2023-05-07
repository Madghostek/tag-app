import re
import io
import json
import os
import PIL.Image as Image

from classes import Tag, Img


class TagManager():
    """
    Stores all known tags, also handles json file <-> tags.

    The mapping between images and tags is based on image hash,
    because filename can change.
    """

    def __init__(self, workingDir="./"):
        # this is the master tag storage, any up to date tag must be here
        # dict {image: Tag}
        self.stale = True
        self._workingDir = workingDir
        self._tags = self.load_tags_file()

    def load_tags_file(self, tagsname="tags.json") -> dict:
        tags = {}
        try:
            with open(self._workingDir+"/"+tagsname, "r") as f:
                jsontags = json.load(f)
        except FileNotFoundError:
            print("tags.json not found!")
            self.stale = False
            return tags
        for image in jsontags:
            tagarray = jsontags[image]
            tags[image] = set()
            for tag in tagarray:
                if 'type' not in tag:
                    tag['type'] = 'default'
                tags[image].add(Tag(tag['value'], tag['type']))

        print(f"Loaded tags from '{self._workingDir+tagsname}'")
        self.stale = False
        return tags

    def save_tags_file(self, tagsname="tags.json"):
        tagjson = {}
        for image in self._tags:
            tagjson[image] = []
            for tag in self._tags[image]:
                builded = {}
                builded['type'] = tag.type
                builded['value'] = tag.value
                tagjson[image].append(builded)

        with open(self._workingDir+"/"+tagsname, "w") as f:
            json.dump(tagjson, f)

        print(f"Saved tags to '{self._workingDir+tagsname}'")
        self.stale = False

    def add_tag(self, targetImg, tag: Tag):
        if targetImg.hash in self._tags:
            self._tags[targetImg.hash].add(tag)
        else:
            self._tags[targetImg.hash] = set([tag])
        self.stale = True

    def remove_tags(self, targetImg, targetTags: list[Tag]):
        for toRemove in targetTags:
            for validTag in self._tags[targetImg.hash]:
                if validTag == toRemove:
                    self._tags[targetImg.hash].discard(validTag)
                    break  # no other tag will match
        self.stale = True

    def merge_tags(self, tags):
        for img in tags:
            if img in self._tags:
                self._tags[img.hash] |= tags[img.hash]
            else:
                self._tags[img.hash] = tags[img.hash]
        self.stale = True

    def overwrite_tags(self, tags):
        for img in tags:
            self._tags[img.hash] = tags[img.hash]
        self.stale = True

    def get_tags(self, targetImg) -> list:
        return self._tags[targetImg.hash] if targetImg.hash in self._tags else []


class ImageManager():
    supported_images = ['png', 'jpg', 'jpeg', 'gif']

    def __init__(self, path=".", pattern=""):
        self.err = False
        self.index = 0

        r = re.compile(pattern)

        images = []
        for ext in self.supported_images:
            images.extend(Img(path+"/"+img) for img in os.listdir(path)
                          if img.endswith(ext) and r.match(img))

        self.collection = images

        if len(self.collection) == 0:
            self.err = True

    def next(self) -> Img:
        self.index = (self.index+1) % len(self.collection)
        return self.current()

    def prev(self) -> Img:
        self.index = (self.index-1) % len(self.collection)
        return self.current()

    def currentBytes(self) -> io.BytesIO:
        bio = io.BytesIO()
        print("Selecting", self.collection[self.index])
        img = Image.open(self.collection[self.index].fname)
        img.thumbnail((500, 500))
        img.save(bio, format="PNG")
        return bio

    def current(self) -> Img:
        return self.collection[self.index]

    def __iter__(self):
        return iter(self.collection)
