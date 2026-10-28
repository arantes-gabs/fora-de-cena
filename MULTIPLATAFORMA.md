# Mac e Linux — acompanhamento dos testes

Esta branch (`testing/mac-linux`) contém trabalho experimental. Os downloads
publicados em `v0.4.0` continuam sendo os pacotes Windows existentes. Não há
anúncio de suporte nativo aprovado para Mac/Linux nem nova tag de versão.

## Matriz de validação

| Alvo | Saída prevista | Estado da candidata 0.5.0-beta.1 |
| --- | --- | --- |
| Windows x64 | EXE portátil e instalador por usuário | Compilação e autotestes da beta passaram; teste físico da atualização pendente |
| Mac Apple Silicon | APP dentro de DMG | OpenCV enxuto, inferência e autoteste do APP da beta passaram; teste físico desta compilação pendente |
| Mac Intel x86_64 | APP dentro de DMG | Colisão na receita nativa identificada; correção em teste; não bloqueia os demais pacotes |
| Linux x86_64 | TAR.GZ com executável e recursos | OpenCV/NumPy enxutos e inferência passaram; investigação da amostra de rede bloqueou o empacotamento |
| Linux ARM64 | TAR.GZ com executável e recursos | OpenCV/NumPy enxutos e inferência passaram; investigação da amostra de rede bloqueou o empacotamento |

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

## Terceira execução — quatro alvos passaram

[Terceira rodada](https://github.com/arantes-gabs/fora-de-cena/actions/runs/40608553144), commit `539da3d`.

- Windows x64: testes e verificação dos formatos portátil, pasta e instalador passaram novamente.
- Apple Silicon: OpenCV próprio, testes, inferência e compilação/autoteste do DMG passaram. A correção de recursos Tk foi validada no APP real do runner.
- Linux x64 e ARM64: testes, inferência e compilação/autoteste dos executáveis passaram após a inclusão de EGL/GLES no runner.
- Intel: a compilação C++ continua em execução. Nenhum resultado dos demais alvos deve ser interpretado como aprovação Intel.

Todos os pacotes continuaram restritos às máquinas temporárias de CI. Nenhuma tag, Release ou download existente foi substituído.

## Amostra de rede — Linux, ainda não validada

`tools/check_dependency_network.py` prepara uma observação limitada com `strace`
no runner Linux limpo. O controle positivo faz uma tentativa local sem payload;
o teste seguinte acompanha o diagnóstico sintético, processos filhos, cinco
segundos de espera e encerramento. O ambiente filho não herda tokens, proxies
ou configurações pessoais. Somente contagens de syscalls são registradas, sem
endereços, conteúdo de pacotes ou captura de tráfego do computador do mantenedor.

Atividade observada exige investigação, sem ser automaticamente chamada de
telemetria. Mesmo uma amostra sem chamadas de rede não comprova ausência de
atividade futura, em sessões longas, no APP empacotado ou em outros sistemas.
`dependency_network_verified=false` e `distribution_ready=false` permanecem.
O aviso oficial do fornecedor continua aplicável: [privacidade MediaPipe](https://developers.google.com/edge/mediapipe/solutions/tasks#mediapipe_tasks_privacy_notice).

## Próxima candidata — 0.5.0-beta.1

A versão de desenvolvimento foi separada da 0.4.0 para identificar corretamente
os próximos pacotes e hashes. Isso não cria nem move uma tag ou Release.

Após revisar as wheels efetivas, a receita Linux passa a compilar OpenCV com
V4L2/JPEG, sem FFmpeg/Qt, e NumPy 2.5.4 sem BLAS/Fortran externos. São mudanças
de empacotamento ainda sujeitas a teste nativo. Não removemos bibliotecas de
uma wheel pronta nem trocamos as versões de execução por versões antigas.

A wheel OpenCV Intel oficial 4.14.0.94 foi inspecionada separadamente: seu
registro de build informa FFmpeg/GStreamer desligados e não contém os codecs
GPL encontrados anteriormente na wheel ARM64. Não se presume que os pacotes
de todos os chips tragam as mesmas bibliotecas.

A tentativa Intel monolítica da terceira rodada foi substituída pela biblioteca
oficial do domínio de visão (`mediapipe_tasks_vision_lib`), suficiente para as
APIs usadas pelo app. Ela evita áudio/texto/busca e aplica o controle de símbolos
do próprio fornecedor. A compilação antiga será cancelada para testar os insumos
atuais; isso não constitui aprovação nem reprovação do novo candidato Intel.

## Rodada da beta — foco na entrega

[Execução da beta](https://github.com/arantes-gabs/fora-de-cena/actions/runs/40614201662).
Windows e Apple Silicon passaram. Linux compilou os dois componentes enxutos e
executou os modelos; a amostra registrou syscalls, sem capturar payload, e parou
a etapa seguinte. Foi identificado que o import opcional de sounddevice
inicializa PortAudio, embora o app não use áudio e o empacotador já o exclua.
O adaptador de visão agora recusa esse import opcional durante a inicialização;
o próximo teste compara com um controle de importação do backend no runner limpo.
Isso ainda não é evidência de ausência geral de telemetria.

Intel falhou no conflito de nomes entre a biblioteca macOS e seu genrule de
cópia. A receita corrige esse conflito e permite três compilações CMake paralelas.

Prioridade da beta: Mac Apple Silicon e Linux x64/ARM64. Intel pode permanecer
experimental separado. Otimizações adicionais e matrizes amplas de versões de
SO ficam para acompanhamento; não bloqueiam pacotes aprovados de outros alvos.

Para a beta de testes, a amostra de rede é informativa: falhas ou atividade
observada continuam registradas e `dependency_network_verified=false` permanece.
Ela não impede gerar um rascunho experimental, sem certificação de operação
offline. Não capturamos payload nem tráfego do computador pessoal. O diagnóstico
adicional classifica conexões locais/externas e portas, sem publicar endereços.
Testes de execução, hashes, barreiras de arquivos privados e licenças exigidas
continuam bloqueando um pacote inválido. A versão final continua dependendo da
revisão das pendências; o proprietário revisa o rascunho antes de qualquer publicação.
