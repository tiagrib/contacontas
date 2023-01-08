import dearpygui.dearpygui as dpg

class ConCoWin:
    def __init__(self, cc):
        self.ids = {}
        self.tabs = {}
        self.cc = cc

    def window_resized(self):
        pass

    def create_table_tab(self, tab, label, tag):
        self.ids[tab] = tag
        self.tabs[tag] = tab

    def create_tab_mensal(self, tab):
        self.create_table_tab(tab, "Mensal", "tabMensal")

    def create_tab_movimentos(self, tab):
        self.create_table_tab(tab, "Movimentos", "tabMovimentos")
        with dpg.table(header_row=False):
            dpg.add_table_column(label="Bank")
            dpg.add_table_column(label="Account")
            dpg.add_table_column(label="Year")
            dpg.add_table_column(label="Month")
            dpg.add_table_column(label="Day")
            dpg.add_table_column(label="Value")
            dpg.add_table_column(label="Description")
            dpg.add_table_column(label="Category")

            for bank in self.cc.banks.values():
                for account in bank.accounts.values():
                    for segment in account.segments:
                        for mov in segment.movements:
                            with dpg.table_row():
                                dpg.add_text(bank.name)
                                dpg.add_text(account.name)
                                dpg.add_text(str(mov.date.year))
                                dpg.add_text(str(mov.date.month))
                                dpg.add_text(str(mov.date.day))
                                dpg.add_text(str(mov.value))
                                dpg.add_text(mov.desc)
                                dpg.add_text("")


    async def run(self):
        dpg.create_context()
        with dpg.window(tag="ContaContas", label="Conta-Contas"):

            with dpg.tab_bar(tag="tabSpaces"):
                with dpg.tab(label='Mensal') as tab:
                    self.create_tab_mensal(tab)
                
                with dpg.tab(label='Movimentos') as tab:
                    self.create_tab_movimentos(tab)

        with dpg.item_handler_registry(tag="window_handler"):
            dpg.add_item_resize_handler(callback=self.window_resized)
        dpg.bind_item_handler_registry("ContaContas", "window_handler")

        dpg.create_viewport(title='Conta-Contas', width=1600, height=1024)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("ContaContas", True)
        dpg.start_dearpygui()
        dpg.destroy_context()

