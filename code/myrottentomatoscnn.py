# -*- coding: utf-8 -*-
"""MyRottenTomatosCNN.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1wWSPGcyE4wjDKa4tnkuACrXwbP0mUVBH
"""

# from google.colab import drive
# drive.mount('/content/gdrive')
# import os
# os.chdir("gdrive/My Drive/")

import numpy as np
import pandas as pd
import nltk
import re

from nltk.tokenize import TweetTokenizer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords 
from nltk import FreqDist
from nltk.stem import WordNetLemmatizer
from nltk.util import ngrams

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.utils import resample

from keras.utils import to_categorical

"""Split Train (0.7) and Test (0.3) Sets"""

data = pd.read_csv('https://raw.githubusercontent.com/cacoderquan/Sentiment-Analysis-on-the-Rotten-Tomatoes-movie-review-dataset/master/train.tsv', sep="\t")
X_train, X_test, Y_train, Y_test = train_test_split(data['Phrase'], data['Sentiment'], test_size=0.3, random_state=2003)

"""Data Exploration"""

Y_train.value_counts()

import matplotlib.pyplot as plt

sizes = Y_train.value_counts().values.tolist()
labels = 'neutral', 'somewhat positive', 'somewhat negative', 'positive', 'negative'
fig1, ax1 = plt.subplots()
ax1.pie(sizes, labels=labels, autopct='%1.1f%%',
        shadow=True, startangle=90)
# Equal aspect ratio ensures that pie is drawn as a circle.
ax1.axis('equal')

plt.show()

X_train = data['Phrase']
Y_train = data['Sentiment']

X_train.head()

X_test.head()

"""Setup NLTK"""

nltk.download('punkt')
nltk.download('wordnet')
nltk.download('stopwords')

lemma = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

"""Remove Punctuations and Numbers"""

def remove_punctuations_and_numbers(review):
  # Remove Punctuations and numbers
  filtered_review = re.sub('[^a-zA-Z]',' ',review)
  return filtered_review

"""Remove Stopwords"""

def remove_stopwords(review):
  # Remove Stopwords
  word_tokens = word_tokenize(review) 
  filtered_review = [w for w in word_tokens if not w in stop_words]
  filtered_review = ' '.join(filtered_review)
  return filtered_review

"""Lematizer"""

def lematize(review):
  filtered_review = [lemma.lemmatize(w) for w in word_tokenize(str(review).lower())]
  filtered_review = ' '.join(filtered_review)
  return filtered_review

"""Test Preprocessing Functions"""

test = 'The man is looking at the 2 old brown trees.'
filtered_test_1 = remove_punctuations_and_numbers(test)
filtered_test_2 = remove_stopwords(filtered_test_1)
filtered_test_3 = lematize(filtered_test_2)
print(filtered_test_1)
print(filtered_test_2)
print(filtered_test_3)

"""Preprocess Reviews"""

def preprecess_reviews(reviews):
  filtered_reviews = []
  for review in reviews:
    filtered_review = remove_punctuations_and_numbers(review)
    filtered_review = remove_stopwords(filtered_review)
    filtered_review = lematize(filtered_review)
    filtered_reviews.append(filtered_review)
  return filtered_reviews

"""Apply Preprocessing"""

column_names = ["Filtered_Review", "Sentiment"]
train = pd.DataFrame(columns = column_names)
test = pd.DataFrame(columns = column_names)

# Apply Preprocessing to reviews
train['Filtered_Review'] = preprecess_reviews(X_train.values)
train['Sentiment'] = Y_train
test['Filtered_Review'] = preprecess_reviews(X_test.values)
test['Sentiment'] = Y_test

"""Data Normalization (Downsampling)"""

def downsampling(train_0, train_1, train_2, train_3, train_4):

  # returns the number of entries of the smallest class
  MIN_SAMPLES = min(len(train_0), len(train_1), len(train_2), len(train_3), len(train_4))

  train_0_sample = resample(train_0, replace=True, n_samples=MIN_SAMPLES, random_state=2003)
  train_1_sample = resample(train_1, replace=True, n_samples=MIN_SAMPLES, random_state=2003)
  train_2_sample = resample(train_2, replace=True, n_samples=MIN_SAMPLES, random_state=2003)
  train_3_sample = resample(train_3, replace=True, n_samples=MIN_SAMPLES, random_state=2003)
  train_4_sample = resample(train_4, replace=True, n_samples=MIN_SAMPLES, random_state=2003)
  
  df_normalized = pd.concat([train_0_sample, train_1_sample, train_2_sample,train_3_sample, train_4_sample])
  return df_normalized

"""Data Normalization (Upsampling)"""

def upsampling(train_0, train_1, train_2, train_3, train_4):

  # returns the number of entries of the largest class
  MAX_SAMPLES = max(len(train_0), len(train_1), len(train_2), len(train_3), len(train_4))

  train_0_sample = resample(train_0, replace=True, n_samples=MAX_SAMPLES, random_state=2003)
  train_1_sample = resample(train_1, replace=True, n_samples=MAX_SAMPLES, random_state=2003)
  train_2_sample = resample(train_2, replace=True, n_samples=MAX_SAMPLES, random_state=2003)
  train_3_sample = resample(train_3, replace=True, n_samples=MAX_SAMPLES, random_state=2003)
  train_4_sample = resample(train_4, replace=True, n_samples=MAX_SAMPLES, random_state=2003)
  
  df_normalized = pd.concat([train_0_sample, train_1_sample, train_2_sample,train_3_sample, train_4_sample])
  return df_normalized

"""Normalize Data"""

train_0 = train[train['Sentiment'] == 0]
train_1 = train[train['Sentiment'] == 1]
train_2 = train[train['Sentiment'] == 2]
train_3 = train[train['Sentiment'] == 3]
train_4 = train[train['Sentiment'] == 4]

# df_normalized = downsampling(train_0, train_1, train_2, train_3, train_4)
df_normalized = upsampling(train_0, train_1, train_2, train_3, train_4)

from keras.preprocessing.text import Tokenizer
from keras.preprocessing import sequence,text
from keras.preprocessing.sequence import pad_sequences
from keras.layers import Dense, Embedding, Flatten, SpatialDropout1D
from keras.layers.convolutional import Conv1D, MaxPooling1D
from keras.models import Sequential
from keras.models import load_model

"""Apply Data Normalization **ONLY** on Train Set **(Not Test Set)**

Labels convert to categorical (One-Hot Encoding)
"""

X_train = df_normalized['Filtered_Review']
Y_train = to_categorical(df_normalized['Sentiment'].values)

# Test set should not normalized!
Y_test = to_categorical(Y_test)

"""Split Train (0.75) and Validation (0.25) Sets"""

X_train, X_val, Y_train, Y_val = train_test_split(X_train, Y_train, test_size=0.25, random_state=2003)

"""Returns Maximum Number of the Words in Reviews"""

def get_max_review_len(t):
  reviews_len = []
  for review in t:
      token = word_tokenize(review)
      reviews_len.append(len(token))      
  return max(reviews_len)

"""Returns number of distinct words"""

def get_num_words(t):
  train_words = ' '.join(t)
  train_words = word_tokenize(train_words)
  dist=FreqDist(train_words)
  return len(dist)

"""Initialize the Model's Parameters"""

BATCH_SIZE = 128
EPOCHS = 20
CLASS_NUM = 5

MAX_FEATURES = get_num_words(X_train)
MAX_WORDS = get_max_review_len(X_train)
print(MAX_FEATURES)
print(MAX_WORDS)

X_train

tokenizer = Tokenizer(num_words=MAX_FEATURES)
tokenizer.fit_on_texts(X_train)
X_train = tokenizer.texts_to_sequences(X_train)
X_train
X_val = tokenizer.texts_to_sequences(X_val)
X_test = tokenizer.texts_to_sequences(test['Filtered_Review'])
# X_test

"""Add Padding to the Dataset for to make the Model Input Sizes same as each other"""

def add_padding_to_seq(dataset):
  return sequence.pad_sequences(dataset, maxlen=MAX_WORDS)

X_train = add_padding_to_seq(X_train)
X_val = add_padding_to_seq(X_val)
X_test = add_padding_to_seq(X_test)

"""Initialize the CNN Model"""

model = Sequential()

# Input Layer
model.add(Embedding(MAX_FEATURES, 150, input_length=MAX_WORDS))

# CNN
model.add(SpatialDropout1D(0.5))

model.add(Conv1D(128, kernel_size=3, padding='same', activation='relu'))
model.add(MaxPooling1D(pool_size=2))

model.add(Flatten())

# Output layer
model.add(Dense(CLASS_NUM, activation='softmax'))

"""Initilize evaluation metrics

Recall, Precision, F1-Score
"""

from keras import backend as K

def recall_m(y_true, y_pred):
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)))
    recall = true_positives / (possible_positives + K.epsilon())
    return recall

def precision_m(y_true, y_pred):
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    predicted_positives = K.sum(K.round(K.clip(y_pred, 0, 1)))
    precision = true_positives / (predicted_positives + K.epsilon())
    return precision

def f1_m(y_true, y_pred):
    precision = precision_m(y_true, y_pred)
    recall = recall_m(y_true, y_pred)
    return 2*((precision*recall)/(precision+recall+K.epsilon()))

"""Train the Model using the Training and Validation Dataset"""

model.compile(loss='categorical_crossentropy', optimizer='nadam', metrics=['acc', f1_m, precision_m, recall_m])
history = model.fit(X_train, Y_train, validation_data=(X_val, Y_val), epochs=EPOCHS, batch_size=BATCH_SIZE, verbose=1)

score, acc, f1, prec, recall = model.evaluate(X_test, Y_test, verbose=1)
print('Score = ' + str(score))
print('Accuracy = ' + str(acc))

"""Plot Loss and Accuracy on Training Phase"""

import matplotlib.pyplot as plt

# Plot training & validation accuracy values
plt.plot(history.history['acc'])
plt.title('Model accuracy')
plt.ylabel('Accuracy')
plt.xlabel('Epoch')
plt.legend(['Train'], loc='upper left')
plt.show()

# Plot training & validation loss values
plt.plot(history.history['loss'])
plt.title('Model loss')
plt.ylabel('Loss')
plt.xlabel('Epoch')
plt.legend(['Train'], loc='upper left')
plt.show()

"""Save the Model for further use"""

MODEL_FILE_NAME = "1114548_1dconv_reg"
model.save(MODEL_FILE_NAME)

"""Evaluate the Model using Testing dataset"""

dependencies = {
     'f1_m': f1_m,
     'precision_m': precision_m,
     'recall_m': recall_m
}

model = load_model(MODEL_FILE_NAME, custom_objects=dependencies)
score, acc, f1, prec, recall = model.evaluate(X_test, Y_test, verbose=1)

print('Score = ' + str(score))
print('Accuracy = ' + str(acc))
print('F1 = ' + str(f1))
print("Precision = " + str(prec))
print("Recall = " + str(recall))

