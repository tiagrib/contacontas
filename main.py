from contacontas import ContaContas
from gui.concowin import ConCoWin
import sys
import asyncio

EXTRACT_CONTA = f"..\IRS2021\Extracto_08-01-2022_113157_.pdf"
EXTRACTO_CC = f"..\movCard4544962970710000-20220108-113338.xlsx"

if __name__ == "__main__":
    cc = ContaContas()
    cc.loadPDF(EXTRACT_CONTA)
    sys.exit(asyncio.run(cc.launchGUI(ConCoWin)))