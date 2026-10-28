# Fora de Cena

> **Candidata 0.5.0-beta.1.** Mac e Linux estão em validação experimental.
> Os downloads publicados continuam sendo a versão Windows 0.4.0.
> Os fontes desta branch preparam a candidata **0.5.0-beta.1**, ainda sem lançamento.
> Veja o [estado dos testes e critérios de lançamento](MULTIPLATAFORMA.md).

![Fora de Cena — saídas criativas para suas chamadas](assets/brand/readme-cover.png)

Desapareça da webcam com um gesto e reapareça quando quiser. Teleporte, fumaça,
poeira, pixels, saída de desenho e portal para suas chamadas de vídeo.

**Windows x64 · Processamento local · Sem áudio · Sem APIs pagas**

[Baixar versão 0.4.0](https://github.com/arantes-gabs/fora-de-cena/releases/tag/v0.4.0) ·
[Como usar](COMO_USAR.md) · [Privacidade](PRIVACY.md)

> **Versão pública inicial · 0.4.0.** Disponível para avaliação no Windows.
> Teste a prévia antes de usar em uma reunião importante.

**Mac e Linux:** adaptação experimental em desenvolvimento, com instruções e
receitas de build em [Mac e Linux](MAC_LINUX.md). Os downloads acima continuam
sendo Windows; ainda não há pacote nativo aprovado para publicar.

## Baixar e abrir

Escolha uma opção abaixo. As duas incluem o aplicativo completo:

| Opção | Arquivo | Como funciona |
|---|---|---|
| **Executável único** | [**Baixar executável único**](https://github.com/arantes-gabs/fora-de-cena/releases/download/v0.4.0/ForaDeCena-0.4.0-Portatil.exe) | Baixe e abra. Sem instalador, sem extrair uma pasta manualmente. |
| **Instalador** | [**Baixar instalador**](https://github.com/arantes-gabs/fora-de-cena/releases/download/v0.4.0/ForaDeCena-0.4.0-Setup.exe) | Instale para seu usuário e abra pelo atalho do menu Iniciar. Inclui desinstalador. |

As duas opções incluem Python, bibliotecas e modelos. **Você não precisa instalar
Python nem baixar o projeto.** O executável único prepara os componentes em uma
pasta temporária ao abrir; por isso pode demorar mais para iniciar.

**Use os links de download acima. Code → Download ZIP baixa os arquivos do repositório, não o aplicativo pronto.**

Os arquivos ainda não têm assinatura digital. Não desative o antivírus ou as
proteções do Windows. O arquivo [SHA256SUMS.txt](https://github.com/arantes-gabs/fora-de-cena/releases/download/v0.4.0/SHA256SUMS.txt) acompanha os downloads para
conferir sua integridade; ele não substitui uma assinatura do editor.

Também estão disponíveis [fontes da saída de vídeo](https://github.com/arantes-gabs/fora-de-cena/releases/download/v0.4.0/ForaDeCena-0.4.0-Fontes-Saida.zip)
e [licenças e avisos](https://github.com/arantes-gabs/fora-de-cena/releases/download/v0.4.0/ForaDeCena-0.4.0-Licencas.zip).
Esses arquivos documentam o componente independente de saída e suas licenças;
quem só quer usar não precisa baixar ou compilar os fontes.

## Preparar uma vez para chamadas

Instale o **[OBS Studio pelo site oficial](https://obsproject.com/download)** para
obter a câmera virtual. Esse componente ainda é necessário para enviar o resultado
às chamadas. Você não precisa manter o OBS aberto.

No Fora de Cena, abra **Configurar → Meet → Preparar vídeo para o Meet**.
Na reunião, escolha **OBS Virtual Camera** como câmera e desative os efeitos de
fundo do serviço. Seu microfone continua sendo o normal da chamada.

A extensão de navegador é **opcional**: serve apenas para sair automaticamente
do Meet. Não é necessária para os efeitos aparecerem na chamada.

## Seu primeiro desaparecimento

1. Em **Configurar → Câmera**, escolha sua webcam e clique em **Iniciar câmera**.
2. Clique em **Capturar fundo (4 s)** e saia do enquadramento.
3. Confira a imagem vazia e clique em **Confirmar fundo vazio**.
4. Volte, escolha um efeito e clique em **Ativar efeito** ou faça o gesto indicado.
5. Use **Reaparecer** para voltar. **Restaurar · F8** interrompe o efeito.

O fundo **Estático** é o padrão recomendado. Mantenha a câmera fixa e refaça a
captura ao mudar a posição ou a iluminação. A opção **Em movimento** é experimental:
atualiza partes visíveis do cenário, mas pode apresentar falhas e artefatos.
A câmera não enxerga o que está atrás de você; a captura inicial continua necessária.

## Efeitos e gestos

Clique em **Como fazer**, no aplicativo, para ver a ilustração e os passos ampliados.

| Gesto | Efeito | Como ativar |
|:---:|---|---|
| <img src="assets/gestures/teleporte.png" width="80" alt="Dois dedos juntos na testa"> | **Teleporte anime / Suave** | Indicador e médio juntos na testa; mantenha até completar a barra. |
| <img src="assets/gestures/selo-uma-mao.png" width="80" alt="Selo ninja com uma mão"> | **Puf! · fumaça** | Uma mão, indicador e médio juntos para cima, outros dedos dobrados. Sem tocar a testa. |
| <img src="assets/gestures/poeira.png" width="80" alt="Preparação do estalo"> | **Virar poeira** | Encoste polegar e médio brevemente, depois faça o movimento de estalar. |
| <img src="assets/gestures/digital.png" width="110" alt="Pinça se abrindo"> | **Saída digital** | Encoste polegar e indicador por um instante; depois abra a pinça. |
| <img src="assets/gestures/palma.png" width="80" alt="Uma palma aberta para a câmera"> | **Saída de cena** | Mostre uma palma aberta e mantenha parada até completar a barra. Não precisa acenar. |
| <img src="assets/gestures/portal.png" width="80" alt="Duas palmas nas laterais do rosto"> | **Portal** | Duas palmas abertas, uma de cada lado do rosto; mantenha até completar a barra. |
| <img src="assets/gestures/manual.png" width="80" alt="Ativação manual"> | **Instantâneo** | Use Ativar efeito ou Reaparecer. |

Relaxe a mão antes de repetir. Estalo e pinça usam movimento; as demais poses
usam a duração configurada. O estalo é reconhecido pela imagem: **não usamos o microfone**.
Boa iluminação e mãos inteiras no enquadramento ajudam. O botão manual está sempre disponível.

## Meet, Teams e Discord

O app entrega o vídeo à câmera virtual. A disponibilidade em cada serviço depende
do suporte e das permissões locais. Comece testando a prévia de vídeo da chamada.

Para sair automaticamente do Meet, vincule explicitamente a extensão à aba da
reunião e ative **Sair do Meet após desaparecer**. A opção começa desligada, fecha
somente a aba vinculada e mostra uma contagem cancelável. Depois que a extensão
recebe o pedido de fechar, pode ser tarde para cancelar.

**[Guia de câmera virtual e extensão →](COMO_USAR.md)**

## Se algo não funcionar

| Situação | O que fazer |
|---|---|
| A webcam não aparece | Feche outros programas que usam a câmera, confira a permissão do Windows e clique em Atualizar lista. |
| A chamada não recebe os efeitos | Escolha OBS Virtual Camera na chamada e use Reconectar saída no app. Deixe a câmera virtual parada no OBS. |
| O app está lento | Pare a câmera, escolha 640 × 480 e mantenha o fundo Estático. Instantâneo é o efeito mais leve. |
| O gesto não dispara | Confira Como fazer, melhore a iluminação e relaxe a mão antes de repetir. Use o botão manual se necessário. |
| Quer voltar imediatamente | Clique em Restaurar ou pressione F8. Se o atalho estiver ocupado, use o botão. |

720p a 30 FPS é o objetivo, condicionado ao computador; não é uma garantia de desempenho.
A configuração e a calibração não substituem o teste na sua própria chamada.

## Privacidade

Captura, reconhecimento e efeitos são processados no computador. O aplicativo
não grava imagens, não abre o microfone e não envia vídeo a servidores próprios.
O fundo fica em memória durante a sessão. Configurações e chave da extensão são
criadas para seu usuário, em `%LOCALAPPDATA%\ForaDeCena`.

A chamada continua transmitindo pelo serviço escolhido, conforme a política dele.
A segmentação pode falhar: desaparecer não garante anonimização.

[Política de privacidade](PRIVACY.md) · [Segurança](SECURITY.md)

## Código-fonte e desenvolvimento

Os **fontes completos estão neste repositório**: aplicativo, efeitos, gestos,
programa independente de saída, extensão opcional, testes e receitas de build.

- [Executar pelos fontes e entender a arquitetura](DESENVOLVIMENTO.md)
- [Gerar o instalador e o executável único](DISTRIBUIR.md)
- [Baixar todos os fontes atuais em ZIP](https://github.com/arantes-gabs/fora-de-cena/archive/refs/heads/main.zip)
- [Baixar o pacote de fontes 0.4.0](https://github.com/arantes-gabs/fora-de-cena/releases/download/v0.4.0/fora-de-cena-0.4.0-source.zip)

Para estudar: `teleport_cam/` contém o aplicativo; `camera_output/` documenta a
saída independente; `meet_extension/` contém a extensão. Veja `tests/`, `tools/`
e `packaging/` para os testes e a construção. Não são necessárias credenciais.
Modelos e dependências são instalados a partir das fontes oficiais.

Para apenas usar, os downloads do início desta página continuam sendo a opção
mais simples. Consulte [CONTRIBUTING.md](CONTRIBUTING.md) para trabalhar na sua cópia.

## Créditos e licenças

O aplicativo principal mantém licença MIT. A saída para OBS é feita por um
programa independente GPL-2.0-only, cujos fontes correspondentes acompanham as
Releases. Bibliotecas, modelos e drivers preservam suas próprias licenças.
Ao redistribuir, ofereça também os pacotes Fontes-Saida e Licencas, com o mesmo acesso.
[Licença](LICENSE) · [Avisos de terceiros](THIRD_PARTY_NOTICES.md).

[VanishCam](https://github.com/Nicovic17/vanish_webcam) foi a referência técnica inicial.
O aplicativo usa implementação própria; não inclui código ou recursos daquele projeto.
As ilustrações e a identidade visual foram fornecidas pelo mantenedor.

### Verificação de Windows, Mac e Linux

A automação da branch de testes no GitHub testa Windows x64, Mac Apple Silicon e Linux x86_64/ARM64 em runners padrão gratuitos de repositório público. A opção de compilação valida candidatos sem armazenar pacotes ou publicar Releases. Mac Intel possui uma receita experimental de compilação própria do MediaPipe atual, ainda pendente de execução e testes nativos; não há download Intel. Veja [MAC_INTEL.md](MAC_INTEL.md). Consulte os limites, testes reais e instruções em [MAC_LINUX.md](MAC_LINUX.md#automação-gratuita-no-github).
