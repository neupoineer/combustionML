import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split

import tensorflow as tf
from keras.models import Model
from keras.layers import Dense, Input
from keras.callbacks import ModelCheckpoint

from resBlock import res_block
from data_reader import read_data
#from writeANNProperties import writeANNProperties


# define the labels
labels = ['T','CH4','O2','CO2','CO','H2O','H2','OH','PVs']
# labels = ['T','CH4']

# read in the data
X, y, df, in_scaler, out_scaler = read_data('./data/fpv_df.H5',labels = labels)

# split into train and test data
X_train, X_test, y_train, y_test = train_test_split(X,y, test_size=0.1)


# %%
print('set up ANN')
# ANN parameters
dim_input = 2
dim_label = y_train.shape[1]
n_neuron = 100
batch_size = 1024*32
epochs = 1_000
vsplit = 0.1
batch_norm = False

# This returns a tensor
inputs = Input(shape=(dim_input,))

# a layer instance is callable on a tensor, and returns a tensor
x = Dense(n_neuron, activation='relu')(inputs)

# less then 2 res_block, there will be variance
x = res_block(x, n_neuron, stage=1, block='a', bn=batch_norm)
x = res_block(x, n_neuron, stage=1, block='b', bn=batch_norm)

predictions = Dense(dim_label, activation='linear')(x)

model = Model(inputs=inputs, outputs=predictions)
model.compile(loss='mse', optimizer='adam', metrics=['accuracy'])

# checkpoint (save the best model based validate loss)
filepath = "./tmp/weights.best.cntk.hdf5"

checkpoint = ModelCheckpoint(filepath,
                             monitor='val_loss',
                             verbose=1,
                             save_best_only=True,
                             mode='min',
                             period=10)

callbacks_list = [checkpoint]

# fit the model
history = model.fit(
    X_train, y_train,
    epochs=epochs,
    batch_size=batch_size,
    validation_split=vsplit,
    verbose=2,
    callbacks=callbacks_list,
    shuffle=True)

# loss
fig = plt.figure()
plt.semilogy(history.history['loss'])
if vsplit:
    plt.semilogy(history.history['val_loss'])
plt.title('mse')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'test'], loc='upper right')
plt.show()


#%%
model.load_weights("./tmp/weights.best.cntk.hdf5")
# cntk.combine(model.outputs).save('mayerTest.dnn')

# # %%
# ref = df.loc[df['p'] == 40]
# x_test = in_scaler.transform(ref[['p', 'he']])

predict_val = model.predict(X_test)

X_test_df = pd.DataFrame(in_scaler.inverse_transform(X_test),columns=['f','PV'])
y_test_df = pd.DataFrame(out_scaler.inverse_transform(y_test),columns=labels)

sp='CH4'

predict_df = pd.DataFrame(out_scaler.inverse_transform(predict_val), columns=labels)

plt.figure()
plt.plot(X_test_df['f'], y_test_df[sp], 'r:')
plt.plot(X_test_df['f'], predict_df[sp], 'b-')
plt.show()

plt.figure()
plt.title('Error of %s ' % sp)
plt.plot((y_test_df[sp] - predict_df[sp]) / y_test_df[sp])
plt.show()

plt.figure()
plt.plot(predict_df[sp],y_test_df[sp])
plt.show()
# %%
a=(y_test_df[sp] - predict_df[sp]) / y_test_df[sp]
test_data=pd.concat([X_test_df,y_test_df],axis=1)
pred_data=pd.concat([X_test_df,predict_df],axis=1)

test_data.to_hdf('sim_check.H5',key='test')
pred_data.to_hdf('sim_check.H5',key='pred')