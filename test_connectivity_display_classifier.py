import unittest
from connectivity_display_classifier import classify_links


class ConnectivityDisplayClassifierTests(unittest.TestCase):
    def link(self, link_id='A->B', direction='forward', modifiers=None):
        return {'link_id':link_id,'source':'A','target':'B','direction':direction,'role_modifiers':modifiers or []}

    def support(self, **extra):
        return {'receiving_states':[{'receiver_id':'B','support_directions':['forward'], 'support_isolated':False,'single_option_support':False}|extra]}

    def test_blue_requires_route_and_multiple_continuations_not_role_semantics(self):
        v2={'structural_links':[self.link()],'progression_routes':[{'node_ids':['A','B']}]}
        self.assertEqual(classify_links(v2,self.support(support_directions=['forward','lateral']))[0]['state'],'very_strong')

    def test_missing_role_semantics_cannot_downgrade_structurally_strong_link(self):
        v2={'structural_links':[self.link()],'progression_routes':[{'node_ids':['A','B']}]}
        self.assertEqual(classify_links(v2,self.support(support_directions=['forward','lateral']))[0]['state'],'very_strong')

    def test_green_is_existing_structural_relationship_without_extra_blue_requirements(self):
        v2={'structural_links':[self.link()],'progression_routes':[{'node_ids':['A','B']}]}
        self.assertEqual(classify_links(v2,self.support())[0]['state'],'smooth')

    def test_pink_requires_concrete_post_reception_limitation(self):
        v2={'structural_links':[self.link()],'progression_routes':[]}
        self.assertEqual(classify_links(v2,self.support(single_option_support=True))[0]['state'],'weak')

    def test_gray_requires_explicit_relevant_unsupported_candidate(self):
        v2={'structural_links':[],'progression_routes':[]}
        rows=classify_links(v2,{},[{'link_id':'A->B','source':'A','target':'B','status':'structurally_unsupported'}])
        self.assertEqual(rows[0]['state'],'unsupported')

    def test_unrelated_players_do_not_create_gray_links(self):
        self.assertEqual(classify_links({'structural_links':[],'progression_routes':[]}),[])

    def test_evidence_completeness_is_not_an_input(self):
        v2={'structural_links':[self.link()],'progression_routes':[]}
        before=classify_links(v2,self.support())
        v2['evidence_completeness']={'evidence_missing':999}
        self.assertEqual(before,classify_links(v2,self.support()))

if __name__=='__main__': unittest.main()
