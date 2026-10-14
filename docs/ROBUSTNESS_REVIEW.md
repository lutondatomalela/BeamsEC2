# Avaliação de robustez do BeamsEC2

Data: 14 de outubro de 2026. Base: `f883304d7a80e4f1425d6418546dd96429e8740a`.
Estado: versão candidata de validação, `v0.2.0-rc1`.

## Conclusão técnica

A versão de partida não deve ser considerada validada para utilização irrestrita em projeto. Os dez testes existentes passam, mas não cobrem a resistência à flexão, a interação corte/torção ou dados inválidos. A revisão corrige os problemas abaixo e estabelece limites explícitos. O executável anteriormente publicado não incorpora estas alterações.

## Problemas corrigidos

| Problema | Alteração | Evidência |
| --- | --- | --- |
| Aço comprimido assumido em cedência e limitado por uma percentagem arbitrária | Equilíbrio N=0 com compatibilidade de extensões, aço elástico/perfeitamente plástico e bloco rectangular para fck <= 50 MPa | Solução analítica de secção simplesmente armada, equilíbrio e aço sem cedência |
| Corte e torção calculados com inclinações independentes | Inclinação comum, definida por cot(theta), e controlo da expressão (6.29) | Caso com utilizações individuais de 0,70 que falha na interação |
| Área de um ramo de torção comparada com área total dos ramos | Conversão para área total de dois ramos; estribos fechados de dois ramos no cálculo com torção | Comparação dimensional com T/(Ak fyd cot(theta)) |
| Torção pequena descartada por T/TRd,max < 0,05 | Toda a torção não nula é tratada como torção de equilíbrio | Caso T=0,01 kNm exige armadura |
| Resistências das subsecções I somadas sem verificar a distribuição imposta | Modelo conservador limitado à alma e revisão obrigatória da disposição das armaduras | Não se declara validação universal de secções I à torção |
| Dados inválidos ou colunas de esforços ausentes convertidos em zero | Validação prévia das componentes selecionadas, dimensões, estações e classe de betão | Texto inválido, NaN, infinito, coluna ausente e secção variável rejeitados |
| Esforço normal e flexão na direção secundária omitidos do estado final | Estado Verificar e motivo explícito | Casos FX e MZ não recebem OK |
| Redução escalar de combinações podia omitir interação | Todas as combinações são conservadas | Regressão da conservação das linhas |
| Índices repetidos interrompiam envelopes | Índice normalizado na limpeza | Tabela concatenada com índices repetidos |
| Diagrama ELS parcial esticado para todo o vão | Estações mantidas em metros; exigir cobertura de 0 a L | Diagrama entre 0 e 1 m não é esticado para 6 m |
| Momentos distintos numa estação eram promediados | Diagrama insuficiente, sem média que esconda o pico | Duplicado conflitante rejeitado para integração |
| Resumo podia esconder Verificar ou misturar valores de combinações | Prioridade Falha, Verificar, OK; seleção de linha integral | Revisão preservada e valor ausente não preenchido por outro caso |
| Exceções na adição de folhas XLSX ignoradas | Erro explícito na cadeia final de exportação | Exportação e reabertura com folhas obrigatórias |

A interação usa os máximos absolutos V e T do mesmo membro e combinação. Se ocorrerem em estações diferentes, esta verificação é conservadora e pode exigir análise localizada.

## Base normativa consultada

- NP EN 1992-1-1:2010: 3.1.7 e Quadro 3.1; 6.1; 6.2.3; 6.3.2, expressões (6.28), (6.29) e (6.30); Secção 7.
- NP EN 1992-1-1:2010/AC:2012: correções em 6.1 relativas a compressão/excentricidade; não autorizam omitir N-M.
- NP EN 1992-1-1:2010/A1:2019: emendas consultadas; as alterações de punçoamento não são utilizadas para o cálculo das vigas nesta revisão.

Os documentos normativos fornecidos pelo utilizador não são redistribuídos no repositório. Esta revisão não constitui uma auditoria integral de todas as cláusulas do Eurocódigo, nem valida incêndio, pontes ou estruturas de retenção de líquidos.

## Verificação executada

- 28 testes automatizados de regressão adicionais, com subcasos de dados inválidos.
- 10 verificações internas já existentes.
- Exportação XLSX pela cadeia final da aplicação, reabertura e confirmação das folhas de resultados, corte/torção, geometria, ELS e pormenorização.
- Compilação sintática dos módulos e controlo de espaços do diff.
- CI preparado para Windows/Linux, Python 3.10 e 3.12; os resultados remotos devem ser consultados no pull request.

Os testes locais foram executados em Linux/Python 3.12. Não foi realizado ensaio visual da interface Windows nem compilação de um novo executável.

## Limites para aprovação em projeto

1. Flexão composta N-M e flexão biaxial não estão implementadas. A seleção de eixos diferentes de MY/FZ exige confirmação da rotação da geometria; o programa não a valida automaticamente.
2. Betões acima de C50/60 exigem os coeficientes lambda/eta e extensões próprios. O programa assinala Verificar; os números expedidos não devem ser aprovados sem cálculo dedicado.
3. A posição da armadura longitudinal considera estribos de 8 mm. Quando a solução requer estribos maiores, o resultado exige revisão da altura útil e da disposição real.
4. A sobreposição da armadura longitudinal de torção com flexão e a distribuição pelo perímetro exigem confirmação. Todos os casos com torção ativa ficam sujeitos a revisão, mesmo que as escoras verifiquem.
5. O dimensionamento longitudinal inicial ainda é aproximado. A resistência da armadura adotada é recalculada; uma solução que falhe pode requerer aumento manual ou alteração da secção. Não existe uma otimização iterativa completa para todos os casos.
6. O cálculo ELS mantém hipóteses de fluência, retração, condições de apoio e armadura local. A validação integral com exemplos independentes de vigas fissuradas contínuas, regime de combinações e flecha após construção permanece necessária.
7. Amarrações, emendas, decalagem, armadura de pele, corte entre alma e banzos, aberturas e regiões D devem ser conferidos nos desenhos e com cálculos adequados.
8. Os resumos apresentam um caso representativo prioritário; a aprovação deve consultar todas as combinações na folha de resultados completos.

A versão candidata melhora a segurança dos resultados e a rastreabilidade. A designação de versão estável para projeto deve aguardar os ensaios independentes e de interface acima; não é sustentada apenas pelo número de testes aprovados.
