from vncorenlp import VnCoreNLP

import os
import re
import string


class FeatureExtractor:
    def __init__(self, annotator: VnCoreNLP, dict_dir: str, feature_types: list = None):
        if feature_types is None:
            feature_types = ["pos", "cf", "sc", "fw", "qb", "num", "loc", "org", "per", "ppos"]
        self.annotator = annotator
        self.feature_types = feature_types

        self.loc_dict = None
        self.org_dict = None
        self.per_dict = None
        self.ppos_dict = None

        self.loc_max_lenght = 0
        self.org_max_lenght = 0
        self.per_max_lenght = 0
        self.ppos_max_lenght = 0

        self.load_dict(dict_dir)

    @staticmethod
    def read_dict(dict_path: str) -> (list, int):
        feature_dict = set()
        feature_max_lenght = 0
        with open(dict_path, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                line_text = line.strip().lower()
                line_text_length = len(line_text.split())
                feature_dict.add(line_text)
                if line_text_length > feature_max_lenght:
                    feature_max_lenght = line_text_length
            f.close()
        return feature_dict, feature_max_lenght

    def load_dict(self, dict_dir: str):
        # Load Location dictionary
        self.loc_dict, self.loc_max_lenght = self.read_dict(os.path.join(dict_dir, 'vnLocation.txt'))
        # Load Location dictionary
        self.org_dict, self.org_max_lenght = self.read_dict(os.path.join(dict_dir, 'vnOrganization.txt'))
        # Load Location dictionary
        self.per_dict, self.per_max_lenght = self.read_dict(os.path.join(dict_dir, 'vnFullNames.txt'))
        # Load Location dictionary
        self.ppos_dict, self.ppos_max_lenght = self.read_dict(os.path.join(dict_dir, 'vnPersonalPositions.txt'))

    def wseg_and_add_pos_tag_feature(self, sentence: str or list, pos_tags: list = None) -> list:
        pos_features = []
        words = []
        if pos_tags is not None and type(sentence) == list:
            words = sentence
            for pos in pos_tags:
                pos_features.append('[POS]' + pos.strip())
        else:
            annotated_text = self.annotator.annotate(sentence)['sentences'][0]
            for anno in annotated_text:
                words.append(anno['form'])
                pos_features.append('[POS]' + anno['posTag'])
        return words, pos_features

    def word_segment(self, sentence: str or list):
        if type(sentence) == str:
            return self.annotator.tokenize(sentence)[0]
        else:
            return sentence

    @staticmethod
    def add_case_feature(sentence: list) -> list:
        case_features = []
        for word in sentence:
            if word.isupper():
                case_features.append('[Case]A_Cap')
            elif word[0].isupper():
                case_features.append('[Case]I_Cap')
            elif any(c.isupper() for c in word):
                case_features.append('[Case]M_Cap')
            else:
                case_features.append('[Case]N_Cap')
        return case_features

    @staticmethod
    def add_sequence_case_feature(sentence: list) -> list:
        sc_features = []
        for idx, word in enumerate(sentence):
            if len(sentence) == 1:
                sc_features.append('[SC]N_Cap')
                continue
            if idx == 0:
                if sentence[idx + 1][0].isupper():
                    sc_features.append('[SC]Pos_Cap')
                else:
                    sc_features.append('[SC]N_Cap')
            elif idx == (len(sentence) - 1):
                if sentence[idx - 1][0].isupper():
                    sc_features.append('[SC]Pre_Cap')
                else:
                    sc_features.append('[SC]N_Cap')
            else:
                if sentence[idx + 1][0].isupper() and sentence[idx - 1][0].isupper():
                    if sentence[idx][0].isupper():
                        sc_features.append('[SC]I_Cap')
                    else:
                        sc_features.append('[SC]NI_Cap')
                elif sentence[idx + 1][0].isupper():
                    sc_features.append('[SC]Pos_Cap')
                elif sentence[idx - 1][0].isupper():
                    sc_features.append('[SC]Pre_Cap')
                else:
                    sc_features.append('[SC]N_Cap')
        return sc_features

    @staticmethod
    def add_fisrt_word_feature(sentence: list) -> list:
        fw_features = []
        for idx in range(len(sentence)):
            if idx == 0:
                fw_features.append('[FW]1')
            elif sentence[idx - 1] in '.!?...':
                fw_features.append('[FW]1')
            else:
                fw_features.append('[FW]0')
        return fw_features

    @staticmethod
    def add_quotes_brackets_feature(sentence: list) -> list:
        qb_features = []
        isquotes = False
        isbrackets = False
        for word in sentence:
            if word == '"' or word == '“' or word == '”':
                isquotes = not isquotes
                qb_features.append('[QB]0')
                continue
            elif word == '(':
                isbrackets = True
                qb_features.append('[QB]0')
                continue
            elif word == ')':
                isbrackets = False
                qb_features.append('[QB]0')
                continue
            if isquotes is True or isbrackets is True:
                qb_features.append('[QB]1')
            else:
                qb_features.append('[QB]0')
        return qb_features

    @staticmethod
    def add_number_feature(sentence: list) -> list:
        num_features = []
        num = ['một', 'hai', 'ba', 'bốn', 'năm', 'sáu', 'bảy', 'tám', 'chín', 'mười', 'chục', 'trăm', 'nghìn', 'vạn',
               'triệu', 'tỷ']
        for word in sentence:
            if word.lower() in num or re.sub(f'[{string.punctuation}]', '', word).isdigit():
                num_features.append('[Num]1')
            else:
                num_features.append('[Num]0')
        return num_features

    def add_location_feature_recursive(self, sentence, max_lenght, startidx, feature):
        if max_lenght > len(sentence) - len(feature):
            max_lenght = len(sentence) - len(feature)
        if max_lenght <= 0:
            return feature
        word = ''
        for idx in range(max_lenght):
            word += " " + sentence[startidx + idx]
        word = word.replace('_', ' ').strip().lower()
        for count in range(max_lenght):
            if word.lower() in self.loc_dict:
                num_word = max_lenght - count
                for id in range(num_word):
                    feature.append('[LOC]1')
                feature = self.add_location_feature_recursive(sentence, max_lenght, startidx + num_word, feature)
                break
            else:
                word = word.rsplit(' ', 1)[0]
        if len(feature) == startidx:
            feature.append('[LOC]0')
            feature = self.add_location_feature_recursive(sentence, max_lenght, startidx + 1, feature)
        return feature

    def add_organization_feature_recursive(self, sentence, max_lenght, startidx, feature):
        if max_lenght > len(sentence) - len(feature):
            max_lenght = len(sentence) - len(feature)
        if max_lenght <= 0:
            return feature
        word = ''
        for idx in range(max_lenght):
            word += " " + sentence[startidx + idx]
        word = word.replace('_', ' ').strip().lower()
        for count in range(max_lenght):
            if word.lower() in self.org_dict:
                num_word = max_lenght - count
                for id in range(num_word):
                    feature.append('[ORG]1')
                feature = self.add_organization_feature_recursive(sentence, max_lenght, startidx + num_word, feature)
                break
            else:
                word = word.rsplit(' ', 1)[0]
        if len(feature) == startidx:
            feature.append('[ORG]0')
            feature = self.add_organization_feature_recursive(sentence, max_lenght, startidx + 1, feature)
        return feature

    def add_person_feature_recursive(self, sentence, max_lenght, startidx, feature):
        if max_lenght > len(sentence) - len(feature):
            max_lenght = len(sentence) - len(feature)
        if max_lenght <= 0:
            return feature
        word = ''
        for idx in range(max_lenght):
            word += " " + sentence[startidx + idx]
        word = word.replace('_', ' ').strip().lower()
        for count in range(max_lenght):
            if word.lower() in self.per_dict:
                num_word = max_lenght - count
                for id in range(num_word):
                    feature.append('[PER]1')
                feature = self.add_person_feature_recursive(sentence, max_lenght, startidx + num_word, feature)
                break
            else:
                word = word.rsplit(' ', 1)[0]
        if len(feature) == startidx:
            feature.append('[PER]0')
            feature = self.add_person_feature_recursive(sentence, max_lenght, startidx + 1, feature)
        return feature

    def add_person_position_feature_recursive(self, sentence, max_lenght, startidx, feature):
        if max_lenght > len(sentence) - len(feature):
            max_lenght = len(sentence) - len(feature)
        if max_lenght <= 0:
            return feature
        word = ''
        for idx in range(max_lenght):
            word += " " + sentence[startidx + idx]
        word = word.replace('_', ' ').strip().lower()
        for count in range(max_lenght):
            if word.lower() in self.ppos_dict:
                num_word = max_lenght - count
                for id in range(num_word):
                    feature.append('[PPOS]1')
                feature = self.add_person_position_feature_recursive(sentence, max_lenght, startidx + num_word, feature)
                break
            else:
                word = word.rsplit(' ', 1)[0]
        if len(feature) == startidx:
            feature.append('[PPOS]0')
            feature = self.add_person_position_feature_recursive(sentence, max_lenght, startidx + 1, feature)
        return feature

    def recover_feature(self, orginal_sentence, feature, type):
        new_feature = []
        for words in orginal_sentence:
            word = words.split("_")
            if (type + '0') in feature[0:len(word)]:
                new_feature.append(type + '0')
            else:
                new_feature.append(type + '1')
            del feature[0:len(word)]
        return new_feature

    def add_dict_feature(self, sentence: list, dict_type: str = '[LOC]') -> list:
        features = []
        dict_features = []
        for word in sentence:
            dict_features.extend(word.replace('_', ' ').split(' '))
        if dict_type == '[LOC]':
            features = self.add_location_feature_recursive(dict_features, self.loc_max_lenght, 0, features)
        elif dict_type == '[ORG]':
            features = self.add_organization_feature_recursive(dict_features, self.org_max_lenght, 0, features)
        elif dict_type == '[PER]':
            features = self.add_person_feature_recursive(dict_features, self.per_max_lenght, 0, features)
        elif dict_type == '[PPOS]':
            features = self.add_person_position_feature_recursive(dict_features, self.ppos_max_lenght, 0, features)
        dict_features = self.recover_feature(sentence, features, dict_type)
        return dict_features

    def extract_feature(self, sentence: str or list, pos_tags: list = None):
        features = []
        result = []
        if "pos" in self.feature_types:
            sentence, pos_features = self.wseg_and_add_pos_tag_feature(sentence, pos_tags)
            features.append(pos_features)
        else:
            sentence = self.word_segment(sentence)
        if "cf" in self.feature_types:
            features.append(self.add_case_feature(sentence))
        if "sc" in self.feature_types:
            features.append(self.add_sequence_case_feature(sentence))
        if "fw" in self.feature_types:
            features.append(self.add_fisrt_word_feature(sentence))
        if "qb" in self.feature_types:
            features.append(self.add_quotes_brackets_feature(sentence))
        if "num" in self.feature_types:
            features.append(self.add_number_feature(sentence))
        if "loc" in self.feature_types:
            features.append(self.add_dict_feature(sentence, '[LOC]'))
        if "org" in self.feature_types:
            features.append(self.add_dict_feature(sentence, '[ORG]'))
        if "per" in self.feature_types:
            features.append(self.add_dict_feature(sentence, '[PER]'))
        if "ppos" in self.feature_types:
            features.append(self.add_dict_feature(sentence, '[PPOS]'))
        for idx, token in enumerate(sentence):
            example = '' + str(sentence[idx])
            for feature in range(len(features)):
                example = f"{example} {features[feature][idx]}"
            result.append(example)
        return result


if __name__ == "__main__":
    vncore = VnCoreNLP("VnCoreNLP-master/VnCoreNLP-1.1.1.jar", annotators="wseg, pos", max_heap_size='-Xmx500m')
    fe = FeatureExtractor(annotator=vncore, dict_dir='./resources/Dict')

    text = "Chỉ	riêng xã Cương Gián	(Hà Tĩnh) đã có 10 thuyền viên tử nạn giữa trùng dương bao la."
    print(fe.extract_feature(text))