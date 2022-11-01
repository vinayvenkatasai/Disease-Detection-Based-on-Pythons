# importing nltk to download resources for stopwords and wordnet
import nltk
nltk.download('stopwords')
nltk.download('wordnet')

# importing all libraries
import numpy as np
import pandas as pd
import math
from sklearn.model_selection import train_test_split,cross_val_score
import math
import operator
import pickle
import re
from nltk.stem import WordNetLemmatizer
import numpy as np
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from nltk.tokenize import RegexpTokenizer
from statistics import mean
from nltk.corpus import wordnet 
import requests
from bs4 import BeautifulSoup
from itertools import combinations
from time import time
from collections import Counter
import operator
import warnings
from Treatment import diseaseDetail

# ignore warnings generated due to usage of old version of tensorflow
warnings.simplefilter("ignore")

"""**Disease Symptom dataset** was created in a separate python program.

**Dataset scrapping** was done using **NHP website** and **wikipedia data**
"""

# Load Dataset scraped from NHP (https://www.nhp.gov.in/disease-a-z) & Wikipedia
# Scrapping and creation of dataset csv is done in a separate program
loc = "D:/Knock/Disease-Detection-based-on-Symptoms/Disease-Detection-based-on-Symptoms-master/Dataset/dis_sym_dataset_norm.csv"
df=pd.read_csv(loc)
documentname_list=list(df['label_dis'])
df=df.iloc[:,1:]
columns_name=list(df.columns)
documentname_list=list(documentname_list)

N=len(df)
M=len(columns_name)

# All symptoms IDF
idf={}
for col in columns_name:
  temp=np.count_nonzero(df[col])
  idf[col]=np.log(N/temp)

# All disease,symptom TF
tf={}
for i in range(N):
  for col in columns_name:
    key=(documentname_list[i],col)
    tf[key]=df.loc[i,col]

# All disease,symptom TF.IDF
tf_idf={}
for i in range(N):
  for col in columns_name:
    key=(documentname_list[i],col)
    tf_idf[key]=float(idf[col])*float(tf[key])

# vector of TF.IDF
D = np.zeros((N, M),dtype='float32')
for i in tf_idf:
    sym = columns_name.index(i[1])
    dis=documentname_list.index(i[0])
    D[dis][sym] = tf_idf[i]

# function for cosine dot product
def cosine_dot(a, b):
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0
    else:
        temp = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        return temp

# convert data to lower case
def convert_tolowercase(data):
    return data.lower()

# tokenizing using regextokenizer
def regextokenizer_func(data):
    tokenizer = RegexpTokenizer(r'\w+')
    data = tokenizer.tokenize(data)
    return data

# function to generate query vector for tf_idf
def gen_vector(tokens):
    Q = np.zeros(M)
    counter = Counter(tokens)
    query_weights = {}
    for token in np.unique(tokens):
        tf = counter[token]
        try:
          idf_temp=idf[token]
        except:
          pass
        try:
            ind = columns_name.index(token)
            Q[ind] = tf*idf_temp
        except:
            pass
    return Q

# function to calculate tf_idf_score
def tf_idf_score(k, query):
    query_weights = {}
    for key in tf_idf:
        if key[1] in query:
            try:
                query_weights[key[0]] += tf_idf[key]
            except:
                query_weights[key[0]] = tf_idf[key]
    query_weights = sorted(query_weights.items(), key=lambda x: x[1], reverse=True)
  
    l = []
    for i in query_weights[:k]:
        l.append(i)
    return l

# function to calculte Cosine Similarity 
def cosine_similarity(k, query):
    d_cosines = []
    query_vector = gen_vector(query)
    for d in D:
        d_cosines.append(cosine_dot(query_vector, d))
    out = np.array(d_cosines).argsort()[-k:][::-1]
  
    final_display_disease={}
    for lt in set(out):
      final_display_disease[lt] = float(d_cosines[lt])
    return final_display_disease

# returns the list of synonyms of the input word from thesaurus.com (https://www.thesaurus.com/) and wordnet (https://www.nltk.org/howto/wordnet.html)
def synonyms(term):
    synonyms = []
    response = requests.get('https://www.thesaurus.com/browse/{}'.format(term))
    soup = BeautifulSoup(response.content,  "html.parser")
    try:
        container=soup.find('section', {'class': 'MainContentContainer'}) 
        row=container.find('div',{'class':'css-191l5o0-ClassicContentCard'})
        row = row.find_all('li')
        for x in row:
            synonyms.append(x.get_text())
    except:
        None
    for syn in wordnet.synsets(term):
        synonyms+=syn.lemma_names()
    return set(synonyms)

# instantiate objects of libraries
splitter = RegexpTokenizer(r'\w+')
stop_words = stopwords.words('english')
lemmatizer = WordNetLemmatizer()

"""**Disease Symptom dataset** was created in a separate python program.

**Dataset scrapping** was done using **NHP website** and **wikipedia data**

Disease Combination dataset contains the combinations for each of the disease present in dataset as practically it is often observed that it is not necessary for a person to have a disease when all the symptoms are faced by the patient or the user.

*To tackle this problem, combinations are made with the symptoms for each disease.*

 **This increases the size of the data exponentially and helps the model to predict the disease with much better accuracy.**

*df_comb -> Dataframe consisting of dataset generated by combining symptoms for each disease.*

*df_norm -> Dataframe consisting of dataset which contains a single row for each diseases with all the symptoms for that corresponding disease.*

**Dataset contains 261 diseases and their symptoms**
"""

# Load Dataset scraped from NHP (https://www.nhp.gov.in/disease-a-z) & Wikipedia
# Scrapping and creation of dataset csv is done in a separate program
df_comb = pd.read_csv("D:\Knock\Disease-Detection-based-on-Symptoms\Disease-Detection-based-on-Symptoms-master\Dataset\dis_sym_dataset_comb.csv") # Disease combination
df_norm = pd.read_csv("D:\Knock\Disease-Detection-based-on-Symptoms\Disease-Detection-based-on-Symptoms-master\Dataset\dis_sym_dataset_norm.csv") # Individual Disease
Y = df_norm.iloc[:, 0:1]
X = df_norm.iloc[:, 1:]
# List of symptoms
dataset_symptoms = list(X.columns)
diseases = list(set(Y['label_dis']))
diseases.sort()

# Taking symptoms from user as input
# Preprocessing the input symtoms 
user_symptoms = str(input("\nPlease enter symptoms separated by comma(,):\n")).lower().split(',')
processed_user_symptoms=[]
for sym in user_symptoms:
    sym=sym.strip()
    sym=sym.replace('-',' ')
    sym=sym.replace("'",'')
    sym = ' '.join([lemmatizer.lemmatize(word) for word in splitter.tokenize(sym)])
    processed_user_symptoms.append(sym)

# Taking each user symptom and finding all its synonyms and appending it to the pre-processed symptom string
user_symptoms = []
for user_sym in processed_user_symptoms:
    user_sym = user_sym.split()
    str_sym = set()
    for comb in range(1, len(user_sym)+1):
        for subset in combinations(user_sym, comb):
            subset=' '.join(subset)
            subset = synonyms(subset) 
            str_sym.update(subset)
    str_sym.add(' '.join(user_sym))
    user_symptoms.append(' '.join(str_sym).replace('_',' '))
# query expansion performed by joining synonyms found for each symptoms initially entered
print("After query expansion done by using the symptoms entered")
print(user_symptoms)

"""The below procedure is performed in order to show the symptom synonmys found for the symptoms entered by the user.

The symptom synonyms and user symptoms are matched with the symptoms present in dataset. Only the symptoms which matches the symptoms present in dataset are shown back to the user.
"""

# Loop over all the symptoms in dataset and check its similarity score to the synonym string of the user-input 
# symptoms. If similarity>0.5, add the symptom to the final list
found_symptoms = set()
for idx, data_sym in enumerate(dataset_symptoms):
    data_sym_split=data_sym.split()
    for user_sym in user_symptoms:
        count=0
        for symp in data_sym_split:
            if symp in user_sym.split():
                count+=1
        if count/len(data_sym_split)>0.5:
            found_symptoms.add(data_sym)
found_symptoms = list(found_symptoms)

# Print all found symptoms
print("Top matching symptoms from your search!")
for idx, symp in enumerate(found_symptoms):
    print(idx,":",symp)

# Show the related symptoms found in the dataset and ask user to select among them
select_list = input("\nPlease select the relevant symptoms. Enter indices (separated-space):\n").split()

# Find other relevant symptoms from the dataset based on user symptoms based on the highest co-occurance with the
# ones that is input by the user
dis_list = set()
final_symp = [] 
counter_list = []
for idx in select_list:
    symp=found_symptoms[int(idx)]
    final_symp.append(symp)
    dis_list.update(set(df_norm[df_norm[symp]==1]['label_dis']))
   
for dis in dis_list:
    row = df_norm.loc[df_norm['label_dis'] == dis].values.tolist()
    row[0].pop(0)
    for idx,val in enumerate(row[0]):
        if val!=0 and dataset_symptoms[idx] not in final_symp:
            counter_list.append(dataset_symptoms[idx])

# Symptoms that co-occur with the ones selected by user              
dict_symp = dict(Counter(counter_list))
dict_symp_tup = sorted(dict_symp.items(), key=operator.itemgetter(1),reverse=True)

# Iteratively, suggest top co-occuring symptoms to the user and ask to select the ones applicable 
found_symptoms=[]
count=0
for tup in dict_symp_tup:
    count+=1
    found_symptoms.append(tup[0])
    if count%5==0 or count==len(dict_symp_tup):
        print("\nCommon co-occuring symptoms:")
        for idx,ele in enumerate(found_symptoms):
            print(idx,":",ele)
        select_list = input("Do you have have of these symptoms? If Yes, enter the indices (space-separated), 'no' to stop, '-1' to skip:\n").lower().split();
        if select_list[0]=='no':
            break
        if select_list[0]=='-1':
            found_symptoms = [] 
            continue
        for idx in select_list:
            final_symp.append(found_symptoms[int(idx)])
        found_symptoms = []

"""Final Symptom list"""

#Calculating TF-IDF and Cosine Similarity using matched symptoms
k = 10

print("Final list of Symptoms used for prediction are : ")
for val in final_symp:
    print(val)

"""# **Showing the list of top k diseases to the user with their prediction probabilities.**

# **For getting information about the suggested treatments, user can enter the corresponding index to know more details.**
"""

topk1=tf_idf_score(k,final_symp)
topk2=cosine_similarity(k,final_symp)
# Show top 10 highly probable disease to the user.
print(f"\nTop {k} diseases predicted based on TF_IDF Matching :\n")
i = 0
topk1_index_mapping = {}
for key, score in topk1:
  print(f"{i}. Disease : {key} \t Score : {round(score, 2)}")
  topk1_index_mapping[i] = key
  i += 1

select = input("\nMore details about the disease? Enter index of disease or '-1' to discontinue:\n")
if select!='-1':
    dis=topk1_index_mapping[int(select)]
    print()
    print(diseaseDetail(dis))

# display top k diseases predicted with cosine probablity
print(f"Top {k} disease based on Cosine Similarity Matching :\n ")
topk2_sorted = dict(sorted(topk2.items(), key=lambda kv: kv[1], reverse=True))
j = 0
topk2_index_mapping = {}
for key in topk2_sorted:
  print(f"{j}. Disease : {diseases[key]} \t Score : {round(topk2_sorted[key], 9)}")
  topk2_index_mapping[j] = diseases[key]
  j += 1

    
select = input("\nMore details about the disease? Enter index of disease or '-1' to discontinue and close the system:\n")
if select!='-1':
    dis=topk2_index_mapping[int(select)]
    print()
    print(diseaseDetail(dis))

"""# New Section
**NEURAL_NETWORK AND GAN**
"""


#importing all libraries
import neural_structured_learning as nsl
import numpy as np
import pandas as pd
import sys
import tensorflow as tf
from matplotlib import pyplot
from keras.datasets import cifar10
from keras.utils import to_categorical
from keras.models import Sequential
from keras.layers import Conv2D
from keras.layers import MaxPooling2D
from keras.layers import Dense
from keras.layers import Flatten
from keras import initializers
from keras.optimizers import SGD
#import neural_structured_learning as nsl
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import math
from sklearn.model_selection import train_test_split,cross_val_score
from imblearn.over_sampling import SMOTE

#reading Dataset and making dataframe
datat=pd.read_csv('/content/drive/My Drive/Python Project data/IR_Project/dis_sym_dataset_comb.csv')
df_new=pd.DataFrame(datat)
df_new=df_new.sample(frac=1)
#print(df_new)
Y=df_new['label_dis']
X=df_new.drop(columns='label_dis',axis=1)
total_symptoms_len=len(X.columns)
total_disease_len=len(set(Y))

#Label Encoding Class to numeric type 
#Converting class to categorical type for categorical cross entropy
lb=LabelEncoder()
Y=lb.fit_transform(Y)
Ycat=to_categorical(Y)
X=np.array(X)
Y=np.array(Y)

#importing tensorflow and keras frameworks
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from keras.utils import to_categorical
from keras.callbacks import ModelCheckpoint
from keras.callbacks import EarlyStopping

#base Model Neurel Net
def base_model():
  inputs=keras.Input(shape=(total_symptoms_len,),dtype=tf.float32,name=IMAGE_INPUT_NAME)#defining input shape and dtype 
  x=inputs
  x=keras.layers.Dense(1000,activation='relu',use_bias=True,kernel_initializer=initializers.he_normal(seed=None))(x)#Dense layer relu

  x=keras.layers.Dense(1000,activation='relu',use_bias=True,kernel_initializer=initializers.he_normal(seed=None))(x)#Dense layer relu

  outputs=keras.layers.Dense(total_disease_len,activation='softmax')(x)#output Dense layer with class size

  model=keras.Model(inputs=inputs,outputs=outputs,name='NN_sequential_model')#creating model

  #model.add(Dense(1500,activation='relu',kernel_initializer='he_uniform'))
  # model.add(Dense(500,activation='relu',use_bias=True,kernel_initializer=initializers.he_normal(seed=None)))
  # model.add(Dense(183,activation='softmax'))

  return model

def convert_to_dictionaries(image, label):
  return {IMAGE_INPUT_NAME: image, LABEL_INPUT_NAME: label}

IMAGE_INPUT_NAME = 'image'
LABEL_INPUT_NAME = 'label'
#making adversarial Configurations for training
adv_config = nsl.configs.make_adv_reg_config(
    multiplier=0.2,
    adv_step_size=0.0001
)
base_adv_model =base_model()#calling base model
#building adversiaral graphs for embedding and combining with base model
adv_model = nsl.keras.AdversarialRegularization(
    base_adv_model,
    label_keys=[LABEL_INPUT_NAME],
    adv_config=adv_config
)
train_set_for_adv_model = convert_to_dictionaries(X,Ycat)#converting it to dictionary for training adversiarial model

base_mod=base_model()
base_mod.summary()
es=tf.keras.callbacks.EarlyStopping(monitor='val_loss',mode='min',verbose=1,patience=10)#early stopping
mc = tf.keras.callbacks.ModelCheckpoint('best_model.h5', monitor='val_accuracy', mode='max', verbose=1, save_best_only=True)#saving best model
print("Normal Feed Forward Neural Network")
base_mod.compile(optimizer='adam',loss='categorical_crossentropy',metrics=['accuracy'])
history=base_mod.fit(X,Ycat,validation_split=0.2,epochs=20,verbose=1,callbacks=[es,mc])#training Neural Network
base_mod.summary()

adv_model.compile(optimizer='adam', loss='categorical_crossentropy',
                   metrics=['acc'])
es=tf.keras.callbacks.EarlyStopping(monitor='val_loss',mode='min',verbose=1,patience=10)
mc = tf.keras.callbacks.ModelCheckpoint('best_model.h5', monitor='val_categorical_accuracy', mode='max', verbose=1, save_best_only=True)
print("applied adversarial regularization on base neural network")
#adv_model.compile(optimizer='adam', loss='categorical_cross_entropy', metrics=['accuracy'])
adv_model.fit(train_set_for_adv_model,validation_split=0.2 ,epochs=15,callbacks=[es,mc])