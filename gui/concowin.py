import dearpygui.dearpygui as dpg
from data import manipulation as manip

def window_resize_cb():
    global ccw
    ccw.window_resized()

def viewport_resize_cb():
    global ccw
    ccw.window_resized()

class ConCoWin:
	def __init__(self):
		self.ids = {}
		self.tabs = {}
		self.cc = None
		self.window_w = 1000
		self.window_h = 1000
		self.current_tab = "mov"
		self.selected_class = None
		self.class_selected_tag = ''
		self.clusters_n = 0
		self._filter_internal = 0

	def window_resized(self):
		self.window_w = dpg.get_viewport_client_width()
		self.window_h = dpg.get_viewport_client_height()
		dpg.set_item_width("ContaContas", width=self.PERW(100))
		dpg.set_item_height("ContaContas", height=self.PERH(100))
		dpg.set_item_width("grpSelectionPanel", width=self.PERW(20))
		dpg.set_item_width('grpMovsTable', width=self.PERW(80))
		dpg.set_item_width("grpClassificationOptions", width=self.PERW(30))
		dpg.set_item_width("grpClasses", width=self.PERW(30))
		dpg.set_item_width('grpClassData', width=self.PERW(70))

	def PERW(self, percentage):
		if isinstance(percentage,int):
			return int((percentage/100.0)*self.window_w)
		return int(percentage*self.window_w)
	
	def PERH(self, percentage):
		if isinstance(percentage,int):
			return int((percentage/100.0)*self.window_h)
		return int(percentage*self.window_h)

	def create_table_tab(self, tab, tag):
		self.ids[tab] = tag
		self.tabs[tag] = tab

	def create_tab_resumos(self, tab):
		self.create_table_tab(tab, "Resumos")

	def create_tab_movimentos(self, tab):

		with dpg.group(horizontal=True):
			with dpg.group(tag='grpSelectionPanel', width=self.PERW(10)):
				dpg.add_button(label="Show Non-internal Only", callback=self.set_non_internal_filter)
				dpg.add_button(label="Show Internal Only", callback=self.set_internal_only_filter)
				dpg.add_button(label="Show All", callback=self.set_internal_all_filter)
				dpg.add_listbox(tag='lstTags', items=self.cc.data.all_tags, num_items=20, callback=self.update_movs, parent='grpSelectionPanel')
			
			with dpg.group(horizontal=False):
				dpg.add_slider_int(tag='sldMovsDate', label="Filter by Date", max_value=len(self.cc.months), callback=self.update_movs)
				dpg.add_group(tag='grpMovsTable', width=self.PERW(90))
			self.create_movs_table()

	def create_movs_table(self):
		with dpg.group(horizontal=False, parent='grpMovsTable'):
			date = self.cc.months[dpg.get_value('sldMovsDate')]
			dpg.add_text(f"Date segment: {date[0]}{date[1]}")
			with dpg.table(header_row=True, resizable=True, policy=dpg.mvTable_SizingStretchProp,
						borders_outerH=True, borders_innerV=True, borders_innerH=True, borders_outerV=True):
				dpg.add_table_column(label="Bank")
				dpg.add_table_column(label="Account")
				dpg.add_table_column(label="Date")
				dpg.add_table_column(label="Tags")
				dpg.add_table_column(label="Internal")
				dpg.add_table_column(label="Value")
				dpg.add_table_column(label="Description")
				self.present_movs()

	def set_non_internal_filter(self, sender):
		self._filter_internal = 1
		self.update_movs(sender)

	def set_internal_only_filter(self, sender):
		self._filter_internal = 2
		self.update_movs(sender)

	def set_internal_all_filter(self, sender):
		self._filter_internal = 0
		self.update_movs(sender)


	def update_movs(self, Sender):
		tag = dpg.get_value('lstTags')
		date = self.cc.months[dpg.get_value('sldMovsDate')]
		manip.set_internal_mask(self.cc.data.m, self._filter_internal)
		if tag != "<ANY>":
			manip.set_tag_mask(self.cc.data.m, tag, accumulate=True)
		if date != 'ALL':
			manip.set_date_mask(self.cc.data.m, *date, accumulate=True)
		dpg.delete_item('grpMovsTable', children_only=True)
		self.create_movs_table()

	def classif_existing_tag_select(self, Sender):
		self.class_selected_tag = dpg.get_value(Sender)
		self.update_txt_classif_assign_tag()

	def create_tab_classificador(self, tab):
		with dpg.group(horizontal=True):
			with dpg.group(tag='grpClassificationOptions', width=self.PERW(30)):
				with dpg.group(horizontal=False):
					with dpg.group(tag='grpClassifControls'):
						self.class_clusters_n = dpg.add_drag_int(label="Clusters", callback=self.reclassify, tracked=False, default_value=self.clusters_n)
						dpg.add_button(label="Reclassify", callback=self.reclassify)
					dpg.add_text("Cluster Classification:")
					with dpg.group(tag='grpClasses', width=self.PERW(30)):
						self.create_classif_classes()
					dpg.add_separator()
					dpg.add_button(label="Assign Tag to selection", callback=self.assign_tag_to_classification)
					with dpg.group(tag='grpAssignTagToSelection', width=self.PERW(30)):
						self.create_ciassif_assign_tag_to_selection_input()
					dpg.add_separator()
					dpg.add_text("Existing Tags:")
					with dpg.group(tag='grpClassificationExistingTags'):
						self.create_class_tags_table()

			with dpg.group(tag='grpClassData', width=self.PERW(70)):
				self.create_class_data_table()

	def create_ciassif_assign_tag_to_selection_input(self):
		self.txt_classif_assign_tag = dpg.add_input_text(default_value=self.class_selected_tag, parent='grpAssignTagToSelection')

	def update_txt_classif_assign_tag(self):
		dpg.set_value(self.txt_classif_assign_tag, self.class_selected_tag)

	def assign_tag_to_classification(self, sender=None, data=None):
		tag = dpg.get_value(self.txt_classif_assign_tag)
		class_indices = self.cc.autoclasses[self.selected_class]
		
		selected_indices = [ i for i, checkbox in zip(class_indices, self.autoclasses_selected_rows) if dpg.get_value(checkbox)]
		self.cc.data.set_tag_over_indices(selected_indices, tag)
		if not tag in self.cc.data.all_tags:
			self.cc.data.all_tags.append(tag)
		self.update_class_data_table()
		self.update_class_existing_tags_table()


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

	def create_class_tags_table(self):
		dpg.add_listbox(tag='lstClassifExistingTags', items=self.cc.data.all_tags, num_items=20, 
				  callback=self.classif_existing_tag_select, parent='grpClassificationExistingTags')


	def create_classif_classes(self):
		dpg.add_listbox(tag='lstClasses', items=list(self.cc.autoclasses.keys()), num_items=20, 
				  callback=self.update_class_data_table, parent='grpClasses')

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

	def present_movs(self):
		for m in self.cc.data.m.itertuples():
			if m.mask:
				with dpg.table_row():
					tag_col = (255, 255, 255, 255)
					if manip.contains_tag(m, 'PayPal'):
						tag_col = (100, 150, 255, 255)
					if m.value < 0:
						val_col = (255,100,100, 255)
					else:
						val_col = (100,255,100, 255)
					dpg.add_text(m.bank, color=tag_col)
					dpg.add_text(m.account, color=tag_col)
					dpg.add_text(f"{m.date.year}-{m.date.month}-{m.date.day}", color=tag_col)
					dpg.add_text(m.tags, color=tag_col)
					dpg.add_text(m.internal, color=tag_col)
					dpg.add_text(m.value, color=val_col)
					dpg.add_text(m.desc, color=tag_col)

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
					

	async def run(self, contacontas):
		debug = True
		self.cc = contacontas
		global ccw
		ccw = self
		dpg.create_context()
		if debug:
			dpg.configure_app(manual_callback_management=True)

		with dpg.item_handler_registry(tag="window_handler"):
			dpg.add_item_resize_handler(callback=viewport_resize_cb)

		with dpg.window(tag="ContaContas", label="Conta-Contas", width=self.window_w, height=self.window_h):

			with dpg.tab_bar(tag="tabSpaces"):
				with dpg.tab(label='Resumos', tag='Resumos') as tab:
					self.create_tab_resumos(tab)
				
				with dpg.tab(label='Movimentos', tag='Movimentos') as tab:
					self.create_tab_movimentos(tab)

				with dpg.tab(label='Classificador', tag='Classificador') as tab:
					self.create_tab_classificador(tab)
					pass

		dpg.set_value("tabSpaces", "Movimentos")
		dpg.bind_item_handler_registry("ContaContas", "window_handler")
		dpg.create_viewport(title='Conta-Contas', width=self.window_w, height=self.window_h, resizable=True)
		dpg.set_viewport_resize_callback(viewport_resize_cb)
		dpg.setup_dearpygui()
		dpg.show_viewport()
		if debug:
			while dpg.is_dearpygui_running():
				jobs = dpg.get_callback_queue() # retrieves and clears queue
				dpg.run_callbacks(jobs)
				dpg.render_dearpygui_frame()
		else:
			dpg.set_primary_window("ContaContas", True)
			dpg.start_dearpygui()
		dpg.destroy_context()

	
					
				