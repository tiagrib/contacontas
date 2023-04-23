import dearpygui.dearpygui as dpg

class ConCoWin:
    def __init__(self):
        self.ids = {}
        self.tabs = {}

    def window_resized(self):
        pass

    def create_table_tab(self, tab, label, tag):
        self.ids[tab] = tag
        self.tabs[tag] = tab

    def create_tab_mensal(self, tab):
        self.create_table_tab(tab, "Mensal", "tabMensal")

    def create_tab_movimentos(self, tab, contacontas):
        self.create_table_tab(tab, "Movimentos", "tabMovimentos")
        with dpg.table(header_row=True, resizable=True, policy=dpg.mvTable_SizingStretchProp,
                   borders_outerH=True, borders_innerV=True, borders_innerH=True, borders_outerV=True):
            dpg.add_table_column(label="Bank")
            dpg.add_table_column(label="Account")
            dpg.add_table_column(label="Sum")
            dpg.add_table_column(label="Year")
            dpg.add_table_column(label="Month")
            dpg.add_table_column(label="Day")
            dpg.add_table_column(label="Value")
            dpg.add_table_column(label="Description")
            dpg.add_table_column(label="Category")
            

            self.present(contacontas)

            


    async def run(self, contacontas):
        dpg.create_context()
        with dpg.window(tag="ContaContas", label="Conta-Contas"):

            with dpg.tab_bar(tag="tabSpaces"):
                with dpg.tab(label='Mensal') as tab:
                    self.create_tab_mensal(tab)
                
                with dpg.tab(label='Movimentos') as tab:
                    self.create_tab_movimentos(tab, contacontas)

        with dpg.item_handler_registry(tag="window_handler"):
            dpg.add_item_resize_handler(callback=self.window_resized)
        dpg.bind_item_handler_registry("ContaContas", "window_handler")

        dpg.create_viewport(title='Conta-Contas', width=1600, height=1024)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("ContaContas", True)
        dpg.start_dearpygui()
        dpg.destroy_context()

    def present(self, contacontas):
        for m in contacontas.data.m.itertuples():
            with dpg.table_row():
                dpg.add_text(m.bank)
                dpg.add_text(m.account)
                dpg.add_text(m.sum)
                dpg.add_text(m.date.year)
                dpg.add_text(m.date.month)
                dpg.add_text(m.date.day)
                dpg.add_text(m.value)
                dpg.add_text(m.desc)
                dpg.add_text(m.classification)
                