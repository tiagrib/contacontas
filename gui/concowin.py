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
		self.window_w = 1920
		self.window_h = 1080
		self.current_tab = "mov"


	def window_resized(self):
		import dearpygui.dearpygui as dpg
		self.window_w = dpg.get_viewport_client_width()
		self.window_h = dpg.get_viewport_client_height()
		dpg.set_item_width("ContaContas", width=self.PERW(100))
		dpg.set_item_height("ContaContas", height=self.PERH(100))
		dpg.set_item_width("grpSelectionPanel", width=self.PERW(20))
		dpg.set_item_width('grpMovsTable', width=self.PERW(80))
		dpg.set_item_width("grpClassificationOptions", width=self.PERW(30))
		dpg.set_item_width("grpClasses", width=self.PERW(30))
		dpg.set_item_width('grpClassData', width=self.PERW(70))
		self.tab_resumos.window_resized()


	def PERW(self, percentage):
		if isinstance(percentage,int):
			return int((percentage/100.0)*self.window_w)
		return int(percentage*self.window_w)
	

	def PERH(self, percentage):
		if isinstance(percentage,int):
			return int((percentage/100.0)*self.window_h)
		return int(percentage*self.window_h)


	async def run(self, contacontas):
		import dearpygui.dearpygui as dpg
		from .tab_classifier import TabClassifier
		from .tab_movements import TabMovements
		from .tab_summary import TabSummary

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
					self.tab_resumos = TabSummary(self, tab)
				
				with dpg.tab(label='Movimentos', tag='Movimentos') as tab:
					self.tab_movimentos = TabMovements(self, tab)

				with dpg.tab(label='Classificador', tag='Classificador') as tab:
					self.tab_classificador = TabClassifier(self, tab)
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

from PySide6 import QtCore, QtQml, QtWidgets
from gui.qtMovementsTab import MovementsBackend
import sys



class ConCoWinQt:
	def __init__(self, contacontas):
		self.cc = contacontas
		self.cc.finalize_before_gui()
		self.debug = True
		global ccw
		ccw = self

		self.movsBackend = MovementsBackend(cc=self.cc)

		QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
		QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
	
		self.app = QtWidgets.QApplication(sys.argv)
		
		QtCore.QCoreApplication.setOrganizationName("TiagoRibeiro")
		QtCore.QCoreApplication.setApplicationName("ContaContas")
		self.engine = QtQml.QQmlApplicationEngine()
		self.engine.rootContext().setContextProperty("movs_backend", self.movsBackend)
	
	def run(self):		
		self.engine.load(QtCore.QUrl.fromLocalFile("gui/qml/main.qml"))
		if not self.engine.rootObjects():
			sys.exit(-1)
		self.app.exec_()
	