"""Regressions for invisible HTML and misleading review checks."""
from html.parser import HTMLParser
import unittest
from scripts.evaluation.tdd_review_prechecks import render_test_field, check_test_numbering
from scripts.evaluation.scan_tdd_model_text import scan_record


class TextOnly(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.text=[];self.tags=[]
    def handle_data(self,data):self.text.append(data)
    def handle_starttag(self,tag,attrs):self.tags.append(tag)


class PrecheckTests(unittest.TestCase):
    def test_html_rendering_retains_code_tokens_and_creates_no_tags(self):
        source='"<url>" < limit and x > 0\n<think> &lt;literal&gt; <script>alert(1)</script>'
        parsed=TextOnly();parsed.feed(render_test_field(source));parsed.close()
        self.assertEqual(''.join(parsed.text),source)
        self.assertEqual(parsed.tags,[])

    def test_numbering_requires_the_named_requirement_in_the_map(self):
        row={'id':'tests/test_app.py::test_r5_cache','requirements':['R4','R6']}
        self.assertEqual(check_test_numbering([row])[0]['numbered_requirement'],'R5')
        self.assertEqual(check_test_numbering([row|{'requirements':['R5','R6']}]),[])
        self.assertEqual(check_test_numbering([row|{'id':'tests/test_app.py::test_cache'}]),[])

    def test_process_file_names_are_flagged_even_inside_code(self):
        for token in ['test_revisions.py','reference','paper','review','llm-bender-lab']:
            with self.subTest(token=token):
                result=scan_record({'messages':[{'role':'assistant','content':'```text\n'+token+'\n```'}]})
                self.assertTrue(any(f['status']!='allowed' for f in result))

    def test_functional_provenance_fields_are_retained(self):
        result=scan_record({'messages':[{'role':'assistant','content':'Return model_revision and data_revision. Save source revisions and model/data revisions. Record effective revisions and all revision identities/seed/settings.'}]})
        self.assertTrue(result)
        self.assertTrue(all(f['status']=='allowed' for f in result))

    def test_historical_facade_framing_requires_assessment(self):
        for text in ['a new public facade', 'a new shared facade', 'new public `tiny_model`']:
            findings=scan_record({'messages':[{'role':'assistant','content':text}]})
            self.assertTrue(any(f['status']=='assess' for f in findings))
        self.assertEqual(scan_record({'messages':[{'role':'assistant','content':'Create a new session on login.'}]}),[])

    def test_public_api_identifiers_are_distinguished_from_source_paths(self):
        row={'messages':[{'role':'assistant','content':'Use `reflexmodels.Choice`.'}],
             'interface':{'imports':[{'module':'reflexmodels','name':'Choice'}]}}
        self.assertTrue(all(f['status']=='allowed' for f in scan_record(row)))
        row['messages'][0]['content']='/Users/example/Documents/GitHub/ReflexModels/private.py'
        self.assertTrue(any(f['status']=='block' for f in scan_record(row)))

if __name__=='__main__':unittest.main()
