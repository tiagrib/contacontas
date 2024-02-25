
import dearpygui.dearpygui as dpg
from data import manipulation as manip

class TabMovements():
	def __init__(self, win, tab, label = "Movimentos"):
		self.tab = tab
		self.win = win
		self.cc = win.cc
		self.win.ids[tab] = label
		self.win.tabs[label] = tab
		self._filter_internal = 0
		with dpg.group(horizontal=True):
			with dpg.group(tag='grpSelectionPanel', width=self.win.PERW(10)):
				dpg.add_button(label="Show Non-internal Only", callback=self.set_non_internal_filter)
				dpg.add_button(label="Show Internal Only", callback=self.set_internal_only_filter)
				dpg.add_button(label="Show All", callback=self.set_internal_all_filter)
				dpg.add_listbox(tag='lstTags', items=self.cc.data.all_tags, num_items=20, callback=self.update_movs, parent='grpSelectionPanel')
			
			with dpg.group(horizontal=False):
				dpg.add_slider_int(tag='sldMovsDate', label="Filter by Date", max_value=len(self.cc.months), callback=self.update_movs)
				dpg.add_group(tag='grpMovsTable', width=self.win.PERW(90))
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