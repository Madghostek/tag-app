import re
import io
import json
import os
import PIL.Image as Image
import logging

from classes import Tag, Img
from exceptions import NoImagesException

from filenameTagger import FilenameTagger


class ImageManager():
    supported_images = ['png', 'jpg', 'jpeg', 'gif']
    collection = []

    # @TODO: make sure this isn't needed, because cool iter interface should work
    def getAllImages(self):
        return self.collection

    def __init__(self, path=".", pattern=""):
        self.err = False
        self.index = 0

        r = re.compile(pattern)

        images = []
        for ext in self.supported_images:
            images.extend(Img(img) for img in os.listdir(path)
                          if img.endswith(ext) and r.match(img))

        self.collection = images

        if len(self.collection) == 0:
            self.err = True

    def next(self) -> Img:
        try:
            self.index = (self.index+1) % len(self.collection)
            return self.current()
        except ZeroDivisionError:
            raise NoImagesException

    def prev(self) -> Img:
        try:
            self.index = (self.index-1) % len(self.collection)
            return self.current()
        except ZeroDivisionError:
            raise NoImagesException
        
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
    
    def renameImage(self, image: Img, newName):
        if not newName:
            newName = f"no tags ({image.hash})"
        ext = os.path.splitext(image.fname)[1]
        os.rename(image.fname, newName+ext)

        image.fname = newName+ext


class TagManager():
    """
    Stores all known tags, also handles json file <-> tags.

    The mapping between images and tags is based on image hash,
    because filename can change.
    """

    tagChangedCallback = None

    def __init__(self, workingDir="./"):
        # this is the master tag storage, any up to date tag must be here
        # dict {image: Tag}
        self.stale = True
        self._workingDir = workingDir
        self._tags = self.load_tags_file()

    # decorator
    def ChangesTags(func):

        def wrapper_func(self, *args, **kwargs):
            ret = func(self, *args, **kwargs)
            if self.tagChangedCallback:
                self.tagChangedCallback()
            return ret
        return wrapper_func

    @ChangesTags
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

    def write_tags_to_filenames(self, imgManager: ImageManager, tagger: FilenameTagger) -> bool:
        """
        Update filenames of all loaded images according to tagging scheme

        Returns amount of files changed
        """
        if not self.stale:
            return 0

        changes = {}
        for image in imgManager:
            tags = self.get_tags(image)
            fname = tagger.tags_to_filename(list(tags))
            # save history in case of rollback
            old = image.fname
            imgManager.renameImage(image, fname)
            if old != image.fname:
                changes[image.hash] = {"old": old, "new": image.fname}
        self.save_tags_file()  # sync the json as well
        with open(self._workingDir+"/filename_changes.json", "w") as f:
            json.dump(changes, f)
        return len(changes)

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

    @ChangesTags
    def add_tag(self, targetImg, tag_value, tag_type):
        tag = Tag(tag_value, tag_type)
        if targetImg.hash in self._tags:
            self._tags[targetImg.hash].add(tag)
        else:
            self._tags[targetImg.hash] = set([tag])
        self.stale = True

    @ChangesTags
    def remove_tags(self, targetImg, targetTags: list[Tag]):
        for toRemove in targetTags:
            for validTag in self._tags[targetImg.hash]:
                if validTag == toRemove:
                    self._tags[targetImg.hash].discard(validTag)
                    break  # no other tag will match
        self.stale = True

    @ChangesTags
    def merge_tags(self, tags):
        for img in tags:
            if img.hash in self._tags:
                self._tags[img.hash] |= set(tags[img])
            else:
                self._tags[img.hash] = set(tags[img])
        self.stale = True

    @ChangesTags
    def overwrite_tags(self, tags):
        for img in tags:
            self._tags[img.hash] = set(tags[img])
        self.stale = True

    def register_tag_change_callback(self, callback: callable):
        self.tagChangedCallback = callback

    def get_tags(self, targetImg) -> list:
        return self._tags[targetImg.hash] if targetImg.hash in self._tags else []
