# BeamsEC2

Aplicação desktop em Python para o dimensionamento e a verificação de vigas de betão armado segundo a **NP EN 1992-1-1**.

A versão pública actual é a **v0.1**. O projecto está separado por domínio funcional para facilitar manutenção, revisão e testes.

## Funcionalidades

- Importação de tabelas de esforços por membro, estaçãoe combinação;
- leitura de ficheiros `.xlsx`, `.xls`, `.csv`, `.txt` e `.tsv`;
- reconhecimento de UTF-8, UTF-8 com BOM, UTF-16, Windows-1252 e Latin-1;
- detecção de tabelas separadas por tabulação, ponto e vírgula, vírgula ou barra vertical;
- criação de envelopes ELU e ELS;
- flexão positiva e negativa;
- esforço transverso e torção;
- fendilhação, tensões e deformação por integração de curvaturas;
- fluência, retracção e histórico simplificado de carregamento;
- secções rectangulares, T, I simétricas e assimétricas;
- identificação automática de secções I através das propriedades geométricas da tabela;
- selecção de armaduras longitudinais, estribos e armadura de pele;
- verificação de espaçamentos, amarração e pormenorização longitudinal;
- relatório `.pdf` e memória de cálculo em formato `.xlsx`;
- testes internos de sanidade e regressão.

## Estrutura do projecto

```text
BeamsEC2.py                  (main) ponto de entrada
beams_ec2/
  base.py                    leitura de dados, classes base e interface
  design.py                  dimensionamento e pormenorização
  reporting.py               relatórios e exportações
  geometry.py                geometria das vigas (secções rectangulares, T e I)
  serviceability.py          verificações para os Estado Limites de Serviço (ELS)
  advanced.py                condições de apoio, histórico e validação
  table_io.py                leitura robusta das tabelas
  release.py                 configuração pública da v0.1
selftest.py                  testes internos e de regressão
table_template.xlsx          tabela-tipo de entrada
requirements.txt             dependências
```

## Instalação

Requer Python 3.10 ou superior.

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

Linux/macOS:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Execução

```bash
python BeamsEC2.py
```

## Tabela de entrada

Cada linha representa uma estação de uma viga numa combinação de acções. Utilize várias estações ao longo de cada membro; para ELS recomendam-se pelo menos cinco.

Colunas obrigatórias:

```text
Member/Node/Case    | FZ    (kN)    | MX    (kNm)    | MY (kNm)    | Length    (m)    | Material    | HY    (cm) | HZ    (cm) | VY    (cm) | VZ    (cm) | VPY (cm) | VPZ (cm) | AX (cm2) | AY (cm2) | AZ (cm2) | IX (cm4) | IY (cm4) | IZ (cm4)
```

Colunas recomendadas:

```text
Name | Story
```

A geometria também pode ser fornecida directamente através de:

```text
Section Type | B Top (cm) | TF Top (cm) | B Bottom (cm) |
TF Bottom (cm) | TW (cm) | I Top
```

## Identificação geométrica

A classificação é apresentada no separador **Envelopes** imediatamente após a importação. Para secções I reconstruídas, o programa indica:

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

## Validação

Execute os testes internos com:

```bash
python selftest.py
```

A v0.1 acrescenta testes específicos para:

- importação de tabelas UTF-16;
- preservação das propriedades geométricas;
- identificação de secções I assimétricas pela cadeia utilizada na interface.

Os resultados de elementos governantes devem ser revistos e comparados com uma verificação independente durante a adopção da ferramenta em projecto.

## Âmbito e responsabilidade

O BeamsEC2 é uma ferramenta de apoio ao dimensionamento. A interpretação do modelo estrutural, a selecção das combinações, a confirmação das condições de apoio, a validação das geometrias e a aprovação das soluções permanecem sob responsabilidade do utilizador.

## Repositório

O programa utiliza o endereço configurado em `GITHUB_URL` para abrir o repositório e associar o nome BeamsEC2 nos relatórios.
