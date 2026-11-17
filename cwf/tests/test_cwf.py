import copy
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from cwf.common import Fault, digest, write_json, scope_info
from cwf.config import settings, DEFAULTS
from cwf.contracts import validate, SCHEMAS, PACKET
from cwf.discovery import discover
from cwf.state import State
from cwf.operations import checkpoint, resume, observation, batch_validate, run_checks, worktree
from cwf.adapters import LocalTextAdapter


class Environment(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='cwf-tests-',dir=os.environ.get('CWF_TEST_TMP'))
        self.base=Path(self.tmp.name).resolve(); self.home=self.base/'personal home'; self.home.mkdir()
        self.repo=self.base/'work repo'; self.repo.mkdir()
        self.config=copy.deepcopy(DEFAULTS)
    def tearDown(self): self.tmp.cleanup()
    def put(self,path,text):
        p=self.repo/path; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text); return p
    def request(self,**kw): return dict(scope=str(self.repo),domain='build',query='widget',**kw)
    def cli(self,*args,request=None,home=None):
        cmd=[sys.executable,'-B',str(ROOT/'cwf.py'),'--home',str(home or self.home),*args]
        if request is not None: cmd+=['--input','-']
        p=subprocess.run(cmd,input=json.dumps(request) if request is not None else None,text=True,capture_output=True)
        self.assertTrue(p.stdout,p.stderr)
        return p.returncode,json.loads(p.stdout)
    def git(self,*args,root=None):
        p=subprocess.run(['git','-C',str(root or self.repo),*args],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr); return p.stdout.strip()
    def initgit(self):
        self.git('init'); self.git('config','user.name','CWF Test'); self.git('config','user.email','test@example.invalid')
        self.put('source.ts','export const widget = 1;\n'); self.git('add','source.ts'); self.git('commit','-m','initial')
    def task(self,**changes):
        t={'schema_version':'cwf/v1','id':'task1','outcome':'Update widget','scope_root':str(self.repo),
           'domains':['build'],'status':'running','acceptance':['works'],'sources':[]}
        t.update(changes); return t


class EnvironmentTests(unittest.TestCase):
    def test_symlinked_temporary_root_is_canonicalized(self):
        with tempfile.TemporaryDirectory(prefix='cwf-fixture-') as tmp:
            root=Path(tmp).resolve()
            real=root/'real'; real.mkdir()
            alias=root/'alias'; alias.symlink_to(real, target_is_directory=True)
            with patch.dict(os.environ, {'CWF_TEST_TMP':str(alias)}):
                fixture=Environment()
                fixture.setUp()
                try:
                    for path in (fixture.base, fixture.home, fixture.repo):
                        self.assertEqual(path, path.resolve())
                    config=fixture.home/'.config/cwf/config.json'
                    write_json(config, {'schema_version':'cwf/v1','mode':'off'})
                    self.assertEqual(settings(fixture.home)['mode'], 'off')
                finally:
                    fixture.tearDown()
            self.assertEqual(list(real.iterdir()), [])


class WriteSafetyTests(Environment):
    def test_writable_destination_symlinks_refused(self):
        for kind in ('ancestor', 'directory', 'file'):
            for dangling in (False, True):
                with self.subTest(kind=kind, dangling=dangling):
                    case=self.home/f'{kind}-{dangling}'; case.mkdir()
                    outside=self.base/f'outside-{kind}-{dangling}'
                    if not dangling:
                        if kind=='file': outside.write_text('keep')
                        else:
                            outside.mkdir()
                            (outside/'sentinel').write_text('keep')
                    link=case/'link'; link.symlink_to(outside, target_is_directory=kind!='file')
                    destination={'ancestor':link/'nested/config.json',
                                 'directory':link/'config.json', 'file':link}[kind]
                    with self.assertRaises(Fault) as caught:
                        write_json(destination, {'changed':True})
                    self.assertEqual(caught.exception.code, 'blocked')
                    self.assertTrue(link.is_symlink())
                    if dangling: self.assertFalse(outside.exists())
                    elif kind=='file': self.assertEqual(outside.read_text(), 'keep')
                    else:
                        self.assertEqual([p.name for p in outside.iterdir()], ['sentinel'])
                        self.assertEqual((outside/'sentinel').read_text(), 'keep')


class DiscoveryTests(Environment):
    def test_deterministic_findings_and_warm_fingerprint(self):
        self.put('b.ts','export const widget = 1;'); self.put('a.ts','export const widget = 2;')
        first=discover(self.home,self.request(),self.config)
        second=discover(self.home,self.request(),self.config)
        self.assertEqual(first['findings'],second['findings'])
        self.assertEqual(first['snapshot_digest'],second['snapshot_digest'])
        self.assertEqual(second['cache'],'fingerprint_match'); validate(second,PACKET)
    def test_add_edit_delete_invalidate(self):
        f=self.put('a.ts','widget'); p=discover(self.home,self.request(),self.config)
        self.put('b.ts','widget'); q=discover(self.home,self.request(),self.config)
        self.assertNotEqual(p['snapshot_digest'],q['snapshot_digest'])
        f.write_text('widget changed'); r=discover(self.home,self.request(),self.config)
        self.assertNotEqual(q['snapshot_digest'],r['snapshot_digest'])
        f.unlink(); s=discover(self.home,self.request(),self.config)
        self.assertNotEqual(r['snapshot_digest'],s['snapshot_digest'])
    def test_sensitive_symlink_and_binary_excluded(self):
        self.put('.env','SECRET=widget'); self.put('id_rsa','widget PRIVATE'); self.put('a.ts','widget')
        outside=self.base/'outside.txt'; outside.write_text('widget SECRET')
        (self.repo/'link.txt').symlink_to(outside)
        (self.repo/'binary.ts').write_bytes(b'widget\0secret')
        p=discover(self.home,self.request(),self.config)
        self.assertEqual([f['source_ref'] for f in p['findings']],['a.ts'])
        self.assertGreater(p['coverage']['excluded'],0)
    def test_git_ignore_respected(self):
        self.initgit(); self.put('.gitignore','private/\n'); self.put('private/x.ts','widget SECRET')
        p=discover(self.home,self.request(),self.config)
        self.assertNotIn('private/x.ts',[f['source_ref'] for f in p['findings']])
    def test_partial_bounds(self):
        for i in range(12): self.put(f'{i}.ts','widget')
        cfg=copy.deepcopy(self.config); cfg['limits']['max_files']=3
        p=discover(self.home,self.request(),cfg)
        self.assertEqual(p['status'],'partial'); self.assertLessEqual(p['coverage']['files'],3)
    def test_output_omissions_are_partial(self):
        for i in range(5): self.put(f'{i}.ts','widget '*300)
        cfg=copy.deepcopy(self.config); cfg['limits']['max_findings']=1
        p=discover(self.home,self.request(),cfg)
        self.assertEqual(len(p['findings']),1); self.assertEqual(p['coverage']['omitted_results'],4)
        self.assertEqual(p['status'],'partial')
    def test_large_file_is_unknown_not_clear(self):
        self.put('large.ts','widget '*100)
        cfg=copy.deepcopy(self.config); cfg['limits']['file_bytes']=100
        p=discover(self.home,self.request(),cfg)
        self.assertEqual(p['status'],'partial'); self.assertGreater(p['coverage']['read_failures'],0)
    def test_ephemeral_leaves_no_state(self):
        self.put('a.ts','widget')
        p=discover(self.home,self.request(),self.config,True)
        self.assertEqual(p['persistence'],'ephemeral'); self.assertFalse((self.home/'.local').exists())
    def test_corrupt_cache_falls_back_without_deletion(self):
        db=self.home/'.local/state/cwf/state.sqlite3'; db.parent.mkdir(parents=True); db.write_text('corrupt')
        self.put('a.ts','widget'); p=discover(self.home,self.request(),self.config)
        self.assertEqual(p['persistence'],'ephemeral'); self.assertEqual(db.read_text(),'corrupt')
    def test_home_scan_refused(self):
        with self.assertRaises(Fault): discover(self.home,dict(self.request(),scope=str(self.home)),self.config)
    def test_traversal_refused(self):
        with self.assertRaises(Fault): discover(self.home,self.request(files=['../outside']),self.config)
    def test_mode_off_does_not_scan_or_write(self):
        write_json(self.home/'.config/cwf/config.json',{'schema_version':'cwf/v1','mode':'off'})
        self.put('.cwf.json','not json')
        code,out=self.cli('discover',request={'scope':str(self.repo)})
        self.assertEqual(code,0); self.assertEqual(out['status'],'skipped'); self.assertFalse((self.home/'.local').exists())
    def test_local_config_cannot_remove_exclusions(self):
        write_json(self.home/'.config/cwf/config.json',{'schema_version':'cwf/v1','exclusions':['private/**'],'mode':'advisory'})
        self.put('.cwf.json',json.dumps({'schema_version':'cwf/v1','exclusions':[],'mode':'active'}))
        cfg=settings(self.home,self.repo)
        self.assertIn('private/**',cfg['exclusions']); self.assertEqual(cfg['mode'],'advisory')
    def test_adapter_provenance_and_freshness(self):
        f=self.put('doc.md','widget'); a=LocalTextAdapter(self.repo,self.config); s=a.read('doc.md')
        self.assertEqual(a.freshness('doc.md',s.revision),'verified')
        f.write_text('changed'); self.assertEqual(a.freshness('doc.md',s.revision),'stale')
        self.assertFalse(a.capabilities()['write'])
    def test_widget_candidates_include_migration_and_successor(self):
        shutil.copytree(ROOT/'fixtures/widget',self.repo,dirs_exist_ok=True)
        p=discover(self.home,dict(self.request(),query='widget value modification',files=['src/component.ts']),self.config)
        refs=[f['source_ref'] for f in p['findings']]
        self.assertIn('docs/migration.md',refs); self.assertIn('src/modify.ts',refs)

    def test_targeted_read_and_check_respect_roots_and_git_ignores(self):
        self.initgit(); self.put('private.md','widget sensitive'); self.put('allowed/a.md','widget')
        self.put('.cwf.json',json.dumps({'schema_version':'cwf/v1','source_roots':['allowed']}))
        code,out=self.cli('inspect-source',request={'scope':str(self.repo),'domain':'docs','path':'private.md'})
        self.assertEqual(code,3); self.assertNotIn('sensitive',json.dumps(out))
        cfg=settings(self.home,self.repo)
        check={'id':'private','kind':'absent_literal','paths':['private.md'],'literal':'sensitive','required':True}
        self.assertEqual(run_checks({'scope':str(self.repo),'checks':[check]},cfg)['checks'][0]['status'],'unknown')
        self.put('.cwf.json',json.dumps({'schema_version':'cwf/v1'})); self.put('.gitignore','private.md\n')
        self.assertEqual(run_checks({'scope':str(self.repo),'checks':[check]},self.config)['checks'][0]['status'],'unknown')

    def test_targeted_nested_repo_refused(self):
        nested=self.repo/'nested'; nested.mkdir(); self.git('init',root=nested); self.put('nested/private.md','widget sensitive')
        code,out=self.cli('inspect-source',request={'scope':str(self.repo),'domain':'docs','path':'nested/private.md'})
        self.assertEqual(code,3); self.assertNotIn('sensitive',json.dumps(out))

    def test_scope_source_roots_intersect(self):
        write_json(self.home/'.config/cwf/config.json',{'schema_version':'cwf/v1','source_roots':['allowed']})
        self.put('.cwf.json',json.dumps({'schema_version':'cwf/v1','source_roots':['outside']}))
        with self.assertRaises(Fault): settings(self.home,self.repo)
        self.put('.cwf.json',json.dumps({'schema_version':'cwf/v1','source_roots':['allowed/sub']}))
        self.assertEqual(settings(self.home,self.repo)['source_roots'],['allowed/sub'])

    def test_observation_retrieval_requires_current_sources(self):
        f=self.put('decision.md','widget convention'); record={'schema_version':'cwf/v1','id':'convention',
          'statement':'widget behavior is shared','claim_status':'inferred','sources':[{'path':'decision.md','content_hash':digest(f.read_bytes())}]}
        observation(self.home,{'scope':str(self.repo),'record':record},self.config)
        a=discover(self.home,self.request(),self.config)
        self.assertTrue(any(x['kind']=='local_observation' for x in a['findings']))
        f.write_text('widget changed')
        b=discover(self.home,self.request(),self.config)
        self.assertFalse(any(x['kind']=='local_observation' for x in b['findings']))

    def test_packet_total_bytes_are_bounded(self):
        for i in range(20): self.put(f'{i}.md','widget '*200)
        cfg=copy.deepcopy(self.config); cfg['limits']['packet_bytes']=1000
        p=discover(self.home,self.request(),cfg)
        from cwf.common import canonical
        self.assertLessEqual(len(canonical(p).encode()),3000)


class StateTests(Environment):
    def test_checkpoint_cas_and_resume(self):
        req={'scope':str(self.repo),'record':self.task(),'expected_revision':0}
        saved=checkpoint(self.home,req,self.config); self.assertEqual(saved['revision'],1)
        with self.assertRaises(Fault): checkpoint(self.home,req,self.config)
        req['expected_revision']=1; req['record']['next_action']='inspect source'
        self.assertEqual(checkpoint(self.home,req,self.config)['revision'],2)
        self.assertTrue(resume(self.home,{'scope':str(self.repo),'id':'task1'},self.config)['ready_to_resume'])
    def test_complete_requires_evidence(self):
        req={'scope':str(self.repo),'record':self.task(status='complete')}
        with self.assertRaises(Fault): checkpoint(self.home,req,self.config)
        req['record']['evidence']=[{'criterion':'works','source':'test run 1'}]
        self.assertEqual(checkpoint(self.home,req,self.config)['record']['status'],'complete')
    def test_stale_resume_and_observation(self):
        f=self.put('a.md','rule'); source={'path':'a.md','content_hash':digest(f.read_bytes())}
        checkpoint(self.home,{'scope':str(self.repo),'record':self.task(sources=[source])},self.config)
        f.write_text('changed')
        self.assertFalse(resume(self.home,{'scope':str(self.repo),'id':'task1'},self.config)['ready_to_resume'])
        with self.assertRaises(Fault): observation(self.home,{'scope':str(self.repo),'record':{'schema_version':'cwf/v1','id':'obs','statement':'rule','claim_status':'observed','sources':[source]}},self.config)
    def test_accepted_observation_needs_attribution(self):
        f=self.put('a.md','Accepted rule'); source={'path':'a.md','content_hash':digest(f.read_bytes())}
        record={'schema_version':'cwf/v1','id':'obs','statement':'rule','claim_status':'accepted','sources':[source]}
        with self.assertRaises(Fault): observation(self.home,{'scope':str(self.repo),'record':record},self.config)
        record.update(accepted_by='team',acceptance_source='a.md')
        saved=observation(self.home,{'scope':str(self.repo),'record':record},self.config)
        self.assertEqual(saved['record']['claim_status'],'accepted')
    def test_scope_isolation_and_summary_export(self):
        checkpoint(self.home,{'scope':str(self.repo),'record':self.task()},self.config)
        other=self.base/'other'; other.mkdir()
        with self.assertRaises(Fault): resume(self.home,{'scope':str(other),'id':'task1'},self.config)
        code,out=self.cli('state','export',request={'scope':str(self.repo)})
        self.assertEqual(code,0); self.assertNotIn('Update widget',json.dumps(out)); self.assertNotIn(str(self.repo),json.dumps(out))
    def test_off_still_allows_explicit_state_management(self):
        checkpoint(self.home,{'scope':str(self.repo),'record':self.task()},self.config)
        write_json(self.home/'.config/cwf/config.json',{'schema_version':'cwf/v1','mode':'off'})
        code,out=self.cli('state','export',request={'scope':str(self.repo)})
        self.assertEqual(code,0); self.assertEqual(out['data']['counts']['task'],1)
    def test_old_record_with_a_version_field_still_resumes(self):
        checkpoint(self.home,{'scope':str(self.repo),'record':self.task()},self.config)
        with State(self.home) as s:
            s.db.execute("UPDATE records SET payload=json_set(payload,'$.framework_version','0.0.1') WHERE kind='task'"); s.db.commit()
        self.assertTrue(resume(self.home,{'scope':str(self.repo),'id':'task1'},self.config)['ready_to_resume'])


class CoordinationTests(Environment):
    def batch(self): return json.loads((ROOT/'fixtures/batch.json').read_text())
    def test_topological_waves(self): self.assertEqual(batch_validate(self.batch())['waves'],[['schema'],['consumer']])
    def test_cycle_rejected(self):
        b=self.batch(); b['items'][0]['depends_on']=['consumer']
        with self.assertRaises(Fault): batch_validate(b)
    def test_unknown_dependency_rejected(self):
        b=self.batch(); b['items'][0]['depends_on']=['missing']
        with self.assertRaises(Fault): batch_validate(b)
    def test_concurrent_write_overlap_rejected(self):
        b=self.batch(); b['items'][1]['depends_on']=[]; b['items'][1]['writes']=['schema/a.sql']
        with self.assertRaises(Fault): batch_validate(b)
    def test_shared_resources_rejected(self):
        b=self.batch(); b['items'][1]['depends_on']=[]
        for i in b['items']: i['resources']=['port:3000']
        with self.assertRaises(Fault): batch_validate(b)
    def test_check_literal_pass_fail_unknown(self):
        self.put('a.ts','modifyWidget1v1()')
        c={'id':'deprecated','kind':'absent_literal','paths':['a.ts'],'literal':'modifyWidget1v1','required':True}
        self.assertFalse(run_checks({'scope':str(self.repo),'checks':[c]},self.config)['required_passed'])
        c['literal']='other'; self.assertTrue(run_checks({'scope':str(self.repo),'checks':[c]},self.config)['required_passed'])
        c['paths']=['missing.ts']; self.assertEqual(run_checks({'scope':str(self.repo),'checks':[c]},self.config)['checks'][0]['status'],'unknown')
    def test_command_checks_require_authorization_and_bound_output(self):
        c={'id':'test','kind':'command','required':True,'argv':[sys.executable,'-c','print("ok")']}
        with self.assertRaises(Fault): run_checks({'scope':str(self.repo),'checks':[c]},self.config)
        c['authorization']='test author'; self.assertTrue(run_checks({'scope':str(self.repo),'checks':[c]},self.config)['required_passed'])
        c['argv']=[sys.executable,'-c','print("x"*50000)']
        r=run_checks({'scope':str(self.repo),'checks':[c]},self.config)
        self.assertEqual(r['checks'][0]['limit'],'output_limit'); self.assertFalse(r['required_passed'])
    def test_command_timeout(self):
        c={'id':'timeout','kind':'command','required':True,'argv':[sys.executable,'-c','import time; time.sleep(5)'],'authorization':'test author','timeout':0.1}
        r=run_checks({'scope':str(self.repo),'checks':[c]},self.config)
        self.assertEqual(r['checks'][0]['limit'],'timeout')
    def test_worktree_clean_remove_dirty_refused(self):
        self.initgit(); dest=self.base/'isolated work'
        req={'scope':str(self.repo),'path':str(dest)}
        worktree(self.home,'create',req); (dest/'untracked').write_text('keep')
        with self.assertRaises(Fault): worktree(self.home,'remove',req)
        (dest/'untracked').unlink(); worktree(self.home,'remove',req); self.assertFalse(dest.exists())
    def test_active_task_prevents_worktree_removal(self):
        self.initgit(); dest=self.base/'isolated'; req={'scope':str(self.repo),'path':str(dest)}
        worktree(self.home,'create',req)
        checkpoint(self.home,{'scope':str(dest),'record':self.task(scope_root=str(dest))},self.config)
        with self.assertRaises(Fault): worktree(self.home,'remove',req)
    def test_worktree_scope_ids_share_identity_not_working_state(self):
        self.initgit(); dest=self.base/'isolated'; worktree(self.home,'create',{'scope':str(self.repo),'path':str(dest)})
        with State(self.home) as s:
            a=s.ids(scope_info(self.repo)); b=s.ids(scope_info(dest))
        self.assertEqual(a[0],b[0]); self.assertNotEqual(a[1],b[1])

    def test_worktree_subscope_task_and_ignored_files_prevent_removal(self):
        self.initgit(); dest=self.base/'isolated'; req={'scope':str(self.repo),'path':str(dest)}
        worktree(self.home,'create',req); sub=dest/'sub'; sub.mkdir()
        checkpoint(self.home,{'scope':str(sub),'record':self.task(scope_root=str(sub))},self.config)
        with self.assertRaises(Fault): worktree(self.home,'remove',req)
        with State(self.home) as s: s.purge(str(sub))
        sub.rmdir(); (dest/'.gitignore').write_text('generated\n'); self.git('add','.gitignore',root=dest)
        self.git('commit','-m','ignore',root=dest); self.git('branch','preserve-ignore',root=dest)
        (dest/'generated').write_text('keep')
        with self.assertRaises(Fault): worktree(self.home,'remove',req)

    def test_worktree_recreation_updates_ownership(self):
        self.initgit(); dest=self.base/'isolated'; req={'scope':str(self.repo),'path':str(dest)}
        worktree(self.home,'create',req); worktree(self.home,'remove',req)
        self.assertGreater(worktree(self.home,'create',req)['revision'],1)

    def test_batch_normalized_paths_and_globs(self):
        for paths in [('./src/a.ts','src/a.ts'),('src/A.ts','src/a.ts'),('.','src/a.ts'),('src/*.ts','src/part/*')]:
            b=self.batch(); b['items'][1]['depends_on']=[]
            for item,path in zip(b['items'],paths): item['writes']=[path]
            with self.assertRaises(Fault): batch_validate(b)


class ContractTests(Environment):
    def test_unknown_config_fields_and_escape_refused(self):
        with self.assertRaises(Fault): validate({'schema_version':'cwf/v1','run':'curl evil'},SCHEMAS['config'])
        self.put('.cwf.json',json.dumps({'schema_version':'cwf/v1','source_roots':['../outside']}))
        with self.assertRaises(Fault): settings(self.home,self.repo)
    def test_published_schemas_equal_runtime_contracts(self):
        for name,schema in SCHEMAS.items():
            published=json.loads((ROOT/f'schemas/{name}.schema.json').read_text())
            published.pop('$schema'); published.pop('$id')
            self.assertEqual(published,schema)
    def test_jsonschema_cross_validation(self):
        try: import jsonschema
        except ImportError: self.skipTest('optional development jsonschema unavailable')
        for name,schema in SCHEMAS.items(): jsonschema.Draft202012Validator.check_schema(schema)
        valid=[('config',DEFAULTS),('task',self.task()),('batch',json.loads((ROOT/'fixtures/batch.json').read_text()))]
        for name,value in valid:
            validate(value,SCHEMAS[name]); jsonschema.validate(value,SCHEMAS[name])
            invalid=dict(value,unexpected=True)
            with self.assertRaises(Fault): validate(invalid,SCHEMAS[name])
            with self.assertRaises(jsonschema.ValidationError): jsonschema.validate(invalid,SCHEMAS[name])
    def test_skill_frontmatter_and_references(self):
        for d in ['product','design','docs','plan','build','maintain']:
            p=ROOT/f'skills/cwf-{d}/SKILL.md'; text=p.read_text()
            self.assertTrue(text.startswith('---\nname: cwf-'+d)); self.assertIn('description:',text)
            for ref in ['../../patterns/core.md','../../patterns/tools.md']:
                self.assertTrue((p.parent/ref).resolve().is_file())
            self.assertNotIn('TODO',text)
    def test_cli_invalid_json_and_exit(self):
        code,out=self.cli('discover',request={'scope':str(self.repo),'domain':'wrong','query':'x'})
        self.assertEqual(code,2); self.assertEqual(out['status'],'error')


if __name__=='__main__': unittest.main(verbosity=2)
