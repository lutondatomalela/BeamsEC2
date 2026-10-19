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
