import unittest
import paraphrase.basic as basic


class MyTestCase(unittest.TestCase):

    def test_sentence_part(self):
        sp = basic.SentencePart("Hello", "WW", .9)
        for _ in range(20):
            t = basic.QwertyDistanceTransformer(sp)
            transformed = t.get_transform_with_threshold(30)
            print(transformed)

    def test_full_sentence(self):
        tagger = basic.get_default_tagger()
        sent = basic.NERSentence("What kind of support will the company provide for employees working from home?",
                                 tagger)
        distorted = sent.distort_sentence()
        print(" ".join(distorted))




if __name__ == '__main__':
    unittest.main()
