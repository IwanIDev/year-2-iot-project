import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import os


# Sets up the basics for our image classifier.
# 224x224 pixel images, processing them in batches of 32,
# training for 15 epochs initially.
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 15
DATASET_PATH = "waste_dataset"  # 

#Paths to training, validation, and test data folders.
train_dir = os.path.join(DATASET_PATH, "train")
val_dir = os.path.join(DATASET_PATH, "val")
test_dir = os.path.join(DATASET_PATH, "test")


# Loads the images resizing to 224 x 224
train_ds = tf.keras.utils.image_dataset_from_directory(
    train_dir,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE
)

val_ds = tf.keras.utils.image_dataset_from_directory(
    val_dir,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE
)

test_ds = tf.keras.utils.image_dataset_from_directory(
    test_dir,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    shuffle=False
)

# Gets the class names
class_names = train_ds.class_names
num_classes = len(class_names)

print("Classes:", class_names)

# Performance boost - prefetching helps load data faster during training.
AUTOTUNE = tf.data.AUTOTUNE
train_ds = train_ds.prefetch(buffer_size=AUTOTUNE)
val_ds = val_ds.prefetch(buffer_size=AUTOTUNE)


# Builds the model using MobileNetV3Small as a base, pre-trained
# model that already knows how to recognise images from ImageNet. 
# It is freezed so it doesn't change during initial training, and add our own classifier on top.

base_model = tf.keras.applications.MobileNetV3Small(
    input_shape=(224, 224, 3),
    include_top=False,
    weights="imagenet"
)

base_model.trainable = False  # freeze base model

# Builds the custom classifier head based on the base model
x = base_model.output
x = layers.GlobalAveragePooling2D()(x)
x = layers.BatchNormalization()(x)
x = layers.Dense(128, activation="relu")(x)
x = layers.Dropout(0.3)(x)
outputs = layers.Dense(num_classes, activation="softmax")(x)

model = keras.Model(inputs=base_model.input, outputs=outputs)


# Tells Keras how to measure success and how to improve.
# Using Adam optimizer, sparse categorical crossentropy for loss , and tracking accuracy.

model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=1e-3),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

model.summary()

# Trains the feeds the dataset into the model and trains it.

history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS,
)


# Unfreeze the base model and train everything
# together with a much smaller learning rate. This helps the model adapt specifically
# to our waste classification task.
base_model.trainable = True

model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=1e-5),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=10
)


# Evaluates the model on the test data to see how it performs
test_loss, test_acc = model.evaluate(test_ds)


# Saves the trained model.
model.save("model_saved")