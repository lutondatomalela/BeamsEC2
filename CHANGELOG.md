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
