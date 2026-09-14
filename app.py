from flask import (
    Flask,
    render_template,
    render_template_string,
    request,
    send_file,
    redirect,
    url_for
)

from io import BytesIO
from datetime import datetime
from pathlib import Path
from html import escape

import base64
import json
import sqlite3

from PIL import Image as PILImage

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)
from reportlab.lib.units import mm

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
    KeepTogether
)


# =========================================================
# CONFIGURAÇÃO
# =========================================================

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent

ARQUIVO_CONTADOR = (
    BASE_DIR / "contador_orcamentos.txt"
)

BANCO_DADOS = (
    BASE_DIR / "orcamentos.db"
)


# =========================================================
# BANCO DE DADOS
# =========================================================

def conectar_banco():

    conexao = sqlite3.connect(
        BANCO_DADOS
    )

    conexao.row_factory = sqlite3.Row

    return conexao


def inicializar_banco():

    conexao = conectar_banco()

    cursor = conexao.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS orcamentos (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            numero TEXT UNIQUE NOT NULL,

            data_emissao TEXT NOT NULL,

            empresa TEXT,
            cnpj_empresa TEXT,
            endereco_empresa TEXT,
            telefone TEXT,

            cliente TEXT NOT NULL,
            documento_cliente TEXT,
            endereco_cliente TEXT,

            valor TEXT NOT NULL,
            validade TEXT,

            forma_pagamento TEXT,
            prazo_execucao TEXT,
            observacoes TEXT,

            servicos TEXT NOT NULL,

            logo_base64 TEXT,

            criado_em TEXT NOT NULL
        )
        """
    )

    # -----------------------------------------------------
    # MIGRAÇÃO PARA BANCOS ANTIGOS
    # -----------------------------------------------------

    colunas = cursor.execute(
        """
        PRAGMA table_info(orcamentos)
        """
    ).fetchall()

    nomes_colunas = {
        coluna["name"]
        for coluna in colunas
    }

    if "logo_base64" not in nomes_colunas:

        cursor.execute(
            """
            ALTER TABLE orcamentos
            ADD COLUMN logo_base64 TEXT
            """
        )

    conexao.commit()

    conexao.close()


def salvar_orcamento(
    numero,
    data_emissao,
    empresa,
    cnpj_empresa,
    endereco_empresa,
    telefone,
    cliente,
    documento_cliente,
    endereco_cliente,
    valor,
    validade,
    forma_pagamento,
    prazo_execucao,
    observacoes,
    servicos,
    logo_base64
):

    conexao = conectar_banco()

    servicos_json = json.dumps(
        servicos,
        ensure_ascii=False
    )

    conexao.execute(
        """
        INSERT INTO orcamentos (

            numero,
            data_emissao,

            empresa,
            cnpj_empresa,
            endereco_empresa,
            telefone,

            cliente,
            documento_cliente,
            endereco_cliente,

            valor,
            validade,

            forma_pagamento,
            prazo_execucao,
            observacoes,

            servicos,
            logo_base64,

            criado_em
        )

        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?
        )
        """,

        (
            numero,
            data_emissao,

            empresa,
            cnpj_empresa,
            endereco_empresa,
            telefone,

            cliente,
            documento_cliente,
            endereco_cliente,

            valor,
            validade,

            forma_pagamento,
            prazo_execucao,
            observacoes,

            servicos_json,
            logo_base64,

            datetime.now().isoformat(
                timespec="seconds"
            )
        )
    )

    conexao.commit()

    conexao.close()


def atualizar_orcamento(
    orcamento_id,
    empresa,
    cnpj_empresa,
    endereco_empresa,
    telefone,
    cliente,
    documento_cliente,
    endereco_cliente,
    valor,
    validade,
    forma_pagamento,
    prazo_execucao,
    observacoes,
    servicos,
    logo_base64
):

    conexao = conectar_banco()

    servicos_json = json.dumps(
        servicos,
        ensure_ascii=False
    )

    conexao.execute(
        """
        UPDATE orcamentos

        SET

            empresa = ?,
            cnpj_empresa = ?,
            endereco_empresa = ?,
            telefone = ?,

            cliente = ?,
            documento_cliente = ?,
            endereco_cliente = ?,

            valor = ?,
            validade = ?,

            forma_pagamento = ?,
            prazo_execucao = ?,
            observacoes = ?,

            servicos = ?,
            logo_base64 = ?

        WHERE id = ?
        """,

        (
            empresa,
            cnpj_empresa,
            endereco_empresa,
            telefone,

            cliente,
            documento_cliente,
            endereco_cliente,

            valor,
            validade,

            forma_pagamento,
            prazo_execucao,
            observacoes,

            servicos_json,
            logo_base64,

            orcamento_id
        )
    )

    conexao.commit()

    conexao.close()


def buscar_orcamento(
    orcamento_id
):

    conexao = conectar_banco()

    orcamento = conexao.execute(
        """
        SELECT *
        FROM orcamentos
        WHERE id = ?
        """,
        (orcamento_id,)
    ).fetchone()

    conexao.close()

    return orcamento


# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def texto_pdf(texto):

    if not texto:
        return ""

    texto = escape(
        str(texto)
    )

    return texto.replace(
        "\n",
        "<br/>"
    )


# =========================================================
# NUMERAÇÃO AUTOMÁTICA
# =========================================================

def gerar_numero_orcamento():

    hoje = datetime.now().strftime(
        "%Y%m%d"
    )

    ultimo_dia = ""
    ultimo_numero = 0

    try:

        if ARQUIVO_CONTADOR.exists():

            conteudo = (
                ARQUIVO_CONTADOR
                .read_text(
                    encoding="utf-8"
                )
                .strip()
            )

            if conteudo:

                partes = conteudo.split("-")

                if len(partes) == 2:

                    ultimo_dia = partes[0]

                    try:

                        ultimo_numero = int(
                            partes[1]
                        )

                    except ValueError:

                        ultimo_numero = 0

    except Exception as erro:

        print(
            "Erro ao ler contador:",
            erro
        )

    if ultimo_dia == hoje:

        novo_numero = (
            ultimo_numero + 1
        )

    else:

        novo_numero = 1

    ARQUIVO_CONTADOR.write_text(
        f"{hoje}-{novo_numero}",
        encoding="utf-8"
    )

    return (
        f"ORC-{hoje}-"
        f"{novo_numero:03d}"
    )


# =========================================================
# LOGO
# =========================================================

def obter_logo_base64_formulario(
    logo_existente=""
):

    arquivo = request.files.get(
        "logo"
    )

    # -----------------------------------------------------
    # NOVA LOGO
    # -----------------------------------------------------

    if (
        arquivo
        and arquivo.filename
    ):

        dados = arquivo.read()

        mimetype = (
            arquivo.mimetype
            or "image/png"
        )

        conteudo = base64.b64encode(
            dados
        ).decode(
            "utf-8"
        )

        return (
            f"data:{mimetype};"
            f"base64,{conteudo}"
        )

    # -----------------------------------------------------
    # LOGO SALVA NO NAVEGADOR
    # -----------------------------------------------------

    logo_formulario = request.form.get(
        "logo_base64",
        ""
    ).strip()

    if logo_formulario:

        return logo_formulario

    # -----------------------------------------------------
    # LOGO JÁ EXISTENTE NO BANCO
    # -----------------------------------------------------

    return logo_existente or ""


def criar_imagem_pdf(
    logo_base64
):

    if not logo_base64:

        return None

    try:

        dados_base64 = logo_base64

        if "," in dados_base64:

            dados_base64 = (
                dados_base64
                .split(
                    ",",
                    1
                )[1]
            )

        dados = base64.b64decode(
            dados_base64
        )

        imagem = PILImage.open(
            BytesIO(dados)
        )

        try:
            imagem.seek(0)
        except Exception:
            pass

        if imagem.mode not in (
            "RGB",
            "RGBA"
        ):

            imagem = imagem.convert(
                "RGBA"
            )

        largura_original, altura_original = (
            imagem.size
        )

        if (
            largura_original <= 0
            or altura_original <= 0
        ):

            return None

        buffer_imagem = BytesIO()

        imagem.save(
            buffer_imagem,
            format="PNG"
        )

        buffer_imagem.seek(0)

        proporcao = (
            altura_original
            /
            largura_original
        )

        largura = 36 * mm

        altura = (
            largura
            *
            proporcao
        )

        if altura > 27 * mm:

            altura = 27 * mm

            largura = (
                altura
                /
                proporcao
            )

        imagem_pdf = RLImage(
            buffer_imagem,
            width=largura,
            height=altura
        )

        imagem_pdf.hAlign = "LEFT"

        # Mantém a imagem viva
        # enquanto o PDF é criado.

        imagem_pdf._buffer_logo = (
            buffer_imagem
        )

        return imagem_pdf

    except Exception as erro:

        print(
            "Erro ao gerar logo:",
            erro
        )

        return None


# =========================================================
# SERVIÇOS
# =========================================================

def ler_servicos_formulario():

    titulos = request.form.getlist(
        "titulos_servicos[]"
    )

    descricoes = request.form.getlist(
        "descricoes_servicos[]"
    )

    quantidade = max(
        len(titulos),
        len(descricoes)
    )

    servicos = []

    for indice in range(
        quantidade
    ):

        titulo = ""
        descricao = ""

        if indice < len(titulos):

            titulo = (
                titulos[indice]
                .strip()
            )

        if indice < len(descricoes):

            descricao = (
                descricoes[indice]
                .strip()
            )

        if titulo or descricao:

            servicos.append(
                {
                    "titulo": titulo,
                    "descricao": descricao
                }
            )

    return servicos


# =========================================================
# GERAR PDF
# =========================================================

def criar_pdf(
    dados,
    servicos,
    logo_base64=""
):

    pdf_buffer = BytesIO()

    documento = SimpleDocTemplate(
        pdf_buffer,

        pagesize=A4,

        leftMargin=18 * mm,
        rightMargin=18 * mm,

        topMargin=15 * mm,
        bottomMargin=22 * mm,

        title=dados["numero"],

        author=dados["empresa"]
    )

    elementos = []

    styles = getSampleStyleSheet()


    # =====================================================
    # CORES
    # =====================================================

    AZUL = colors.HexColor(
        "#2563EB"
    )

    AZUL_CLARO = colors.HexColor(
        "#EFF6FF"
    )

    TEXTO = colors.HexColor(
        "#111827"
    )

    TEXTO_SECUNDARIO = colors.HexColor(
        "#4B5563"
    )

    BORDA = colors.HexColor(
        "#D7DEE8"
    )

    FUNDO = colors.HexColor(
        "#F8FAFC"
    )


    # =====================================================
    # ESTILOS
    # =====================================================

    estilo_empresa = ParagraphStyle(
        "Empresa",

        parent=styles["Normal"],

        fontName="Helvetica-Bold",

        fontSize=15,

        leading=18,

        textColor=TEXTO
    )


    estilo_empresa_info = ParagraphStyle(
        "EmpresaInfo",

        parent=styles["Normal"],

        fontSize=8.5,

        leading=12,

        textColor=TEXTO_SECUNDARIO
    )


    estilo_titulo = ParagraphStyle(
        "Titulo",

        parent=styles["Normal"],

        fontName="Helvetica-Bold",

        fontSize=22,

        leading=26,

        textColor=TEXTO
    )


    estilo_meta = ParagraphStyle(
        "Meta",

        parent=styles["Normal"],

        fontSize=8.5,

        leading=12,

        alignment=TA_RIGHT,

        textColor=TEXTO_SECUNDARIO
    )


    estilo_meta_negrito = ParagraphStyle(
        "MetaNegrito",

        parent=estilo_meta,

        fontName="Helvetica-Bold",

        textColor=TEXTO
    )


    estilo_secao = ParagraphStyle(
        "Secao",

        parent=styles["Normal"],

        fontName="Helvetica-Bold",

        fontSize=10,

        leading=13,

        textColor=AZUL
    )


    estilo_label = ParagraphStyle(
        "Label",

        parent=styles["Normal"],

        fontName="Helvetica-Bold",

        fontSize=8.5,

        leading=12,

        textColor=colors.HexColor(
            "#374151"
        )
    )


    estilo_normal = ParagraphStyle(
        "NormalPDF",

        parent=styles["Normal"],

        fontSize=9,

        leading=13,

        textColor=TEXTO
    )


    estilo_servico_numero = ParagraphStyle(
        "ServicoNumero",

        parent=styles["Normal"],

        fontName="Helvetica-Bold",

        fontSize=9,

        leading=12,

        alignment=TA_CENTER,

        textColor=colors.white
    )


    estilo_servico_titulo = ParagraphStyle(
        "ServicoTitulo",

        parent=styles["Normal"],

        fontName="Helvetica-Bold",

        fontSize=10,

        leading=14,

        textColor=TEXTO
    )


    estilo_servico_descricao = ParagraphStyle(
        "ServicoDescricao",

        parent=styles["Normal"],

        fontSize=9,

        leading=13,

        textColor=TEXTO_SECUNDARIO
    )


    estilo_total_label = ParagraphStyle(
        "TotalLabel",

        parent=styles["Normal"],

        fontName="Helvetica-Bold",

        fontSize=9,

        alignment=TA_RIGHT,

        textColor=TEXTO_SECUNDARIO
    )


    estilo_total = ParagraphStyle(
        "Total",

        parent=styles["Normal"],

        fontName="Helvetica-Bold",

        fontSize=19,

        leading=23,

        alignment=TA_RIGHT,

        textColor=TEXTO
    )


    # =====================================================
    # CABEÇALHO
    # =====================================================

    logo = criar_imagem_pdf(
        logo_base64
    )


    dados_empresa = [
        Paragraph(
            texto_pdf(
                dados["empresa"]
            ),
            estilo_empresa
        )
    ]


    documentos_empresa = []


    if dados["cnpj_empresa"]:

        documentos_empresa.append(
            "CNPJ: "
            + texto_pdf(
                dados["cnpj_empresa"]
            )
        )


    if dados["telefone"]:

        documentos_empresa.append(
            "Telefone: "
            + texto_pdf(
                dados["telefone"]
            )
        )


    if documentos_empresa:

        dados_empresa.append(
            Paragraph(
                " &nbsp;&nbsp; • &nbsp;&nbsp; ".join(
                    documentos_empresa
                ),
                estilo_empresa_info
            )
        )


    if dados["endereco_empresa"]:

        dados_empresa.append(
            Paragraph(
                texto_pdf(
                    dados[
                        "endereco_empresa"
                    ]
                ),
                estilo_empresa_info
            )
        )


    cabecalho = Table(
        [
            [
                logo if logo else "",
                dados_empresa
            ]
        ],

        colWidths=[
            42 * mm,
            132 * mm
        ]
    )


    cabecalho.setStyle(
        TableStyle([

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                0
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                0
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                0
            )
        ])
    )


    elementos.append(
        cabecalho
    )


    elementos.append(
        Spacer(
            1,
            11
        )
    )


    # =====================================================
    # FAIXA AZUL
    # =====================================================

    faixa = Table(
        [[""]],

        colWidths=[
            174 * mm
        ],

        rowHeights=[
            1.3 * mm
        ]
    )


    faixa.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                AZUL
            )
        ])
    )


    elementos.append(
        faixa
    )


    elementos.append(
        Spacer(
            1,
            13
        )
    )


    # =====================================================
    # ORÇAMENTO
    # =====================================================

    dados_orcamento = [
        Paragraph(
            f"Nº {dados['numero']}",
            estilo_meta_negrito
        ),

        Paragraph(
            (
                "Emissão: "
                f"{dados['data_emissao']}"
            ),
            estilo_meta
        )
    ]


    if dados["validade"]:

        dados_orcamento.append(
            Paragraph(
                (
                    "Validade: "
                    f"{texto_pdf(dados['validade'])}"
                    " dias"
                ),
                estilo_meta
            )
        )


    tabela_titulo = Table(
        [
            [
                Paragraph(
                    "ORÇAMENTO",
                    estilo_titulo
                ),

                dados_orcamento
            ]
        ],

        colWidths=[
            100 * mm,
            74 * mm
        ]
    )


    tabela_titulo.setStyle(
        TableStyle([

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                0
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                0
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                0
            )

        ])
    )


    elementos.append(
        tabela_titulo
    )


    elementos.append(
        Spacer(
            1,
            20
        )
    )


    # =====================================================
    # CLIENTE
    # =====================================================

    elementos.append(
        Paragraph(
            "DADOS DO CLIENTE",
            estilo_secao
        )
    )


    elementos.append(
        Spacer(
            1,
            6
        )
    )


    dados_cliente = [
        [
            Paragraph(
                "Cliente / Empresa",
                estilo_label
            ),

            Paragraph(
                texto_pdf(
                    dados["cliente"]
                ),
                estilo_normal
            )
        ]
    ]


    if dados["documento_cliente"]:

        dados_cliente.append(
            [
                Paragraph(
                    "CPF / CNPJ",
                    estilo_label
                ),

                Paragraph(
                    texto_pdf(
                        dados[
                            "documento_cliente"
                        ]
                    ),
                    estilo_normal
                )
            ]
        )


    if dados["endereco_cliente"]:

        dados_cliente.append(
            [
                Paragraph(
                    "Endereço",
                    estilo_label
                ),

                Paragraph(
                    texto_pdf(
                        dados[
                            "endereco_cliente"
                        ]
                    ),
                    estilo_normal
                )
            ]
        )


    tabela_cliente = Table(
        dados_cliente,

        colWidths=[
            38 * mm,
            136 * mm
        ]
    )


    tabela_cliente.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                FUNDO
            ),

            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.5,
                BORDA
            ),

            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.35,
                BORDA
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                7
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                7
            )

        ])
    )


    elementos.append(
        tabela_cliente
    )


    elementos.append(
        Spacer(
            1,
            20
        )
    )


    # =====================================================
    # SERVIÇOS
    # =====================================================

    elementos.append(
        Paragraph(
            "SERVIÇOS",
            estilo_secao
        )
    )


    elementos.append(
        Spacer(
            1,
            7
        )
    )


    numero_servico = 1


    for servico in servicos:

        conteudo = []


        if servico["titulo"]:

            conteudo.append(
                Paragraph(
                    texto_pdf(
                        servico["titulo"]
                    ),
                    estilo_servico_titulo
                )
            )


        if servico["descricao"]:

            if servico["titulo"]:

                conteudo.append(
                    Spacer(
                        1,
                        3
                    )
                )


            conteudo.append(
                Paragraph(
                    texto_pdf(
                        servico[
                            "descricao"
                        ]
                    ),
                    estilo_servico_descricao
                )
            )


        tabela_servico = Table(
            [
                [
                    Paragraph(
                        f"{numero_servico:02d}",
                        estilo_servico_numero
                    ),

                    conteudo
                ]
            ],

            colWidths=[
                14 * mm,
                160 * mm
            ]
        )


        tabela_servico.setStyle(
            TableStyle([

                (
                    "BACKGROUND",
                    (0, 0),
                    (0, 0),
                    AZUL
                ),

                (
                    "BACKGROUND",
                    (1, 0),
                    (1, 0),
                    FUNDO
                ),

                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.45,
                    BORDA
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),

                (
                    "ALIGN",
                    (0, 0),
                    (0, 0),
                    "CENTER"
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                )

            ])
        )


        elementos.append(
            KeepTogether(
                [
                    tabela_servico,

                    Spacer(
                        1,
                        7
                    )
                ]
            )
        )


        numero_servico += 1


    # =====================================================
    # CONDIÇÕES COMERCIAIS
    # =====================================================

    if (
        dados["forma_pagamento"]
        or dados["prazo_execucao"]
    ):

        elementos.append(
            Spacer(
                1,
                8
            )
        )


        elementos.append(
            Paragraph(
                "CONDIÇÕES COMERCIAIS",
                estilo_secao
            )
        )


        elementos.append(
            Spacer(
                1,
                6
            )
        )


        condicoes = []


        if dados["forma_pagamento"]:

            condicoes.append(
                [
                    Paragraph(
                        "Forma de pagamento",
                        estilo_label
                    ),

                    Paragraph(
                        texto_pdf(
                            dados[
                                "forma_pagamento"
                            ]
                        ),
                        estilo_normal
                    )
                ]
            )


        if dados["prazo_execucao"]:

            condicoes.append(
                [
                    Paragraph(
                        "Prazo de execução",
                        estilo_label
                    ),

                    Paragraph(
                        texto_pdf(
                            dados[
                                "prazo_execucao"
                            ]
                        ),
                        estilo_normal
                    )
                ]
            )


        tabela_condicoes = Table(
            condicoes,

            colWidths=[
                38 * mm,
                136 * mm
            ]
        )


        tabela_condicoes.setStyle(
            TableStyle([

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    FUNDO
                ),

                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.45,
                    BORDA
                ),

                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    BORDA
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                )

            ])
        )


        elementos.append(
            tabela_condicoes
        )


    # =====================================================
    # OBSERVAÇÕES
    # =====================================================

    if dados["observacoes"]:

        elementos.append(
            Spacer(
                1,
                14
            )
        )


        elementos.append(
            Paragraph(
                "OBSERVAÇÕES",
                estilo_secao
            )
        )


        elementos.append(
            Spacer(
                1,
                6
            )
        )


        caixa_observacoes = Table(
            [
                [
                    Paragraph(
                        texto_pdf(
                            dados[
                                "observacoes"
                            ]
                        ),
                        estilo_normal
                    )
                ]
            ],

            colWidths=[
                174 * mm
            ]
        )


        caixa_observacoes.setStyle(
            TableStyle([

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    FUNDO
                ),

                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.45,
                    BORDA
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    9
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    9
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    9
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    9
                )

            ])
        )


        elementos.append(
            caixa_observacoes
        )


    # =====================================================
    # VALOR TOTAL
    # =====================================================

    elementos.append(
        Spacer(
            1,
            20
        )
    )


    tabela_total = Table(
        [
            [
                "",

                [
                    Paragraph(
                        "VALOR TOTAL",
                        estilo_total_label
                    ),

                    Spacer(
                        1,
                        3
                    ),

                    Paragraph(
                        texto_pdf(
                            dados["valor"]
                        ),
                        estilo_total
                    )
                ]
            ]
        ],

        colWidths=[
            90 * mm,
            84 * mm
        ]
    )


    tabela_total.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (1, 0),
                (1, 0),
                AZUL_CLARO
            ),

            (
                "BOX",
                (1, 0),
                (1, 0),
                0.8,
                colors.HexColor(
                    "#BFDBFE"
                )
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "RIGHTPADDING",
                (1, 0),
                (1, 0),
                12
            ),

            (
                "TOPPADDING",
                (1, 0),
                (1, 0),
                11
            ),

            (
                "BOTTOMPADDING",
                (1, 0),
                (1, 0),
                11
            )

        ])
    )


    elementos.append(
        tabela_total
    )


    # =====================================================
    # RODAPÉ
    # =====================================================

    def desenhar_rodape(
        canvas,
        doc
    ):

        canvas.saveState()

        largura_pagina, _ = A4

        canvas.setStrokeColor(
            BORDA
        )

        canvas.setLineWidth(
            0.5
        )

        canvas.line(
            18 * mm,
            14 * mm,

            largura_pagina - 18 * mm,
            14 * mm
        )

        canvas.setFont(
            "Helvetica",
            7.5
        )

        canvas.setFillColor(
            colors.HexColor(
                "#6B7280"
            )
        )

        canvas.drawString(
            18 * mm,
            9 * mm,
            dados["numero"]
        )

        canvas.drawRightString(
            largura_pagina - 18 * mm,
            9 * mm,
            f"Página {doc.page}"
        )

        canvas.restoreState()


    documento.build(
        elementos,

        onFirstPage=desenhar_rodape,

        onLaterPages=desenhar_rodape
    )


    pdf_buffer.seek(0)

    return pdf_buffer


# =========================================================
# PÁGINA PRINCIPAL
# =========================================================

@app.route("/")
def index():

    return render_template(
        "index.html"
    )


# =========================================================
# CRIAR NOVO ORÇAMENTO
# =========================================================

@app.route(
    "/gerar-pdf",
    methods=["POST"]
)
def gerar_pdf():

    empresa = request.form.get(
        "empresa",
        ""
    ).strip()

    cnpj_empresa = request.form.get(
        "cnpj_empresa",
        ""
    ).strip()

    endereco_empresa = request.form.get(
        "endereco_empresa",
        ""
    ).strip()

    telefone = request.form.get(
        "telefone",
        ""
    ).strip()


    cliente = request.form.get(
        "cliente",
        ""
    ).strip()

    documento_cliente = request.form.get(
        "documento_cliente",
        ""
    ).strip()

    endereco_cliente = request.form.get(
        "endereco_cliente",
        ""
    ).strip()


    valor = request.form.get(
        "valor",
        ""
    ).strip()

    validade = request.form.get(
        "validade",
        ""
    ).strip()

    forma_pagamento = request.form.get(
        "forma_pagamento",
        ""
    ).strip()

    prazo_execucao = request.form.get(
        "prazo_execucao",
        ""
    ).strip()

    observacoes = request.form.get(
        "observacoes",
        ""
    ).strip()


    servicos = (
        ler_servicos_formulario()
    )


    if not empresa:

        return (
            "Informe o nome da empresa.",
            400
        )


    if not cliente:

        return (
            "Informe o cliente.",
            400
        )


    if not servicos:

        return (
            "Adicione pelo menos um serviço.",
            400
        )


    if not valor:

        return (
            "Informe o valor.",
            400
        )


    numero = gerar_numero_orcamento()


    data_emissao = (
        datetime.now()
        .strftime(
            "%d/%m/%Y"
        )
    )


    logo_base64 = (
        obter_logo_base64_formulario()
    )


    dados = {

        "numero":
            numero,

        "data_emissao":
            data_emissao,

        "empresa":
            empresa,

        "cnpj_empresa":
            cnpj_empresa,

        "endereco_empresa":
            endereco_empresa,

        "telefone":
            telefone,

        "cliente":
            cliente,

        "documento_cliente":
            documento_cliente,

        "endereco_cliente":
            endereco_cliente,

        "valor":
            valor,

        "validade":
            validade,

        "forma_pagamento":
            forma_pagamento,

        "prazo_execucao":
            prazo_execucao,

        "observacoes":
            observacoes
    }


    pdf_buffer = criar_pdf(
        dados,
        servicos,
        logo_base64
    )


    salvar_orcamento(

        numero,
        data_emissao,

        empresa,
        cnpj_empresa,
        endereco_empresa,
        telefone,

        cliente,
        documento_cliente,
        endereco_cliente,

        valor,
        validade,

        forma_pagamento,
        prazo_execucao,
        observacoes,

        servicos,
        logo_base64
    )


    return send_file(
        pdf_buffer,

        as_attachment=True,

        download_name=(
            f"{numero}.pdf"
        ),

        mimetype="application/pdf"
    )


# =========================================================
# HISTÓRICO
# =========================================================

@app.route("/historico")
def historico():

    conexao = conectar_banco()

    orcamentos = conexao.execute(
        """
        SELECT
            id,
            numero,
            cliente,
            data_emissao,
            valor,
            criado_em

        FROM orcamentos

        ORDER BY id DESC
        """
    ).fetchall()

    conexao.close()

    return render_template(
        "historico.html",
        orcamentos=orcamentos
    )


# =========================================================
# VISUALIZAR ORÇAMENTO
# =========================================================

DETALHES_TEMPLATE = """
<!DOCTYPE html>

<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta
name="viewport"
content="width=device-width, initial-scale=1.0"
>

<title>
{{ orcamento["numero"] }}
</title>

<link
rel="stylesheet"
href="{{ url_for('static', filename='style.css') }}"
>

</head>


<body>

<main class="container">


<header class="topo historico-topo">

<div>

<h1>
{{ orcamento["numero"] }}
</h1>

<p>
Emitido em
{{ orcamento["data_emissao"] }}
</p>

</div>


<a
href="{{ url_for('historico') }}"
class="btn-secundario link-botao"
>
← Histórico
</a>

</header>


<section class="card">

<h2>
Dados do Cliente
</h2>


<p>
<strong>Cliente / Empresa:</strong>
{{ orcamento["cliente"] }}
</p>


{% if orcamento["documento_cliente"] %}

<p>
<strong>CPF / CNPJ:</strong>
{{ orcamento["documento_cliente"] }}
</p>

{% endif %}


{% if orcamento["endereco_cliente"] %}

<p>
<strong>Endereço:</strong>
{{ orcamento["endereco_cliente"] }}
</p>

{% endif %}

</section>


<section class="card">

<h2>
Serviços
</h2>


{% for servico in servicos %}

<div class="servico-detalhe">

<h3>
{{ loop.index }}.
{{ servico["titulo"] }}
</h3>

<p>
{{ servico["descricao"] }}
</p>

</div>

{% endfor %}

</section>


<section class="card">

<h2>
Valores e Condições
</h2>


<p>

<strong>
Valor total:
</strong>

{{ orcamento["valor"] }}

</p>


{% if orcamento["validade"] %}

<p>

<strong>
Validade:
</strong>

{{ orcamento["validade"] }}
dias

</p>

{% endif %}


{% if orcamento["forma_pagamento"] %}

<p>

<strong>
Forma de pagamento:
</strong>

{{ orcamento["forma_pagamento"] }}

</p>

{% endif %}


{% if orcamento["prazo_execucao"] %}

<p>

<strong>
Prazo de execução:
</strong>

{{ orcamento["prazo_execucao"] }}

</p>

{% endif %}


{% if orcamento["observacoes"] %}

<p>

<strong>
Observações:
</strong>

{{ orcamento["observacoes"] }}

</p>

{% endif %}

</section>


<div class="acoes">

<a
href="{{ url_for('editar_orcamento', orcamento_id=orcamento['id']) }}"
class="btn-secundario link-botao"
>
Editar
</a>


<a
href="{{ url_for('baixar_pdf_orcamento', orcamento_id=orcamento['id']) }}"
class="btn-principal link-botao"
>
Baixar PDF
</a>

</div>


</main>

</body>

</html>
"""


@app.route(
    "/orcamento/<int:orcamento_id>"
)
def visualizar_orcamento(
    orcamento_id
):

    orcamento = buscar_orcamento(
        orcamento_id
    )


    if orcamento is None:

        return (
            "Orçamento não encontrado.",
            404
        )


    servicos = json.loads(
        orcamento["servicos"]
    )


    return render_template_string(
        DETALHES_TEMPLATE,

        orcamento=orcamento,

        servicos=servicos
    )


# =========================================================
# BAIXAR PDF DO HISTÓRICO
# =========================================================

@app.route(
    "/orcamento/<int:orcamento_id>/pdf"
)
def baixar_pdf_orcamento(
    orcamento_id
):

    orcamento = buscar_orcamento(
        orcamento_id
    )


    if orcamento is None:

        return (
            "Orçamento não encontrado.",
            404
        )


    servicos = json.loads(
        orcamento["servicos"]
    )


    dados = dict(
        orcamento
    )


    pdf_buffer = criar_pdf(
        dados,
        servicos,
        orcamento["logo_base64"] or ""
    )


    return send_file(
        pdf_buffer,

        as_attachment=True,

        download_name=(
            f"{orcamento['numero']}.pdf"
        ),

        mimetype="application/pdf"
    )


# =========================================================
# TEMPLATE DE EDIÇÃO
# =========================================================

EDITAR_TEMPLATE = """
<!DOCTYPE html>

<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta
name="viewport"
content="width=device-width, initial-scale=1.0"
>

<title>
Editar {{ orcamento["numero"] }}
</title>

<link
rel="stylesheet"
href="{{ url_for('static', filename='style.css') }}"
>

</head>


<body>

<main class="container">


<header class="topo historico-topo">

<div>

<h1>
Editar Orçamento
</h1>

<p>
{{ orcamento["numero"] }}
</p>

</div>


<a
href="{{ url_for('historico') }}"
class="btn-secundario link-botao"
>
← Histórico
</a>

</header>


<form
method="POST"
enctype="multipart/form-data"
>


<!-- ===================================== -->
<!-- EMPRESA -->
<!-- ===================================== -->

<section class="card">

<h2>
Dados da Empresa
</h2>


<div class="logo-area">

<label>
Logo da empresa
</label>


<input
type="file"
name="logo"
accept="image/*"
>


<input
type="hidden"
name="logo_base64"
value="{{ orcamento['logo_base64'] or '' }}"
>


{% if orcamento["logo_base64"] %}

<div id="preview-logo">

<img
src="{{ orcamento['logo_base64'] }}"
alt="Logo da empresa"
>

</div>

{% endif %}

</div>


<div class="grid">


<div class="campo">

<label>
Nome / Razão Social
</label>

<input
type="text"
name="empresa"
value="{{ orcamento['empresa'] or '' }}"
required
>

</div>


<div class="campo">

<label>
CNPJ
</label>

<input
type="text"
id="cnpj-edicao"
name="cnpj_empresa"
value="{{ orcamento['cnpj_empresa'] or '' }}"
maxlength="18"
>

</div>


<div class="campo campo-grande">

<label>
Endereço
</label>

<input
type="text"
name="endereco_empresa"
value="{{ orcamento['endereco_empresa'] or '' }}"
>

</div>


<div class="campo">

<label>
Telefone
</label>

<input
type="text"
id="telefone-edicao"
name="telefone"
value="{{ orcamento['telefone'] or '' }}"
>

</div>


</div>

</section>


<!-- ===================================== -->
<!-- CLIENTE -->
<!-- ===================================== -->

<section class="card">

<h2>
Dados do Cliente
</h2>


<div class="grid">


<div class="campo">

<label>
Nome / Empresa
</label>

<input
type="text"
name="cliente"
value="{{ orcamento['cliente'] }}"
required
>

</div>


<div class="campo">

<label>
CPF / CNPJ
</label>

<input
type="text"
id="documento-edicao"
name="documento_cliente"
value="{{ orcamento['documento_cliente'] or '' }}"
>

</div>


<div class="campo campo-grande">

<label>
Endereço
</label>

<input
type="text"
name="endereco_cliente"
value="{{ orcamento['endereco_cliente'] or '' }}"
>

</div>


</div>

</section>


<!-- ===================================== -->
<!-- SERVIÇOS -->
<!-- ===================================== -->

<section class="card">

<div class="titulo-servicos">

<h2>
Serviços
</h2>


<button
type="button"
id="adicionar-servico-edicao"
class="btn-secundario"
>
+ Adicionar Serviço
</button>

</div>


<div id="servicos-edicao">


{% for servico in servicos %}

<div class="servico">


<div class="conteudo-servico">

<input
type="text"
name="titulos_servicos[]"
class="titulo-servico"
value="{{ servico['titulo'] }}"
required
>


<textarea
name="descricoes_servicos[]"
required
>{{ servico["descricao"] }}</textarea>

</div>


<button
type="button"
class="remover-servico-edicao remover-servico"
>
Remover
</button>


</div>

{% endfor %}


</div>

</section>


<!-- ===================================== -->
<!-- VALORES -->
<!-- ===================================== -->

<section class="card">

<h2>
Valores e Condições
</h2>


<div class="grid">


<div class="campo">

<label>
Valor total
</label>

<input
type="text"
id="valor-edicao"
name="valor"
value="{{ orcamento['valor'] }}"
required
>

</div>


<div class="campo">

<label>
Validade
</label>

<input
type="number"
name="validade"
value="{{ orcamento['validade'] or '' }}"
>

</div>


<div class="campo">

<label>
Forma de pagamento
</label>

<input
type="text"
name="forma_pagamento"
value="{{ orcamento['forma_pagamento'] or '' }}"
>

</div>


<div class="campo">

<label>
Prazo de execução
</label>

<input
type="text"
name="prazo_execucao"
value="{{ orcamento['prazo_execucao'] or '' }}"
>

</div>


<div class="campo campo-grande">

<label>
Observações
</label>

<textarea
name="observacoes"
>{{ orcamento["observacoes"] or "" }}</textarea>

</div>


</div>

</section>


<div class="acoes">


<a
href="{{ url_for('visualizar_orcamento', orcamento_id=orcamento['id']) }}"
class="btn-secundario link-botao"
>
Cancelar
</a>


<button
type="submit"
class="btn-principal"
>
Salvar Alterações
</button>


</div>


</form>

</main>


<script>

// =====================================================
// SERVIÇOS
// =====================================================

const listaServicos =
    document.getElementById(
        "servicos-edicao"
    );


const botaoAdicionar =
    document.getElementById(
        "adicionar-servico-edicao"
    );


botaoAdicionar.addEventListener(
    "click",
    function () {

        const novo =
            document.createElement(
                "div"
            );


        novo.className =
            "servico";


        novo.innerHTML = `

            <div class="conteudo-servico">

                <input
                    type="text"
                    name="titulos_servicos[]"
                    class="titulo-servico"
                    placeholder="Título do serviço"
                    required
                >

                <textarea
                    name="descricoes_servicos[]"
                    placeholder="Descrição do serviço"
                    required
                ></textarea>

            </div>

            <button
                type="button"
                class="remover-servico-edicao remover-servico"
            >
                Remover
            </button>

        `;


        listaServicos.appendChild(
            novo
        );
    }
);


listaServicos.addEventListener(
    "click",
    function (evento) {

        if (
            evento.target.classList.contains(
                "remover-servico-edicao"
            )
        ) {

            const servicos =
                listaServicos.querySelectorAll(
                    ".servico"
                );


            if (servicos.length <= 1) {

                alert(
                    "O orçamento precisa ter pelo menos um serviço."
                );

                return;
            }


            evento.target
                .closest(
                    ".servico"
                )
                .remove();
        }
    }
);


// =====================================================
// CPF / CNPJ
// =====================================================

function formatarDocumento(valor) {

    valor =
        valor.replace(
            /\\D/g,
            ""
        );


    if (valor.length <= 11) {

        valor =
            valor.slice(
                0,
                11
            );


        return valor
            .replace(
                /(\\d{3})(\\d)/,
                "$1.$2"
            )
            .replace(
                /(\\d{3})(\\d)/,
                "$1.$2"
            )
            .replace(
                /(\\d{3})(\\d{1,2})$/,
                "$1-$2"
            );
    }


    valor =
        valor.slice(
            0,
            14
        );


    return valor
        .replace(
            /^(\\d{2})(\\d)/,
            "$1.$2"
        )
        .replace(
            /^(\\d{2})\\.(\\d{3})(\\d)/,
            "$1.$2.$3"
        )
        .replace(
            /\\.(\\d{3})(\\d)/,
            ".$1/$2"
        )
        .replace(
            /(\\d{4})(\\d)/,
            "$1-$2"
        );
}


const documentoEdicao =
    document.getElementById(
        "documento-edicao"
    );


documentoEdicao.addEventListener(
    "input",
    function () {

        this.value =
            formatarDocumento(
                this.value
            );
    }
);


// =====================================================
// CNPJ DA EMPRESA
// =====================================================

const cnpjEdicao =
    document.getElementById(
        "cnpj-edicao"
    );


cnpjEdicao.addEventListener(
    "input",
    function () {

        let valor =
            this.value.replace(
                /\\D/g,
                ""
            );


        valor =
            valor.slice(
                0,
                14
            );


        valor = valor
            .replace(
                /^(\\d{2})(\\d)/,
                "$1.$2"
            )
            .replace(
                /^(\\d{2})\\.(\\d{3})(\\d)/,
                "$1.$2.$3"
            )
            .replace(
                /\\.(\\d{3})(\\d)/,
                ".$1/$2"
            )
            .replace(
                /(\\d{4})(\\d)/,
                "$1-$2"
            );


        this.value = valor;
    }
);


// =====================================================
// TELEFONE
// =====================================================

const telefoneEdicao =
    document.getElementById(
        "telefone-edicao"
    );


telefoneEdicao.addEventListener(
    "input",
    function () {

        let valor =
            this.value.replace(
                /\\D/g,
                ""
            );


        valor =
            valor.slice(
                0,
                11
            );


        if (valor.length <= 10) {

            valor = valor
                .replace(
                    /^(\\d{2})(\\d)/,
                    "($1) $2"
                )
                .replace(
                    /(\\d{4})(\\d)/,
                    "$1-$2"
                );

        } else {

            valor = valor
                .replace(
                    /^(\\d{2})(\\d)/,
                    "($1) $2"
                )
                .replace(
                    /(\\d{5})(\\d)/,
                    "$1-$2"
                );
        }


        this.value = valor;
    }
);


// =====================================================
// VALOR EM REAL
// =====================================================

const campoValorEdicao =
    document.getElementById(
        "valor-edicao"
    );


campoValorEdicao.addEventListener(
    "input",
    function () {

        let valor =
            this.value.replace(
                /\\D/g,
                ""
            );


        if (!valor) {

            this.value = "";

            return;
        }


        const numero =
            Number(valor)
            / 100;


        this.value =
            numero.toLocaleString(
                "pt-BR",
                {
                    style:
                        "currency",

                    currency:
                        "BRL"
                }
            );
    }
);

</script>


</body>

</html>
"""


# =========================================================
# EDITAR ORÇAMENTO
# =========================================================

@app.route(
    "/orcamento/<int:orcamento_id>/editar",
    methods=[
        "GET",
        "POST"
    ]
)
def editar_orcamento(
    orcamento_id
):

    orcamento = buscar_orcamento(
        orcamento_id
    )


    if orcamento is None:

        return (
            "Orçamento não encontrado.",
            404
        )


    # =====================================================
    # SALVAR EDIÇÃO
    # =====================================================

    if request.method == "POST":

        empresa = request.form.get(
            "empresa",
            ""
        ).strip()

        cnpj_empresa = request.form.get(
            "cnpj_empresa",
            ""
        ).strip()

        endereco_empresa = request.form.get(
            "endereco_empresa",
            ""
        ).strip()

        telefone = request.form.get(
            "telefone",
            ""
        ).strip()


        cliente = request.form.get(
            "cliente",
            ""
        ).strip()

        documento_cliente = request.form.get(
            "documento_cliente",
            ""
        ).strip()

        endereco_cliente = request.form.get(
            "endereco_cliente",
            ""
        ).strip()


        valor = request.form.get(
            "valor",
            ""
        ).strip()

        validade = request.form.get(
            "validade",
            ""
        ).strip()

        forma_pagamento = request.form.get(
            "forma_pagamento",
            ""
        ).strip()

        prazo_execucao = request.form.get(
            "prazo_execucao",
            ""
        ).strip()

        observacoes = request.form.get(
            "observacoes",
            ""
        ).strip()


        servicos = (
            ler_servicos_formulario()
        )


        if not empresa:

            return (
                "Informe a empresa.",
                400
            )


        if not cliente:

            return (
                "Informe o cliente.",
                400
            )


        if not servicos:

            return (
                "Adicione pelo menos um serviço.",
                400
            )


        if not valor:

            return (
                "Informe o valor.",
                400
            )


        logo_base64 = (
            obter_logo_base64_formulario(
                orcamento[
                    "logo_base64"
                ]
                or ""
            )
        )


        atualizar_orcamento(

            orcamento_id,

            empresa,
            cnpj_empresa,
            endereco_empresa,
            telefone,

            cliente,
            documento_cliente,
            endereco_cliente,

            valor,
            validade,

            forma_pagamento,
            prazo_execucao,
            observacoes,

            servicos,
            logo_base64
        )


        return redirect(
            url_for(
                "visualizar_orcamento",
                orcamento_id=orcamento_id
            )
        )


    # =====================================================
    # ABRIR EDIÇÃO
    # =====================================================

    servicos = json.loads(
        orcamento["servicos"]
    )


    return render_template_string(
        EDITAR_TEMPLATE,

        orcamento=orcamento,

        servicos=servicos
    )


# =========================================================
# EXCLUIR ORÇAMENTO
# =========================================================

@app.route(
    "/orcamento/<int:orcamento_id>/excluir",
    methods=["POST"]
)
def excluir_orcamento(
    orcamento_id
):

    conexao = conectar_banco()


    conexao.execute(
        """
        DELETE FROM orcamentos
        WHERE id = ?
        """,
        (orcamento_id,)
    )


    conexao.commit()

    conexao.close()


    return redirect(
        url_for(
            "historico"
        )
    )


# =========================================================
# INICIALIZA O BANCO
# =========================================================

inicializar_banco()


# =========================================================
# EXECUTAR
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )