import unittest
from copy import deepcopy
from learning_kernel import Blocked, CompiledImageJob, StyleProgramCompiler, OfflineStyleImageGateway, witness_to_candidate

SHA='a'*64

def fixture():
    brief={'brief_id':'original-01','subject':'original explorer','setting':'deep-sea observatory',
           'action':'reaches toward a floating organism','visual_role':'focal','view':'three-quarter'}
    skill={'skill_id':'world-character-style','version':'0.1-fixture','status':'CANDIDATE_EXPERIMENT',
           'allowed_operations':['whole_art','pose_edit'],
           'decisions':[{'id':'SD01','when':{'visual_role':'focal'},'clause_ids':['C01'],
                         'operation_id':'whole_art','evidence_ids':['W01'],'visual_prediction':'coherent major shapes'},
                        {'id':'SD02','when':{'view':'three-quarter'},'clause_ids':['C02'],
                         'operation_id':'pose_edit','evidence_ids':['W01'],'visual_prediction':'matched pose'}],
           'clauses':[{'id':'C01','priority':1,'template':'Organize ${subject} as coherent original designed masses in ${setting}; preserve focal identity.'},
                      {'id':'C02','priority':1,'template':'Keep the approved subject recognizable when viewed ${view}.'}]}
    scene={'required_decision_ids':['SD01'],'operation_id':'whole_art','reference_images':[],
           'output_contract':{'width':1024,'height':576,'format':'PNG','asset_kind':'whole_scene'}}
    provider={'model_air_id':'fixture:model-only','max_prompt_chars':10000,'max_reference_images':4,
              'size_multiple':16,'supported_operations':['whole_art','pose_edit']}
    return brief,skill,scene,provider

class LearningKernelTests(unittest.TestCase):
    def setUp(self):
        self.brief,self.skill,self.scene,self.provider=fixture()
        self.compiler=StyleProgramCompiler(); self.gateway=OfflineStyleImageGateway()
    def test_fixture_compiles(self):
        job=self.compiler.compile(self.brief,self.skill,self.scene,self.provider)
        self.assertTrue(self.gateway.submit(job)['OFFLINE_ONLY'])
    def test_deterministic_request(self):
        a=self.compiler.compile(self.brief,self.skill,self.scene,self.provider)
        b=self.compiler.compile(self.brief,self.skill,self.scene,self.provider)
        self.assertEqual(a.logical_sha256,b.logical_sha256)
    def test_skill_change_changes_prompt(self):
        a=self.compiler.compile(self.brief,self.skill,self.scene,self.provider)
        self.skill['clauses'][0]['template']+=' Include designed internal masses.'
        b=self.compiler.compile(self.brief,self.skill,self.scene,self.provider)
        self.assertNotEqual(a.logical_payload['positivePrompt'],b.logical_payload['positivePrompt'])
    def test_unselected_clause_change_not_prompt(self):
        a=self.compiler.compile(self.brief,self.skill,self.scene,self.provider)
        self.skill['clauses'][1]['template']+=' Extra detail.'
        b=self.compiler.compile(self.brief,self.skill,self.scene,self.provider)
        self.assertEqual(a.logical_payload['positivePrompt'],b.logical_payload['positivePrompt'])
    def test_no_style_skill(self):
        del self.skill['clauses']
        with self.assertRaises(Blocked): self.compiler.compile(self.brief,self.skill,self.scene,self.provider)
    def test_cannot_submit_raw_prompt(self):
        with self.assertRaises(Blocked): self.gateway.submit({'positivePrompt':'beautiful world'})
    def test_cannot_construct_job_directly(self):
        with self.assertRaises(Blocked): CompiledImageJob({}, {}, 'bad', object())
    def test_job_immutable_dataclass(self):
        import dataclasses
        j=self.compiler.compile(self.brief,self.skill,self.scene,self.provider)
        with self.assertRaises(dataclasses.FrozenInstanceError): j.logical_sha256='X'
    def test_mutated_nested_payload_refused(self):
        j=self.compiler.compile(self.brief,self.skill,self.scene,self.provider)
        j.logical_payload['positivePrompt']='an improvised aesthetic'
        with self.assertRaises(Blocked): self.gateway.submit(j)
    def test_unsupported_operation(self):
        self.provider['supported_operations']=[]
        with self.assertRaises(Blocked): self.compiler.compile(self.brief,self.skill,self.scene,self.provider)
    def test_unapproved_operation(self):
        self.skill['allowed_operations']=[]
        with self.assertRaises(Blocked): self.compiler.compile(self.brief,self.skill,self.scene,self.provider)
    def test_missing_decision(self):
        self.scene['required_decision_ids']=['nonexistent']
        with self.assertRaises(Blocked): self.compiler.compile(self.brief,self.skill,self.scene,self.provider)
    def test_missing_template(self):
        self.skill['clauses']=[]
        with self.assertRaises(Blocked): self.compiler.compile(self.brief,self.skill,self.scene,self.provider)
    def test_unknown_style_variable(self):
        self.skill['clauses'][0]['template']='${random_beautiful_style}'
        with self.assertRaises(Blocked): self.compiler.compile(self.brief,self.skill,self.scene,self.provider)
    def test_content_style_smuggling(self):
        self.brief['subject']='in the style of Kurzgesagt explorer'
        with self.assertRaises(Blocked): self.compiler.compile(self.brief,self.skill,self.scene,self.provider)
    def test_reference_limit(self):
        self.scene['reference_images']=[{'id':str(i),'role':'style','sha256':SHA,'approved':True} for i in range(5)]
        with self.assertRaises(Blocked): self.compiler.compile(self.brief,self.skill,self.scene,self.provider)
    def test_unapproved_reference(self):
        self.scene['reference_images']=[{'id':'a','role':'style','sha256':SHA,'approved':False}]
        with self.assertRaises(Blocked): self.compiler.compile(self.brief,self.skill,self.scene,self.provider)
    def test_missing_identity_reference(self):
        self.scene['requires_identity']=True
        with self.assertRaises(Blocked): self.compiler.compile(self.brief,self.skill,self.scene,self.provider)
    def test_valid_identity_reference(self):
        self.scene['requires_identity']=True
        self.scene['reference_images']=[{'id':'c','role':'canonical_identity','sha256':SHA,'approved':True}]
        self.assertTrue(self.compiler.compile(self.brief,self.skill,self.scene,self.provider).logical_payload['referenceRoles'])
    def test_extra_matching_unrequired_decision_does_not_append_style(self):
        self.skill['decisions'].append({'id':'SD03','when':{'visual_role':'focal'},'clause_ids':['C03'],
             'operation_id':'whole_art','evidence_ids':['W02'],'visual_prediction':'unrelated treatment'})
        self.skill['clauses'].append({'id':'C03','priority':0,'template':'Unrelated decorative style treatment.'})
        out=self.compiler.compile(self.brief,self.skill,self.scene,self.provider)
        self.assertNotIn('Unrelated decorative',out.logical_payload['positivePrompt'])
    def test_missing_declared_style_dependency(self):
        self.skill['decisions'][0]['depends_on']=['MISSING']
        with self.assertRaises(Blocked): self.compiler.compile(self.brief,self.skill,self.scene,self.provider)
    def test_unpinned_style_reference(self):
        self.scene['reference_images']=[{'id':'r','role':'learned_style','sha256':SHA,'approved':True}]
        with self.assertRaises(Blocked): self.compiler.compile(self.brief,self.skill,self.scene,self.provider)
    def test_pinned_style_reference_passes(self):
        self.scene['reference_images']=[{'id':'r','role':'learned_style','sha256':SHA,'approved':True}]
        self.skill['authorized_reference_sha256s']=[SHA]
        self.skill['required_reference_roles']=['learned_style']
        self.assertEqual(self.compiler.compile(self.brief,self.skill,self.scene,self.provider).logical_payload['referenceRoles'][0]['role'],'learned_style')
    def test_missing_required_style_reference(self):
        self.skill['required_reference_roles']=['learned_style']
        with self.assertRaises(Blocked): self.compiler.compile(self.brief,self.skill,self.scene,self.provider)
    def test_invalid_dimensions(self):
        self.scene['output_contract']['height']=1080
        with self.assertRaises(Blocked): self.compiler.compile(self.brief,self.skill,self.scene,self.provider)
    def test_prompt_limit(self):
        self.provider['max_prompt_chars']=12
        with self.assertRaises(Blocked): self.compiler.compile(self.brief,self.skill,self.scene,self.provider)
    def test_candidate_witness(self):
        w={'bundle_id':'W01','visible_effect':'structural illustration', 'contrasting_evidence':['difference'],
           'witnesses':[{'film_sha256':SHA,'frame_index':12,'visible_description':'full scene'},
                        {'film_sha256':SHA,'frame_index':20,'visible_description':'other context'}]}
        p={'decision_id':'D01','conditions':{'visual_role':'focal'},'invariants':'relationship of parts',
           'adaptations':'adapts with viewpoint','exceptions':'diagram mode','operation_ids':['whole_art'],
           'expected_visible_effect':'coherent silhouettes','what_may_vary':'new subject and colour',
           'excluded_source_specifics':['source fly']}
        self.assertEqual(witness_to_candidate(w,p)['status'],'STYLE_CANDIDATE_NOT_QUALIFIED')
    def test_source_copy_rejected(self):
        w={'bundle_id':'W01','visible_effect':'structure','contrasting_evidence':['case'],
           'witnesses':[{'film_sha256':SHA,'frame_index':12,'visible_description':'one'},
                        {'film_sha256':SHA,'frame_index':20,'visible_description':'two'}]}
        p={'decision_id':'D01','conditions':{'visual_role':'focal'},'invariants':'source fly eye',
           'adaptations':'view','exceptions':'diagram','operation_ids':['whole_art'],
           'expected_visible_effect':'nice','what_may_vary':'subject', 'excluded_source_specifics':['source fly']}
        with self.assertRaises(Blocked): witness_to_candidate(w,p)
    def test_one_witness_insufficient(self):
        w={'bundle_id':'W01','visible_effect':'structure','contrasting_evidence':['case'],
           'witnesses':[{'film_sha256':SHA,'frame_index':12,'visible_description':'one'}]}
        p={'decision_id':'D01','conditions':{},'invariants':'distinct silhouette','adaptations':'view','exceptions':'none','operation_ids':['whole_art'],
           'expected_visible_effect':'quality','what_may_vary':'subject','excluded_source_specifics':[]}
        with self.assertRaises(Blocked): witness_to_candidate(w,p)

if __name__=='__main__': unittest.main(verbosity=2)
