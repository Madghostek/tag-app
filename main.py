#!/usr/bin/python3

import PySimpleGUI as sg
import PIL.Image as Image
import os
import re
import collections
import io
import yaml

class ImageManager():
	supported_images = ['png','jpg','jpeg','gif']

	def __init__(self, path, pattern=""):
		self.index = 0

		r = re.compile(pattern)
		
		images = []
		for ext in self.supported_images:
			images.extend(img for img in os.listdir(path) if img.endswith(ext) and r.match(img))

		self.collection = images
		try:
			self.load_config()
		except FileNotFoundError:
			sg.popup("Warning: config not found")


	def load_config(self) -> list:
		with open("config.yaml","r") as conf:
			self._config_raw = yaml.safe_load(conf)
		self.tagtypes = self._config_raw['tag types']
		self.separator = self._config_raw['tag separator']


	def next(self):
		self.index = (self.index+1)%len(self.collection)
		return self.currentBytes()

	def prev(self):
		self.index = (self.index-1)%len(self.collection)
		return self.currentBytes()

	def currentBytes(self):
		bio = io.BytesIO()
		print("Selecting",self.collection[self.index])
		img = Image.open(self.collection[self.index])
		img.thumbnail((500,500))
		img.save(bio, format="PNG")
		return bio

	def getTags(self):
		name,_ = os.path.splitext(self.collection[self.index])
		taglist = name.split(self.separator)
		for i in range(len(taglist)):
			tag = taglist[i]
			for category, wrap in zip(self.tagtypes.keys(),self.tagtypes.values()):
				if wrap[0] in tag and wrap[1] in tag: # cry about it
					print(tag,"is",category)


		return taglist
	
	def __iter__(self):
		return iter(self.collection)

def getTagTypesSummary(tagtypes):
	# returns dict of description like [author]: ["[","]"]
	res = {"default":["",""]}
	for t in tagtypes:
		pattern = tagtypes[t][0]+t+tagtypes[t][1]
		res[pattern] = tagtypes[t]
	return res


def main():

	images = ImageManager(os.getcwd())
	comboboxTags = getTagTypesSummary(images.tagtypes)

	menu = [["File",["Load tag scheme..."]],
			  ["Help",["About"]]
			]

	rcolumn_layout=[
			[sg.Listbox(key='tags',values=images.getTags(),expand_y=True,expand_x=True)],
			[sg.Text("Tag:"),sg.Input(key="new_tag_value"),sg.Text("Type:"),sg.Combo(list(comboboxTags.keys()), default_value = list(comboboxTags.keys())[0])],
			[sg.Button("Add tag", key='add_tag'),sg.Button("Remove selected tag", key='remove_tag')]
			]

	image_display = [[sg.Image(images.currentBytes().getvalue(),key='img'),sg.Column(rcolumn_layout,expand_y=True)]]
	navbar = [sg.Button("Prev"),sg.Button("Next"),sg.Text(os.getcwd()),sg.FolderBrowse("Change")]
	
	layout = [[sg.Menu(menu)],navbar,[sg.Frame('Display',image_display)]]
	window = sg.Window('Tag app',layout,resizable=True)

	while True:
		event, values = window.read()
		if event == sg.WIN_CLOSED: # if user closes window or clicks cancel
			break
		elif event == "Prev":
			window['img'].update(images.prev().getvalue())
			window['tags'].update(images.getTags())
		elif event == "Next":
			window['img'].update(images.next().getvalue())
			window['tags'].update(images.getTags())
		elif event == "add_tag":
			print("Adding:",window['new_tag_value'])
		print('You entered ', event, values)

	window.close()

if __name__=="__main__":
	main()