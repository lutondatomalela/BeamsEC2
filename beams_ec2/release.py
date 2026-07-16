# -*- coding: utf-8 -*-
"""Configuração pública e interface da versão v0.1.1.1."""

from pathlib import Path
import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import advanced as _implementation
from .table_io import read_table_file
globals().update({k: v for k, v in vars(_implementation).items() if not k.startswith("__")})

APP_VERSION = "v0.1"
APP_TITLE = "BeamsEC2 - Dimensionamento de Vigas Segundo o EC2"
APP_AUTHOR = ""
APP_TABLE_DESCRIPTION = (
    "Memória de cálculo de vigas de betão armado com dados de entrada, "
    "envelopes, verificações ELU e ELS, pormenorização e validação."
)

# As funções foram separadas por domínio, mas mantêm o mesmo núcleo validado.
# Actualizar a identificação em todos os módulos porque os métodos conservam
# o espaço global do módulo onde foram definidos.
from . import base as _base, design as _design, reporting as _reporting
from . import geometry as _geometry, serviceability as _serviceability
for _module in (_base, _design, _reporting, _geometry, _serviceability, _implementation):
    _module.APP_VERSION = APP_VERSION
    _module.APP_TITLE = APP_TITLE
    _module.APP_AUTHOR = APP_AUTHOR
    _module.APP_TABLE_DESCRIPTION = APP_TABLE_DESCRIPTION

TABLE_COLUMNS_REQUIRED = [
    "Member/Node/Case", "Station (m)", "FZ (kN)", "MX (kNm)", "MY (kNm)",
    "Length (m)", "Material", "HY (cm)", "HZ (cm)",
]
TABLE_COLUMNS_RECOMMENDED = ["Name", "Story"]
TABLE_COLUMNS_ELS = [
    "Support Condition", "As Bot Local (mm2)", "As Top Local (mm2)",
    "Bot Rebar Local", "Top Rebar Local",
]
TABLE_COLUMNS_GEOMETRY = [
    "VY (cm)", "VZ (cm)", "VPY (cm)", "VPZ (cm)", "AX (cm2)",
    "AY (cm2)", "AZ (cm2)", "IX (cm4)", "IY (cm4)", "IZ (cm4)",
    "Section Type", "B Top (cm)", "TF Top (cm)", "B Bottom (cm)",
    "TF Bottom (cm)", "TW (cm)", "I Top",
]


def _build_sidebar_clean(self, parent):
    _ensure_sls_vars_advanced(self)
    self.var_agg.set(f"{DEFAULT_AGGREGATE_MM_Reporting:.0f}")
    self.var_gamma_c.set(f"{DEFAULT_GAMMA_C_Reporting:.2f}")
    self.var_gamma_s.set(f"{DEFAULT_GAMMA_S_Reporting:.2f}")
    if finite(self.var_ld_limit.get(), 20.0) < 100:
        self.var_ld_limit.set("250")

    hero = ttk.LabelFrame(parent, text=f"{APP_NAME} {APP_VERSION}")
    hero.pack(fill="x", pady=(0, 8))
    link = ttk.Label(hero, text=APP_NAME, style="Header.TLabel", cursor="hand2")
    link.pack(anchor="w")
    link.bind("<Button-1>", lambda _e: webbrowser.open_new(GITHUB_URL))
    ttk.Label(hero, text="Dimensionamento de vigas de betão armado", style="Header.TLabel").pack(anchor="w", pady=(2, 0))
    ttk.Label(
        hero,
        text="Importa tabelas de esforços, cria envelopes e executa verificações ELU e ELS segundo a NP EN 1992-1-1.",
        style="Subtle.TLabel", wraplength=340, justify="left",
    ).pack(anchor="w", pady=(2, 0))

    data = ttk.LabelFrame(parent, text="1. Tabela de entrada")
    data.pack(fill="x", pady=(0, 8))
    ttk.Button(data, text="Colar tabela", command=self.paste_clipboard).grid(row=0, column=0, sticky="ew", padx=4, pady=4)
    ttk.Button(data, text="Importar tabela", command=self.import_file).grid(row=0, column=1, sticky="ew", padx=4, pady=4)
    ttk.Button(data, text="Ler caixa de texto", command=self.load_from_textbox).grid(row=1, column=0, sticky="ew", padx=4, pady=4)
    ttk.Button(data, text="Guardar tabela-tipo", command=self.export_template).grid(row=1, column=1, sticky="ew", padx=4, pady=4)
    data.columnconfigure(0, weight=1); data.columnconfigure(1, weight=1)

    params = ttk.LabelFrame(parent, text="2. Parâmetros de cálculo")
    params.pack(fill="x", pady=(0, 8))
    self._add_label_entry(params, "Recobrimento [mm]", self.var_cover, 0)
    ttk.Label(params, text="Aço fyk [MPa]").grid(row=1, column=0, sticky="w", padx=6, pady=4)
    ttk.Combobox(params, textvariable=self.var_fyk, values=["400", "500"], state="readonly", width=14).grid(row=1, column=1, sticky="ew", padx=6, pady=4)
    self._add_label_entry(params, "wk,lim [mm]", self.var_crack_limit, 2)
    self._add_label_entry(params, "Limite de flecha L/", self.var_ld_limit, 3)
    ttk.Label(params, text="Momento principal").grid(row=4, column=0, sticky="w", padx=6, pady=4)
    ttk.Combobox(params, textvariable=self.var_moment_axis, values=["MY", "MZ"], state="readonly").grid(row=4, column=1, sticky="ew", padx=6, pady=4)
    ttk.Label(params, text="Corte vertical").grid(row=5, column=0, sticky="w", padx=6, pady=4)
    ttk.Combobox(params, textvariable=self.var_shear_axis, values=["FZ", "FY"], state="readonly").grid(row=5, column=1, sticky="ew", padx=6, pady=4)
    ttk.Label(params, text="Torção").grid(row=6, column=0, sticky="w", padx=6, pady=4)
    ttk.Combobox(params, textvariable=self.var_torsion_axis, values=["MX", "MY", "MZ", "Nenhuma"], state="readonly").grid(row=6, column=1, sticky="ew", padx=6, pady=4)
    ttk.Checkbutton(params, text="Reduzir para casos governantes", variable=self.var_reduce_cases).grid(row=7, column=0, columnspan=2, sticky="w", padx=6, pady=3)
    ttk.Checkbutton(params, text="Gerar resumo por viga", variable=self.var_summary).grid(row=8, column=0, columnspan=2, sticky="w", padx=6, pady=3)
    params.columnconfigure(1, weight=1)

    sls = ttk.LabelFrame(parent, text="3. Estados-limite de serviço")
    sls.pack(fill="x", pady=(0, 8))
    ttk.Label(sls, text="Combinações ELS").grid(row=0, column=0, sticky="w", padx=6, pady=4)
    ttk.Entry(sls, textvariable=self.var_service_case).grid(row=0, column=1, sticky="ew", padx=6, pady=4)
    ttk.Checkbutton(sls, text="Reconhecer automaticamente o regime", variable=self.var_service_auto_regime).grid(row=1, column=0, columnspan=2, sticky="w", padx=6, pady=3)
    ttk.Label(sls, text="Regime base").grid(row=2, column=0, sticky="w", padx=6, pady=4)
    ttk.Combobox(sls, textvariable=self.var_service_regime, values=["Quase-permanente / longo prazo", "Frequente / repetida", "Característica / curta duração"], state="readonly").grid(row=2, column=1, sticky="ew", padx=6, pady=4)
    ttk.Label(sls, text="Condição de apoio").grid(row=3, column=0, sticky="w", padx=6, pady=4)
    ttk.Combobox(sls, textvariable=self.var_support_condition, values=["Automática / por tabela", "Entre apoios (y0=yL=0)", "Consola - encastrada à esquerda", "Consola - encastrada à direita", "Encastre-encastre"], state="readonly").grid(row=3, column=1, sticky="ew", padx=6, pady=4)
    ttk.Label(sls, text="Histórico").grid(row=4, column=0, sticky="w", padx=6, pady=4)
    ttk.Combobox(sls, textvariable=self.var_history_mode, values=["Duas fases G+Q", "Uma idade efectiva"], state="readonly").grid(row=4, column=1, sticky="ew", padx=6, pady=4)
    self._add_label_entry(sls, "Fração permanente [%]", self.var_permanent_fraction, 5)
    self._add_label_entry(sls, "t0,G [d]", self.var_t0_permanent, 6)
    self._add_label_entry(sls, "t0,Q [d]", self.var_t0_variable, 7)
    self._add_label_entry(sls, "Humidade RH [%]", self.var_service_rh, 8)
    self._add_label_entry(sls, "t0 efectivo [d]", self.var_service_t0, 9)
    self._add_label_entry(sls, "Idade final t [d]", self.var_service_t, 10)
    self._add_label_entry(sls, "Início da secagem ts [d]", self.var_service_ts, 11)
    ttk.Label(sls, text="Classe de cimento").grid(row=12, column=0, sticky="w", padx=6, pady=4)
    ttk.Combobox(sls, textvariable=self.var_service_cement, values=["S", "N", "R"], state="readonly", width=8).grid(row=12, column=1, sticky="ew", padx=6, pady=4)
    self._add_label_entry(sls, "h0 [mm] (0=automático)", self.var_service_h0, 13)
    ttk.Checkbutton(sls, text="Considerar retracção", variable=self.var_service_shrinkage).grid(row=14, column=0, columnspan=2, sticky="w", padx=6, pady=3)
    ttk.Label(sls, text="Campo vazio: verifica todas as combinações ELS reconhecidas. Várias combinações podem ser separadas por ponto e vírgula.", style="Subtle.TLabel", wraplength=320, justify="left").grid(row=15, column=0, columnspan=2, sticky="w", padx=6, pady=(0, 4))
    sls.columnconfigure(1, weight=1)

    filters = ttk.LabelFrame(parent, text="4. Filtros")
    filters.pack(fill="x", pady=(0, 8))
    ttk.Label(filters, text="Viga/membro").grid(row=0, column=0, sticky="w", padx=6, pady=4)
    ttk.Entry(filters, textvariable=self.var_filter_member).grid(row=0, column=1, sticky="ew", padx=6, pady=4)
    ttk.Label(filters, text="Estado").grid(row=1, column=0, sticky="w", padx=6, pady=4)
    ttk.Combobox(filters, textvariable=self.var_filter_status, values=["Todos", "OK", "Falha", "Verificar"], state="readonly").grid(row=1, column=1, sticky="ew", padx=6, pady=4)
    ttk.Label(filters, text="Tipo de falha").grid(row=2, column=0, sticky="w", padx=6, pady=4)
    ttk.Combobox(filters, textvariable=self.var_filter_fail, values=["Todos", "flexao", "corte", "torcao", "pormenorizacao", "els", "dados", "outra"], state="readonly").grid(row=2, column=1, sticky="ew", padx=6, pady=4)
    ttk.Button(filters, text="Aplicar", command=self.apply_filters).grid(row=3, column=0, sticky="ew", padx=4, pady=4)
    ttk.Button(filters, text="Limpar", command=self.clear_filters).grid(row=3, column=1, sticky="ew", padx=4, pady=4)
    filters.columnconfigure(1, weight=1)

    actions = ttk.LabelFrame(parent, text="5. Cálculo e exportação")
    actions.pack(fill="x", pady=(0, 8))
    ttk.Button(actions, text="Calcular", command=self.run_design, style="Primary.TButton").grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=4)
    ttk.Button(actions, text="Memória de cálculo (.xlsx)", command=self.export_excel).grid(row=1, column=0, sticky="ew", padx=4, pady=4)
    ttk.Button(actions, text="Relatório (.pdf)", command=self.export_pdf_report).grid(row=1, column=1, sticky="ew", padx=4, pady=4)
    ttk.Label(actions, text="Tipo de relatório").grid(row=2, column=0, sticky="w", padx=6, pady=4)
    ttk.Combobox(actions, textvariable=self.var_pdf_scope, values=PDF_SCOPES_Reporting, state="readonly").grid(row=2, column=1, sticky="ew", padx=6, pady=4)
    ttk.Button(actions, text="Tabela de resultados (.csv)", command=self.export_csv).grid(row=3, column=0, sticky="ew", padx=4, pady=4)
    ttk.Button(actions, text="Abrir repositório", command=lambda: webbrowser.open_new(GITHUB_URL)).grid(row=3, column=1, sticky="ew", padx=4, pady=4)
    actions.columnconfigure(0, weight=1); actions.columnconfigure(1, weight=1)

    status_box = ttk.LabelFrame(parent, text="6. Estado")
    status_box.pack(fill="x", pady=(0, 8))
    ttk.Label(status_box, textvariable=self.status_var, wraplength=340, justify="left").pack(fill="x", padx=6, pady=(4, 2))
    ttk.Progressbar(status_box, variable=self.progress_var, maximum=100).pack(fill="x", padx=6, pady=(2, 2))
    ttk.Label(status_box, textvariable=self.progress_text_var, anchor="e").pack(fill="x", padx=6, pady=(0, 4))

    notes = ttk.LabelFrame(parent, text="7. Notas")
    notes.pack(fill="x", pady=(0, 8))
    ttk.Label(notes, text=(
        "• Utilize várias estações ao longo de cada viga.\n"
        "• Confirme os eixos locais e a geometria identificada.\n"
        "• Para ELS, recomenda-se um mínimo de cinco estações por combinação.\n"
        "• Os estados ‘Verificar’ exigem revisão técnica antes da aprovação."
    ), wraplength=340, justify="left").pack(fill="x", padx=6, pady=6)


BeamsEC2App._build_sidebar = _build_sidebar_clean


def _build_instructions_clean(self, parent):
    outer = ttk.Frame(parent, padding=10)
    outer.pack(fill="both", expand=True)
    outer.rowconfigure(1, weight=1); outer.columnconfigure(0, weight=1)
    ttk.Label(outer, text="Instruções de utilização", style="Header.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))
    host = ttk.Frame(outer); host.grid(row=1, column=0, sticky="nsew")
    txt = self._make_text_view(host)
    required = " | ".join(TABLE_COLUMNS_REQUIRED)
    recommended = " | ".join(TABLE_COLUMNS_RECOMMENDED)
    els = " | ".join(TABLE_COLUMNS_ELS)
    geometry = " | ".join(TABLE_COLUMNS_GEOMETRY)
    content = (
        "1. OBJECTIVO\n"
        "O BeamsEC2 dimensiona e verifica vigas de betão armado segundo a NP EN 1992-1-1. A aplicação recebe uma tabela de esforços por membro, estação e combinação, cria as envolventes e apresenta resultados ELU, ELS e de pormenorização.\n\n"
        "2. TABELA-TIPO\n"
        "Cada linha deve corresponder a uma estação de uma viga numa combinação de acções. Não agregue várias estações na mesma célula.\n\n"
        f"Colunas obrigatórias:\n{required}\n\n"
        f"Colunas recomendadas:\n{recommended}\n\n"
        f"Colunas opcionais para ELS e armadura variável:\n{els}\n\n"
        f"Colunas opcionais para identificação de secções T ou I:\n{geometry}\n\n"
        "Use o botão ‘Guardar tabela-tipo’ para obter um ficheiro preparado com os cabeçalhos reconhecidos.\n\n"
        "3. COMBINAÇÕES DE AÇÕES\n"
        "Para ELU, importe os pontos necessários para representar os extremos de momento, esforço transverso e torção. Para ELS, cada combinação deve conter pelo menos três estações; recomendam-se cinco ou mais, incluindo apoios, mudanças de sinal e máximos interiores.\n\n"
        "4. GEOMETRIA\n"
        "Secções rectangulares utilizam HY e HZ. Secções T podem ser definidas por BF e HF. Secções I podem ser introduzidas pelas dimensões dos banzos e da alma ou identificadas através das propriedades geométricas. Confirme sempre a geometria indicada no separador de envelopes antes de aceitar o cálculo.\n\n"
        "5. Estados Limites de Serviço - ELS\n"
        "Deixe ‘Combinações ELS’ em branco para verificar todas as combinações reconhecidas. O programa determina governantes separados para fendilhação, flecha, tensão no aço e tensão no betão. A condição de apoio pode ser global ou definida na própria tabela.\n\n"
        "6. RESULTADOS\n"
        "‘OK’ indica cumprimento dos critérios implementados. ‘Falha’ identifica incumprimento. ‘Verificar’ assinala dados insuficientes, hipóteses que exigem confirmação ou situações fora do âmbito automático. A memória de cálculo contém os dados e resultados de auditoria; os relatórios em PDF destinam-se à apresentação.\n\n"
        "7. CONTROLO DE QUALIDADE\n"
        "Antes da aprovação, confirme as unidades, os eixos locais, as combinações, as condições de apoio, a geometria, os casos governantes e a coerência construtiva das armaduras."
    )
    txt.insert("1.0", content)
    txt.config(state="disabled")


BeamsEC2App._build_instructions_tab = _build_instructions_clean


def _prepare_input_frames(df: pd.DataFrame, moment_axis="my", shear_axis="fz", torsion_axis="mx"):
    """Executa a cadeia pública completa de limpeza e identificação geométrica."""
    clean = _implementation.clean_dataframe(df)
    envelopes = _implementation.build_beam_envelopes(
        clean,
        moment_axis=moment_axis,
        shear_axis=shear_axis,
        torsion_axis=torsion_axis,
    )
    return clean, envelopes


def _load_df_clean(self, df: pd.DataFrame, source: str = ""):
    """Carrega a tabela usando os módulos finais, sem regressar às rotinas base."""
    self.df_raw = df.copy()
    self.df_clean, self.df_env = _prepare_input_frames(
        df,
        moment_axis=self.var_moment_axis.get().lower(),
        shear_axis=self.var_shear_axis.get().lower(),
        torsion_axis=self.var_torsion_axis.get().lower(),
    )
    self.df_calc_input = pd.DataFrame()
    self.df_results = pd.DataFrame()
    self.df_summary = pd.DataFrame()
    self.df_failures = pd.DataFrame()
    self.df_ok = pd.DataFrame()
    self.df_filtered = pd.DataFrame()
    self.df_validation = _implementation.build_data_validation(self.df_clean, self.df_env)
    self.df_notes = _implementation.build_normative_notes()
    self.show_df(self.tree_input, self.df_clean)
    self.show_df(self.tree_env, self.df_env)
    self.show_df(self.tree_validation, self.df_validation)
    self.show_df(self.tree_results, self.df_results)
    self.show_df(self.tree_summary, self.df_summary)
    self.show_df(self.tree_failures, self.df_failures)
    self.show_df(self.tree_shortlists, pd.DataFrame())
    self.show_df(self.tree_notes, self.df_notes)
    self.update_report()
    self.progress_var.set(0.0)

    section_counts = ""
    if "section_type" in self.df_env.columns and not self.df_env.empty:
        counts = self.df_env["section_type"].fillna("Não identificada").astype(str).value_counts()
        section_counts = "; secções: " + ", ".join(f"{name}={int(count)}" for name, count in counts.items())
    self.status_var.set(
        f"Tabela carregada ({source}): {len(self.df_clean)} linhas; "
        f"{len(self.df_env)} envelopes{section_counts}."
    )


def _import_table_clean(self):
    path = filedialog.askopenfilename(
        title="Importar tabela",
        filetypes=[
            ("Ficheiros de tabela", "*.xlsx *.xls *.csv *.txt *.tsv"),
            ("Todos os ficheiros", "*.*"),
        ],
    )
    if not path:
        return
    try:
        df, info = read_table_file(path)
        if df is None or df.empty:
            raise ValueError("a tabela não contém linhas de dados")
        self.input_file_path = path
        self.load_df(df, source=f"{os.path.basename(path)}; {info.description}")
    except Exception as err:
        messagebox.showerror(
            "Erro",
            "Não foi possível importar a tabela.\n\n"
            f"{err}\n\n"
            "Confirme se o ficheiro contém uma tabela com cabeçalhos na primeira linha.",
        )


BeamsEC2App.load_df = _load_df_clean
BeamsEC2App.import_file = _import_table_clean


def _export_memory_clean(self):
    if self.df_results is None or self.df_results.empty:
        messagebox.showwarning("Aviso", "Execute o cálculo antes de exportar a memória de cálculo.")
        return
    path = filedialog.asksaveasfilename(
        title="Exportar memória de cálculo",
        defaultextension=".xlsx",
        filetypes=[("Memória de cálculo", "*.xlsx")],
    )
    if not path:
        return
    try:
        self._write_excel(path)
        self.status_var.set(f"Memória de cálculo exportada: {path}")
    except Exception as err:
        messagebox.showerror("Erro", f"Não foi possível exportar a memória de cálculo.\n\n{err}")


BeamsEC2App.export_excel = _export_memory_clean


def _export_template_clean(self):
    path = filedialog.asksaveasfilename(
        title="Guardar tabela-tipo",
        defaultextension=".xlsx",
        filetypes=[("Tabela-tipo", "*.xlsx")],
    )
    if not path:
        return
    try:
        sample = pd.DataFrame([
            {
                "Member/Node/Case": "1/1/101 (C)", "Station (m)": 0.0,
                "FX (kN)": 0.0, "FY (kN)": 0.0, "FZ (kN)": 45.0,
                "MX (kNm)": 0.0, "MY (kNm)": -35.0, "MZ (kNm)": 0.0,
                "Length (m)": 6.0, "Material": "C30/37", "HY (cm)": 30.0,
                "HZ (cm)": 55.0, "Name": "V1", "Story": "PISO 1",
                "Support Condition": "Entre apoios (y0=yL=0)",
            },
            {
                "Member/Node/Case": "1/2/101 (C)", "Station (m)": 3.0,
                "FX (kN)": 0.0, "FY (kN)": 0.0, "FZ (kN)": 0.0,
                "MX (kNm)": 0.0, "MY (kNm)": 65.0, "MZ (kNm)": 0.0,
                "Length (m)": 6.0, "Material": "C30/37", "HY (cm)": 30.0,
                "HZ (cm)": 55.0, "Name": "V1", "Story": "PISO 1",
                "Support Condition": "Entre apoios (y0=yL=0)",
            },
            {
                "Member/Node/Case": "1/3/101 (C)", "Station (m)": 6.0,
                "FX (kN)": 0.0, "FY (kN)": 0.0, "FZ (kN)": -45.0,
                "MX (kNm)": 0.0, "MY (kNm)": -35.0, "MZ (kNm)": 0.0,
                "Length (m)": 6.0, "Material": "C30/37", "HY (cm)": 30.0,
                "HZ (cm)": 55.0, "Name": "V1", "Story": "PISO 1",
                "Support Condition": "Entre apoios (y0=yL=0)",
            },
        ], columns=self.TEMPLATE_COLUMNS)
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            sample.to_excel(writer, sheet_name="TABELA_TIPO", index=False)
            writer.book.properties.title = f"{APP_NAME} — tabela-tipo"
            writer.book.properties.creator = ""
            writer.book.properties.lastModifiedBy = ""
            writer.book.properties.description = "Tabela de entrada para o BeamsEC2."
        self.status_var.set(f"Tabela-tipo guardada: {path}")
    except Exception as err:
        messagebox.showerror("Erro", f"Não foi possível guardar a tabela-tipo.\n\n{err}")


BeamsEC2App.export_template = _export_template_clean


# 
# 
__all__ = [
    "APP_NAME", "APP_VERSION", "APP_TITLE", "BeamsEC2App", "BeamDesigner",
    "clean_dataframe", "build_beam_envelopes", "reduce_to_governing_cases",
    "read_table_file", "_prepare_input_frames",
    "build_summary_by_member", "build_normative_notes",
]
