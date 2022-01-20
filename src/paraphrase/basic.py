from flair.data import Sentence
from flair.models import SequenceTagger
import clavier
import random


def get_default_tagger():
    _tagger = SequenceTagger.load("flair/pos-english")
    return _tagger


class NERSentence:
    def __init__(self, sentence_as_string: str, __tagger: SequenceTagger):
        self.sentence_string = sentence_as_string
        self.sentence = Sentence(self.sentence_string)
        self.tagger = __tagger
        self.tagger.predict(self.sentence)
        self.parts = []
        for entity in self.sentence.get_spans('pos'):
            labels = entity.get_labels()
            if labels:
                label = labels[0]
                part = SentencePart(entity.text, label.value, label.score)
                self.parts.append(part)

    def get_parts(self):
        return self.parts

    def get_original_sentence(self):
        return self.sentence_string

    def distort_sentence(self) -> list[str]:
        distorted = []

        for part in self.parts:
            if part.part_type in ['IN', 'DT']:
                if random.randint(0, 1) < 1:
                    distorted.append(part.text)
            else:
                qwerty_trans = QwertyDistanceTransformer(part)
                t_text = qwerty_trans.get_transform_with_threshold(40)
                distorted.append(t_text[0])
        return distorted


class SentencePart:
    def __init__(self, part, part_type, part_prob):
        self.text = part
        self.part_type = part_type
        self.prop = part_prob

    def __repr__(self) -> str:
        return "{}::{}, p={:.4f}".format(self.text, self.part_type, self.prop)


class QwertyDistanceTransformer:
    def __init__(self, part: SentencePart):
        self.part = part

    def get_transform_with_threshold(self, threshold_p:float):
        text, count = self.get_transform()
        change_p = count*100. / len(self.part.text)
        if change_p < threshold_p:
            return text, change_p
        return self.part.text , change_p

    def get_transform(self):
        t_string = ""
        change_count = 0
        for c in self.part.text:
            r = random.randint(0, 20)
            if c.isalnum():
                qwerty = clavier.load_qwerty()
                nn = list(qwerty.nearest_neighbors(c.lower(), k=4, cache=True))
                if r < 4:
                    c_rep = nn[r][0]
                    t_string = t_string + c_rep
                    change_count+=1
                if r ==4:
                    change_count +=1
                if r > 4:
                    t_string = t_string+c
            else:
                t_string = t_string+c
        return t_string, change_count


if __name__ == '__main__':
    tagger = get_default_tagger()
    sent = "What kind of support will the company provide for employees working from home?"
    sentence = NERSentence(sent, tagger)
    for p in sentence.get_parts():
        print(p)
    d_sent = sentence.distort_sentence()
    print(sent)
    print(d_sent)