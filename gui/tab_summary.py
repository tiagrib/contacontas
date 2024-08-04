
from multiprocessing import Lock
import matplotlib.pyplot as plt
from data import manipulation as manip
import numpy as np
import dearpygui.dearpygui as dpg
from matplotlib.backends.backend_agg import FigureCanvasAgg

class TabSummary():
	def __init__(self, win, tab, label = "Resumos"):
		self.tab = tab
		self.resize_mutex = Lock()
		self.win = win
		self.cc = win.cc
		self.win.ids[tab] = label
		self.win.tabs[label] = tab
		self.plot_dpi = 100
		self.plot_perc_h = 80
		self.current_width = 0
		self.current_height = 0
		with dpg.group(horizontal=False):
			dpg.add_slider_int(tag='sldSummaryDate', label="View by Date", max_value=len(self.cc.months), callback=self.update_summary)
			dpg.add_group(tag='grpSummaryPlot', width=self.win.PERW(100))
		self.make_plot()
		self.update_summary()

	def window_resized(self):
		if self.current_width != self.win.PERW(100) or self.current_height != self.win.PERH(100):
			print("window_resized")
			self.current_width = self.win.PERW(100)
			self.current_height = self.win.PERH(100)
			if dpg.does_item_exist("tex_summary"):
				dpg.set_item_width("tex_summary", self.win.PERW(100))
				dpg.set_item_height("tex_summary", self.win.PERH(100))
			self.fig.set_size_inches(self.win.PERW(100)/self.plot_dpi, self.win.PERH(self.plot_perc_h)/self.plot_dpi, forward=True)
			#self.update_plot()


	def make_plot(self):
		print("make_plot")
		self.fig = plt.figure(figsize=(self.win.PERW(100)/self.plot_dpi, self.win.PERH(self.plot_perc_h)/self.plot_dpi), dpi=self.plot_dpi)
		self.axes = self.fig.add_subplot(111)
		self.canvas = FigureCanvasAgg(self.fig)
		self.ax = self.fig.gca()

	def update_plot(self):
		print("update_plot")
		try:
			if not self.resize_mutex.acquire(block=False):
				print("update_plot: mutex locked")
				return
			
			self.canvas.draw()
			buf = self.canvas.buffer_rgba()
			image = np.asarray(buf)
			image = image.astype(np.float32) / 255
			image = image.flatten().astype(np.uint8)
			width, height = self.win.PERW(100), self.win.PERH(self.plot_perc_h)
			
			if dpg.does_item_exist("tex_summary"):
				print("update_plot: updating texture")
				# Update the existing texture instead of recreating it
				dpg.configure_item("tex_summary", width=width, height=height)
				dpg.set_value("tex_summary", image)
			else:
				print("update_plot: creating texture")
				try:
					with dpg.texture_registry():
						dpg.add_dynamic_texture(width, height, default_value=image, tag="tex_summary")
				except Exception as e:
					print(e)

				try:
					print("update_plot: adding texture to group")
					# Ensure the image is added to 'grpSummaryPlot' only if it doesn't exist
					if not dpg.does_item_exist("grpSummaryPlot_tex_summary"):
						dpg.add_image("tex_summary", parent="grpSummaryPlot", tag="grpSummaryPlot_tex_summary")
				except Exception as e:
					print(e)
			self.resize_mutex.release()
		except Exception as e:
			print(e)
			


	def update_summary(self, Sender=None):
		print("update_summary")
		date = self.cc.months[dpg.get_value('sldSummaryDate')]
		#manip.set_internal_mask(self.cc.data.m, self._filter_internal)
		self.axes.clear()
		if date == 'ALL':
			self.plot_full_summary()
			self.update_plot()
		else:
			#manip.set_date_mask(self.cc.data.m, *date, accumulate=True)
			pass
		

	def plot_full_summary(self):
		x_labels = self.cc.months[1:]
		x_values = range(len(x_labels))
		for account in self.cc.over.accounts_monthly:
			acc_data = np.zeros(len(x_values))
			for i, am in enumerate(self.cc.over.accounts_monthly[account].items()):
				acc_data[i] = am[1].sum
			acc_name = "ALL" if account is None else f"{account.bank.name}.{account.name}"
			self.axes.plot(x_values, acc_data, label=acc_name)
		xticks = [f"{m}/{y}" for m, y in x_labels]
		self.axes.set_xticks(x_values, xticks)
		self.fig.legend()
