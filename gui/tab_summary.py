from multiprocessing import Lock
import matplotlib.pyplot as plt
from data import manipulation as manip
from matplotlib.pyplot import cm
import numpy as np
import dearpygui.dearpygui as dpg
from matplotlib.backends.backend_agg import FigureCanvasAgg


class TabSummary:
    def __init__(self, win, tab, label="Resumos"):
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
            dpg.add_slider_int(tag="sldSummaryDate", label="View by Date", max_value=len(self.cc.months) - 1, callback=self.update_summary)
            dpg.add_group(tag="grpSummaryPlot", width=self.win.PERW(100))
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
            self.fig.set_size_inches(self.win.PERW(100) / self.plot_dpi, self.win.PERH(self.plot_perc_h) / self.plot_dpi, forward=True)
            self.update_plot()

    def make_plot(self):
        print("make_plot")
        self.fig = plt.figure(figsize=(self.win.PERW(100) / self.plot_dpi, self.win.PERH(self.plot_perc_h) / self.plot_dpi), dpi=self.plot_dpi)
        self.axes = self.fig.add_subplot(111)
        self.canvas = FigureCanvasAgg(self.fig)
        self.ax = self.fig.gca()

    def update_plot(self):
        print("update_plot start")
        try:
            if not self.resize_mutex.acquire(block=False):
                print("update_plot: mutex locked")
                return

            print("update_plot redraw chart")
            self.canvas.draw()
            image = np.asarray(self.canvas.buffer_rgba())
            image = image.flatten().astype(np.float32) / 255.0
            width, height = self.win.PERW(100), self.win.PERH(self.plot_perc_h)

            # image = np.frombuffer(self.canvas.tostring_rgb(), dtype=np.uint8)
            # image = image.reshape(self.canvas.get_width_height()[::-1] + (3,)).flatten()

            try:
                print("update_plot: Delete existing image")
                dpg.delete_item("grpSummaryPlot", children_only=True)
                dpg.delete_item("tex_summary")

                print("update_plot: creating texture")
                with dpg.texture_registry():
                    # dpg.add_dynamic_texture(width, height, default_value=image, tag="tex_summary")
                    dpg.add_raw_texture(width=width, height=height, default_value=image, format=dpg.mvFormat_Float_rgba, tag="tex_summary")

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
        date = self.cc.months[dpg.get_value("sldSummaryDate")]
        # manip.set_internal_mask(self.cc.data.m, self._filter_internal)
        self.axes.clear()
        if date == "ALL":
            self.plot_full_summary()
            self.update_plot()
        else:
            # manip.set_date_mask(self.cc.data.m, *date, accumulate=True)
            self.plot_monthly_summary(date)
            self.update_plot()
            pass

    def plot_monthly_summary(self, date):
        x_values = range(31)
        acc_colors = dict(zip(self.cc.over.accounts_monthly.keys(), cm.rainbow(np.linspace(0, 1, len(self.cc.over.accounts_monthly)))))
        for account in self.cc.over.accounts_monthly:
            acc_data = np.zeros(len(x_values))
            month_overview = self.cc.over.accounts_monthly[account][date]
            for d in x_values:
                acc_data[d] = month_overview.data[month_overview.data["date"].dt.day == d].value.sum()
            acc_name = "ALL" if account is None else f"{account.bank.name}.{account.name}"
            self.axes.bar(x_values, acc_data, label=acc_name, color=acc_colors[account])
        xticks = [f"{d + 1}" for d in x_values]
        self.axes.set_xticks(x_values, xticks)
        self.fig.legend()

    def plot_full_summary(self):
        x_labels = self.cc.months[1:]
        x_values = range(len(x_labels))
        acc_colors = dict(zip(self.cc.over.accounts_monthly.keys(), cm.rainbow(np.linspace(0, 1, len(self.cc.over.accounts_monthly)))))
        for account in self.cc.over.accounts_monthly:
            acc_data = np.zeros(len(x_values))
            for i, am in enumerate(self.cc.over.accounts_monthly[account].items()):
                acc_data[i] = am[1].sum
            acc_name = "ALL" if account is None else f"{account.bank.name}.{account.name}"
            self.axes.plot(x_values, acc_data, label=acc_name, color=acc_colors[account])
        xticks = [f"{m}/{y}" for m, y in x_labels]
        self.axes.set_xticks(x_values, xticks)
        self.fig.legend()
