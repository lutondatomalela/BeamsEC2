# BeamsEC2

Aplicação desktop para o dimensionamento e a verificação de vigas de betão armado segundo a **NP EN 1992-1-1**.

O código-fonte nesta branch corresponde à **v0.2.0-rc6**, candidata de validação. Consulte a [avaliação técnica e os limites de utilização](docs/ROBUSTNESS_REVIEW.md). A distribuição Windows anteriormente publicada é a **v0.1.2** e não incorpora estas correções. O projecto inclui uma aplicação gráfica, uma distribuição executável para Windows e o código-fonte modular para revisão e desenvolvimento.

## Instalação para utilizadores

Para testar a **rc6**, abra o workflow **Validation** desta branch no separador **Actions** e descarregue o artefacto `BeamsEC2-rc6-Windows-x64` de uma execução concluída com sucesso. Extraia o ZIP e abra `BeamsEC2.exe`. O artefacto permanece disponível durante 30 dias.

A página **Releases** ainda contém a versão anterior v0.1.2.

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

Também são aceites tabelas `Member/Point (m)/Case`, com posições `user x=…`, `auto x=…`, `x=…`, `origin (…)` e `end (…)`. Rótulos `+/- MY x=…` são preservados. Sem posições, as tabelas por nós permitem verificar as secções disponíveis, mas a flecha fica sem dados suficientes. Posições inválidas explicitamente fornecidas continuam a impedir a importação.

Cada linha representa uma secção disponível de uma viga numa combinação de ações. Aceitam-se tabelas por nós sem posições e tabelas por pontos. As posições são opcionais para ELU e para tensões/fissuração nas secções fornecidas. A flecha por integração requer um diagrama com posições ao longo do vão; recomendam-se pelo menos cinco pontos.

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

## Classificação das combinações

A interface tem quatro campos independentes. Cada campo aceita listas e intervalos separados por espaços, vírgulas ou ponto e vírgula. A numeração não identifica automaticamente o estado limite.

| Campo | Exemplo de seleção | Utilização |
| --- | --- | --- |
| ELU | `101-133` | Dimensionamento e resistência |
| ELS característica | `205-220` | Tensões no aço e no betão |
| ELS frequente | `202` | Resultados separados, informativos para as verificações implementadas |
| ELS quase-permanente | `203` | Fissuração, flecha final e controlo da hipótese de fluência linear |

Os números acima são exemplos e devem corresponder à tabela importada. Sobreposições entre grupos e números não encontrados impedem o cálculo. Quando existe uma seleção manual, todos os casos não selecionados ficam excluídos; não são assumidos como ELU.

Sem seleção manual, apenas nomes explícitos como `ELU`, `ELS CARACTERÍSTICA`, `ELS FREQ` ou `ELS QP` são reconhecidos. A indicação `(C)` significa apenas combinação. `ELS` sem regime definido fica por classificar.

A ausência de combinações QP ou características para uma viga impede o estado global ELS **OK**, mas permite calcular o ELU e as verificações disponíveis. Se a tensão QP exceder 0,45 fck, o programa pede revisão da fluência não linear; isto não é confundido com o controlo de resistência às tensões características. A folha `04A_Grupos_Combinacoes` documenta a classificação e os casos excluídos.

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
python -m pip install -r requirements-test.txt
python selftest.py
python -m unittest discover -s tests -v
```

Os testes incluem verificações de cálculo, importação UTF-16, preservação das propriedades geométricas e identificação de secções I assimétricas pela cadeia utilizada na interface.

## Validação automática

O workflow `.github/workflows/validation.yml` executa os testes em Windows e Linux, com Python 3.10 e 3.12. O ensaio de integração Windows testa a janela Tk, o cálculo ELU/ELS e os relatórios. Depois dos testes, o workflow compila um executável Windows x64 e executa nele uma importação XLSX, um cálculo com os quatro grupos e as exportações XLSX e dos três PDF. Só depois disponibiliza o artefacto da candidata, acompanhado do commit de origem, dependências resolvidas e SHA256 em `BUILD.txt`. Consulte os [casos analíticos de validação](docs/VALIDATION_CASES.md).

As estações são expressas em metros. Os diagramas ELS devem cobrir 0 a L; diagramas parciais não são reescalados. Todas as combinações ELU são conservadas para as verificações acopladas. O programa adota uma armadura comum por membro e volta a verificar cada combinação; se a solução comum não convergir, o resultado é Falha. Os dados e os parâmetros são fixados durante cada cálculo.

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
  release.py                 configuração pública da versão candidata
selftest.py                  testes internos e de regressão
table_template.xlsx          tabela-tipo de entrada
requirements.txt             dependências da aplicação
```

## Âmbito e responsabilidade

O BeamsEC2 é uma ferramenta de apoio ao dimensionamento. A interpretação do modelo estrutural, a selecção das combinações, a confirmação das condições de apoio, a validação das geometrias e a aprovação das soluções permanecem sob responsabilidade do utilizador.

## Compilação Windows

Em Windows x64 com Python 3.12:

```powershell
python -m pip install -r requirements-build.txt
python -m PyInstaller --noconfirm --clean --onefile --windowed --name BeamsEC2 --hidden-import xlrd BeamsEC2.py
Start-Process -FilePath "$pwd/dist/BeamsEC2.exe" -ArgumentList "--smoke-test", "`"$pwd/out/frozen check`"" -Wait
Get-Content "out/frozen check/smoke-test.json"
```

O ensaio deve terminar com `"ok": true`. Sem `--smoke-test`, o executável abre a interface habitual. A compilação utiliza PyInstaller fixado e regista as versões efectivamente instaladas; não garante executáveis idênticos byte a byte. Os artefactos de CI destinam-se a validação da candidata e não substituem uma release aprovada.

Os cálculos ELS equivalentes são reutilizados para a mesma secção e armadura. Os resultados ELU continuam separados por combinação; os pontos ELS e a pormenorização da armadura comum são apresentados sem repetições por combinação ELU.

Sem posições ou com momentos diferentes na mesma posição, o programa calcula tensões e fissuração nas secções fornecidas com a armadura uniforme adotada. A flecha fica sem valor e identificada como «Dados insuficientes». Não são gerados perfis de dispensas de varões a partir de diagramas ELU incompletos. Estes resultados não demonstram os máximos entre secções importadas.
