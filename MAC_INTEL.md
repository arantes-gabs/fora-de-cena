# Fora de Cena no Mac — Intel

**Beta experimental para Mac Intel x86_64, com macOS 15 ou posterior.**

[**Baixar o aplicativo Intel — DMG**](https://github.com/arantes-gabs/fora-de-cena/releases/download/v0.5.0-beta.2-intel.1/ForaDeCena-0.5.0-beta.2-macos-x86_64-experimental.dmg) · [Notas, fontes, licenças e checksums](https://github.com/arantes-gabs/fora-de-cena/releases/tag/v0.5.0-beta.2-intel.1)

O aplicativo já inclui Python, bibliotecas e modelos. Quem só quer usar precisa
baixar apenas o DMG; não precisa clonar o projeto ou compilar os fontes.

## Instalar e abrir

1. Confira o processador em **menu Apple → Sobre Este Mac**. Se for M1 em diante,
   prefira o [pacote Apple Silicon](MAC_APPLE_SILICON.md). Este download é para Intel.
2. Baixe e abra o DMG. Arraste **Fora de Cena.app** para **Aplicativos**.
3. Se houver outra versão instalada, preserve-a em uma pasta separada antes de
   substituir o app. Não mantenha as duas usando a webcam ao mesmo tempo.
4. Abra o app pela pasta Aplicativos. Como não há notarização Apple, pode aparecer
   “A Apple não pôde verificar…”. Após tentar abrir, use **Ajustes do Sistema →
   Privacidade e Segurança → Abrir Mesmo Assim** somente para o download oficial.
   Não desative Gatekeeper ou outras proteções do Mac.
5. Permita o acesso à webcam. Se negou, confira **Privacidade e Segurança → Câmera**.

## Primeiro teste

Selecione **Só prévia**, escolha sua webcam e inicie a câmera. Mantenha o fundo
**Estático**, capture o cenário vazio e confirme. Volte e teste o gesto ilustrado
em **Como fazer** ou **Ativar efeito**. Use **Reaparecer** e **Restaurar** para
recuperar sua imagem; alguns teclados exigem **Fn + F8**.

## Usar no Meet, Discord, Teams ou OBS

1. Instale [OBS Studio 30 ou posterior](https://obsproject.com/download), compatível
   com seu macOS. A prévia dentro do Fora de Cena funciona sem OBS.
2. No OBS, inicie e pare a câmera virtual uma vez. Feche o OBS.
3. Se solicitado, autorize **OBS Virtual Camera** em **Ajustes do Sistema → Geral →
   Itens de Início e Extensões → Extensões de Câmera**. Reabra o navegador.
4. No Fora de Cena, use sua webcam física como entrada e **OBS Virtual Camera** como
   saída. Inicie o vídeo antes de selecionar essa câmera na chamada.
5. Desative desfoque e fundos virtuais no serviço de chamada.

Não deixe a câmera virtual iniciada no OBS enquanto o Fora de Cena a utiliza.
A extensão de navegador é opcional e serve somente para fechar a aba vinculada
no Meet. Veja [COMO_USAR.md](COMO_USAR.md).

## O que foi validado

- Build completo no runner Mac Intel `macos-15-intel`, em cerca de 20 minutos.
- Dependências, testes, quatro modelos, interface e executável empacotado.
- As sete imagens de gestos, arquitetura x86_64, bibliotecas e assinatura ad-hoc.
- O proprietário informou que o teste completo em **M1 com Rosetta** funcionou.
  Não foram informadas separadamente a versão do macOS ou medições de desempenho.
- **Ainda não há confirmação de webcam/chamada em um Mac Intel físico.** O teste
  pelo Rosetta não certifica desempenho ou compatibilidade de todos os Macs Intel.

[Execução nativa](https://github.com/arantes-gabs/fora-de-cena/actions/runs/40733625127).

## Limites e privacidade

Intel usa **OpenCV DNN em CPU**, com modelos locais de palma, pontos da mão,
rosto e segmentação. Este pacote não importa MediaPipe nem ONNX Runtime.
A interface, os efeitos e as regras dos gestos são compartilhados com os demais
sistemas; a precisão do recorte e dos gestos pode diferir. Sem garantia de 30 FPS.
Se necessário, teste 640 × 480 e fundo Estático.

A ausência de MediaPipe neste perfil não é uma certificação de ausência de rede.
A verificação geral de dependências segue pendente. Permanecem
`distribution_ready=false` e `dependency_network_verified=false`. Leia
[Privacidade](PRIVACY.md). Os efeitos não garantem anonimização.

## Fontes, versão e integridade

A versão interna do app continua **0.5.0-beta.2**. A tag **v0.5.0-beta.2-intel.1** identifica
esta distribuição Intel separada, preservando a Release beta.2 do Linux.
O DMG é exatamente o testado no CI e pelo proprietário, sem recompilação.

Os [fontes desta distribuição](https://github.com/arantes-gabs/fora-de-cena/tree/v0.5.0-beta.2-intel.1) correspondem ao commit
`03b49f86d3f784c0ee2a58c33db691c6f406e12d`. Para reproduzir ou estudar o Intel,
use essa tag ou o ZIP de fontes da Release; a main pode conter outro estado de
código. A documentação atualizada fica na main. A licença do aplicativo é MIT;
o auxiliar independente de saída é GPL-2.0-only e seus fontes/avisos acompanham o DMG.

Para conferir o DMG no Terminal:

```sh
shasum -a 256 ForaDeCena-0.5.0-beta.2-macos-x86_64-experimental.dmg
```

Compare com `SHA256SUMS.txt` da [Release](https://github.com/arantes-gabs/fora-de-cena/releases/tag/v0.5.0-beta.2-intel.1). O checksum confere os bytes;
não substitui assinatura Developer ID ou notarização.

## Relatar problemas

[Abra um relato](https://github.com/arantes-gabs/fora-de-cena/issues/new/choose) com versão do macOS, chip, versão do
app e passos para reproduzir. Informe se usou Intel físico ou Rosetta.
Remova dados pessoais, caminhos privados e credenciais antes de compartilhar logs.
Para vulnerabilidades, siga [SECURITY.md](SECURITY.md).
