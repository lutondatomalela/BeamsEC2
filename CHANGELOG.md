# v0.2.0-rc2 - 2026-10-15

- Seleção iterativa das armaduras com posições reais e estribos de 6/8/10 mm.
- Armadura comprimida para os dois sinais do momento; rejeição explícita de não convergência.
- Verificação de espaço entre faces, área máxima por face, transição banzo/alma e espaçamento transversal dos ramos.
- Armadura mínima com largura média da zona tracionada nas secções T.
- ELS: betão substituído por aço descontado na zona comprimida; tensão no aço não fissurado com a inércia correspondente.
- Referências analíticas independentes para secção homogeneizada, fissuração, curvatura e flecha.
- Ensaio de integração Windows com aplicação Tk real, cálculo ELU/ELS e exportações XLSX/PDF.
- 45 testes gerais e um ensaio Windows, além das dez verificações internas existentes.

# v0.2.0-rc1 - 2026-10-14

- Resistência à flexão com compatibilidade de extensões e equilíbrio de forças.
- Interação corte/torção (6.29), inclinação comum e área de dois ramos fechados.
- Torção não nula conservada; modelo conservador da alma para secções I.
- Validação de esforços, dimensões, estações, material e dados variáveis.
- Revisão obrigatória para N-M, flexão biaxial, eixos alternativos, betões de alta resistência e pormenorização de torção.
- Todas as combinações conservadas; resumos sem mistura de casos e sem ocultação de Verificar.
- Estações ELS em metros, sem reescala nem média de momentos conflitantes.
- Exportação XLSX com erros de folhas adicionais explícitos.
- 28 testes de regressão adicionais e CI Windows/Linux.
- Avaliação técnica e limitações em docs/ROBUSTNESS_REVIEW.md.

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
