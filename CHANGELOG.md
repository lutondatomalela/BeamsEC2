# Changelog

## v0.1.1

- Corrigida a importação de tabelas UTF-16, UTF-8 com BOM, Windows-1252 e Latin-1.
- Adicionado reconhecimento automático dos separadores tabulação, ponto e vírgula, vírgula e barra vertical.
- O tipo real do ficheiro é agora detectado pela assinatura, evitando tratar tabelas de texto como livros de cálculo apenas por causa da extensão.
- Corrigida a cadeia da interface que regressava às rotinas base durante a importação.
- Restabelecida a identificação automática de secções I simétricas e assimétricas através de AX, IY, IZ, VZ e VPZ.
- Adicionados testes de regressão específicos para importação e identificação geométrica.

## v0.1

- Primeira versão pública modular.
- Interface e instruções revistas.
- Terminologia independente do programa de origem das tabelas.
- Dimensionamento ELU e ELS, secções rectangulares, T e I, relatórios e memória de cálculo.
