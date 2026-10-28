"""Stage an allowlisted Intel test download locally. Never upload or publish."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from teleport_cam import __version__
from tools.distribution_licenses import runtime_signature
from tools.release_candidates import candidate_files


def validate_reports(folder: Path) -> dict[str, object]:
    manifest = json.loads((folder / 'candidate.json').read_text(encoding='utf-8'))
    inference = json.loads((folder / 'native-self-test.json').read_text(encoding='utf-8'))
    gui = json.loads((folder / 'native-gui-self-test.json').read_text(encoding='utf-8'))
    audit = json.loads((folder / 'macos-bundle-audit.json').read_text(encoding='utf-8'))
    signature = runtime_signature()
    if (manifest.get('target') != 'macos-x86_64' or manifest.get('version') != __version__
            or manifest.get('vision_backend') != 'opencv-dnn'
            or manifest.get('runtime_signature') != signature
            or manifest.get('distribution_ready') is not False
            or manifest.get('validation', {}).get('ad_hoc_signature_verified') is not True
            or manifest.get('validation', {}).get('dependency_network_verified') is not False):
        raise ValueError('Intel manifest is not the selected experimental source/profile.')
    if (inference.get('ok') is not True or inference.get('frozen') is not True
            or inference.get('version') != __version__ or inference.get('runtime_signature') != signature
            or inference.get('vision_backend') != 'opencv-dnn'
            or inference.get('camera_opened') is not False
            or inference.get('dependency_network_verified') is not False):
        raise ValueError('Intel frozen model diagnostic is incomplete.')
    if (gui.get('ok') is not True or gui.get('frozen') is not True
            or gui.get('version') != __version__ or gui.get('guide_images_rendered') != 7
            or gui.get('camera_opened') is not False or gui.get('meet_bridge_opened') is not False):
        raise ValueError('Intel frozen guide image diagnostic is incomplete.')
    if audit.get('architecture') != 'x86_64' or not audit.get('binaries'):
        raise ValueError('Intel bundle architecture audit is incomplete.')
    # Select only fixed aggregate fields. Never copy arbitrary build logs/reports.
    return {'product': 'Fora de Cena', 'version': __version__, 'target': 'macos-x86_64',
            'vision_backend': 'opencv-dnn', 'runtime_signature': signature,
            'minimum_target': manifest['minimum_target'], 'native_frozen_self_test': True,
            'guide_images_rendered': 7, 'ad_hoc_signature_verified': True,
            'camera_opened': False, 'real_camera_and_calls_tested': False,
            'dependency_network_verified': False, 'distribution_ready': False}


def stage(root: Path = ROOT) -> Path:
    selected = candidate_files('macos-x86_64')
    summary = validate_reports(selected[0].parent)
    destination = root / 'work' / 'intel-candidate-download'
    if destination.exists() or not destination.resolve().is_relative_to((root / 'work').resolve()):
        raise ValueError('Intel staging destination must be new and inside project work/.')
    allowed = {f'ForaDeCena-{__version__}-macos-x86_64-experimental.dmg',
               f'ForaDeCena-{__version__}-Fontes-Saida.zip', f'ForaDeCena-{__version__}-Licencas.zip'}
    files = [path for path in selected if path.name in allowed]
    if {path.name for path in files} != allowed:
        raise ValueError('Intel download allowlist is incomplete.')
    if any(path.is_symlink() or not path.is_file()
           or not path.resolve().is_relative_to((root / 'dist').resolve()) for path in files):
        raise ValueError('Intel download contains a missing or redirected asset.')
    destination.mkdir(parents=True)
    for path in files:
        shutil.copyfile(path, destination / path.name)
    (destination / 'VALIDACAO.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    (destination / 'LEIA_PRIMEIRO.txt').write_text(
        'Fora de Cena — Mac Intel, candidato experimental\n\n'
        'Abra o DMG e copie Fora de Cena.app para Aplicativos. Não precisa de Python.\n'
        'Mínimo do pacote: ' + str(summary['minimum_target']) + '.\n'
        'O app não tem notarização Apple. Depois de tentar abrir, autorize somente\n'
        'este arquivo em Ajustes do Sistema > Privacidade e Segurança > Abrir Mesmo Assim.\n'
        'Não desative as proteções do Mac.\n\n'
        'Teste primeiro em Só prévia, com fundo Estático e os gestos indicados.\n'
        'Para chamadas, instale OBS 30+, autorize sua extensão de câmera e inicie/pare\n'
        'a câmera virtual uma vez no OBS. Feche o OBS. Use OBS Virtual Camera no app\n'
        'e na chamada. O microfone permanece o da chamada.\n\n'
        'Testes automatizados passaram; webcam, qualidade dos gestos, desempenho\n'
        'e chamadas em Mac Intel real ainda precisam de teste. Sem garantia de 30 FPS.\n'
        'A verificação geral de rede/dependências continua pendente. Leia PRIVACY.md\n'
        'no repositório antes de usar. Não é uma certificação de ausência de rede.\n\n'
        'Fontes-Saida e Licencas acompanham o auxiliar GPL e as dependências.\n'
        'Não precisam ser instalados. Preserve o acesso a eles ao redistribuir.\n'
        'Erros: https://github.com/arantes-gabs/fora-de-cena/issues/new/choose\n'
        'Remova dados pessoais e credenciais antes de compartilhar logs.\n', encoding='utf-8')
    checksums = []
    for path in sorted(destination.iterdir()):
        with path.open('rb') as stream:
            checksum = hashlib.file_digest(stream, 'sha256').hexdigest()
        checksums.append(f'{checksum}  {path.name}\n')
    (destination / 'SHA256SUMS.txt').write_text(''.join(checksums), encoding='ascii')
    print('Intel candidate staged: 6 allowlisted files. No commit, upload or Release.')
    return destination


if __name__ == '__main__':
    stage()
