from gensim.models import KeyedVectors
import numpy as np
import re
import math
import json
import os
import jieba
from sklearn.decomposition import PCA
import xlrd


# 数据处理策略
def data_process(text, strategypath):
    with open(strategypath, 'rb') as fp:
        fileJson = json.load(fp)

    use_flag = fileJson['usestrategy']
    if use_flag:
        strategy_name = fileJson['name']
        sentence_num = fileJson['sentence_num']
        regular_exp = fileJson['regular']
        ignore_word = fileJson['ignore_word']
    else:
        return -1
    print("we are using %s parse the text.", strategy_name)
    # 第一步将文本中的忽略词去掉
    # 第二部去掉小于句子长度要求的句子
    # 处理正则表达式
    temp_text = []
    for sent in text:
        if len(sent) < sentence_num:
            continue
        sent = ''.join(list(filter(lambda x: not ignore_word.__contains__(x), sent)))
        for i in regular_exp:
            pattern = i['expression']
            repl = i['repl']
            sent = re.sub(pattern, repl, sent)
        if len(sent) < sentence_num:
            continue
        temp_text.append(sent)
    return temp_text


# 获取词向量
def get_w2v(word):
    # return np.random.random((300))
    if (vac.get(word) is None):
        return np.zeros((300))
    return w2v.wv[word]


# 获取所有数据的词向量
def get_content_w2v(content_list):
    # with open(stop_word, 'r', encoding='utf-8') as fi:
    #     stop_word_list = fi.read().split('\n')
    # stop_word_list.append('\n')
    # stop_word_list.append(' ')

    stop_word_list = []
    res_list = []
    res_content = []
    for item in content_list:
        word_list = list(jieba.cut(item))
        word_list = [word for word in word_list if word not in stop_word_list]
        if len(word_list) == 0:
            continue
        w2v_item_matrix = np.zeros(shape=(len(word_list), 300))
        for i in range(len(word_list)):
            w2v_item_matrix[i] = get_w2v(word_list[i])
        res = w2v_item_matrix.sum(axis=0) / len(word_list)
        res_list.append(res)
        res_content.append(item)
    return np.asarray(res_list), res_content


# 创建文本的词频字典
def create_looktable(sents):
    vocab = {}
    new_sentence_list = []
    for line in sents:
        try:
            word_list = list(jieba.cut(line))
            new_sentence_list.append(word_list)
            for word in word_list:
                if word in vocab:
                    vocab[word] += 1
                else:
                    vocab[word] = 1
        except:
            continue
    return vocab, new_sentence_list


# 获取词频
def get_word_frequency(word_text, looktable):
    if word_text in looktable:
        return looktable[word_text]
    else:
        return 1.


# 句子向量
def sentence_to_vec(sentences, embedding_size, looktable, a=1e-3):
    # with open(stop_word, 'r', encoding='utf-8') as fi:
    #     stop_word_list = fi.read().split('\n')
    # stop_word_list.append('\n')
    # stop_word_list.append(' ')

    stop_word_list = []

    sentence_set = []
    for sentence in sentences:

        try:
            vs = np.zeros(embedding_size)  # add all word2vec values into one vector for the sentence
            sentence_len = len(sentence)
            word_list = list(jieba.cut(sentence))
            # word_list = [word for word in word_list if word not in stop_word_list]
            for word in word_list:
                a_value = a / (a + get_word_frequency(word, looktable))  # smooth inverse frequency, SIF
                vs = np.add(vs, np.multiply(a_value, get_w2v(word)))  # vs += sif * word_vector
            vs = np.divide(vs, sentence_len)  # weighted average
            sentence_set.append(vs)  # add to our existing re-calculated set of sentences
        except:
            continue

    # calculate PCA of this sentence
    pca = PCA()
    pca.fit(np.array(sentence_set))
    u = pca.components_[0]  # the PCA vector
    u = np.multiply(u, np.transpose(u))

    # pad the vector?  (occurs if we have less sentences than embeddings_size)
    if len(u) < embedding_size:
        for i in range(embedding_size - len(u)):
            if i > 0:
                u = np.append(u, 0)  # add needed extension for multiplication below
    # resulting sentence vectors, vs = vs - uuT * vs
    sentence_vecs = []
    for vs in sentence_set:
        sub = np.multiply(u, vs)
        sentence_vecs.append(np.subtract(vs, sub))

    return np.asarray(sentence_vecs)


# 句子向量
def new_sentence_to_vec(sentences, embedding_size):
    sentence_set = []
    for sentence in sentences:
        vs = np.zeros(embedding_size)  # add all word2vec values into one vector for the sentence
        # word_list = list(jieba.cut(sentence))
        # word_list = [word for word in word_list if word not in stop_word_list]
        for word in sentence:
            vs = np.add(vs, get_w2v(word))  # vs += sif * word_vector
        vs = np.divide(vs, len(sentence))  # weighted average
        sentence_set.append(vs)  # add to our existing re-calculated set of sentences

    return np.asarray(sentence_set)


# 计算余弦夹角
def cos_sent(a, b):
    if len(a) != len(b):
        return None
    part_up = 0.0
    a_sq = 0.0
    b_sq = 0.0
    for a1, b1 in zip(a, b):
        part_up += a1 * b1
        a_sq += a1 ** 2
        b_sq += b1 ** 2
    part_down = math.sqrt(a_sq * b_sq)
    if part_down == 0.0:
        return None
    else:
        return part_up / part_down


# 利用余弦相似度进行集合聚类
def get_similarity_cluster(root, data_vec, cluster_max, cluster_min, threshold):
    if not os.path.exists(root):
        os.makedirs(root)

    cluster_num = 0
    while (data_vec.shape[0] > 1):
        print(data.__len__())
        delete_index = []
        i = data_vec[0]
        delete_index.append(0)
        temp = []
        num = 0
        for j in range(1, data_vec.shape[0]):
            similarity = cos_sent(i, data_vec[j])
            if (similarity is not None) and (similarity > threshold):
                num += 1
                temp.append(j)
        # print(data_vec.shape[0],data.__len__(),num)
        delete_index.extend(temp)
        if num > cluster_max:
            fw = open(root + "cluster_" + str(cluster_num) + "_" + str(num) + ".txt", 'w', encoding='utf-8')
            cluster_num += 1
            for ele in delete_index:
                fw.write(data[ele])
            fw.close()
        if num < cluster_min:
            fw = open(root + str(cluster_min) + "_" + "cluster_" + str(-1) + ".txt", 'a', encoding='utf-8')
            for ele in delete_index:
                fw.write(data[ele])
            fw.write("##########################################\n")
            fw.close()
        for ele in reversed(delete_index):
            try:
                data_vec = np.delete(data_vec, ele, axis=0)
                del data[ele]
            except:
                print(delete_index, len(data), data_vec.shape[0])


# wbname==即文件名称，sheetname==工作表名称，可以为空，若为空默认第一个工作表
def readwb(wbname, sheetname):
    dataset = []
    workbook = xlrd.open_workbook(wbname)
    table = workbook.sheets()[0]
    for row in range(table.nrows):
        dataset.append(table.row_values(row)[14])
    return dataset


if __name__ == '__main__':
    # data = []  # 保存所有的客户问题数据
    # strategypath=""
    # dir = "C:/Users/Lenovo/Desktop/hubei"
    # print("read customer begin ....")
    # for root, dirs, files in os.walk(dir):
    #     for i in files:
    #         fr = open(root + '/' + i, 'r', encoding='utf-8')
    #         for j in fr.readlines():
    #             if j[0] == '1':
    #                 data.append(j[2:])
    #         fr.close()
    print("open data")
    # data = readwb("data/7-9月北京应答原始交互日志/7月-中国移动10086微信.xlsx", "智能应答日志交互明细表")
    data = readwb("data/7-9月北京应答原始交互日志/测试.xlsx", "智能应答日志交互明细表")
    print("data loaded")

    print("loading w2v......")
    w2v_path = 'data/w2v_model_YING_SEG.vec'
    # stop_word = 'stopwords.txt'
    w2v = KeyedVectors.load_word2vec_format(w2v_path)
    vac = w2v.vocab
    print("load w2v done...")

    print("read customer done ....")
    # data = data_process(sents, strategypath)
    # print("trans w2v begin ....")
    # data_vec,data_content = get_content_w2v(data)
    # print("trans w2v done .....")
    print("trans sentencevec begin ....")
    lookable, newdata = create_looktable(data)
    sentence_vecs = new_sentence_to_vec(newdata, 300, lookable)
    print("trans sentencevec done .....")
    print("cluster begin ....")
    # get_similarity_cluster("cluster/", data_content, data_vec, 200,20, 0.9)
    get_similarity_cluster("cluster_sentence/", sentence_vecs, 200, 50, 0.9)
    print("cluster done .....")
