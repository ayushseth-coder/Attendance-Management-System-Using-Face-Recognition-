import tensorflow as tf
print("========================================")
print("Num GPUs Available: ", len(tf.config.list_physical_devices('GPU')))
if len(tf.config.list_physical_devices('GPU')) > 0:
    for gpu in tf.config.list_physical_devices('GPU'):
        print("GPU Details:", gpu)
else:
    print("TensorFlow did not detect a compatible NVIDIA GPU with CUDA installed.")
print("========================================")
