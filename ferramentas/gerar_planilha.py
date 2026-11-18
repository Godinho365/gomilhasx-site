"""Gera a planilha gratuita de controle de milhas (planilha-de-milhas/).

Precisa do openpyxl (não é dependência do site): rode com um Python que tenha o pacote.
    python3 ferramentas/gerar_planilha.py
O arquivo gerado fica versionado no repositório; o CI não roda este script.
"""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "planilha-de-milhas" / "planilha-de-milhas-gomilhasx.xlsx"

MARINHO, DOURADO, CINZA, OFF = "102442", "D9A441", "6B6B6B", "F5F5F3"
LINHAS = 200
CAB = Font(bold=True, color="FFFFFF")
FUNDO_CAB = PatternFill("solid", fgColor=MARINHO)
FUNDO_CALC = PatternFill("solid", fgColor=OFF)
LINHA = Side(style="thin", color="E8E8E4")
BORDA = Border(bottom=LINHA)
BRL = '"R$" #,##0.00'
INT = "#,##0"


def cabecalho(ws, colunas: list[tuple[str, int]]) -> None:
    for i, (nome, largura) in enumerate(colunas, start=1):
        c = ws.cell(row=1, column=i, value=nome)
        c.font, c.fill = CAB, FUNDO_CAB
        c.alignment = Alignment(vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(i)].width = largura
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = "A2"


def formatar(ws, col: str, fmt: str, calculada: bool = False) -> None:
    for r in range(2, LINHAS + 2):
        c = ws[f"{col}{r}"]
        c.number_format = fmt
        c.border = BORDA
        if calculada:
            c.fill = FUNDO_CALC


def principal() -> None:
    wb = Workbook()

    # Como usar
    ws = wb.active
    ws.title = "Como usar"
    ws.column_dimensions["A"].width = 100
    textos = [
        ("Planilha de controle de milhas · GONORTE", Font(bold=True, size=16, color=MARINHO)),
        ("Grátis para usar e adaptar. As colunas com fundo cinza são calculadas: não precisa preencher.", Font(color=CINZA)),
        ("", None),
        ("1. Contas: uma linha por programa e titular, com o saldo e quanto você pagou no total por ele.", None),
        ("   O custo do milheiro (R$ por 1.000 milhas) aparece sozinho.", None),
        ("2. Movimentações: registre cada compra, transferência, bônus, venda ou emissão.", None),
        ("   Milhas creditadas = pontos ÷ pontos por milha × (1 + bônus). Use a proporção do programa (1 quando é 1 para 1).", None),
        ("3. Vendas: para cada venda, informe as milhas, o preço do milheiro e o seu custo do milheiro.", None),
        ("   Receita, custo e lucro são calculados. O lucro é uma estimativa: não inclui taxas nem impostos.", None),
        ("", None),
        ("Lembre de atualizar a aba Contas depois de cada movimentação: a planilha não soma sozinha entre as abas.", Font(italic=True, color=CINZA)),
        ("", None),
        ("Quer tudo isso automático, por titular e por programa, com o custo do milheiro recalculado a cada movimento?", Font(bold=True, color=MARINHO)),
        ("O GO Manager faz essas contas sozinho e tem plano grátis: manager.gomilhasx.com/register", Font(color=MARINHO, underline="single")),
        ("Calculadora rápida do custo do milheiro: gomilhasx.com/calculadora-custo-do-milheiro", Font(color=MARINHO, underline="single")),
    ]
    # Links clicáveis com a origem (utm_*), para o painel de estatísticas e o Manager saberem que a pessoa veio da planilha
    utm = "utm_source=planilha&utm_medium=xlsx&utm_campaign=planilha_de_milhas&utm_content="
    links = {
        len(textos) - 1: f"https://manager.gomilhasx.com/register?{utm}como_usar_manager",
        len(textos): f"https://gomilhasx.com/calculadora-custo-do-milheiro/?{utm}como_usar_calculadora",
    }
    for i, (t, fonte) in enumerate(textos, start=1):
        c = ws.cell(row=i, column=1, value=t)
        if fonte:
            c.font = fonte
        if i in links:
            c.hyperlink = links[i]
    ws["A1"].border = Border(bottom=Side(style="medium", color=DOURADO))

    # Contas
    ws = wb.create_sheet("Contas")
    cabecalho(ws, [("Titular", 24), ("Programa", 20), ("Saldo (milhas)", 16), ("Total pago (R$)", 18),
                   ("Custo do milheiro (R$)", 20), ("Vencimento mais próximo", 20), ("Observações", 36)])
    for r in range(2, LINHAS + 2):
        ws[f"E{r}"] = f'=IF(AND(ISNUMBER(C{r}),C{r}>0,ISNUMBER(D{r})),D{r}/C{r}*1000,"")'
        ws[f"F{r}"].number_format = "DD/MM/YYYY"
    formatar(ws, "C", INT)
    formatar(ws, "D", BRL)
    formatar(ws, "E", BRL, calculada=True)

    # Movimentações
    ws = wb.create_sheet("Movimentações")
    cabecalho(ws, [("Data", 13), ("Titular", 22), ("Programa", 18), ("Tipo", 16), ("Pontos ou milhas", 16),
                   ("Pontos por milha", 14), ("Bônus (%)", 11), ("Milhas creditadas", 17), ("Valor (R$)", 15), ("Observação", 34)])
    tipos = DataValidation(type="list", formula1='"Compra,Transferência,Bônus,Venda,Emissão,Ajuste"', allow_blank=True)
    tipos.error, tipos.errorTitle = "Escolha um tipo da lista.", "Tipo"
    ws.add_data_validation(tipos)
    tipos.add(f"D2:D{LINHAS + 1}")
    for r in range(2, LINHAS + 2):
        ws[f"A{r}"].number_format = "DD/MM/YYYY"
        ws[f"H{r}"] = (f'=IF(ISNUMBER(E{r}),E{r}/IF(AND(ISNUMBER(F{r}),F{r}>0),F{r},1)'
                       f'*(1+IF(ISNUMBER(G{r}),G{r},0)/100),"")')
    formatar(ws, "E", INT)
    formatar(ws, "F", "0.##")
    formatar(ws, "G", "0.##")
    formatar(ws, "H", INT, calculada=True)
    formatar(ws, "I", BRL)

    # Vendas
    ws = wb.create_sheet("Vendas")
    cabecalho(ws, [("Data", 13), ("Programa", 18), ("Milhas vendidas", 16), ("Preço do milheiro (R$)", 19),
                   ("Custo do milheiro (R$)", 19), ("Receita (R$)", 16), ("Custo (R$)", 16), ("Lucro (R$)", 16), ("Comprador", 26)])
    for r in range(2, LINHAS + 2):
        ws[f"A{r}"].number_format = "DD/MM/YYYY"
        ws[f"F{r}"] = f'=IF(AND(ISNUMBER(C{r}),ISNUMBER(D{r})),C{r}/1000*D{r},"")'
        ws[f"G{r}"] = f'=IF(AND(ISNUMBER(C{r}),ISNUMBER(E{r})),C{r}/1000*E{r},"")'
        ws[f"H{r}"] = f'=IF(AND(ISNUMBER(F{r}),ISNUMBER(G{r})),F{r}-G{r},"")'
    formatar(ws, "C", INT)
    for col in "DE":
        formatar(ws, col, BRL)
    for col in "FGH":
        formatar(ws, col, BRL, calculada=True)
    total = LINHAS + 3
    ws[f"B{total}"] = "Total"
    ws[f"B{total}"].font = Font(bold=True, color=MARINHO)
    for col in "CFGH":
        c = ws[f"{col}{total}"]
        c.value = f"=SUM({col}2:{col}{LINHAS + 1})"
        c.font = Font(bold=True, color=MARINHO)
        c.number_format = INT if col == "C" else BRL
        c.border = Border(top=Side(style="medium", color=DOURADO))

    wb.properties.title = "Planilha de controle de milhas"
    wb.properties.creator = "GONORTE"
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    wb.save(DESTINO)
    print(DESTINO.relative_to(RAIZ))


if __name__ == "__main__":
    principal()
