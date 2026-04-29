import tensorflow as tf

#Converts the trained model to tensorflow lite to be run on the Pi

converter = tf.lite.TFLiteConverter.from_saved_model("model_saved")

converter.optimizations = [tf.lite.Optimize.DEFAULT]

# Keep compatibility safe
converter.target_spec.supported_ops = [
    tf.lite.OpsSet.TFLITE_BUILTINS
]

tflite_model = converter.convert()

with open("model.tflite", "wb") as f:
    f.write(tflite_model)