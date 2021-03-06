from django.db import models
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from datetime import datetime
import tensorflow as tf
from tensorflow.keras.models import Model, load_model
from tensorflow.keras import preprocessing
from konlpy.tag import Komoran
import pickle
import jpype


# 챗봇 대답
class Answercount(models.Model):
    id = models.AutoField(primary_key=True) #pk
    email = models.CharField(blank=True, max_length=50, null=True)  # FK(사용자id값)
    intent = models.CharField(blank=True, max_length=50, null=True)
    answer = models.CharField(blank=True,max_length=50, null=True)

    class Meta:
        db_table = 'ANSWER_COUNT'

    def __str__(self):
        return self.name

# 챗봇 의도 분류
class IntentModel:
    tf.compat.v1.enable_eager_execution()
    tf.compat.v1.logging.set_verbosity( tf.compat.v1.logging.ERROR)
    def __init__(self, model_name, proprocess):
        # 의도 클래스 별 레이블
        self.labels = {0: "달걀개수", 1: "레몬개수", 2: "자두개수", 3: "오이개수", 4: "사이다개수", 5: "당근개수", 6: "애호박개수", 7: "옥수수개수", 8: "파인애플개수",
                       9: "사과개수", 10: "양파개수", 11: "마늘개수", 12: "토마토개수", 13: "브로콜리개수", 14: "깻잎개수", 15: "가지개수", 16: "단호박개수",
                       17: "무개수", 18: "양배추개수", 19: "파프리카개수", 20: "야쿠르트개수", 21: "맥주개수", 22: "콜라개수", 23: "인사"}

        # 의도 분류 모델 불러오기
        self.model = load_model(model_name)

        # 챗봇 Preprocess 객체
        self.p = proprocess

    # 의도 클래스 예측
    def predict_class(self, query):
        # 형태소 분석
        pos = self.p.pos(query)

        # 문장내 키워드 추출(불용어 제거)
        keywords = self.p.get_keywords(pos, without_tag=True)
        sequences = [self.p.get_wordidx_sequence(keywords)]

        # 패딩처리
        padded_seqs = preprocessing.sequence.pad_sequences(sequences, maxlen=15, padding='post')

        predict = self.model.predict(padded_seqs)
        predict_class = tf.math.argmax(predict, axis=1)
        return predict_class.numpy()[0]


# 챗봇 전처리
class Preprocess:
    def __init__(self, word2index_dic = '', userdic=None):
        # 단어 인덱스 사전 불러오기
        if (word2index_dic != ''):
            f = open(word2index_dic, "rb")
            self.word_index = pickle.load(f)
            f.close()
        else:
            self.word_index = None

        # 형태소 분석기 초기화
        self.komoran = Komoran(userdic=userdic)

        # 제외할 품사
        # 관계언 제거, 기호 제거
        # 어미 제거
        # 접미사 제거
        self.exclusion_tags = [
            'JKS', 'JKC', 'JKG', 'JKO', 'JKB', 'JKV', 'JKQ',
            'JX', 'JC',
            'SF', 'SP', 'SS', 'SE', 'SO',
            'EP', 'EF', 'EC', 'ETN', 'ETM',
            'XSN', 'XSV', 'XSA'
        ]

    # 형태소 분석기 POS 태거
    def pos(self, sentence):
        jpype.attachThreadToJVM()
        return self.komoran.pos(sentence)

    # 불용어 제거 후, 필요한 품사 정보만 가져오기
    def get_keywords(self, pos, without_tag=False):
        f = lambda x: x in self.exclusion_tags
        word_list = []
        for p in pos:
            if f(p[1]) is False:
                word_list.append(p if without_tag is False else p[0])
        return word_list

    # 키워드를 단어 인덱스 시퀀스로 변환
    def get_wordidx_sequence(self, keywords):
        if self.word_index is None:
            return []

        w2i = []
        for word in keywords:
            try:
                w2i.append(self.word_index[word])
            except KeyError:
                # 해당 단어가 사전에 없는 경우, OOV 처리
                w2i.append(self.word_index['OOV'])
        return w2i


# 현재 식재료 
class Grocery(models.Model):
    id = models.AutoField(primary_key=True) #PK(현재식재료PK)
    email = models.CharField(blank=True, max_length=50, null=True) # FK(사용자id값)
    all_grocery_id = models.IntegerField(blank=True, null=True) # FK(식료품id값)
    name = models.CharField(blank=True, max_length=20, null=True)
    count = models.IntegerField(blank=True, null=True)
    reg_date = models.DateTimeField(blank=True, null=True)
    gubun = models.IntegerField(blank=True, null=True)
    coordinate = models.JSONField(blank=True, null=True)
    expiration_date = models.DateField(blank=True, null=True) #유통기한 추가

    class Meta:
        db_table = 'GROCERY'

    def __str__(self):
        return self.name


# 사용자
class UserInfo(models.Model):
    email = models.CharField(primary_key=True,max_length=50) # PK(사용자PK)
    age = models.IntegerField(blank=True,null=True)
    sex = models.IntegerField(blank=True,null=True)
    phone_number = models.CharField(max_length=500, null=True)
    name = models.CharField(max_length=500, null=True)
    password = models.CharField(max_length=500, null=True)
    guardian_name = models.CharField(max_length=500, null=True)
    guardian_phone_number = models.CharField(max_length=500, null=True)
    purpose = models.CharField(max_length=500, null=True)
    img_url = models.CharField(max_length=500, null=True)

    class Meta:
        db_table = 'USER_INFO'

    def __int__(self):
        return self.id