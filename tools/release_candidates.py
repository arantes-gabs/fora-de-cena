"""Prepare review-only draft assets for this repository. Never publish a release."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from teleport_cam import __version__
from tools.distribution_licenses import runtime_signature
from tools.package_release import build as source_zip

REPOSITORY='arantes-gabs/fora-de-cena'
TARGETS={
    'windows-x64': ('windows-2022','x64'),
    'macos-arm64': ('macos-15','arm64'),
    'macos-x86_64': ('macos-15-intel','x64'),
    'linux-x86_64': ('ubuntu-22.04','x64'),
    'linux-arm64': ('ubuntu-22.04-arm','arm64'),
}


def matrix(selection):
    if selection not in ('all','mac-linux') and selection not in TARGETS:
        raise ValueError('Unknown release target.')
    return {'include':[{'target':target,'runner':runner,'architecture':arch}
                       for target,(runner,arch) in TARGETS.items()
                       if selection=='all' or selection==target or
                       (selection=='mac-linux' and target in ('macos-arm64','linux-x86_64','linux-arm64'))]}


def require_context(env=None):
    env=os.environ if env is None else env
    if (env.get('GITHUB_ACTIONS')!='true' or env.get('GITHUB_REPOSITORY')!=REPOSITORY
            or env.get('GITHUB_EVENT_NAME')!='workflow_dispatch'
            or env.get('GITHUB_REF')!='refs/heads/main'
            or env.get('GITHUB_ACTOR')!='arantes-gabs'
            or env.get('GITHUB_TRIGGERING_ACTOR',env.get('GITHUB_ACTOR'))!='arantes-gabs'
            or env.get('FDC_OWNER_CONFIRMED')!='true'):
        raise RuntimeError('Draft operations require an owner-triggered main workflow in Fora de Cena.')
    expected=env.get('FDC_EXPECTED_COMMIT','')
    if not re.fullmatch('[0-9a-f]{40}',expected) or expected!=env.get('GITHUB_SHA'):
        raise RuntimeError('The reviewed commit must match the workflow commit exactly.')
    if not re.fullmatch(r'\d+\.\d+\.\d+-beta\.\d+',__version__):
        raise RuntimeError('This tool creates only beta review drafts, never stable releases.')
    return expected


def gh(arguments, body=None, missing_ok=False):
    require_context()
    token=os.environ.get('GH_TOKEN')
    if not token:
        raise RuntimeError('The repository workflow token is required.')
    home=ROOT/'work/draft-gh-home'
    if not home.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError('Redirected draft CLI profile.')
    home.mkdir(parents=True,exist_ok=True)
    environment={key:os.environ[key] for key in ('PATH','SystemRoot','WINDIR','TEMP','TMP') if key in os.environ}
    environment.update(GH_TOKEN=token,GH_HOST='github.com',GH_PROMPT_DISABLED='1',
                       GH_CONFIG_DIR=str(home/'config'),HOME=str(home),USERPROFILE=str(home),
                       XDG_CONFIG_HOME=str(home/'config'),XDG_STATE_HOME=str(home/'state'),
                       XDG_CACHE_HOME=str(home/'cache'),APPDATA=str(home),LOCALAPPDATA=str(home))
    result=subprocess.run(['gh',*arguments],input=json.dumps(body) if body is not None else None,
                          env=environment,text=True,capture_output=True,timeout=600)
    if result.returncode:
        if missing_ok and 'HTTP 404' in result.stderr:
            return None
        raise RuntimeError('GitHub draft request failed; credentials and raw response are not printed.')
    return result.stdout


def draft(create=False):
    commit=require_context()
    tag='v'+__version__
    route='repos/'+REPOSITORY+'/releases'
    raw=gh(['api','--hostname','github.com',route+'/tags/'+tag],missing_ok=True)
    if raw is None:
        if not create:
            raise RuntimeError('Create the reviewed draft before uploading assets.')
        raw=gh(['api','--hostname','github.com','--method','POST',route,'--input','-'],{
            'tag_name':tag,'target_commitish':commit,'name':'Fora de Cena '+__version__+' — revisão',
            'draft':True,'prerelease':True,
            'body':('Rascunho para revisão do proprietário; sem publicação automática.\n\n'
                    'Commit: `'+commit+'`.\n\n'
                    'Pacotes experimentais, `distribution_ready=false`. Validar câmera, '
                    'gestos, OBS/saída virtual, chamadas, licenças e rede antes de publicar.\n\n'
                    'Os fontes correspondentes da saída e as licenças são específicos de cada plataforma. '
                    'Confira o arquivo SHA256SUMS da plataforma escolhida.\n')})
    record=json.loads(raw)
    if (not record.get('draft') or not record.get('prerelease')
            or record.get('tag_name')!=tag or record.get('target_commitish')!=commit):
        raise RuntimeError('Existing release is not the matching owner review draft; do not overwrite it.')
    return record


def passed_report(path):
    report=json.loads(path.read_text(encoding='utf-8'))
    if (report.get('ok') is not True or report.get('frozen') is not True
            or report.get('camera_opened') is not False or report.get('version')!=__version__
            or report.get('runtime_signature')!=runtime_signature()):
        raise ValueError('Frozen diagnostic does not match the candidate source.')


def candidate_files(target):
    if target not in TARGETS:
        raise ValueError('Unknown candidate target.')
    if target=='windows-x64':
        folder=ROOT/'dist/windows'
        manifest=json.loads((ROOT/'work/bundle-build.json').read_text(encoding='utf-8'))
        for name in ('single-file-self-test.json','frozen-self-test.json','extracted-self-test.json'):
            passed_report(ROOT/'work'/name)
        selected=[folder/('ForaDeCena-'+__version__+'-'+suffix)
                  for suffix in ('Portatil.exe','Setup.exe','Fontes-Saida.zip','Licencas.zip')]
        platform=manifest.get('platform')
    else:
        folders=list((ROOT/'dist/native').glob(target+'-*/candidate.json'))
        if len(folders)!=1:
            raise ValueError('Expected one fresh native candidate, never an older output.')
        folder=folders[0].parent
        manifest=json.loads(folders[0].read_text(encoding='utf-8'))
        passed_report(folder/'native-self-test.json')
        extension='.dmg' if target.startswith('macos') else '.tar.gz'
        selected=[folder/('ForaDeCena-'+__version__+'-'+target+'-experimental'+extension)]
        selected += [folder/('ForaDeCena-'+__version__+'-'+suffix) for suffix in ('Fontes-Saida.zip','Licencas.zip')]
        selected += [folder/name for name in ('candidate.json','native-self-test.json','native-libraries.json')]
        platform=manifest.get('target')
    if (manifest.get('version')!=__version__ or platform!=target
            or manifest.get('runtime_signature')!=runtime_signature()
            or manifest.get('distribution_ready') is not False):
        raise ValueError('Build manifest differs from the selected experimental source.')
    for path in selected:
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to((ROOT/'dist').resolve()):
            raise ValueError('Missing or redirected candidate asset.')
        if path.stat().st_size>=2*1024**3:
            raise ValueError('Candidate exceeds the GitHub release file limit.')
    return selected


def upload(files, target):
    record=draft()
    stage=ROOT/'work/draft-upload'/target
    if stage.exists() or not stage.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError('Use a new candidate upload staging directory.')
    stage.mkdir(parents=True)
    staged=[]
    for source in files:
        name=source.name
        if target not in name and target!='source':
            name='ForaDeCena-'+__version__+'-'+target+'-'+name.removeprefix('ForaDeCena-'+__version__+'-')
        path=stage/name
        shutil.copyfile(source,path)
        staged.append(path)
    checksums=stage/(target+'-SHA256SUMS.txt')
    def digest(path):
        with path.open('rb') as stream:
            return hashlib.file_digest(stream,'sha256').hexdigest()
    checksums.write_text(''.join(digest(p)+'  '+p.name+'\n' for p in staged),encoding='ascii')
    staged.append(checksums)
    existing={asset['name']:asset.get('digest') for asset in record.get('assets',[])}
    for path in staged:
        if path.name in existing and existing[path.name]!='sha256:'+digest(path):
            raise ValueError('Existing draft asset differs; no executable, source or checksum is overwritten.')
    missing=[path for path in staged if path.name not in existing]
    if missing:
        gh(['release','upload','v'+__version__,'--repo','github.com/'+REPOSITORY,*map(str,missing)])
    print('Review draft assets verified:',target,len(staged),'files. No release was published.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('plan','prepare','upload'))
    parser.add_argument('--target',default='all')
    args=parser.parse_args()
    if args.action=='plan':
        print(json.dumps(matrix(args.target)))
    elif args.action=='prepare':
        require_context()
        draft(create=True)
        upload([source_zip(destination=ROOT/'work/draft-source')],'source')
    else:
        require_context()
        upload(candidate_files(args.target),args.target)


if __name__=='__main__':
    main()
