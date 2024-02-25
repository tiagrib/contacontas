import dearpygui.dearpygui as dpg
from data import manipulation as manip

class TabClassifier():
	def __init__(self, win, tab, label = "Classificador"):
		self.tab = tab
		self.win = win
		self.cc = win.cc
		self.win.ids[tab] = label
		self.win.tabs[label] = tab
		self.class_clusters_n = 0
		self.clusters_n = 0
		self.selected_class = None
		self.txt_classif_assign_tag = None
		self.class_selected_tag = ""
		self.autoclasses_selected_rows = []
		with dpg.group(horizontal=True):
			with dpg.group(tag='grpClassificationOptions', width=self.win.PERW(30)):
				with dpg.group(horizontal=False):
					with dpg.group(tag='grpClassifControls'):
						self.class_clusters_n = dpg.add_drag_int(label="Clusters", callback=self.reclassify, tracked=False, default_value=self.clusters_n)
						dpg.add_button(label="Reclassify", callback=self.reclassify)
					dpg.add_text("Cluster Classification:")
					with dpg.group(tag='grpClasses', width=self.win.PERW(30)):
						self.create_classif_classes()
					dpg.add_separator()
					dpg.add_button(label="Assign Tag to selection", callback=self.assign_tag_to_classification)
					with dpg.group(tag='grpAssignTagToSelection', width=self.win.PERW(30)):
						self.create_ciassif_assign_tag_to_selection_input()
					dpg.add_separator()
					dpg.add_text("Existing Tags:")
					with dpg.group(tag='grpClassificationExistingTags'):
						self.create_class_tags_table()

			with dpg.group(tag='grpClassData', width=self.win.PERW(70)):
				self.create_class_data_table()


	def reclassify(self, sender=None, data=None):
		if sender!=None and data != None:
			if sender == self.class_clusters_n:
				self.clusters_n = data
				return
		dpg.delete_item('grpClassData', children_only=True)
		dpg.delete_item('grpClasses', children_only=True)
		self.cc.run_clustering_kmeans(clusters=self.clusters_n)
		self.create_classif_classes()
		self.create_class_data_table()
		
	
	def create_classif_classes(self):
		dpg.add_listbox(tag='lstClasses', items=list(self.cc.autoclasses.keys()), num_items=20, 
				  callback=self.update_class_data_table, parent='grpClasses')


	def update_class_data_table(self, Sender=None):
		if Sender is not None:
			print(dpg.get_value(Sender))
			selected = dpg.get_value(Sender)
			self.selected_class = selected
		dpg.delete_item('grpClassData', children_only=True)
		self.create_class_data_table()
		

	def assign_tag_to_classification(self, sender=None, data=None):
		tag = dpg.get_value(self.txt_classif_assign_tag)
		if tag is None:
			return
		class_indices = self.cc.autoclasses[self.selected_class]
		
		selected_indices = [ i for i, checkbox in zip(class_indices, self.autoclasses_selected_rows) if dpg.get_value(checkbox)]
		self.cc.data.set_tag_over_indices(selected_indices, tag)
		if not tag in self.cc.data.all_tags:
			self.cc.data.all_tags.append(tag)
		self.update_class_data_table()
		self.update_class_existing_tags_table()
		

	def update_class_data_table(self, Sender=None):
		if Sender is not None:
			print(dpg.get_value(Sender))
			selected = dpg.get_value(Sender)
			self.selected_class = selected
		dpg.delete_item('grpClassData', children_only=True)
		self.create_class_data_table()
		
	
	def update_class_existing_tags_table(self, Sender=None):		
		dpg.delete_item('grpClassificationExistingTags', children_only=True)
		self.create_class_tags_table()


	def create_class_tags_table(self):
		dpg.add_listbox(tag='lstClassifExistingTags', items=self.cc.data.all_tags, num_items=20, 
				  callback=self.classif_existing_tag_select, parent='grpClassificationExistingTags')
		

	def classif_existing_tag_select(self, Sender):
		self.class_selected_tag = dpg.get_value(Sender)
		self.update_txt_classif_assign_tag()
		

	def update_txt_classif_assign_tag(self):
		dpg.set_value(self.txt_classif_assign_tag, self.class_selected_tag)


	def create_ciassif_assign_tag_to_selection_input(self):
		self.txt_classif_assign_tag = dpg.add_input_text(default_value=self.class_selected_tag, parent='grpAssignTagToSelection')


	def create_class_data_table(self):
		with dpg.table(header_row=True, resizable=True, policy=dpg.mvTable_SizingStretchProp,
					borders_outerH=True, borders_innerV=True, borders_innerH=True, borders_outerV=True, parent='grpClassData'):
			dpg.add_table_column(label="Selected")
			dpg.add_table_column(label="Bank")
			dpg.add_table_column(label="Account")
			dpg.add_table_column(label="Tags")
			dpg.add_table_column(label="Description")
			dpg.add_table_column(label="Category")
			self.present_classes_data()
			

	def present_classes_data(self):
		self.autoclasses_selected_rows = []
		if self.selected_class is not None:
			for i in self.cc.autoclasses[self.selected_class]:
				m = self.cc.data.m.iloc[i]
				with dpg.table_row():
					tag_col = (255, 255, 255, 255)
					if manip.contains_tag(m, 'PayPal'):
						tag_col = (100, 150, 255, 255)
					if m.value < 0:
						val_col = (255,100,100, 255)
					else:
						val_col = (100,255,100, 255)
					self.autoclasses_selected_rows.append(dpg.add_checkbox(label="", default_value=True))
					dpg.add_text(m.bank, color=tag_col)
					dpg.add_text(m.account, color=tag_col)
					dpg.add_text(m.tags, color=tag_col)
					dpg.add_text(m.desc, color=tag_col)