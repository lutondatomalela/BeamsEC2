# BeamsEC2

Aplicação desktop para o dimensionamento e a verificação de vigas de betão armado segundo a **NP EN 1992-1-1**.

A versão pública actual é a **v0.1.2**. O projecto inclui uma aplicação gráfica, uma distribuição executável para Windows e o código-fonte modular para revisão e desenvolvimento.

## Instalação para utilizadores

A forma recomendada é descarregar a versão Windows na página **Releases** do repositório.

Ficheiros disponíveis:

- `BeamsEC2.exe` — aplicação portátil para Windows de 64 bits;
- `BeamsEC2-v0.1.2-Windows-x64.zip` — aplicação, tabela-tipo, README e changelog.

Não é necessário instalar Python nem utilizar o terminal. Depois de descarregar, basta abrir `BeamsEC2.exe`.

> O executável ainda não possui assinatura digital. O Windows pode apresentar um aviso SmartScreen nas primeiras versões. O código-fonte e o processo de compilação estão disponíveis no repositório para auditoria.

## Funcionalidades

- importação de tabelas de esforços por membro, estação e combinação;
- leitura de `.xlsx`, `.xls`, `.csv`, `.txt` e `.tsv`;
- reconhecimento de UTF-8, UTF-8 com BOM, UTF-16, Windows-1252 e Latin-1;
- detecção de tabulação, ponto e vírgula, vírgula e barra vertical;
- criação de envelopes ELU e ELS;
- flexão positiva e negativa;
- esforço transverso e torção;
- fendilhação, tensões e deformação por integração de curvaturas;
- fluência, retracção e histórico simplificado de carregamento;
- secções rectangulares, T, I simétricas e I assimétricas;
- identificação automática de secções I através das propriedades geométricas;
- selecção de armaduras longitudinais, estribos e armadura de pele;
- verificação de espaçamentos, amarração e pormenorização longitudinal;
- relatórios PDF e memória de cálculo em formato `.xlsx`;
- testes internos de sanidade e regressão.

## Tabela de entrada

Cada linha representa uma estação de uma viga numa combinação de acções. Devem ser utilizadas várias estações ao longo de cada membro; para ELS recomendam-se pelo menos cinco.

Colunas obrigatórias:

```text
Member/Node/Case | FZ (kN) | MX (kNm) | MY (kNm) |
Length (m) | Material | HY (cm) | HZ (cm)
```

Colunas recomendadas:

```text
Name | Story
```

Para identificação automática de secções I:

```text
VY (cm) | VZ (cm) | VPY (cm) | VPZ (cm) | AX (cm2) |
IY (cm4) | IZ (cm4)
```

A geometria também pode ser fornecida directamente:

```text
Section Type | B Top (cm) | TF Top (cm) | B Bottom (cm) |
TF Bottom (cm) | TW (cm) | I Top
```

A tabela-tipo incluída contém ainda colunas opcionais para condições de apoio, armadura local e secções T ou I. Os eixos utilizados no cálculo podem ser alterados na interface.

## Identificação geométrica

A classificação é apresentada no separador **Envelopes** após a importação. Para secções I reconstruídas, o programa indica:

- tipo identificado;
- dimensões aproximadas dos banzos e da alma;
- origem da identificação;
- nível de confiança;
- erro de ajustamento das propriedades.

A geometria e a orientação dos eixos locais devem ser confirmadas antes da aprovação do cálculo.

## Estados dos resultados

- **OK** — os critérios implementados são satisfeitos;
- **Falha** — foi identificado um incumprimento;
- **Verificar** — existem dados insuficientes, hipóteses a confirmar ou uma situação que exige revisão técnica.

## Utilização a partir do código-fonte

Requer Python 3.10 ou superior.

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
python -m pip install -r requirements.txt
python BeamsEC2.py
```

Linux/macOS:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python BeamsEC2.py
```

## Testes

```bash
python selftest.py
```

Os testes incluem verificações de cálculo, importação UTF-16, preservação das propriedades geométricas e identificação de secções I assimétricas pela cadeia utilizada na interface.

## Compilação do executável Windows

A compilação está automatizada por GitHub Actions através de:

```text
.github/workflows/build-windows.yml
```

Também pode ser efectuada localmente, em Windows, executando por duplo clique:

```text
build_windows.bat
```

As instruções completas estão em [BUILD_WINDOWS.md](BUILD_WINDOWS.md).

## Estrutura do projecto

```text
BeamsEC2.py                  ponto de entrada
beams_ec2/
  base.py                    classes base e interface
  design.py                  dimensionamento e pormenorização
  reporting.py               relatórios e exportações
  geometry.py                secções rectangulares, T e I
  serviceability.py          verificações ELS
  advanced.py                condições de apoio, histórico e validação
  table_io.py                leitura robusta das tabelas
  release.py                 configuração pública da v0.1.2
selftest.py                  testes internos e de regressão
table_template.xlsx          tabela-tipo de entrada
BeamsEC2.spec                configuração do executável
build_windows.bat            compilação local em Windows
requirements.txt             dependências da aplicação
requirements-build.txt       dependências de compilação
```

## Âmbito e responsabilidade

O BeamsEC2 é uma ferramenta de apoio ao dimensionamento. A interpretação do modelo estrutural, a selecção das combinações, a confirmação das condições de apoio, a validação das geometrias e a aprovação das soluções permanecem sob responsabilidade do utilizador.

### Seleção das combinações (desenvolvimento a partir da v0.1.2)

O campo opcional **Combinações ELU** aceita listas e intervalos, por exemplo `101-117 201-208`. O campo **Combinações ELS** aceita o mesmo formato e nomes completos separados por ponto e vírgula. Os números são comparados exatamente: selecionar `101` não seleciona `1101`.

Uma combinação explicitamente selecionada como ELS deixa de entrar no cálculo ELU. Sobreposições explícitas entre os dois grupos e números inexistentes são recusados antes de iniciar o cálculo. Com o campo ELU vazio, mantém-se a seleção original por nome, excluindo também os ELS indicados. Com o campo ELS vazio, mantém-se o reconhecimento original pelo nome; para combinações apenas numéricas, indique os grupos explicitamente.

A importação por nós continua disponível sem `Station`. A identificação `Member/Point (m)/Case` também é aceite, preservando rótulos como `+/- MY x=...`. Neste passo, estes rótulos são tratados como identificadores: não são convertidos em coordenadas. Os métodos de cálculo e as hipóteses ELS da versão original mantêm-se e serão objeto de validação própria.

### Grupos explícitos ELS

Os campos **ELS característica**, **ELS frequente** e **ELS quase-permanente** ativam o modo explícito quando pelo menos um é preenchido. Neste modo, preencha também **Combinações ELU** e deixe vazio **ELS (modo anterior)**. Cada grupo aceita listas/intervalos. Os casos sem grupo ficam excluídos e a mesma combinação não pode pertencer a dois grupos. `CQC` não determina um regime ELS.

- Característica: verificações das tensões no aço e no betão.
- Quase-permanente: fissuração, flecha final e controlo da hipótese de fluência linear.
- Frequente: valores informativos, sem governar os critérios anteriores.

Sem resultados CAR ou QP, o ELS global fica incompleto. A tensão QP acima do limite de fluência linear pede revisão do modelo de fluência; não equivale, por si só, a falha resistente. A folha **11B_Grupos_Combinacoes** regista também os casos excluídos; **11C_ELS_Combinacoes** conserva os resultados por grupo e combinação.

A importação por nós continua aceite. No modo explícito, a flecha calculada com posições inferidas pela ordem das linhas, normalizadas ou ajustadas ao vão fica como **Dados insuficientes**, sem impedir as restantes verificações disponíveis. Os métodos originais de secção mantêm-se nesta etapa. Deixar os três novos campos vazios mantém o modo anterior, com as limitações já documentadas.

### Executável de teste v0.1.3-dev1

A distribuição portátil desta etapa contém o executável, a tabela-tipo e a documentação. Extraia o ZIP para uma pasta nova e execute `BeamsEC2.exe`; não requer instalação de Python. O ficheiro BUILD.txt identifica o commit, as dependências e o SHA256 do executável. A compilação só disponibiliza o pacote depois de um ensaio dentro do próprio executável com importação XLSX, nós sem Station, seleção dos grupos, cálculo e exportações XLSX/PDF.

O programa reutiliza verificações ELS apenas para dados de secção/armadura iguais na mesma análise. As tabelas ELS relacionam-se com os resultados ELU através de `service_cage_id`. Cada alteração de dados ou parâmetros inicia uma nova análise, sem reutilização de resultados anteriores. A pormenorização usa os grupos ELU selecionados e é calculada uma vez por solução distinta; um diagrama incompleto conserva as indicações de amarração, mas não origina perfis de dispensas.

Esta é uma distribuição de teste. As limitações do motor original documentadas em `docs/RESTART_VALIDATION.md` continuam aplicáveis.
