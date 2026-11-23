import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from device_inspection.text import TextModel,features,matrix,phrase_evidence
from device_inspection.learning import group_split
from device_inspection.vision import inspect_photos,crop_bounds


class TextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.model=TextModel(ROOT/'models/text_baseline.json')

    def test_negation_and_unknown_are_distinct(self):
        for text,expected in [('Ladekabel dabei.','yes'),('Ohne Ladekabel.','no'),('Weitere Informationen auf Anfrage.','unknown')]:
            with self.subTest(text=text):
                self.assertEqual(self.model.predict(text)['fields']['cable_included']['value'],expected)

    def test_empty_and_out_of_vocabulary_are_unknown(self):
        for text in ['', '🦉🦉🦉']:
            self.assertTrue(all(p['value']=='unknown' for p in self.model.predict(text)['fields'].values()))

    def test_missing_topic_is_not_a_negative_label(self):
        result=self.model.predict('Das Display ist gesprungen.')['fields']
        self.assertEqual(result['cable_included']['value'],'unknown')
        self.assertEqual(result['cable_included']['decision_source'],'missing_topic_guard')
        self.assertEqual(result['account_lock']['value'],'unknown')

    def test_scores_and_passages_have_explicit_provenance(self):
        text='Ohne Ladekabel. iCloud wurde abgemeldet.'
        result=self.model.predict(text)
        for field in result['fields'].values():
            self.assertFalse(field['score_calibrated'])
            self.assertTrue(field['requires_review'])
        for span in result['evidence']:
            self.assertEqual(text[span['start']:span['end']],span['text'])
            self.assertEqual(span['source'],'phrase_rule')

    def test_synthetic_fixture_holdout_has_no_exact_text_duplicates(self):
        rows=json.loads((ROOT/'examples/text_training.json').read_text())
        train={r['text'] for r in rows if r['split']=='train'}
        test={r['text'] for r in rows if r['split']=='test'}
        self.assertFalse(train&test)


class DataIntegrityTests(unittest.TestCase):
    def test_duplicate_connects_entire_listings(self):
        rows=[{'photo_id':'a1','listing_id':'a','content_sha256':'same'},
              {'photo_id':'b1','listing_id':'b','content_sha256':'same'},
              {'photo_id':'b2','listing_id':'b','content_sha256':'other'}]
        split=group_split(rows)
        self.assertEqual(len(set(split.values())),1)
        self.assertEqual(split,group_split(list(reversed(rows))))

    def test_coordinate_projection_and_all_photo_processing(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'device.png';Image.new('RGB',(500,500)).save(path)
            features=lambda image:[{'label':'phone','xyxy':[100,100,400,400],'score':.9}]
            condition=lambda image:[{'label':'scratch','xyxy':[20,20,40,40],'score':.7}]
            result=inspect_photos([{'photo_id':'a','path':path},{'photo_id':'b','path':path}],features,condition)
            self.assertEqual(len(result['photos']),2)
            self.assertEqual(result['photos'][0]['devices'][0]['findings'][0]['xyxy'],[90,90,110,110])
            self.assertEqual(result['condition_verdict'],'finding_requires_review')

    def test_no_detection_never_means_undamaged(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'device.png';Image.new('RGB',(500,500)).save(path)
            result=inspect_photos([{'photo_id':'a','path':path}],lambda image:[],lambda image:[])
            self.assertEqual(result['condition_verdict'],'unresolved')
        missing=inspect_photos([{'photo_id':'a','path':'/nonexistent-demo-fixture.png'}],lambda image:[],lambda image:[])
        self.assertFalse(missing['coverage_complete'])

    def test_invalid_boxes_are_rejected(self):
        with self.assertRaises(ValueError):crop_bounds([40,40,10,10],(500,500))


@unittest.skipUnless(importlib.util.find_spec('torch') and importlib.util.find_spec('torchvision'),'Install vision extra')
class VisionTests(unittest.TestCase):
    def test_unknown_targets_do_not_affect_loss_or_gradient(self):
        import torch
        from device_inspection.learning import masked_binary_loss
        logits=torch.tensor([[0.,100.]],requires_grad=True)
        value=masked_binary_loss(logits,torch.tensor([[1.,0.]]),torch.tensor([[True,False]]))
        value.backward()
        self.assertAlmostEqual(float(value.detach()),float(np.log(2)),places=5)
        self.assertEqual(float(logits.grad[0,1]),0.)

    def test_bundled_model_runs_real_inference(self):
        from device_inspection.vision import ViewModel
        result=ViewModel(ROOT/'models/device_views.npz').predict(Image.new('RGB',(384,384),(100,110,120)))
        self.assertEqual([a['label'] for a in result['attributes']],['display','back','camera'])
        self.assertTrue(all(0<=a['score']<=1 for a in result['attributes']))
        self.assertEqual(result['condition_verdict'],'unresolved')


if __name__=='__main__':unittest.main()
