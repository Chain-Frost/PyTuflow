"""Fork-only acceptance of an exact, separately checked-out curated source."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

UPSTREAM = 'cf908cc922ca8448ed6002834877b0b377329eae'
INTEGRATION = '251387feeae0e53e48fddae762d59b13b2a8f525'
CANDIDATE = '127a4df24f40fe8e4d1bfa37b33893c3dd2dd88f'
HARNESS = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--case-only', action='store_true')
    args = parser.parse_args()
    source, out = args.source.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    def run(name, command, cwd=source, required=True):
        with (out / (name+'.log')).open('w', encoding='utf-8') as stream:
            code = subprocess.run([str(x) for x in command], cwd=cwd, stdout=stream, stderr=subprocess.STDOUT).returncode
        (out / (name+'.exit.json')).write_text(json.dumps({'command':list(map(str,command)), 'exit_code':code}))
        print(name, code, flush=True)
        if required and code: raise RuntimeError(f'{name} failed with {code}; see retained log')
        return code
    def git(*params):
        return subprocess.check_output(['git','-C',str(source),*params], text=True).strip()
    assert git('rev-parse','HEAD') == CANDIDATE
    assert not git('status','--porcelain')
    assert git('merge-base',UPSTREAM,CANDIDATE) == UPSTREAM
    # The reviewed update is an intentionally narrow post-curation fix:
    # only the 3D scalar-component reader and its existing FV regression module.
    updated=git('diff','--name-only','ee0f6e2f64c80305b5c7734a83b93f7dee18e64e',CANDIDATE).splitlines()
    assert set(updated)=={
        'pytuflow/_outputs/pymesh/cell_data_mixin.py',
        'tests/test_numerical_fv_reader.py',
    }, updated
    assert git('rev-parse',INTEGRATION+':tests/ci/test_fm_comparison.py') == git('rev-parse',CANDIDATE+':tests/test_fm_comparison.py')
    paths=git('diff','--name-only',UPSTREAM,CANDIDATE).splitlines()
    assert not any(p.startswith(('.github/','ci/','tests/ci/','docs/contributing/')) or p in ('AGENTS.md','UPSTREAM_STACK.md') or p.endswith(('.pyi','py.typed')) for p in paths)
    (out/'provenance.json').write_text(json.dumps({'candidate':CANDIDATE,'upstream':UPSTREAM,'accepted_integration':INTEGRATION,'python':sys.version,'paths':paths,'post_curation_correction':True},indent=2))
    run('grammar',[sys.executable,HARNESS/'ci/python_compatibility.py'])
    if args.case_only:
        run('case-policy',[sys.executable,'-m','pytest','-q','-ra','tests/test_linux_case_policy.py','--junitxml='+str(out/'case.xml')])
        return
    run('harness-contracts',[sys.executable,'-m','pytest','-q','tests/ci','--junitxml='+str(out/'harness.xml')],cwd=HARNESS)
    run('build',[sys.executable,'-m','build','--no-isolation','--outdir',out/'dist'])
    wheels=list((out/'dist').glob('*.whl'));assert len(wheels)==1
    run('install-wheel',[sys.executable,'-m','pip','install','--no-deps','--force-reinstall',wheels[0]])
    run('dependency-check',[sys.executable,'-m','pip','check'])
    outside=out/'outside';outside.mkdir()
    run('wheel-smoke',[sys.executable,'-I',HARNESS/'ci/wheel_smoke.py','--source-root',source,'--wheel',wheels[0],'--report',out/'wheel-smoke.json'],cwd=outside)
    # Every new standalone non-provider regression module, including import/API tests.
    modules=['fm_comparison','package_import_logging','mesh_backend_capability','public_api_contracts','result_time_correctness','pandas31_output_compatibility','raster_cache_reader_recovery','numerical_depth_averaging','numerical_mesh_reductions','numerical_fv_reader','qgis_centroid_math','qgis_vertex_angle_math','cell_point_vector_corrections']
    run('focused',[sys.executable,'-m','pytest','-q','-ra',*['tests/test_'+m+'.py' for m in modules],'--junitxml='+str(out/'focused.xml')])
    run('case-policy',[sys.executable,'-m','pytest','-q','-ra','tests/test_linux_case_policy.py','--junitxml='+str(out/'case.xml')])
    for role,sha in [('upstream',UPSTREAM),('base',INTEGRATION),('candidate',CANDIDATE)]:
        run(role,[sys.executable,HARNESS/'ci/run_regression.py','--source',source,'--ref',sha,'--label',role,'--report-dir',out/role],required=False)
        report=json.loads((out/role/'report.json').read_text())
        assert report['completed'] and report['source']['sha']==sha and report['source']['checkout_unchanged']
    for baseline in ['upstream','base']:
        run(baseline+'-comparison',[sys.executable,HARNESS/'ci/compare_regression.py','--baseline',out/baseline/'report.json','--candidate',out/'candidate/report.json','--output',out/(baseline+'-comparison.json')])
    # Installed public-API tests are copied outside every checkout and run in -I mode.
    import shutil
    shutil.copyfile(source/'tests/test_public_api_contracts.py',outside/'test_public_api_contracts.py')
    run('wheel-api',[sys.executable,'-I','-m','pytest','-q','test_public_api_contracts.py','--junitxml='+str(out/'wheel-api.xml')],cwd=outside)
    assert not git('status','--porcelain')
    (out/'COMPLETE.json').write_text(json.dumps({'candidate':CANDIDATE,'status':'passed'}))

if __name__ == '__main__': main()
