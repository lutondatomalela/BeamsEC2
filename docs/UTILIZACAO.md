# Utilização do BeamsEC2

1. Guarde a tabela-tipo e importe os esforços em CSV ou XLSX. Cada linha corresponde a uma viga, posição e combinação. Confirme unidades e eixos locais.
2. Confirme geometria, comprimento, materiais e recobrimento antes do cálculo.
3. Classifique as combinações pelos campos ELU, ELS característica, frequente e quase-permanente. Aceitam-se listas e intervalos, como `101-117 201-208`. A classificação deve vir do modelo de análise; CQC não identifica o regime ELS. Casos não classificados ficam excluídos. Uma combinação não pode pertencer a dois grupos.
4. Para completar as verificações ELS implementadas, forneça combinações característica e quase-permanente. A característica governa tensões no aço e betão; a quase-permanente governa fendilhação, flecha e controlo da hipótese de fluência linear. Os resultados frequentes são informativos nesta implementação.
5. Defina condição de apoio, histórico de carregamento, idades, humidade e retração de acordo com o modelo. Confirme a armadura utilizada e a sua distribuição ao longo do vão.
6. Calcule e consulte os estados individuais, casos governantes e diagnóstico ELS. Exporte PDF para apresentação e XLSX para auditoria. A exportação mantém a janela ativa e usa uma cópia dos resultados e parâmetros do instante em que foi iniciada.

## Dados ELS insuficientes

Este estado significa que pelo menos uma verificação necessária ficou incompleta. Não implica, por si só, incumprimento resistente. Também não permite aprovar o conjunto das verificações ELS.

- **Grupo em falta:** importe os esforços da combinação e classifique-os no regime correto para a viga em causa.
- **Flecha sem diagrama validado:** forneça `Station (m)` com posições físicas, cobrindo todo o vão e os apoios, com pelo menos três posições distintas, preferencialmente cinco ou mais, incluindo máximos interiores e mudanças de sinal. Um número de nó não é uma posição. Não invente uma distribuição uniforme para preencher a coluna. O número de posições, por si só, não garante a qualidade do diagrama: confirme o comprimento, a cobertura do vão e a condição de apoio.
- **Esforço normal relevante:** o diagnóstico identifica uma limitação do modelo ELS implementado. Acrescentar estações não resolve esta situação; faça a verificação com um modelo adequado à interação entre esforço normal e flexão.

As verificações concluídas conservam os seus próprios estados. A flecha incompleta é apresentada como não verificada na memória. O estado global permanece `Verificar` enquanto subsistir incompletude. Se não conseguir obter os dados necessários, verifique externamente e documente o método e o resultado; o programa não transforma essa verificação externa em aprovação automática.

A indicação de três/cinco posições é um critério da implementação e uma orientação para discretizar o diagrama, não uma quantidade prescrita pela norma.
