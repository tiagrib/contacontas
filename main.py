from contacontas import ContaContas
from gui.concowin import ConCoWin  # , ConCoWinQt
import sys
import asyncio

EXTRACT_CONTA_21 = r"..\Contas\IRS2021\Extracto_08-01-2022_113157_.pdf"
EXTRACTO_PayPal_21 = r"..\Contas\IRS2021\PayPal_2021.CSV"
EXTRACT_CONTA_22 = r"..\Contas\IRS2022\Extracto_Ordem_2022_26-02-2023_124409_.pdf"
EXTRACTO_PayPal_22 = r"..\Contas\IRS2022\PayPal 2022.CSV"

if __name__ == "__main__":
    cc = ContaContas()
    asyncio.run(cc.launchGUI(ConCoWin))
    # win = ConCoWinQt(cc)
    # win.run()
    cc.save()
    sys.exit(0)
