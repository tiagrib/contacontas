from contacontas import ContaContas
from gui.concowin import ConCoWin
import sys
import asyncio

EXTRACT_CONTA_21 = f"..\IRS2021\Extracto_08-01-2022_113157_.pdf"
EXTRACTO_PayPal_21 = f"..\IRS2021\PayPal_2021.CSV"
EXTRACT_CONTA_22 = f"..\IRS2022\Extracto_Ordem_2022_26-02-2023_124409_.pdf"
EXTRACTO_PayPal_22 = f"..\IRS2022\PayPal 2022.CSV"

if __name__ == "__main__":
    cc = ContaContas()
    cc.loadPDF(EXTRACT_CONTA_21)
    cc.loadCSV(EXTRACTO_PayPal_21)
    cc.digest()
    sys.exit(asyncio.run(cc.launchGUI(ConCoWin)))