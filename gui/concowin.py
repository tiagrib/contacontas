import dearpygui.dearpygui as dpg
from data.manipulation import contains_tag, set_mask
class ConCoWin:
    def __init__(self):
        self.ids = {}
        self.tabs = {}
        self.cc = None
        self.window_w = 1000
        self.window_h = 1000
        self.current_tab = "mov"

    def window_resized(self):
        self.window_w = dpg.get_viewport_client_width()-50
        self.window_h = dpg.get_viewport_client_height()-50
        dpg.set_item_width("grpSelectionPanel", width=self.PERW(20))
        dpg.set_item_width('grpMovsTable', width=self.PERW(80))
        #if self.current_tab=='mov':
            #dpg.delete_item('grpMovsTable', children_only=True)
            #self.create_movs_table()

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

    def update_movs(self, Sender):
        print(dpg.get_value(Sender))
        selected = dpg.get_value(Sender)
        self.cc.data.m.loc[self.cc.data.m.index,'mask'] = False
        set_mask(self.cc.data.m, selected, True)
        dpg.delete_item('grpMovsTable', children_only=True)
        self.create_movs_table()

    def create_movs_table(self):
        with dpg.table(header_row=True, resizable=True, policy=dpg.mvTable_SizingStretchProp,
                    borders_outerH=True, borders_innerV=True, borders_innerH=True, borders_outerV=True, parent='grpMovsTable'):
            dpg.add_table_column(label="Bank")
            dpg.add_table_column(label="Account")
            dpg.add_table_column(label="CumSum")
            dpg.add_table_column(label="Year")
            dpg.add_table_column(label="Month")
            dpg.add_table_column(label="Day")
            dpg.add_table_column(label="Tags")
            dpg.add_table_column(label="Value")
            dpg.add_table_column(label="Description")
            dpg.add_table_column(label="Category")
            self.present()

    def create_selection_panel(self):
        dpg.add_listbox(tag='lstTags', items=self.cc.data.all_tags, num_items=20, callback=self.update_movs, parent='grpSelectionPanel')

    def create_tab_movimentos(self, tab):
        with dpg.group(horizontal=True):
            dpg.add_group(tag='grpSelectionPanel', width=self.PERW(20))
            dpg.add_group(tag='grpMovsTable', width=self.PERW(80))
            self.create_selection_panel()
            self.create_movs_table()

    def present(self):
        for m in self.cc.data.m.itertuples():
            if m.mask:
                with dpg.table_row():
                    tag_col = (255, 255, 255, 255)
                    if contains_tag(m, 'PayPal'):
                        tag_col = (100, 150, 255, 255)
                    if m.value < 0:
                        val_col = (255,100,100, 255)
                    else:
                        val_col = (100,255,100, 255)
                    dpg.add_text(m.bank, color=tag_col)
                    dpg.add_text(m.account, color=tag_col)
                    dpg.add_text(m.cumsum, color=tag_col)
                    dpg.add_text(m.date.year, color=tag_col)
                    dpg.add_text(m.date.month, color=tag_col)
                    dpg.add_text(m.date.day, color=tag_col)
                    dpg.add_text(m.tags, color=tag_col)
                    dpg.add_text(m.value, color=val_col)
                    dpg.add_text(m.desc, color=tag_col)


    async def run(self, contacontas):
        self.cc = contacontas
        dpg.create_context()
        with dpg.window(tag="ContaContas", label="Conta-Contas", width=self.window_w, height=self.window_h):

            with dpg.tab_bar(tag="tabSpaces"):
                with dpg.tab(label='Resumos', tag='Resumos') as tab:
                    self.create_tab_resumos(tab)
                
                with dpg.tab(label='Movimentos', tag='Movimentos') as tab:
                    self.create_tab_movimentos(tab)

                with dpg.tab(label='Classificador', tag='Classificador') as tab:
                    self.create_tab_classificador(tab)

        dpg.set_value("tabSpaces", "Movimentos")

        with dpg.item_handler_registry(tag="window_handler"):
            dpg.add_item_resize_handler(callback=self.window_resized)
        dpg.bind_item_handler_registry("ContaContas", "window_handler")

        dpg.create_viewport(title='Conta-Contas', width=self.window_w, height=self.window_h, resizable=True)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("ContaContas", True)
        dpg.start_dearpygui()
        dpg.destroy_context()

    
                    
                