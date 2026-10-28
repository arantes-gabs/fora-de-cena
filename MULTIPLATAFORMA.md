# Mac e Linux — acompanhamento dos testes

Esta branch (`testing/mac-linux`) contém trabalho experimental. Os downloads
publicados em `v0.4.0` continuam sendo os pacotes Windows existentes. Não há
anúncio de suporte nativo aprovado para Mac/Linux nem nova tag de versão.

## Matriz de validação

| Alvo | Saída prevista | Estado após a segunda rodada |
| --- | --- | --- |
| Windows x64 | EXE portátil e instalador por usuário | Testes de fontes, EXE portátil, pacote em pasta e instalador passaram no CI; testes físicos da atualização pendentes |
| Mac Apple Silicon | APP dentro de DMG | OpenCV enxuto e APP compilados; autoteste do pacote ainda em correção |
| Mac Intel x86_64 | APP dentro de DMG | Receita avançou até OpenCV privado; correção para zlib do SDK em reteste |
| Linux x86_64 | TAR.GZ com executável e recursos | Testes de fontes passaram; diagnóstico de inferência e build em correção; teste físico pendente |
| Linux ARM64 | TAR.GZ com executável e recursos | Testes de fontes passaram; diagnóstico de inferência e build em correção; teste físico pendente |

O estado será atualizado com resultados reais e links das execuções. Check verde
de CI não certifica câmera, chamada ou desempenho em todos os computadores.

## Organização

- Fontes: `teleport_cam/`, `camera_output/` e `meet_extension/`.
- Testes automatizados: `tests/`.
- Receitas, perfis e avisos de terceiros: `tools/`, `packaging/` e requirements.
- Configuração CI: `.github/workflows/native-candidates.yml`.
- Preparação e limitações: [MAC_LINUX.md](MAC_LINUX.md), [MAC_INTEL.md](MAC_INTEL.md)
  e [OPENCV_ENXUTO_MAC.md](OPENCV_ENXUTO_MAC.md).

Preferências, pareamento Meet, ambientes Python, modelos baixados, logs,
temporários, binários e materiais pessoais não entram no Git. Nenhum workflow
usa certificados pessoais, secrets ou runners pagos. As actions usadas estão
fixadas por SHA e o token do CI tem somente leitura.

## Execução dos testes

Pushes autorizados em `testing/mac-linux` executam instalação limpa, testes e
compilações nos runners padrão do repositório público. Nenhum PR ou push na
main dispara esse fluxo. A execução manual exige que o workflow também esteja
na branch padrão, conforme o funcionamento do GitHub; isso não foi usado como
motivo para enviar código experimental à main.

Pacotes gerados ficam apenas no runner, são autotestados e descartados ao final.
Não há upload de artifacts ou criação de Releases, evitando consumo de storage
de artifacts. Esse primeiro CI verifica a reprodução do build; disponibilizar
um candidato para testes físicos é uma etapa posterior, com revisão das licenças
e autorização do proprietário.

## Critérios para uma nova versão

1. Build e testes dos alvos anunciados sem erro, incluindo autoteste do pacote
   fora do ambiente Python de desenvolvimento.
2. Licenças, avisos e fontes correspondentes das bibliotecas nativas revisados.
3. Verificação de rede das dependências, especialmente MediaPipe, documentada.
4. Testes reais no hardware anunciado: câmera, fundo, gestos, efeitos,
   restauração, OBS/câmera virtual e chamada com outro participante.
5. Documentação, versão interna, nomes dos pacotes e hashes consistentes.

Somente depois desses critérios será definida uma nova versão/tag e uma Release.
A tag `v0.4.0` não será movida ou sobrescrita. A primeira candidata pode usar
uma versão como `v0.5.0-beta.1`; o lançamento dependerá da validação e indicará
somente as plataformas efetivamente aprovadas. Intel pode seguir experimental
se exigir mais trabalho. `distribution_ready=false` permanece durante os testes.

## Primeira execução nativa — 27/10/2026

[Execução inicial](https://github.com/arantes-gabs/fora-de-cena/actions/runs/40584483138). Nenhum pacote foi publicado.

- Linux x64/ARM64: os testes identificaram dois casos de timeout que usavam backend OBS real; corrigidos para modo de teste sem câmera.
- Windows: fontes e compilação do EXE passaram; o diagnóstico recusou o layout Tk 9 com recursos ZIP dentro da DLL. A validação agora reconhece esse layout, mantendo a exigência dos scripts Tk.
- Apple Silicon: o OpenCV enxuto compilou, mas a barreira de privacidade detectou caminhos do usuário padrão `runner` do GitHub na biblioteca. O remapeamento foi estendido ao diretório do toolchain e à proveniência; a barreira continua ativa.
- Intel: a compilação avançou até o OpenCV privado. O teste de link C++ falhou por caminho relativo do wrapper Apple no CMake. A receita foi ajustada com base no código da versão fixada do rules_foreign_cc.

Estas correções precisam passar por nova execução. Suporte nativo e distribuição continuam pendentes.

## Segunda execução — Windows aprovado no CI

[Segunda rodada](https://github.com/arantes-gabs/fora-de-cena/actions/runs/40587140243).

- Windows x64: testes de fontes e compilação/verificação do EXE portátil, pacote em pasta e instalador concluídos com sucesso. Não houve upload dos pacotes ou alteração da Release existente.
- Linux x64/ARM64: testes Python/JavaScript passaram; diagnóstico dos modelos interrompeu a etapa seguinte. A receita foi complementada com EGL/GLES, dependências diretas verificadas na biblioteca oficial MediaPipe, e mensagens de erro públicas sanitizadas.
- Apple Silicon: OpenCV enxuto passou pela compilação e pela barreira de caminhos privados; o aplicativo foi compilado, mas seu autoteste ainda falhou. Foi corrigida a validação de links entre Frameworks e Resources dentro do mesmo APP, e os próximos erros serão mostrados sem caminhos de perfil.
- Intel: o ajuste de linker permitiu avançar. O build parou na versão antiga de zlib embutida no OpenCV privado; a receita agora seleciona a zlib do SDK macOS, sem acrescentar bibliotecas ao computador do usuário. A compilação ainda precisa passar.

A próxima rodada valida essas correções. Câmera/chamadas reais, revisão final de bibliotecas/licenças e verificação de rede permanecem pendentes. Nenhuma nova versão/tag foi criada.
