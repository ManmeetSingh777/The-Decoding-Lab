import unittest
from copy import deepcopy
from skill_prompt_compiler import compile_request, CompileBlocked

BRIEF={'brief_id':'test-brief','scene_id':'original-1','subject':'an original penguin-like robot exploring a bioluminescent cavern','action':'looks at a floating mineral and raises its left hand'}
SKILL={'state':'FIXTURE_ONLY','version':'fixture-v1','style_clauses':[
  {'id':'S-1','when':{'visual_role':'focal'},'priority':1,'operation_id':'canonical-whole-art','template':'Build the focal subject as one visually coherent illustrated whole with integrated head, torso and limb masses; do not assemble unrelated pictograms.'},
  {'id':'S-2','when':{'world_role':'complete'},'priority':2,'operation_id':'whole-world-layout','template':'Construct an interconnected environment with near, middle and far visual structures designed as one coherent art family.'},
]}
SCENE={'scene_id':'original-1','conditions':{'visual_role':'focal','world_role':'complete'},'required_style_clause_ids':['S-1','S-2'],'route':'whole_scene'}
PROVIDER={'model_id':'fixture-provider','max_prompt_chars':2000}

class TestCompiler(unittest.TestCase):
  def test_source_is_skill_and_brief_only(self):
    x=compile_request(BRIEF,SKILL,SCENE,PROVIDER,fixture_mode=True)
    self.assertIn(BRIEF['subject'],x['positivePrompt'])
    self.assertIn(SKILL['style_clauses'][1]['template'],x['positivePrompt'])
    self.assertEqual(x['authorities']['style'],'FrozenSkill')
  def test_deterministic_and_changed_skill_matters(self):
    x=compile_request(BRIEF,SKILL,SCENE,PROVIDER,fixture_mode=True)
    self.assertEqual(x,compile_request(BRIEF,SKILL,SCENE,PROVIDER,fixture_mode=True))
    edited=deepcopy(SKILL); edited['style_clauses'][0]['template']+=' Distinctly changed approved art decision.'
    self.assertNotEqual(x['request_sha256'],compile_request(BRIEF,edited,SCENE,PROVIDER,fixture_mode=True)['request_sha256'])
  def test_no_style_skill_is_blocked(self):
    with self.assertRaises(CompileBlocked): compile_request(BRIEF,{'state':'FIXTURE_ONLY','version':'x','style_clauses':[]},SCENE,PROVIDER,fixture_mode=True)
  def test_unrepresented_style_is_blocked(self):
    scene=deepcopy(SCENE);scene['required_style_clause_ids'].append('S-UNKNOWN')
    with self.assertRaisesRegex(CompileBlocked,'REQUIRED_STYLE_CLAUSE'): compile_request(BRIEF,SKILL,scene,PROVIDER,fixture_mode=True)
  def test_unapproved_live_skill_is_blocked(self):
    with self.assertRaises(CompileBlocked): compile_request(BRIEF,SKILL,SCENE,PROVIDER)
  def test_arbitrary_template_variables_blocked(self):
    skill=deepcopy(SKILL);skill['style_clauses'][0]['template']='A beautiful {invented_stylistic_concept}'
    with self.assertRaisesRegex(CompileBlocked,'UNDECLARED_STYLE_TEMPLATE'): compile_request(BRIEF,skill,SCENE,PROVIDER,fixture_mode=True)
  def test_unknown_provider_and_overflow(self):
    with self.assertRaises(CompileBlocked): compile_request(BRIEF,SKILL,SCENE,{},fixture_mode=True)
    with self.assertRaisesRegex(CompileBlocked,'PROMPT_LIMIT'): compile_request(BRIEF,SKILL,SCENE,{'model_id':'x','max_prompt_chars':10},fixture_mode=True)

if __name__=='__main__': unittest.main()
