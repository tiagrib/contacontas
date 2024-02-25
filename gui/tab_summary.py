import matplotlib.pyplot as plt
from data import manipulation as manip
import numpy as np
import dearpygui.dearpygui as dpg
from matplotlib.backends.backend_agg import FigureCanvasAgg

class TabSummary():
	def __init__(self, win, tab, label = "Resumos"):
		self.tab = tab
		self.win = win
		self.cc = win.cc
		self.win.ids[tab] = label
		self.win.tabs[label] = tab
		self.plot_dpi = 100
		self.plot_perc_h = 80
		with dpg.group(horizontal=False):
			dpg.add_slider_int(tag='sldSummaryDate', label="View by Date", max_value=len(self.cc.months), callback=self.update_summary)
			dpg.add_group(tag='grpSummaryPlot', width=self.win.PERW(100))
		self.draw_plot()


	def draw_plot(self):
		self.fig = plt.figure(figsize=(self.win.PERW(100)/self.plot_dpi, self.win.PERH(self.plot_perc_h)/self.plot_dpi), dpi=self.plot_dpi)
		self.canvas = FigureCanvasAgg(self.fig)
		self.ax = self.fig.gca()
		self.canvas.draw()
		buf = self.canvas.buffer_rgba()
		image = np.asarray(buf)
		image = image.astype(np.float32) / 255

		with dpg.texture_registry():
			dpg.add_raw_texture(
				self.win.PERW(100), self.win.PERH(self.plot_perc_h), image, format=dpg.mvFormat_Float_rgba, id="tex_summary"
			)

		dpg.delete_item('grpPlot', children_only=True)

		with dpg.group(horizontal=False, parent='grpSummaryPlot'):
			dpg.add_image("tex_summary")


	def update_summary(self, Sender):
		date = self.cc.months[dpg.get_value('sldSummaryDate')]
		manip.set_internal_mask(self.cc.data.m, self._filter_internal)
		if date != 'ALL':
			manip.set_date_mask(self.cc.data.m, *date, accumulate=True)
		
		self.draw_plot()
