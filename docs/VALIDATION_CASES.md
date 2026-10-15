# Casos independentes de validação

As referências seguintes são calculadas no módulo de testes por expressões analíticas, sem chamar as rotinas do programa para obter os valores esperados. Não constituem ensaios laboratoriais nem uma comparação com software externo certificado.

## Secção rectangular em ELS

Dados: b=300 mm; h=600 mm; As,inferior=1500 mm²; As,superior=600 mm²; eixos a 550 e 50 mm do topo; Es=200000 MPa; Ec=30000 MPa; fctm=3 MPa; sem retração. A zona comprimida contém a armadura superior.

Secção fissurada: n=Es/Ec, B=n As,inferior+(n-1) As,superior e C=-n As,inferior d-(n-1) As,superior d'. O eixo neutro é a raiz positiva de b x²/2+B x+C=0. A inércia é b x³/3+n As,inferior(d-x)²+(n-1) As,superior(x-d')².

Secção não fissurada: a homogeneização adiciona (n-1) As à área bruta de betão. A tensão do aço antes da fendilhação utiliza o centroide e a inércia desta secção.

| Grandeza | Referência |
| --- | ---: |
| Eixo neutro fissurado x | 154,820453497 mm |
| Inércia fissurada | 1 970 120 570,164492 mm⁴ |
| Centroide não fissurado | 306,644085461 mm |
| Inércia não fissurada | 6 135 278 791,036998 mm⁴ |
| Tensão no aço para M=10 kNm, não fissurada | 2,644334217 MPa |
| Tensão no aço para M=100 kNm, fissurada | 133,724318700 MPa |
| wk para M=100 kNm, curta duração | 0,092751187450 mm |
| Curvatura interpolada para M=100 kNm, curta duração | 1,357001014105 × 10⁻⁶ mm⁻¹ |
| Curvatura para Ec,eff=15000 MPa, beta=0,5 | 1,806108741314 × 10⁻⁶ mm⁻¹ |

Para wk: diâmetro tracionado 20 mm, recobrimento 35 mm, estribo 8 mm, espaçamento livre 100 mm e kt=0,6. Aplicam-se as expressões (7.8), (7.9) e (7.11) da NP EN 1992-1-1:2010. A curvatura usa a interpolação da expressão (7.18), com zeta da expressão (7.19). O teste diferido isola a rigidez com Ec,eff conhecido; não valida por si só o modelo completo de fluência.

## Integração da flecha

- Momento constante em secção fissurada: flecha máxima kappa L²/8 num vão entre apoios. Ensaio completo da rotina de ELS, desde os dados da secção até à flecha.
- Dois vãos contínuos iguais, com carga uniforme q: no primeiro vão M(x)=3qLx/8-qx²/2. Para rigidez constante, y(x)=q/EI (Lx³/16-x⁴/24-L³x/48). O extremo interior verifica x/L=(1+sqrt(33))/16. O teste confere o sinal do momento e a integração sobre um diagrama que muda de sinal.
- Inversão do momento numa secção e armadura simétricas: mesma largura de fendas e curvatura com sinal oposto.

O caso de dois vãos valida a integração com rigidez constante. Não é uma validação integral de uma viga contínua com fissuração variável e redistribuição estrutural.

## Dimensionamento e pormenorização

A seleção itera até 24 vezes por diâmetro de estribo (8, 10 e 6 mm), verifica as duas faces e conserva uma solução convergida antes de considerar a preferência entre alternativas. Os resultados incluem o número de iterações e o diâmetro utilizado no cálculo das posições. Se nenhuma alternativa convergir, o estado é Falha.

Os testes cobrem flexão positiva/negativa com armadura dupla, simetria da solução, estribos de 10 mm, secções impossíveis, espaçamento transversal dos ramos e largura média da zona tracionada nas secções T. A busca é limitada à gama construtiva implementada; não demonstra o mínimo global de aço entre todas as disposições possíveis.

## Interface Windows

O teste opcional `test_windows_gui.py` abre a aplicação Tk, importa duas combinações com cinco estações cada, executa o cálculo assíncrono ELU/ELS e exporta XLSX e os três tipos de PDF. Requer `BEAMSEC2_GUI_TESTS=1` em Windows e corre num passo próprio do CI. Verifica funcionamento e geração de ficheiros; não substitui inspeção visual dos relatórios e da interface.
