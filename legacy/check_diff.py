import pandas as pd, joblib, itertools
m = joblib.load('fraud_detection/fraud_detection_model.pkl')
parts = []
for ch in pd.read_csv('fraud_detection/AIML Dataset.csv', chunksize=500000):
    parts.append(pd.concat([ch[ch.isFraud == 1], ch[ch.isFraud == 0].sample(frac=0.01, random_state=1)]))
df = pd.concat(parts)
print('rows:', len(df), 'fraud rows:', int(df.isFraud.sum()))
for so, sd in itertools.product([1, -1], [1, -1]):
    X = df[['type','amount','oldbalanceOrg','newbalanceOrig','oldbalanceDest','newbalanceDest']].copy()
    X['balanceDiffOriginal'] = so * (df.newbalanceOrig - df.oldbalanceOrg)
    X['balanceDiffDestination'] = sd * (df.newbalanceDest - df.oldbalanceDest)
    pred = m.predict(X[list(m.feature_names_in_)])
    recall = pred[df.isFraud == 1].mean()
    fpr = pred[df.isFraud == 0].mean()
    print('orig', 'new-old' if so == 1 else 'old-new', '| dest', 'new-old' if sd == 1 else 'old-new', '| fraud caught: %.1f%%' % (100*recall), '| legit wrongly flagged: %.1f%%' % (100*fpr))
