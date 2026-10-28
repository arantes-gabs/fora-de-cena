# Mac Intel — candidato OpenCV DNN

**Em preparação, sem download Intel publicado.** `distribution_ready=false` e
`dependency_network_verified=false` permanecem. Mac Apple Silicon, Windows e os
pacotes Linux publicados mantêm seus próprios processamentos e downloads.

## O que mudou

A compilação Intel do MediaPipe 1.1.1 chegou a 7.912 de 8.079 ações e falhou em
um header GPU ausente (`gpu_shared_data_internal.h`). Aumentar o timeout não
resolve esse erro. A receita antiga permanece nos fontes para rastreabilidade;
não é o caminho selecionado para este candidato.

O perfil Intel usa **OpenCV DNN em CPU**, com quatro modelos ONNX oficiais do
OpenCV Zoo: palma, pontos da mão, rosto YuNet e recorte PPHumanSeg. Não precisa
instalar MediaPipe nem ONNX Runtime nesse perfil. As regras dos gestos, os
efeitos e a interface são compartilhados; precisão e desempenho podem diferir.

## Evidência disponível e o que falta

| Etapa | Situação |
| --- | --- |
| Quatro modelos em Mac Intel nativo | Passou no runner `macos-15-intel`; job de prova de 22 segundos |
| Integração com o app, modelos reais e quadros sintéticos | Passou no Windows; não certifica execução no macOS |
| Dependências Intel fixadas | Wheels compatíveis e dependências transitivas conferidas no PyPI |
| OpenCV mínimo Intel com DNN/objdetect | Receita preparada; compilação nativa ainda pendente |
| Aplicativo completo e DMG Intel | Pendente de build, autoteste congelado, GUI e auditoria Mach-O |
| Webcam, gestos, qualidade dos recortes e chamadas em Intel | Teste real ainda pendente |
| Publicação | Exige revisão do pacote e autorização do mantenedor |

[Prova nativa dos modelos](https://github.com/arantes-gabs/fora-de-cena/actions/runs/40705849916).
Os 22 segundos são do job da prova; não são tempo de geração do DMG ou medida
de FPS do aplicativo. Não prometemos 720p/30 FPS no hardware Intel.

## Perfil e limites

- Python 3.14.7, macOS 15+, x86_64. O mínimo efetivo é auditado nas bibliotecas.
- `requirements-intel.lock.txt` fixa as dependências sem alterar o lock das outras plataformas.
- `tools/opencv_profile.py` seleciona somente para Intel os módulos DNN/objdetect.
  FFmpeg, GStreamer, HighGUI, Qt, GTK e IPP ficam desligados; Protobuf é o incluído no sdist.
- `teleport_cam/opencv_models.py` fixa commit, URLs e SHA-256 dos quatro modelos.
  Download somente no preparo/build; o aplicativo não baixa modelos ao abrir.
- `packaging/notices/opencv-zoo/` preserva os avisos Apache-2.0/MIT e Protobuf.
- A câmera virtual usa o auxiliar GPL independente e OBS 30+; não é carregada no processo principal.
- Sem Developer ID ou notarização Apple. Autorize o arquivo individual nos ajustes do Mac;
  não desative Gatekeeper, Secure Boot ou outras proteções para executar o app.
- O perfil Intel não importa MediaPipe. A verificação de rede de todas as dependências
  continua pendente; isso não altera as declarações de privacidade dos outros pacotes.

## Teste no GitHub

Após autorização de commit/envio, use **Free native checks and candidates** na
branch **`testing/intel-dnn`**, marcando somente **`intel_dnn_candidate`**.

O job é manual, aceita somente o repositório público `arantes-gabs/fora-de-cena`
e o proprietário, com token de leitura, checkout sem credenciais persistidas,
Actions fixadas por SHA e runner padrão. Limite: 60 minutos. Não roda em PRs.

A sequência é: dependências → OpenCV mínimo → testes Python/JS → inferência
integrada → DMG → autotestes do executável e das sete imagens → auditoria de
arquitetura, bibliotecas e assinatura ad-hoc. Nenhuma câmera é aberta.

Somente após todos os bloqueios passarem, seis arquivos selecionados são
guardados como artifact por sete dias: DMG, fontes do auxiliar, licenças,
instruções, resumo de validação e checksums. Não inclui logs brutos, preferências,
chaves ou a pasta de trabalho inteira. Artifacts de Actions de um repositório
público podem ser baixados por usuários autenticados; não são uma área privada.
Não cria Release, tag ou download anunciado, e não altera os pacotes anteriores.

## Reproduzir em um Mac Intel

Etapas para desenvolvedores, em um checkout limpo com Python 3.14.7 x86_64/Tk e
ferramentas de linha de comando do Xcode. Quem recebe o DMG não precisa compilar.

```sh
python3.14 -m venv .venv
. .venv/bin/activate
python tools/prepare_minimal_opencv.py
python -m venv work/opencv-build-env
work/opencv-build-env/bin/python -m pip install --only-binary=:all: -r requirements-opencv-build.txt
work/opencv-build-env/bin/python tools/build_minimal_opencv.py --source work/opencv-minimal/source/opencv_contrib_python-4.14.0.94
python -m pip install --only-binary=:all: work/opencv-minimal/wheels/*.whl -r requirements-intel.lock.txt -r requirements-build.txt
python -m pip check
python -m unittest discover -s tests -q
node --test tests/meet_extension.test.mjs
python setup_models.py
python tools/ci_native.py diagnose --target macos-x86_64
python tools/fetch_distribution_sources.py
python tools/ci_native.py build
python tools/stage_intel_candidate.py
```

O build recusa insumos/proveniência diferentes e destinos de saída anteriores;
não remove pastas automaticamente. O estágio de download é local, sem envio.
Leia [Privacidade](PRIVACY.md) e os [avisos de terceiros](THIRD_PARTY_NOTICES.md).
