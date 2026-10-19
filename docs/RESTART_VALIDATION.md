# Validação do reinício a partir da versão pública

Base: commit `f883304d7a80e4f1425d6418546dd96429e8740a` da `main` (v0.1.2).

## Âmbito desta alteração

Seleção de combinações e identificação das linhas importadas. Mantêm-se as rotinas de dimensionamento, as hipóteses ELS e a leitura de tabelas por nós sem coordenadas. Não foram incorporadas as candidatas rc1–rc7.

O novo campo ELU é opcional. Uma combinação explicitamente indicada como ELS deixa de entrar no cálculo ELU. A seleção numérica é exata, aceita listas/intervalos e rejeita números inexistentes e sobreposições explícitas.

## Verificação local em 19 de outubro de 2026

- Os dez testes internos da versão pública passam.
- Oito testes de importação e seleção passam.
- CSV por nós: 4 788 linhas, 57 barras, 42 combinações, sem coluna Station.
- CSV por pontos: 704 970 linhas, 57 barras e 42 combinações após corrigir o reconhecimento do cabeçalho e os rótulos com barras.
- Comparação no CSV por nós: seleção de teste ELU `101-117 201-208` e ELS `302-318`, sem constituir recomendação para a classificação real das ações.
- Os 1 425 resultados ELU selecionados mantêm os valores das 77 colunas numéricas e os estados do dimensionamento original para as mesmas combinações.

Os CSV do utilizador não são incluídos no repositório. Os tempos dependem do ambiente e não são usados como critério de validação estrutural.

## Limites desta etapa

Esta comparação demonstra preservação dos cálculos existentes, não a sua correção regulamentar. A versão original infere diagramas pela ordem das linhas quando faltam posições e pode ajustar as posições ao comprimento. Essas hipóteses permanecem nesta alteração e exigem revisão antes de validar flechas para utilização em projeto. A separação entre ELS característica, frequente e quase-permanente também não faz parte desta etapa: mantém-se o regime original configurado pelo utilizador.

## Etapa 2 — grupos ELS explícitos

Foram acrescentados nove testes para o encaminhamento dos regimes e um ensaio da janela Windows com tabela por nós sem Station, ELU CQC, um caso excluído e exportações XLSX/PDF. O ensaio altera um campo ELS durante o cálculo para confirmar que os resultados conservam a seleção validada no arranque.

O modo explícito separa tensões CAR, fissuração/flecha QP e informação frequente. A seleção é independente da numeração e dos rótulos CQC. Os critérios já existentes são encaminhados por regime; esta etapa não constitui uma validação independente das resistências ou dos modelos ELS originais.

Referências consultadas: NP EN 1992-1-1:2010, 7.2(2), 7.2(3), 7.2(5), 7.3/Quadro 7.1N e 7.4. A aplicabilidade dos limites às classes de exposição e às ações impostas deve continuar a ser revista no âmbito da validação do motor.

No modo explícito, o estado da flecha fica incompleto se o diagrama for insuficiente, inferido pela ordem das linhas ou ajustado ao vão. Os restantes critérios não ficam bloqueados por essa condição; esforços axiais relevantes continuam a exigir uma análise N-M própria. Um resultado incompleto não governante também não desaparece do estado ELS global.

## Etapa 3 — desempenho e distribuição de teste

Ensaio no CSV por nós (4 788 linhas), com seleção de teste ELU `101-117 201-208`, QP `302`, frequente `303` e característica `304`:

| Fase | Antes | Depois |
|---|---:|---:|
| ELS | 32,14 s | 2,60 s |
| Pormenorização | 31,04 s | 0,64 s |

Os tempos foram medidos no ambiente local e excluem a importação e o cálculo ELU. As 1 425 linhas e 189 colunas de resultados preexistentes mantiveram-se iguais numa comparação integral. A seleção dos grupos nesta medição é uma hipótese de teste, não a classificação normativa dos ficheiros.

A pormenorização mudou deliberadamente: utiliza os grupos ELU selecionados, elimina repetições por solução e deixa de produzir perfis de dispensas inferidos quando os diagramas são insuficientes no modo explícito. Os 1 425 registos repetidos passaram a 70 soluções distintas com notas de amarração e perfil incompleto no ensaio por nós. Não se atribui a redução de tempo apenas à reutilização.

Foram acrescentados cinco testes: reutilização de soluções iguais, invalidação por mudança do recobrimento, invalidação entre análises, seleção correta dos casos na pormenorização e preservação de ângulos de corte diferentes. A compilação inclui um ensaio dentro do executável, sem Python externo, com importação e exportações.

## Etapa 4 — avaliação da memória e identidade visual

A avaliação de uma memória real revelou que a indicação de localização concatenava `x=... m` a identificadores de nós, omitia os estados Verificar no cabeçalho e não utilizava a cadeia final da memória ELS. Foram corrigidas as apresentações sem modificar os modelos resistentes. A memória passa a usar todas as combinações calculadas, inclui os critérios e seleções e conserva os governantes por regime. Valores de flecha não validada ficam substituídos por uma indicação de insuficiência.

Dois testes verificam localizações por nó/coordenada, ausência de flechas numéricas não validadas e rastreabilidade das combinações características. O ensaio Windows e o ensaio do executável verificam também a aplicação do ícone. Os dados e o PDF do utilizador não são distribuídos.

O ícone foi gerado a partir da capa pública do repositório (paleta escura, betão, armaduras e laranja) e convertido para PNG/ICO multirresolução para a aplicação. O resultado não constitui um pormenor construtivo.
