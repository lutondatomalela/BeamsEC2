# v0.1.3-dev4 — interface e diagnóstico ELS

- Removidos os controlos do modo ELS anterior, reconhecimento automático e regime base da interface pública; classificação explícita por grupos.
- Corrigida a sobreposição de campos no painel ELS.
- Instruções atualizadas para os grupos atuais, posições físicas, resultados incompletos e verificação externa.
- Diagnóstico por verificação/combinação, distinguindo grupos em falta, diagrama de flecha incompleto e limitação do modelo para esforço normal relevante.
- Resultados concluídos conservados; incompletude não convertida em aprovação ou falha resistente. Diagnóstico incluído na auditoria XLSX e memória PDF.

# v0.1.3-dev3 — exportação mais rápida

- XLSX escrito numa única passagem, sem reabrir e regravar todas as folhas a cada extensão.
- Memória XLSX usa as mesmas correções e os mesmos governantes ELS da memória PDF.
- PDF reutiliza células de texto repetidas por coluna e usa tabelas otimizadas para documentos extensos.
- Preparação da memória indexada por viga/caso, evitando pesquisas integrais repetidas.
- Exportações em segundo plano com cópia dos resultados/parâmetros, janela responsiva e tempo decorrido.
- Gravação temporária seguida de substituição apenas após sucesso; erros deixam de ser ocultados.
- Testes de integridade das células, fórmulas literais, conservação do ficheiro anterior e isolamento do trabalho em segundo plano.
- Ensaio local com CSV de 5964 linhas, 200 envelopes ELU e 44019 pontos ELS: XLSX 183,7 s → 8,5 s; memória PDF 12,2 s → 7,2 s. Tempos dependem do computador e da seleção de casos. O XLSX anterior terminou com um ficheiro inválido neste ensaio; o novo foi reaberto e verificado.
- Texto e paginação dos três PDF comparados com a versão anterior, sem supressão de linhas; sem alterações aos modelos de cálculo.

# v0.1.3-dev2 — ícone e rastreabilidade dos relatórios

- Ícone da janela e do executável baseado na capa do repositório, com ficheiros PNG/ICO em assets.
- As localizações por nó deixam de ser apresentadas como distâncias em metros.
- Cabeçalhos distinguem envelopes ELU, barras e estados OK/Falha/Verificar.
- Memória de cálculo inclui critérios, seleções e governantes ELS, usando todas as combinações calculadas em vez do resumo por barra.
- Valores de flecha não validada deixam de ser apresentados como resultados numéricos na memória; o motivo da insuficiência fica explícito.
- Alterações de apresentação e rastreabilidade, sem alteração dos modelos resistentes nesta etapa.

# v0.1.3-dev1 — distribuição de teste

- Reutilização local de verificações ELS com secção/armadura e parâmetros iguais, sem alterar resultados por combinação ELU.
- Rastreabilidade das verificações reutilizadas pelo identificador service_cage_id.
- Pormenorização por solução distinta, respeitando a seleção explícita ELU, incluindo CQC e excluindo ELS numerados.
- No modo explícito, um diagrama ELU insuficiente conserva as notas de amarração sem produzir perfis de dispensas inferidos.
- Mensagens distinguem cálculo ELS, pormenorização e preparação das tabelas.
- Compilação Windows com ensaio interno do executável e registo de proveniência.

# Desenvolvimento — grupos ELS explícitos

- Campos separados para ELS característica, frequente e quase-permanente, mantendo o modo anterior com os campos vazios.
- Seleção explícita prevalece sobre os nomes e exclui casos não classificados; CQC deixa de ser uma indicação de regime quase-permanente.
- Governantes por regime: tensões CAR, fissuração/flecha QP e frequentes informativos.
- Controlo QP da hipótese de fluência linear separado da falha resistente; falta de grupos e verificações incompletas mantida no estado global.
- Auditoria da classificação no XLSX, seleções conservadas durante a análise e bloqueio de análises simultâneas.
- No modo explícito, flechas com posições inferidas não recebem OK. A importação por nós e os métodos originais de secção mantêm-se.
- Testes de seleção e regime e ensaio Windows com cálculo e exportações por nós sem Station.

# Desenvolvimento — reinício a partir da v0.1.2

- Seleção opcional de combinações ELU por listas e intervalos; seleção ELS com correspondência exata.
- Combinações ELS indicadas deixam de ser incluídas no dimensionamento ELU.
- Validação de sobreposições, seleções inválidas e combinações inexistentes.
- Preservação da importação por nós sem posições; reconhecimento do cabeçalho por pontos e de identificadores que contêm barras.
- Métodos de cálculo mantidos nesta etapa; testes de regressão da importação e seleção.

# Changelog

## v0.1.2

- adicionada distribuição executável portátil para Windows de 64 bits;
- adicionada configuração PyInstaller sem janela de terminal;
- adicionados metadados de versão ao executável;
- adicionada compilação local através de `build_windows.bat`;
- adicionada compilação automática através de GitHub Actions;
- publicação automática do executável e do pacote ZIP em GitHub Releases quando é enviada uma etiqueta de versão;
- incluídos testes internos antes de cada compilação;
- actualizadas as instruções de instalação e distribuição;
- mantido o núcleo de cálculo validado da v0.1.1.

## v0.1.1

- corrigida a importação de tabelas UTF-16 e de ficheiros com extensão diferente do formato real;
- adicionada detecção robusta de codificação e separador;
- corrigida a passagem das propriedades geométricas entre a interface e o módulo de identificação de secções;
- restabelecida a identificação automática de secções I simétricas e assimétricas;
- adicionados testes de regressão para importação e geometria.

## v0.1

- primeira versão pública;
- código separado por domínio funcional;
- interface e instruções revistas;
- relatórios e memória de cálculo limpos para publicação;
- suporte a secções rectangulares, T e I;
- verificações ELU e ELS;
- testes internos de sanidade.
